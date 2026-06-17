### A4.8 Quality Check

Before declaring the output complete, verify:

1. **CSS completeness**: All 6 semantic color families have both light and dark variables
2. **JS completeness**: Progress bar, back-to-top, IntersectionObserver sidebar highlight, theme toggle + localStorage persistence, print handler, entrance animation, lightbox (click-to-zoom + keyboard nav), mobile sidebar toggle, code block copy button, table horizontal scroll detection — all 10 features present
3. **Sidebar ↔ section alignment (HARD GATE)**: Every sidebar `<a href="#xxx">` must point to an existing `id="xxx"`, and every section `<div class="section" id="xxx">` (except `<div id="math">`) must have a corresponding sidebar link. Visible link text must overlap the target `<h2>` text by ≥ 4 characters. No template placeholder text may remain. If any check fails, **stop and fix the sidebar before declaring the output complete** — do not proceed to delivery. All `<details>` blocks must be `open` by default.
4. **Print styles**: `@media print` hides sidebar, top-bar, progress-bar, btt; reveals all entrance-animated sections
5. **Content accuracy**: Compare key claims and numbers against the extracted paper text
6. **No orphan components**: Every rendered component corresponds to actual paper content
7. **Language consistency**: All user-facing text is in the chosen annotation language (Chinese or English). No mixed-language annotations except preserved terms.
8. **No leftover placeholders**: No `[PLACEHOLDER_TEXT]` remains in the output. All 8 `<meta name="paper-*">` tags in `<head>` have non-empty `content` values.
8b. **No orphaned bold text**: `<strong>` or `<b>` text should flow inline within paragraphs, NOT appear alone on its own line separated by `<br>` or paragraph breaks. Bold text wrapped in isolation looks unintended.
9. **Base64 integrity**: Open the HTML in a browser; all figures render without broken-image icons. Each `<img src="data:image/png;base64,...">` is well-formed
10. **Image sizing**: No inline image exceeds 100% container width or 500px height; `max-width` and `max-height` CSS constraints are in effect
11. **Lightbox functional**: Clicking any `figure.paper-fig img` opens the lightbox overlay displaying the full-resolution image
12. **Lightbox dismiss**: The lightbox closes on × button, backdrop click, and Escape key
13. **Gallery navigation**: With 2+ figures, prev/next arrows and ArrowLeft/ArrowRight keyboard keys navigate between them
14. **Dark mode images**: Toggle dark mode; images have visible borders (`border-color:#334155`) and are not washed out against the dark background
15. **Print images**: Print preview shows images at reasonable size (`max-height:300px`); lightbox overlay is hidden
16. **Lazy loading + caption**: Every `figure.paper-fig img` has both `loading="lazy"` and `data-caption` attributes; `data-caption` matches its `figcaption` text
17. **Figure cropping quality**: Each embedded figure is an individual cropped image (not a full-page render). Verify by checking that figures don't contain surrounding body text, page headers, or footnotes — the image should show only the diagram/figure itself
18. **Formula rendering**: All `$...$` and `$$...$$` formulas render correctly when KaTeX loads; check for `\` command typos and unmatched braces
19. **Formula normalization**: Any pdftotext-mangled symbols (e.g., ∑ → `Sigma`) have been corrected back to proper LaTeX
20. **Formula explanation**: Every display formula (`$$...$$`) is followed by an explanation in the user's chosen annotation language
21. **KaTeX fallback**: When the CDN is unavailable, `.formula-inline` and `.formula-display` fallback styles show readable monospace content
22. **Mobile sidebar toggle**: On viewports <960px, sidebar is hidden and ☰ button appears at bottom-right. Tapping opens sidebar as overlay with semi-transparent backdrop. Tapping backdrop closes it.
23. **Code copy button**: Hovering over any `<pre>` block reveals a "复制" button at top-right. Clicking copies the code to clipboard and shows "已复制" for 1.5s. Falls back gracefully if clipboard API is unavailable.
24. **Table scroll indicator**: When a table overflows its container, a gradient fade appears on the right edge to indicate scrollability. Disappears when fully scrolled.
25. **Section flash on :target**: When navigating to a section via anchor link (sidebar or h2 anchor), the section briefly flashes with a blue highlight (`section-flash` animation) to orient the reader.
26. **No intermediate file references**: The final HTML is self-contained (CSS/JS inline, images as base64 data URIs). Grep for any local file paths that might have leaked — there should be no references to `paper_text.txt`, `figures_b64.json`, `section_*.html`, `assembled_body.html`, `template.css`, `template.js`, or `<!-- STYLESHEET -->` / `<!-- SCRIPT -->` placeholders.
27. **Strategy marker present**: The `<body>` tag has a `data-strategy` attribute matching the strategy chosen in Phase 0b (e.g., `data-strategy="cognition-first"`). Verify with: `grep -o 'data-strategy="[^"]*"' <output>.html`.
28. **Strategy section ordering**: The h2 titles appear in the sequence specified by the chosen strategy's ordering rules (from Organization Strategy Reference). When the strategy is NOT paper-structure-aligned, the section order should NOT match the template's default order.
29. **Strategy-specific heading style**: For question-driven, every h2 heading contains an actual question (ends with `？` or `?`). For persona-driven, section titles use conversational/practitioner-oriented language rather than academic section headings.

