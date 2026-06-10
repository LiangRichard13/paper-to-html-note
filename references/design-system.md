# Design System — CSS Variables, Component Styles, and JavaScript

This file is the canonical design system for the HTML reading notes. It is intended to be **embedded inline** in every generated HTML file. Read this file with the Read tool when generating the output HTML, then copy the relevant parts.

---

## Part 1: CSS Custom Properties (embed in `<style>` tag, before all other CSS)

### Light Theme (`:root`)

```css
:root {
  --bg: #f8f9fa; --card: #ffffff; --text: #1e293b; --text2: #64748b;
  --border: #e2e8f0; --code-bg: #f1f5f9;
  --accent: #2563eb; --accent-lt: #dbeafe; --accent-dk: #1d4ed8;
  --success: #16a34a; --success-lt: #dcfce7;
  --warn: #f59e0b; --warn-lt: #fef3c7;
  --danger: #dc2626; --danger-lt: #fee2e2;
  --purple: #7c3aed; --purple-lt: #f3e8ff;
  --cyan: #0891b2; --cyan-lt: #cffafe;
  --shadow: 0 1px 2px rgba(0,0,0,.03);
  --shadow-md: 0 4px 12px rgba(0,0,0,.08);
  --radius: 12px; --radius-sm: 8px;
  --sans: -apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans SC',sans-serif;
  --mono: 'JetBrains Mono','Fira Code','Cascadia Code',monospace;
}
```

### Dark Theme (`[data-theme="dark"]`)

```css
[data-theme="dark"] {
  --bg: #0f172a; --card: #1e293b; --text: #e2e8f0; --text2: #94a3b8;
  --border: #334155; --code-bg: #1e293b;
  --accent: #60a5fa; --accent-lt: #1e3a5f; --accent-dk: #3b82f6;
  --success: #4ade80; --success-lt: #14532d;
  --warn: #fbbf24; --warn-lt: #422006;
  --danger: #f87171; --danger-lt: #450a0a;
  --purple: #a78bfa; --purple-lt: #2e1065;
  --cyan: #22d3ee; --cyan-lt: #083344;
  --shadow: 0 1px 3px rgba(0,0,0,.25);
  --shadow-md: 0 4px 16px rgba(0,0,0,.4);
}
```

---

## Part 2: Global Reset and Layout (embed in `<style>` tag, after variables)

```css
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--sans);background:var(--bg);color:var(--text);line-height:1.72;font-size:15px;transition:background .3s,color .3s}

/* Progress bar */
#progress-bar{position:fixed;top:0;left:0;height:3px;background:var(--accent);z-index:200;transition:width .1s linear}

/* Top bar */
.top-bar{position:sticky;top:0;z-index:100;background:var(--card);border-bottom:1px solid var(--border);padding:8px 0;box-shadow:var(--shadow);backdrop-filter:blur(8px)}
.top-inner{max-width:1280px;margin:0 auto;padding:0 24px;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.top-badge{background:var(--accent);color:#fff;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600}
.top-meta{color:var(--text2);font-size:13px}
.top-meta a{color:var(--accent);text-decoration:none}
.top-spacer{flex:1}
.top-btn{background:var(--code-bg);border:1px solid var(--border);padding:5px 12px;border-radius:6px;color:var(--text);font-size:12px;cursor:pointer;transition:all .2s}
.top-btn:hover{background:var(--accent-lt);color:var(--accent)}

/* Layout */
.container{max-width:1280px;margin:0 auto;padding:24px;display:flex;gap:32px}
.content{flex:1;min-width:0}

/* Sidebar */
.sidebar{width:260px;flex-shrink:0;position:sticky;top:68px;height:calc(100vh - 90px);overflow-y:auto;padding-right:6px;font-size:13px}
.sidebar::-webkit-scrollbar{width:4px}
.sidebar::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
.sidebar h3{font-size:12px;text-transform:uppercase;letter-spacing:.6px;color:var(--text2);margin-bottom:6px}
.sidebar details{margin-bottom:4px}
.sidebar summary{color:var(--text);font-weight:500;padding:4px 6px;border-radius:4px;cursor:pointer;font-size:13px}
.sidebar summary:hover{background:var(--code-bg)}
.sidebar a{display:block;padding:3px 8px 3px 22px;color:var(--text2);text-decoration:none;border-radius:4px;font-size:12.5px;border-left:2px solid transparent;transition:all .15s}
.sidebar a:hover,.sidebar a.active{color:var(--accent);background:var(--accent-lt);border-left-color:var(--accent)}

/* Back to top */
#btt{position:fixed;bottom:28px;right:28px;width:40px;height:40px;border-radius:50%;background:var(--accent);color:#fff;border:none;font-size:18px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.2);opacity:0;transform:translateY(20px);transition:all .3s;z-index:150}
#btt.show{opacity:1;transform:translateY(0)}
#btt:hover{transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,.3)}
```

---

## Part 3: Component Styles (embed in `<style>` tag)

### Sections and Headings

```css
.section{background:var(--card);border-radius:var(--radius);padding:26px 30px;margin-bottom:20px;border:1px solid var(--border);box-shadow:var(--shadow);transition:background .3s}
.section:target{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-lt)}
h1{font-size:28px;line-height:1.3;margin-bottom:6px}
h1 .sub{font-size:15px;font-weight:400;color:var(--text2);display:block;margin-top:4px}
h2{font-size:21px;margin-bottom:14px;padding-bottom:7px;border-bottom:2px solid var(--accent-lt);display:flex;align-items:center;gap:10px}
h2 .num{background:var(--accent);color:#fff;width:27px;height:27px;border-radius:6px;display:inline-flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;flex-shrink:0}
h3{font-size:17px;margin:18px 0 8px;color:var(--text)}
h4{font-size:14.5px;margin:14px 0 6px;color:var(--text2)}
p,li{margin-bottom:9px}
ul,ol{padding-left:20px}
```

### Callout Boxes (6 types)

```css
.callout{padding:13px 17px;border-radius:var(--radius-sm);margin:12px 0;border-left:4px solid;font-size:14px}
.callout>strong{display:block;margin-bottom:3px;font-size:14px}
.callout.info{background:var(--accent-lt);border-color:var(--accent)}
.callout.warn{background:var(--warn-lt);border-color:var(--warn)}
.callout.success{background:var(--success-lt);border-color:var(--success)}
.callout.danger{background:var(--danger-lt);border-color:var(--danger)}
.callout.purple{background:var(--purple-lt);border-color:var(--purple)}
.callout.cyan{background:var(--cyan-lt);border-color:var(--cyan)}
```

### Tags (6 color variants)

```css
.tag{display:inline-block;padding:1px 7px;border-radius:4px;font-size:11.5px;font-weight:500}
.tag.bl{background:var(--accent-lt);color:var(--accent)}
.tag.gr{background:var(--success-lt);color:var(--success)}
.tag.or{background:var(--warn-lt);color:var(--warn)}
.tag.rd{background:var(--danger-lt);color:var(--danger)}
.tag.pu{background:var(--purple-lt);color:var(--purple)}
.tag.cy{background:var(--cyan-lt);color:var(--cyan)}
```

### Grid Cards

```css
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:12px 0}
.grid-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin:12px 0}
.mini-card{background:var(--code-bg);padding:13px;border-radius:var(--radius-sm);border:1px solid var(--border)}
.mini-card strong{display:block;margin-bottom:3px;font-size:13.5px}
.mini-card p{font-size:12.5px;margin:0;color:var(--text2)}
```

### Principle Boxes

```css
.pbox{display:flex;gap:10px;align-items:flex-start;padding:12px;margin:8px 0;background:var(--code-bg);border-radius:var(--radius-sm);border-left:3px solid var(--accent)}
.pbox .pn{background:var(--accent);color:#fff;width:22px;height:22px;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0}
.pbox .pb{flex:1}.pbox .pb strong{display:block}
```

### Tables

```css
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:13.5px}
th,td{padding:9px 12px;border:1px solid var(--border);text-align:left;vertical-align:top}
th{background:var(--code-bg);font-weight:600;font-size:12.5px}
tr:nth-child(even) td{background:var(--code-bg)}
```

### Code Blocks

```css
code{background:var(--code-bg);padding:2px 6px;border-radius:4px;font-size:12.5px;font-family:var(--mono)}
pre{background:#0f172a;color:#e2e8f0;padding:15px 18px;border-radius:var(--radius-sm);overflow-x:auto;font-size:12.5px;line-height:1.55;margin:12px 0}
pre .c{color:#94a3b8}pre .kw{color:#c084fc}pre .s{color:#34d399}pre .fn{color:#60a5fa}pre .num{color:#fb923c}
```

### Specialty Components

```css
/* Running example trace */
.trace{margin:10px 0;counter-reset:step}
.trace li{list-style:none;padding:8px 0 8px 34px;position:relative;border-left:2px solid var(--border);margin-left:12px}
.trace li::before{counter-increment:step;content:counter(step);position:absolute;left:-13px;top:8px;width:24px;height:24px;background:var(--accent);color:#fff;border-radius:50%;text-align:center;line-height:24px;font-size:11px;font-weight:700}

/* Running example callout */
.run-ex{border:2px dashed var(--accent);border-radius:var(--radius-sm);padding:12px 16px;margin:14px 0;background:var(--accent-lt);font-size:13.5px}
.run-ex strong{color:var(--accent-dk)}

/* Metadata row */
.meta-row{display:flex;flex-wrap:wrap;gap:18px;margin:12px 0 18px;padding:12px 16px;background:var(--code-bg);border-radius:var(--radius-sm);font-size:13px}
.meta-row span{color:var(--text2)}
.meta-row strong{color:var(--text)}

/* Summary grid (key metrics dashboard) */
.summary-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;margin:12px 0}
.summary-grid .sg-item{background:var(--code-bg);padding:12px;border-radius:var(--radius-sm);text-align:center;border:1px solid var(--border)}
.sg-item .sg-val{font-size:24px;font-weight:800;color:var(--accent)}
.sg-item .sg-lbl{font-size:11.5px;color:var(--text2);margin-top:2px}

/* Source file reference */
.fref{font-size:11.5px;color:var(--text2);font-family:var(--mono)}
.src-link{font-size:11px;color:var(--accent);font-family:var(--mono);cursor:default;white-space:nowrap}

/* Equation pair */
.eq-pair{display:flex;align-items:center;gap:8px;justify-content:center;font-size:15px;margin:8px 0;flex-wrap:wrap}
.eq-pair .eq-box{background:var(--accent-lt);padding:4px 10px;border-radius:4px;font-weight:500;font-size:13px}
.eq-pair .eq-arrow{color:var(--accent);font-weight:700}

/* Mindmap */
.mindmap{padding:20px;text-align:center;background:#0f172a;border-radius:10px;margin:12px 0}
.mindmap .center-node{display:inline-block;background:var(--accent);color:#fff;padding:10px 22px;border-radius:8px;font-weight:700;margin-bottom:14px}
.mindmap .children{display:flex;flex-wrap:wrap;gap:8px;justify-content:center}
.mindmap .child{background:#1e293b;color:#e2e8f0;padding:6px 12px;border-radius:6px;font-size:12.5px;border:1px solid #334155}

/* Figure with caption (embedded base64 images from Phase 1.2) */
figure.paper-fig{margin:20px 0;text-align:center;break-inside:avoid}
figure.paper-fig img{max-width:100%;max-height:500px;width:auto;height:auto;
  border-radius:var(--radius-sm);border:1px solid var(--border);box-shadow:var(--shadow);
  cursor:zoom-in;transition:box-shadow .2s,transform .2s}
figure.paper-fig img:hover{box-shadow:var(--shadow-md);transform:scale(1.01)}
figure.paper-fig figcaption{font-size:12.5px;color:var(--text2);margin-top:8px;
  font-style:italic}
[data-theme="dark"] figure.paper-fig img{border-color:#334155}

/* Formula display — KaTeX fallback for offline mode */
.formula-inline{padding:1px 5px;background:var(--code-bg);border-radius:4px;font-size:13px;font-family:var(--mono);white-space:nowrap}
.formula-display{display:block;text-align:center;padding:12px 16px;margin:10px 0;background:var(--code-bg);border-radius:var(--radius-sm);font-size:14px;font-family:var(--mono);overflow-x:auto;border:1px solid var(--border)}
.formula-array{display:block;text-align:center;padding:8px 16px;margin:8px 0;font-size:14px;font-family:var(--mono);overflow-x:auto}
.katex + .formula-fallback{display:none}
```

### Responsive and Print

```css
@media(max-width:960px){
  .sidebar{display:none}
  .container{padding:14px}
  .section{padding:18px 16px}
  .grid-2,.grid-3{grid-template-columns:1fr}
}

@media print{
  .sidebar,#btt,.top-bar,#progress-bar{display:none}
  .container{display:block;padding:0}
  .section{box-shadow:none;border:1px solid #ddd;break-inside:avoid;margin-bottom:12px;padding:16px 20px}
  body{font-size:12px;color:#000;background:#fff}
  figure.paper-fig img{max-height:300px;box-shadow:none;border:1px solid #ccc}
  .section-entrance{opacity:1!important;transform:none!important}
  .lightbox{display:none!important}
}
```

---

## Part 4: JavaScript (embed in `<script>` tag at end of `<body>`)

```javascript
// ====== Progress Bar ======
window.addEventListener('scroll',()=>{
  const h=document.documentElement, b=document.body;
  const st=h.scrollTop||b.scrollTop, sh=h.scrollHeight||b.scrollHeight, ch=h.clientHeight;
  const pct=Math.round(st/(sh-ch)*100);
  document.getElementById('progress-bar').style.width=pct+'%';
  // Back to top button visibility
  const btt=document.getElementById('btt');
  if(st>600) btt.classList.add('show'); else btt.classList.remove('show');
});

// ====== Sidebar Active Highlight (IntersectionObserver) ======
const obs=new IntersectionObserver(entries=>{
  entries.forEach(e=>{
    if(e.isIntersecting){
      document.querySelectorAll('.sidebar a').forEach(a=>a.classList.remove('active'));
      const link=document.querySelector(`.sidebar a[href="#${e.target.id}"]`);
      if(link) link.classList.add('active');
    }
  });
},{rootMargin:'-80px 0px -70% 0px'});
document.querySelectorAll('.section[id]').forEach(s=>obs.observe(s));

// ====== Dark/Light Theme Toggle ======
function toggleTheme(){
  const html=document.documentElement;
  const cur=html.getAttribute('data-theme');
  const next=cur==='dark'?'light':'dark';
  html.setAttribute('data-theme',next);
  localStorage.setItem('ppr-note-theme',next);
}
// Load saved theme on startup
(function(){
  try{
    const saved=localStorage.getItem('ppr-note-theme');
    if(saved) document.documentElement.setAttribute('data-theme',saved);
  }catch(e){}
})();

// ====== Print: expand all details elements ======
window.addEventListener('beforeprint',()=>{
  document.querySelectorAll('details').forEach(d=>d.setAttribute('open',''));
});

// ====== Entrance Animation (scroll-triggered reveal) ======
(function(){
  const observer=new IntersectionObserver(entries=>{
    entries.forEach(e=>{
      if(e.isIntersecting){
        e.target.classList.add('revealed');
        observer.unobserve(e.target);
      }
    });
  },{threshold:0.1,rootMargin:'0px 0px -40px 0px'});
  document.querySelectorAll('.section-entrance').forEach(el=>observer.observe(el));
})();

// ====== Lightbox (click-to-zoom) ======
// See template.html PART 5A for the complete lightbox implementation.
// Key: creates overlay DOM, attaches click to figure.paper-fig img,
// supports prev/next navigation, keyboard Escape/Arrow, body scroll lock.
```

---

## Part 5: Enhancement Styles (from frontend-design aesthetics)

These styles are optional upgrades. Apply them when you want the reading notes to feel more polished and less "default AI output." All enhancements are pure CSS — zero external dependencies.

### 5a. Entrance Animation — Scroll-triggered section reveal

**What**: Sections fade in from below as the user scrolls. Creates one high-impact moment of polish.  
**When**: Add `class="section-entrance"` to any `.section` div you want animated. Best used on the first 2-3 sections only — overuse dilutes the effect.  
**From**: frontend-design Rule 4 — "one high-impact moment > many small animations"

```css
.section-entrance{opacity:0;transform:translateY(30px);transition:opacity .6s cubic-bezier(0.16,1,0.3,1),transform .6s cubic-bezier(0.16,1,0.3,1)}
.section-entrance.revealed{opacity:1;transform:translateY(0)}
```

**Required JS** (add to the `<script>` block):

```javascript
(function(){
  const observer=new IntersectionObserver(entries=>{
    entries.forEach(e=>{
      if(e.isIntersecting){
        e.target.classList.add('revealed');
        observer.unobserve(e.target);
      }
    });
  },{threshold:0.1,rootMargin:'0px 0px -40px 0px'});
  document.querySelectorAll('.section-entrance').forEach(el=>observer.observe(el));
})();
```

**Print note**: Add `.section-entrance{opacity:1!important;transform:none!important}` to the `@media print` block so printed output shows all sections immediately.

### 5b. Card Lift — Hover elevation effect

**What**: Cards and principle boxes gently lift on hover, adding tactile depth.  
**When**: Add `class="card-lift"` to `.mini-card` elements or any `.section` you want to respond to hover.  
**From**: frontend-design Rule 8 — texture and depth create materiality

```css
.card-lift{transition:transform .25s ease,box-shadow .25s ease}
.card-lift:hover{transform:translateY(-3px);box-shadow:var(--shadow-md)}
```

**Also applied by default** in template.html: `.mini-card:hover` already lifts 2px. `.pbox:hover` shifts 3px right. `.sg-item:hover` lifts 3px up.

### 5c. Accent Gradient — Gradient accent bar

**What**: Replaces the flat accent color on key UI elements with a subtle accent→cyan gradient.  
**When**: Use on `h2` bottom borders, the progress bar, or any element where the flat `var(--accent)` feels too plain.  
**From**: frontend-design Rule 2 — dominant color + sharp accent

```css
.accent-gradient{background:linear-gradient(90deg,var(--accent),var(--cyan))}
```

**Usage examples**:
- Progress bar: `<div id="progress-bar" class="accent-gradient"></div>`
- Section divider: `<hr class="accent-gradient" style="height:3px;border:none;border-radius:2px">`
- h2 bottom border override: `<h2 style="border-bottom-color:transparent;border-image:linear-gradient(90deg,var(--accent),var(--cyan)) 1">`

### 5d. Background Texture — Subtle dot grid

**What**: A microscopic dot-grid pattern on the page background. Adds visual texture without distraction. Completely pure CSS — no image files needed.  
**When**: Add `class="bg-texture"` to `<body>` for a subtle paper-like feel. Pairs well with the "material metaphor" of card-based layouts.  
**From**: frontend-design Rule 8 — background texture creates atmosphere

```css
.bg-texture{background-image:radial-gradient(circle,var(--border) 1px,transparent 1px);background-size:20px 20px}
```

**Dark mode note**: The texture uses `var(--border)` which is already darker in dark theme, so it works automatically in both modes.

### 5e. Anchor Link on Headings (pure CSS)

**What**: Section headings reveal a `#` link icon on hover, making it easy to share/bookmark specific sections.  
**When**: Always included in the template.html h2 style.  

```css
h2 .anchor{opacity:0;font-size:16px;color:var(--text2);text-decoration:none;transition:opacity .2s;margin-left:auto}
h2:hover .anchor{opacity:1}
```

Usage in HTML: `<h2>Title<a href="#section-id" class="anchor">#</a></h2>`

### 5f. Dark-mode table row contrast

**What**: In dark mode, the alternating row background is replaced with a subtle semi-transparent overlay instead of the solid `--code-bg`, improving legibility.  
**When**: Always included in template.html.

```css
[data-theme="dark"] tr:nth-child(even) td{background:rgba(255,255,255,.03)}
```

### 5g. Image Lightbox — Click-to-Zoom Overlay

**What**: Full-screen image viewer for paper figures. Click any `figure.paper-fig img` to zoom; click backdrop, press Escape, or click the × close button to dismiss. Arrow keys and on-screen prev/next buttons navigate between multiple figures. Caption is displayed from the `data-caption` attribute.  
**When**: Always include when the paper has figures (Component 19). Enabled automatically — no manual HTML needed beyond `figure.paper-fig img`.  
**From**: paper-to-html-note v3 image integration — improves figure usability with zero external dependencies.

```css
/* Lightbox overlay */
.lightbox{display:none;position:fixed;top:0;left:0;width:100%;height:100%;
  background:rgba(0,0,0,.85);z-index:9999;justify-content:center;align-items:center;
  flex-direction:column;cursor:zoom-out}
.lightbox.active{display:flex}
.lightbox img{max-width:92vw;max-height:85vh;object-fit:contain;
  border-radius:6px;box-shadow:0 4px 32px rgba(0,0,0,.5);background:#fff}
.lightbox .lb-caption{color:#ccc;font-size:13px;margin-top:12px;
  max-width:80vw;text-align:center}
.lightbox .lb-close{position:fixed;top:16px;right:24px;color:#fff;
  font-size:36px;cursor:pointer;line-height:1;z-index:10000;
  opacity:.7;transition:opacity .2s;background:none;border:none;font-family:var(--sans)}
.lightbox .lb-close:hover{opacity:1}
.lightbox .lb-nav{position:fixed;top:50%;transform:translateY(-50%);color:#fff;
  font-size:32px;cursor:pointer;opacity:.5;transition:opacity .2s;
  background:none;border:none;padding:16px;z-index:10000}
.lightbox .lb-nav:hover{opacity:1}
.lightbox .lb-prev{left:16px}
.lightbox .lb-next{right:16px}
```

**Required JS**: See Part 5A in `template.html` — the lightbox JavaScript creates the overlay DOM once, attaches click handlers to all `figure.paper-fig img` elements, and handles keyboard navigation.

**Print note**: Lightbox is hidden in print via `.lightbox{display:none!important}` in the `@media print` block.
