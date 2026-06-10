#!/usr/bin/env python3
"""
Extract individual figures from academic PDFs using caption-anchored
drawing density refinement.

Algorithm (V4):
  1. Scan all pages for "Fig. N" caption text blocks
  2. For each caption, the figure is ABOVE it
  3. Determine initial bounds from caption position + page layout
  4. Refine bounds using drawing density — vector graphics cells
     tighten the crop, EXCLUDING only full-width body paragraphs
     (not figure-internal labels or example dialogues)
  5. Render only the refined region at target DPI

Key insight from paper-ingestion study:
  - Academic PDF figures are vector graphics (drawings), not raster images
  - Figure captions are detectable via text extraction
  - Figure-internal text (axis labels, dialogue examples, taxonomy labels)
    must NOT be excluded from the crop region
  - Only genuine body paragraphs (full-width, substantial text) should
    constrain the crop boundaries

Usage:
  python extract_figures.py <pdf_path> [--dpi 200] [--output figures_b64.json]
  python extract_figures.py <pdf_path> --save-images  # also save PNGs
"""

import fitz
import re
import json
import base64
import argparse
import sys
import collections
from pathlib import Path


def _is_body_paragraph(block, text_area_w):
    """
    Determine if a text block is a genuine body paragraph (should constrain
    figure cropping) vs figure-internal content (should be included).

    Body paragraph criteria:
      - Spans >70% of the text area width (full-width paragraph)
      - Contains substantial text (>150 characters)
    """
    text = block[4].strip() if len(block) > 4 else ''
    if not text:
        return False
    w = block[2] - block[0]
    return w > text_area_w * 0.7 and len(text) > 150


def extract_figure_regions(doc, dpi=200):
    """
    Extract individual figures from a PDF document.

    Args:
        doc: fitz.Document (already opened)
        dpi: rendering DPI (default 200)

    Returns:
        list of dicts: page, fig_num, caption, method, bbox_pts,
                       width, height, dpi, base64
    """
    figures = []

    for pg_num in range(doc.page_count):
        page = doc[pg_num]
        pw = page.rect.width
        ph = page.rect.height
        text_area_w = pw - 144  # ~468 pts for letter paper

        all_blocks = page.get_text('blocks')

        # === Step 1: Find caption blocks ===
        captions = []
        for b in all_blocks:
            if b[6] != 0:  # not text type
                continue
            text = b[4].strip() if len(b) > 4 else ''
            # Match "Fig. 1", "Fig 1", "Figure 1",
            # "Fig. 1a", "Fig. 3(b)", "Figure 2c"
            m = re.match(r'Fig(?:\.|ure)?\s*(\d+[a-z]?(?:\s*\([a-z]\))?)', text)
            if m:
                captions.append({
                    'num': m.group(1),
                    'bbox': b[:4],
                    'text': text[:200]
                })

        if not captions:
            continue

        # === Step 2: Identify body paragraphs ===
        body_paragraphs = []
        for b in all_blocks:
            if b[6] != 0:
                continue
            if _is_body_paragraph(b, text_area_w):
                body_paragraphs.append(b[:4])

        # === Step 3: Build drawing density grid ===
        grid = {}
        cell_w = cell_h = None
        drawings = page.get_drawings()
        if drawings:
            GRID = 50
            cell_w = pw / GRID
            cell_h = ph / GRID
            for d in drawings:
                rect = d['rect']
                cx = (rect[0] + rect[2]) / 2
                cy = (rect[1] + rect[3]) / 2
                gx = int(cx / cell_w)
                gy = int(cy / cell_h)
                if 0 <= gx < GRID and 0 <= gy < GRID:
                    grid[(gx, gy)] = grid.get((gx, gy), 0) + 1

        sorted_captions = sorted(captions, key=lambda c: c['bbox'][1])

        # === Step 4: Process each caption ===
        for cap in sorted_captions:
            cap_x0, cap_y0, cap_x1, cap_y1 = cap['bbox']

            # Figure bottom = just above caption
            fig_bottom = cap_y0 - 2

            # --- Determine top bound ---
            fig_top = 55  # default top margin

            # Body paragraphs above this caption constrain the top
            for (_bx0, _by0, _bx1, by1) in body_paragraphs:
                if by1 < cap_y0 - 5:
                    fig_top = max(fig_top, by1 + 6)

            # Previous figure captions on the same page constrain the top
            for prev in sorted_captions:
                if prev['bbox'][3] < fig_top and prev != cap:
                    fig_top = max(fig_top, prev['bbox'][3] + 8)

            # --- Determine horizontal bounds from drawing extent ---
            # Caption width is unreliable: many full-width figures have
            # short centered captions (e.g., "Fig. 2. ..." at 192pt wide
            # but the actual diagram spans the full text area).
            # Instead, use the drawing extent in the vertical figure band
            # to decide full-width vs single-column.
            method = 'caption'

            if grid and cell_w:
                # Helper: check if a grid cell overlaps a body paragraph
                def cell_in_body(gx, gy):
                    cx = (gx + 0.5) * cell_w
                    cy = (gy + 0.5) * cell_h
                    for (bx0, by0, bx1, by1) in body_paragraphs:
                        if (bx0 - 3 <= cx <= bx1 + 3 and
                            by0 - 3 <= cy <= by1 + 3):
                            return True
                    return False

                # Collect ALL drawing cells in the vertical figure band
                # (use full text-area width for the initial search)
                band_cells = []
                for (gx, gy), count in grid.items():
                    cx = (gx + 0.5) * cell_w
                    cy = (gy + 0.5) * cell_h
                    if (65 <= cx <= pw - 65 and
                        fig_top <= cy <= fig_bottom and
                        count > 0 and
                        not cell_in_body(gx, gy)):
                        band_cells.append((gx, gy, cx, cy))

                if len(band_cells) >= 5:
                    # Determine horizontal extent from actual drawings
                    draw_left = min(cx for _, _, cx, _ in band_cells)
                    draw_right = max(cx for _, _, cx, _ in band_cells)
                    draw_width = draw_right - draw_left

                    if draw_width > text_area_w * 0.7:
                        # Drawings span the full text area → full-width figure
                        fig_left = 65
                        fig_right = pw - 65
                    else:
                        # Narrow drawings → single-column figure
                        draw_center = (draw_left + draw_right) / 2
                        half_col = text_area_w / 4 + 5
                        fig_left = max(65, draw_center - half_col)
                        fig_right = min(pw - 65, draw_center + half_col)

                    # Density refinement: use actual drawing bounding
                    # boxes, NOT grid cell centers.  Grid centers miss
                    # edges of wide-spanning drawings (e.g. a rect from
                    # x=289 to x=478 has center at x=384, so grid cells
                    # only go to gx=31 — 100px short of the true edge).
                    band_cell_set = {(gx, gy) for gx, gy, _, _ in band_cells}

                    draw_x0s, draw_y0s, draw_x1s, draw_y1s = [], [], [], []
                    for d in drawings:
                        rect = d['rect']
                        cx = (rect[0] + rect[2]) / 2
                        cy = (rect[1] + rect[3]) / 2
                        gx = int(cx / cell_w)
                        gy = int(cy / cell_h)
                        if ((gx, gy) in band_cell_set and
                            not cell_in_body(gx, gy)):
                            draw_x0s.append(rect[0])
                            draw_y0s.append(rect[1])
                            draw_x1s.append(rect[2])
                            draw_y1s.append(rect[3])

                    if draw_x0s and len(draw_x0s) >= 5:
                        pad_pts = 6  # 6pt padding on each side
                        nl = max(40, min(draw_x0s) - pad_pts)
                        nt = max(40, min(draw_y0s) - pad_pts)
                        nr = min(pw - 40, max(draw_x1s) + pad_pts)
                        nb = min(fig_bottom, max(draw_y1s) + pad_pts)

                        if nb - nt > 50 and nr - nl > 80:
                            fig_left, fig_top = nl, nt
                            fig_right, fig_bottom = nr, nb
                            method = 'density'
                else:
                    # Not enough drawings — fall back to caption-based
                    cap_w = cap_x1 - cap_x0
                    if cap_w > text_area_w * 0.55:
                        fig_left, fig_right = 65, pw - 65
                    else:
                        col_center = (cap_x0 + cap_x1) / 2
                        if col_center < pw / 2:
                            fig_left, fig_right = 65, pw / 2 + 5
                        else:
                            fig_left, fig_right = pw / 2 - 5, pw - 65
            else:
                # No drawings at all — fall back to caption-based
                cap_w = cap_x1 - cap_x0
                if cap_w > text_area_w * 0.55:
                    fig_left, fig_right = 65, pw - 65
                else:
                    col_center = (cap_x0 + cap_x1) / 2
                    if col_center < pw / 2:
                        fig_left, fig_right = 65, pw / 2 + 5
                    else:
                        fig_left, fig_right = pw / 2 - 5, pw - 65

            # --- Text-block boundary refinement (drawing-sparse only) ---
            # When no vector drawings anchor the figure region (text-only
            # figures like taxonomy trees, tables, code listings), the
            # body-paragraph-based fig_top may be too conservative (pushed
            # too far down by a paragraph above the figure).
            #
            # This refinement checks whether a cluster of non-body text
            # blocks exists above fig_top — if so, the figure likely
            # extends upward beyond the body-paragraph boundary.
            #
            # Safety: ONLY runs when method == 'caption' (no drawing data),
            #         and requires >= 5 clustered blocks to avoid single
            #         false positives (page numbers, running headers).
            if method == 'caption':
                above_blocks = []
                for b in all_blocks:
                    if (b[6] == 0  # text block
                        and 70 <= b[3] < fig_top - 15  # above current top, below header
                        and not _is_body_paragraph(b, text_area_w)  # not body text
                        and 65 <= b[0] <= pw - 65):  # within text column
                        above_blocks.append(b)

                if len(above_blocks) >= 5:
                    # A substantial cluster of non-body text blocks exists
                    # above fig_top — figure content is being excluded.
                    text_top = min(b[1] for b in above_blocks)
                    text_bot = max(b[3] for b in above_blocks)
                    cluster_height = text_bot - text_top

                    if cluster_height > 30 and fig_top - text_top > 20:
                        # The cluster spans meaningful vertical space and
                        # starts well above fig_top. Pull fig_top up.
                        # Constrain to not re-include body paragraphs:
                        for (_bx0, _by0, _bx1, by1) in body_paragraphs:
                            if by1 < text_top - 5:
                                fig_top = max(by1 + 6, text_top - 6)
                                break
                        else:
                            fig_top = text_top - 6
                        fig_top = max(70, fig_top)

            # --- Clamp and validate ---
            fig_left = max(40, fig_left)
            fig_top = max(40, fig_top)
            fig_right = min(pw - 40, fig_right)
            fig_bottom = min(ph - 40, fig_bottom)

            if fig_bottom - fig_top < 50 or fig_right - fig_left < 80:
                continue

            # --- Render ---
            clip = fitz.Rect(fig_left, fig_top, fig_right, fig_bottom)
            pix = page.get_pixmap(dpi=dpi, clip=clip)

            figures.append({
                'page': pg_num + 1,
                'fig_num': cap['num'],
                'caption': cap['text'],
                'method': method,
                'bbox_pts': (fig_left, fig_top, fig_right, fig_bottom),
                'width': pix.width,
                'height': pix.height,
                'dpi': dpi,
                'base64': base64.b64encode(pix.tobytes('png')).decode('ascii')
            })

    return figures


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Extract individual figures from academic PDFs via '
                    'caption-anchored drawing density refinement'
    )
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('--dpi', type=int, default=200,
                        help='Rendering DPI (default: 200)')
    parser.add_argument('--output', '-o', default=None,
                        help='Output JSON path (default: <pdf_dir>/figures_b64.json)')
    parser.add_argument('--save-images', action='store_true',
                        help='Also save individual PNG files')
    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f'Error: PDF not found: {pdf_path}', file=sys.stderr)
        sys.exit(1)

    output_path = (Path(args.output) if args.output
                   else pdf_path.parent / 'figures_b64.json')

    doc = fitz.open(str(pdf_path))
    figures = extract_figure_regions(doc, dpi=args.dpi)
    doc.close()

    if not figures:
        print('Warning: No figures detected. The PDF may use non-standard '
              'caption formats or have no figures with "Fig." captions.',
              file=sys.stderr)
        with open(output_path, 'w') as f:
            json.dump({'figures': []}, f)
        sys.exit(0)

    summary = []
    total_kb = 0
    n_density = 0
    for f in figures:
        kb = len(f['base64']) / 1024
        total_kb += kb
        if f['method'] == 'density':
            n_density += 1
        summary.append({
            'page': f['page'],
            'fig_num': f['fig_num'],
            'width': f['width'],
            'height': f['height'],
            'dpi': f['dpi'],
            'method': f['method'],
            'size_kb': round(kb, 1),
        })

    n_caption = len(figures) - n_density
    print(f'Extracted {len(figures)} figures '
          f'(density: {n_density}, caption: {n_caption}, '
          f'total {total_kb:.0f} KB base64):')
    for s in summary:
        print(f"  Fig {s['fig_num']} (p{s['page']}, {s['method']}): "
              f"{s['width']}x{s['height']}px, {s['size_kb']} KB")

    with open(output_path, 'w') as f:
        json.dump({
            'figures': figures,
            'summary': summary,
            'total_size_kb': round(total_kb, 1),
        }, f)
    print(f'\nSaved to: {output_path}')

    if args.save_images:
        img_dir = output_path.parent / 'extracted_figures'
        img_dir.mkdir(exist_ok=True)
        for f in figures:
            img_bytes = base64.b64decode(f['base64'])
            fname = f"fig_{f['fig_num']}_p{f['page']}_{f['method']}.png"
            with open(img_dir / fname, 'wb') as fout:
                fout.write(img_bytes)
        print(f'Saved individual PNGs to: {img_dir}')


if __name__ == '__main__':
    main()
