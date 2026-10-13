# Inline KaTeX into a reading-note HTML, replacing the jsdelivr CDN tags so
# formulas render fully offline. Uses the pre-built asset assets/katex_inline.html
# (no network needed). Idempotent: files already inlined are skipped.
#
# Usage:
#   python inline_katex.py <note.html>        # single file
#   python inline_katex.py <notes-directory>  # every .html in the directory
import os, re, sys

os.environ['PYTHONIOENCODING'] = 'utf-8'
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET = os.path.join(SKILL, 'assets', 'katex_inline.html')

CDN_MARK = 'cdn.jsdelivr.net/npm/katex'
pat_link = re.compile(r'<link[^>]*katex\.min\.css[^>]*>\s*', re.I)
pat_js1 = re.compile(r'<script[^>]*katex\.min\.js[^>]*>\s*</script>\s*', re.I)
pat_js2 = re.compile(r'<script[^>]*auto-render\.min\.js[^>]*>\s*</script>\s*', re.I)

def process(path, block):
    with open(path, encoding='utf-8') as f:
        h = f.read()
    if 'KaTeX 0.16.11 inlined' in h:
        print(f'[SKIP] {os.path.basename(path)}: already inlined')
        return
    if CDN_MARK not in h:
        print(f'[SKIP] {os.path.basename(path)}: no KaTeX CDN reference')
        return
    h = pat_js2.sub('', h)
    h = pat_js1.sub('', h)
    h, n = pat_link.subn(lambda m: block + '\n', h, count=1)
    if n == 0 or CDN_MARK in h:
        print(f'[WARN] {os.path.basename(path)}: KaTeX reference still present, NOT written')
        return
    with open(path, 'w', encoding='utf-8') as f:
        f.write(h)
    print(f'[OK] {os.path.basename(path)}: KaTeX inlined ({os.path.getsize(path)//1024}KB total)')

def main():
    with open(ASSET, encoding='utf-8') as f:
        block = f.read().strip()
    target = sys.argv[1]
    files = [target] if os.path.isfile(target) else [
        os.path.join(target, f) for f in sorted(os.listdir(target)) if f.endswith('.html')]
    for p in files:
        process(p, block)

if __name__ == '__main__':
    main()
