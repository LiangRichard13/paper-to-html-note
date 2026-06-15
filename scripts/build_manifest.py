#!/usr/bin/env python3
"""
Build manifest.json for the reading notes index page.

Usage:
    python build_manifest.py [directory]     # Scan directory, write manifest.json there
    python build_manifest.py                 # Scan current directory

The generated manifest.json is read by index.html to render the card-based catalog.
"""
import sys, os, json, re
from datetime import datetime
from pathlib import Path


def extract_metadata(filepath: str) -> dict:
    """Extract metadata from a reading note HTML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    meta = {'annotation_count': 0, 'note_previews': []}

    # ---- Primary: read <meta> tags (new template format) ----
    for tag in re.findall(r'<meta name="paper-([^"]+)" content="([^"]*)"', html):
        key, val = tag[0], tag[1].strip()
        if val:
            if key == 'type': meta['paper_type'] = val
            elif key == 'title': meta['paper_title'] = val
            elif key in ('authors','venue','date','institution','method','key-finding'):
                meta[key.replace('-','_')] = val

    # ---- Title (from <title> tag) ----
    m = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
    if m:
        title = m.group(1).strip()
        title = re.sub(r'论文精读[：:]\s*', '', title)
        title = re.sub(r'Paper Reading[：:]\s*', '', title)
        if title and title != '[PAPER_TITLE]':
            meta['title'] = title

    # ---- Annotations (from embedded <script>) ----
    m = re.search(r'<script id="ppr-annotation-data"[^>]*>(.*?)</script>', html, re.DOTALL)
    if m:
        try:
            annotations = json.loads(m.group(1))
            if annotations:
                meta['annotation_count'] = len(annotations)
                previews = []
                for a in annotations:
                    n = a.get('note','').strip()
                    if n: previews.append(n[:100])
                if not previews:
                    for a in annotations:
                        t = a.get('text','').strip()
                        if t: previews.append(t[:100])
                meta['note_previews'] = previews[:3]
        except: pass

    # If no title found, use filename
    if not meta.get('title') and not meta.get('paper_title'):
        meta['title'] = os.path.splitext(os.path.basename(filepath))[0]

    return meta


def build_manifest(root_dir: str, template: str = None, output: str = None):
    """Scan directory recursively, build index.html with inline data."""
    root = Path(root_dir).resolve()

    if template:
        template_path = Path(template).resolve()
    else:
        script_dir = Path(__file__).resolve().parent
        template_path = script_dir.parent / 'assets' / 'index-template.html'
    if not template_path.exists():
        print('ERROR: template not found at', template_path, file=sys.stderr)
        sys.exit(1)

    notes = []
    html_files = sorted(root.rglob('*.html'))

    for f in html_files:
        # Skip index files and templates
        if f.name in ('index.html', 'index-template.html', 'template.html', 'template_en.html'):
            continue
        try:
            rel_path = str(f.resolve().relative_to(root))
        except ValueError:
            rel_path = f.name

        folder = str(Path(rel_path).parent) if Path(rel_path).parent != Path('.') else '.'
        folder = folder.replace('\\', '/')

        try:
            meta = extract_metadata(str(f))
        except Exception as e:
            print(f'  WARNING: Failed to parse {rel_path}: {e}', file=sys.stderr)
            meta = {'title': f.stem}

        meta['path'] = rel_path
        meta['folder'] = folder

        title = meta.get('paper_title') or meta.get('title') or f.stem
        count = meta.get('annotation_count', 0)
        ptype = meta.get('paper_type', '?')
        print(f'  {rel_path}')
        print(f'    "{title[:60]}"  [{ptype}]  {count} annotations')

        notes.append(meta)

    manifest = {
        'generated': datetime.now().isoformat(),
        'root': '.',
        'note_count': len(notes),
        'notes': notes,
    }

    # Read template and inject data
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()

    manifest_json = json.dumps(manifest, ensure_ascii=False)
    html = html.replace('__MANIFEST_JSON__', manifest_json)

    # Write index.html (also write manifest.json for reference)
    index_path = Path(output).resolve() if output else root / 'index.html'
    manifest_path = root / 'manifest.json'

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f'\nDone: {len(notes)} notes -> {index_path}')


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Build index.html for a folder of paper reading notes.')
    p.add_argument('dir', nargs='?', default='.', help='Directory to scan (default: .)')
    p.add_argument('--template', '-t', help='Path to index template HTML (default: assets/index-template.html)')
    p.add_argument('--output', '-o', help='Output path for index.html (default: <dir>/index.html)')
    args = p.parse_args()
    build_manifest(args.dir, template=args.template, output=args.output)
