#!/usr/bin/env python3
"""
B4 Assembly Pass 1: Figure placeholder replacement, section renumbering,
and structural validation — all programmatic, no LLM involved.

Replaces:
  <!-- FIG:N -->  →  <figure class="paper-fig"><img src="data:image/png;base64,..."/></figure>
  <span class="num">N</span>  →  <span class="num">1</span>, <span class="num">2</span>, ...

Validates:
  - Every section has <div class="section" id="...">...</div> wrapper
  - No duplicate figure references
  - No unreplaced <!-- FIG: placeholders

Usage:
  python scripts/assemble_figures.py \
    --sections sections_raw.html \
    --figures figures_b64.json \
    --meta sections_meta.json \
    --output assembled_body.html
"""

import re
import json
import argparse
import sys
from pathlib import Path
from html import escape


# ---------------------------------------------------------------------------
# Div balance validation
# ---------------------------------------------------------------------------

def validate_div_balance(body, sections_meta):
    """
    Strict div balance validation for all sections.

    Checks:
      - Each section from sections_meta has its opening tag present
      - Inner divs of each section are balanced (open == close)
      - No nested <div class="section"> inside another

    Returns (passed: bool, errors: list[str]).
    """
    errors = []

    # 1. Validate each section's div balance
    for sec in sections_meta:
        sec_id = sec.get('id', '')
        sec_num = sec.get('num', '')

        # Find this section's opening tag (raw string — .find() doesn't use regex)
        pattern = f'<div class="section" id="{sec_id}">'
        start = body.find(pattern)
        if start < 0:
            # Try without id (some auto-wrap produced id="")
            alt_pattern = f'<div class="section" id="">'
            start = body.find(alt_pattern)
            if start < 0:
                errors.append(f"Section [{sec_id}]: opening tag not found")
                continue
            else:
                # Found an id="" wrapper — likely from the old auto-wrap bug
                # Try to find the real section inside
                errors.append(f"Section [{sec_id}]: has empty id wrapper (legacy auto-wrap artifact)")

        # Find content after the opening tag's '>'
        tag_end = body.find('>', start) + 1
        if tag_end <= 0:
            errors.append(f"Section [{sec_id}]: malformed opening tag")
            continue

        # Count div depth to find matching </div>
        depth = 1
        pos = tag_end
        while depth > 0 and pos < len(body):
            next_open = body.find('<div', pos)
            next_close = body.find('</div>', pos)

            if next_close != -1 and (next_open == -1 or next_close < next_open):
                depth -= 1
                pos = next_close + 6
            elif next_open != -1:
                close_tag = body.find('>', next_open)
                if close_tag != -1 and close_tag > 0 and body[close_tag - 1] == '/':
                    pos = close_tag + 1  # self-closing <div ... />
                else:
                    depth += 1
                    pos = close_tag + 1
            else:
                break

        if depth != 0:
            errors.append(f"Section [{sec_id}]: matching </div> not found (depth={depth})")
            continue

        section_close = pos - 6  # position of the < in </div>
        section_content = body[tag_end:section_close]

        inner_opens = section_content.count('<div ')
        inner_closes = section_content.count('</div>')
        if inner_opens != inner_closes:
            errors.append(
                f"Section [{sec_id}]: div imbalance "
                f"(open={inner_opens}, close={inner_closes}, diff={inner_opens - inner_closes})"
            )

    # 2. Check for nested section divs
    nested = len(re.findall(
        r'<div class="section"[^>]*>\s*<div class="section"', body
    ))
    if nested > 0:
        errors.append(f"Found {nested} nested section div(s)")

    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# Figure replacement
# ---------------------------------------------------------------------------

def build_figure_html(fig_data):
    """Build a complete <figure class="paper-fig"> block from figure metadata."""
    b64 = fig_data.get('base64', '')
    caption = fig_data.get('caption', '')
    # Escape caption for HTML: attributes need & " < > escaped; content needs & < >
    caption_attr = escape(caption, quote=True)
    caption_html = escape(caption)
    return (
        f'<figure class="paper-fig">\n'
        f'  <img src="data:image/png;base64,{b64}"\n'
        f'       alt="{caption_attr}" loading="lazy"\n'
        f'       data-caption="{caption_attr}">\n'
        f'  <figcaption>{caption_html}</figcaption>\n'
        f'</figure>'
    )


def replace_figure_placeholders(body, figures):
    """Replace all <!-- FIG:N --> placeholders with actual <figure> blocks.

    First occurrence of each figure: full <figure> block with id="fig-N".
    Subsequent occurrences: cross-reference link to the first occurrence.
    """
    fig_map = {}
    for f in figures:
        fn = f.get('fig_num', '')
        fig_map[fn] = f

    first_seen = {}  # fig_num -> True once we've embedded it
    duplicates = []

    def replacer(match):
        fn = match.group(1).strip()
        if fn not in fig_map:
            print(f"  ⚠ Warning: <!-- FIG:{fn} --> has no matching figure data, left unchanged",
                  file=sys.stderr)
            return match.group(0)

        if fn in first_seen:
            # Duplicate — replace with cross-reference, not the full image
            duplicates.append(fn)
            caption_short = fig_map[fn].get('caption', f'Figure {fn}')[:80]
            return (
                f'<p class="fig-ref">'
                f'📊 <em>参见 <a href="#fig-{fn}">{caption_short}</a>'
                f'</em></p>'
            )
        else:
            # First occurrence — embed the full figure with anchor id
            first_seen[fn] = True
            fig_html = build_figure_html(fig_map[fn])
            # Insert id="fig-N" into the <figure> tag for cross-reference targeting
            fig_html = fig_html.replace(
                '<figure class="paper-fig">',
                f'<figure class="paper-fig" id="fig-{fn}">',
                1
            )
            return fig_html

    body = re.sub(r'<!--\s*FIG:\s*(\d+[a-z]?(?:\s*\([a-z]\))?)\s*-->', replacer, body)

    if duplicates:
        print(f"  ⚠ Deduplicated {len(duplicates)} repeated figure reference(s): "
              f"FIG:{set(duplicates)} → cross-reference links",
              file=sys.stderr)

    # Check for leftover placeholders
    leftover = re.findall(r'<!--\s*FIG:', body)
    if leftover:
        print(f"  ⚠ Warning: {len(leftover)} unreplaced FIG placeholder(s) remain",
              file=sys.stderr)

    return body


# ---------------------------------------------------------------------------
# Section numbering
# ---------------------------------------------------------------------------

def renumber_sections(body, sections_meta=None):
    """
    Renumber <span class="num">N</span> sequentially from 1.

    If sections_meta is provided, numbers are drawn from meta order
    (preserving the original section numbering from B2). Otherwise
    numbers are 1, 2, 3... in occurrence order.
    """
    if sections_meta:
        # Use meta order to determine correct numbers
        def replacer(_match):
            if not hasattr(replacer, 'counter'):
                replacer.counter = [0]
            replacer.counter[0] += 1
            idx = replacer.counter[0] - 1
            if idx < len(sections_meta):
                return f'<span class="num">{sections_meta[idx]["num"]}</span>'
            return f'<span class="num">{replacer.counter[0]}</span>'
    else:
        def replacer(_match):
            if not hasattr(replacer, 'counter'):
                replacer.counter = [0]
            replacer.counter[0] += 1
            return f'<span class="num">{replacer.counter[0]}</span>'

    body = re.sub(r'<span class="num">\d+</span>', replacer, body)
    count = replacer.counter[0] if hasattr(replacer, 'counter') else 0
    print(f"  ✓ Renumbered {count} sections")
    return body


# ---------------------------------------------------------------------------
# Structural validation
# ---------------------------------------------------------------------------

def validate_section_structure(body):
    """
    Validate that each section block is properly wrapped.
    Returns (fixed_body, warnings).

    Checks:
      - Each <h2> with .num belongs inside a .section wrapper
      - Auto-wrap orphan sections that are missing their wrapper
    """
    warnings = []

    # Find all potential section starts: <h2><span class="num">
    h2_pattern = re.compile(r'<h2>\s*<span class="num">(\d+)</span>')
    section_div = re.compile(r'<div class="section" id="([^"]+)">')

    # Strategy: split body by <div class="section" id="..."> markers,
    # then check each segment for proper closing </div>

    # First, check if body starts with a section div
    if not body.strip().startswith('<div class="section"'):
        warnings.append(
            "Body does not start with <div class=\"section\" id=\"...\">. "
            "Sections may be unwrapped."
        )
        # Try to find the first h2 and wrap everything before it
        first_h2 = re.search(r'<h2>\s*<span class="num">', body)
        if first_h2:
            warnings.append(
                f"First <h2> found at position {first_h2.start()}. "
                "Consider running with --fix to auto-wrap."
            )

    # Count opening and closing section divs
    open_sections = len(re.findall(r'<div class="section" id="[^"]+">', body))
    close_sections = len(re.findall(r'</div>', body))
    # Note: close_sections overcounts (cards, callouts also use </div>)
    # This is a rough check — detailed validation needs a proper HTML parser

    if open_sections == 0:
        warnings.append("CRITICAL: No <div class=\"section\" id=\"...\"> found!")

    for w in warnings:
        print(f"  ⚠ {w}", file=sys.stderr)

    return body, warnings


def auto_fix_sections(body, sections_meta, force_wrap=False):
    """
    Validate section wrapping. If force_wrap is True, wrap orphan h2 blocks
    that are missing their .section wrapper (legacy behavior, not recommended).

    sections_meta is a list of {id, num, title} dicts from B2.
    """
    if not sections_meta:
        return body

    if force_wrap:
        # Legacy auto-wrap behavior — wraps sections that lack a wrapper
        fixed_parts = []
        remaining = body

        for sec in sections_meta:
            sec_id = sec.get('id', '')
            sec_num = str(sec.get('num', ''))
            sec_title = sec.get('title', '')

            wrapper_pattern = re.compile(
                rf'<div class="section" id="{re.escape(sec_id)}">',
                re.DOTALL
            )
            if wrapper_pattern.search(remaining):
                start = wrapper_pattern.search(remaining).start()
                if start > 0:
                    fixed_parts.append(remaining[:start])
                    remaining = remaining[start:]
                continue

            # Not wrapped — find the h2 for this section
            h2_pattern = re.compile(
                rf'<h2>\s*<span class="num">\s*{re.escape(sec_num)}\s*</span>\s*'
                rf'([^<]*(?:<[^>]+>[^<]*)*)</h2>',
                re.DOTALL
            )
            m = h2_pattern.search(remaining)
            if not m:
                print(f"  ⚠ Section [{sec_num}] \"{sec_title}\": h2 not found, skipping",
                      file=sys.stderr)
                continue

            h2_start = m.start()
            next_h2 = re.search(
                r'<h2>\s*<span class="num">', remaining[m.end():]
            )
            section_end = (m.end() + next_h2.start()) if next_h2 else len(remaining)
            section_content = remaining[h2_start:section_end]

            wrapped = (
                f'<div class="section" id="{sec_id}">\n'
                f'{section_content}\n'
                f'</div>\n'
            )
            fixed_parts.append(remaining[:h2_start])
            fixed_parts.append(wrapped)
            remaining = remaining[section_end:]
            print(f"  ⚠ Auto-wrapped section [{sec_num}] \"{sec_title}\" "
                  f"with id=\"{sec_id}\"", file=sys.stderr)

        fixed_parts.append(remaining)
        return ''.join(fixed_parts)
    else:
        # Non-force mode: just detect and warn
        for sec in sections_meta:
            sec_id = sec.get('id', '')
            wrapper_pattern = re.compile(
                rf'<div class="section" id="{re.escape(sec_id)}">',
                re.DOTALL
            )
            if not wrapper_pattern.search(body):
                print(f"  ⚠ Section [{sec_id}] has no <div class=\"section\"> wrapper. "
                      f"Run with --force-wrap to auto-wrap.", file=sys.stderr)
        return body


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='B4 Assembly Pass 1: Replace figure placeholders, '
                    'renumber sections, validate structure'
    )
    parser.add_argument('--sections', required=True,
                        help='Path to sections_raw.html (concatenated section HTML from B3)')
    parser.add_argument('--figures', required=True,
                        help='Path to figures_b64.json (from extract_figures.py)')
    parser.add_argument('--meta', default=None,
                        help='Path to sections_meta.json (section id/num/title from B2)')
    parser.add_argument('--output', '-o', required=True,
                        help='Output path for assembled_body.html')
    parser.add_argument('--fix', action='store_true',
                        help='[DEPRECATED] Alias for --force-wrap (auto-fix structural issues)')
    parser.add_argument('--force-wrap', action='store_true',
                        help='Auto-wrap orphan sections (legacy behavior, use --validate-divs instead)')
    parser.add_argument('--validate-divs', action='store_true',
                        help='Strict div balance validation (recommended over --fix)')
    parser.add_argument('--no-renumber', action='store_true',
                        help='Skip section renumbering (use when sub-agents already numbered correctly)')
    args = parser.parse_args()

    # --- Load inputs ---
    sections_path = Path(args.sections)
    figures_path = Path(args.figures)
    output_path = Path(args.output)

    if not sections_path.exists():
        print(f"Error: sections file not found: {sections_path}", file=sys.stderr)
        sys.exit(1)
    if not figures_path.exists():
        print(f"Error: figures file not found: {figures_path}", file=sys.stderr)
        sys.exit(1)

    body = sections_path.read_text(encoding='utf-8')

    with open(figures_path, 'r', encoding='utf-8') as f:
        figures_data = json.load(f)
    figures = figures_data.get('figures', [])

    sections_meta = None
    if args.meta:
        meta_path = Path(args.meta)
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                sections_meta = json.load(f)

    print(f"Input: {len(body)} chars body, {len(figures)} figures, "
          f"{len(sections_meta) if sections_meta else 0} sections")

    # --- Pass 1: Replace figure placeholders ---
    print("--- Figure replacement ---")
    body = replace_figure_placeholders(body, figures)

    # --- Pass 2: Structural validation ---
    print("--- Structural validation ---")
    body, warnings = validate_section_structure(body)

    # --- Pass 2b: Div balance validation (if requested) ---
    if args.validate_divs and sections_meta:
        print("--- Div balance validation ---")
        passed, errors = validate_div_balance(body, sections_meta)
        if not passed:
            for e in errors:
                print(f"  ❌ {e}", file=sys.stderr)
            print("\n❌ Div balance validation FAILED.")
            print("   Fix issues in section HTML files and re-run.", file=sys.stderr)
            sys.exit(1)
        else:
            print("  ✅ All sections balanced — no nesting detected")

    # --- Pass 3: Auto-fix if requested ---
    should_wrap = args.fix or args.force_wrap
    if should_wrap and sections_meta:
        print("--- Auto-fix ---")
        body = auto_fix_sections(body, sections_meta, force_wrap=True)

    # --- Pass 4: Renumber sections (unless skipped) ---
    if not args.no_renumber:
        print("--- Renumbering ---")
        body = renumber_sections(body, sections_meta)
    else:
        print("--- Renumbering (skipped by --no-renumber) ---")

    # --- Write output ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(body, encoding='utf-8')

    # --- Summary ---
    n_fig_replaced = len(re.findall(r'<figure class="paper-fig">', body))
    n_placeholders_left = len(re.findall(r'<!--\s*FIG:', body))
    n_sections = len(re.findall(r'<div class="section" id="[^"]+">', body))

    print(f"\n✓ Assembly complete:")
    print(f"  {n_sections} sections")
    print(f"  {n_fig_replaced} figures embedded")
    if n_placeholders_left:
        print(f"  ⚠ {n_placeholders_left} unreplaced placeholders remain")
    print(f"  Output: {output_path} ({len(body)} chars)")


if __name__ == '__main__':
    main()
