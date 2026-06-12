# Index Builder

Generates a searchable, filterable index page for a folder of reading notes.

## Quick Start

```bash
python scripts/build_manifest.py ./my-notes/
```

This scans `./my-notes/` (recursively), extracts metadata from every note, and writes `./my-notes/index.html` — a self-contained catalog page.

Open `index.html` in any browser. No server needed.

## How It Works

1. `build_manifest.py` reads each `.html` file in the directory
2. Extracts metadata from `<meta name="paper-*">` tags (title, type, authors, venue, date, institution, method, key finding, subtitle)
3. Reads annotation data from `<script id="ppr-annotation-data">` (count + note previews)
4. Injects everything into `assets/index-template.html` and writes `index.html`

## CLI Options

```
python build_manifest.py [dir] [-t template] [-o output]
```

| Flag | Default | Description |
|------|---------|-------------|
| `dir` | `.` | Directory to scan recursively for notes |
| `-t, --template` | `assets/index-template.html` | Path to a custom index template |
| `-o, --output` | `<dir>/index.html` | Output path for the generated index page |

## Index Page Features

- **Search**: real-time filtering by title, authors, institution, venue
- **Tag filters**: 5 paper types (system/algorithm/survey/empirical/position)
- **File tree**: folders expand/collapse, click to scroll to matching card
- **Cards**: paper title (serif), type badge, authors/venue/date, annotation count + content preview
- **Dark/light theme**: persisted to localStorage, coordinated with reading note theme
- **Mobile responsive**: sidebar collapses to overlay below 840px

## Updating the Index

After adding or modifying notes:

```bash
python scripts/build_manifest.py ./my-notes/
```

This regenerates `index.html` with the latest data. The index page itself is static — only the embedded data changes.

## Prerequisites

- Python 3.9+ (standard library only — no extra dependencies)
- Notes must use the current template (with `<meta>` tags and `<script id="ppr-annotation-data">`)
