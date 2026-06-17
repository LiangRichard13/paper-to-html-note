// ===============================================================
// PART 1: Reading Progress Bar
// ===============================================================
(function(){
  const bar=document.getElementById('progress-bar');
  const btt=document.getElementById('btt');
  window.addEventListener('scroll',()=>{
    const h=document.documentElement, b=document.body;
    const st=h.scrollTop||b.scrollTop, sh=h.scrollHeight||b.scrollHeight, ch=h.clientHeight;
    const range=sh-ch;
    bar.style.width=(range>0?Math.round(st/range*100):0)+'%';
    if(st>600) btt.classList.add('show'); else btt.classList.remove('show');
  });
})();

// ===============================================================
// PART 2: Sidebar Active Highlight (IntersectionObserver)
// ===============================================================
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

// ===============================================================
// PART 3: Dark/Light Theme Toggle
// ===============================================================
function toggleTheme(){
  const html=document.documentElement;
  const cur=html.getAttribute('data-theme');
  const next=cur==='dark'?'light':'dark';
  html.setAttribute('data-theme',next);
  try{localStorage.setItem('ppr-note-theme',next)}catch(e){}
}
// Load saved theme on startup
(function(){
  try{
    const saved=localStorage.getItem('ppr-note-theme');
    if(saved) document.documentElement.setAttribute('data-theme',saved);
  }catch(e){}
})();

// ===============================================================
// PART 4: Print — expand all sidebar details
// ===============================================================
window.addEventListener('beforeprint',()=>{
  document.querySelectorAll('details').forEach(d=>d.setAttribute('open',''));
});

// ===============================================================
// PART 5A: Lightbox — click-to-zoom for paper figures
// ===============================================================
(function(){
  // Create lightbox DOM once
  const lb = document.createElement('div');
  lb.className = 'lightbox';
  lb.innerHTML = `
    <button class="lb-close" title="关闭" type="button">&times;</button>
    <button class="lb-nav lb-prev" title="上一张" type="button">&lsaquo;</button>
    <button class="lb-nav lb-next" title="下一张" type="button">&rsaquo;</button>
    <img src="" alt="">
    <div class="lb-caption"></div>`;
  document.body.appendChild(lb);

  const lbImg = lb.querySelector('img');
  const lbCaption = lb.querySelector('.lb-caption');
  const prevBtn = lb.querySelector('.lb-prev');
  const nextBtn = lb.querySelector('.lb-next');

  let currentFigures = [];
  let currentIndex = 0;

  function showFigure(index) {
    if (index < 0) index = currentFigures.length - 1;
    if (index >= currentFigures.length) index = 0;
    currentIndex = index;
    const fig = currentFigures[index];
    lbImg.src = fig.src;
    lbImg.alt = fig.alt;
    lbCaption.textContent = fig.dataset.caption || fig.alt || '';
    prevBtn.style.display = currentFigures.length > 1 ? '' : 'none';
    nextBtn.style.display = currentFigures.length > 1 ? '' : 'none';
  }

  function closeLightbox() {
    lb.classList.remove('active');
    document.body.style.overflow = '';
  }

  // Attach click handlers to all paper-fig images
  function attachLightbox() {
    document.querySelectorAll('figure.paper-fig img').forEach(img => {
      img.addEventListener('click', () => {
        currentFigures = Array.from(document.querySelectorAll('figure.paper-fig img'));
        currentIndex = currentFigures.indexOf(img);
        showFigure(currentIndex);
        lb.classList.add('active');
        document.body.style.overflow = 'hidden';
      });
    });
  }
  attachLightbox();

  // Close handlers
  lb.querySelector('.lb-close').addEventListener('click', closeLightbox);
  lb.addEventListener('click', (e) => {
    if (e.target === lb) closeLightbox();
  });

  // Navigation
  prevBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    showFigure(currentIndex - 1);
  });
  nextBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    showFigure(currentIndex + 1);
  });

  // Keyboard
  document.addEventListener('keydown', (e) => {
    if (!lb.classList.contains('active')) return;
    if (e.key === 'Escape') closeLightbox();
    if (e.key === 'ArrowLeft') showFigure(currentIndex - 1);
    if (e.key === 'ArrowRight') showFigure(currentIndex + 1);
  });
})();

// ===============================================================
// PART 6: Entrance Animation (scroll-triggered reveal)
// ===============================================================
(function(){
  const observer=new IntersectionObserver(entries=>{
    entries.forEach(e=>{
      if(e.isIntersecting){
        e.target.classList.add('revealed');
        observer.unobserve(e.target); // animate only once
      }
    });
  },{threshold:0.1,rootMargin:'0px 0px -40px 0px'});
  document.querySelectorAll('.section-entrance').forEach(el=>observer.observe(el));
})();

// ===============================================================
// PART 7: Mobile sidebar toggle
// ===============================================================
function toggleSidebar(){
  const s=document.querySelector('.sidebar'), o=document.querySelector('.sidebar-overlay');
  if(!s||!o)return;
  s.classList.toggle('active'); o.classList.toggle('active');
  document.body.style.overflow=s.classList.contains('active')?'hidden':'';
}

// ===============================================================
// PART 8: Code block copy button
// ===============================================================
(function(){
  document.querySelectorAll('pre').forEach(pre=>{
    const btn=document.createElement('button');
    btn.textContent='复制';
    Object.assign(btn.style,{
      position:'absolute',top:'6px',right:'6px',padding:'3px 9px',fontSize:'11px',
      borderRadius:'4px',border:'1px solid #334155',background:'#1e293b',color:'#94a3b8',
      cursor:'pointer',opacity:'0',transition:'opacity .2s',fontFamily:'var(--sans)'
    });
    pre.style.position='relative';
    pre.appendChild(btn);
    pre.addEventListener('mouseenter',()=>btn.style.opacity='1');
    pre.addEventListener('mouseleave',()=>btn.style.opacity='0');
    btn.addEventListener('click',async()=>{
      const code=pre.querySelector('code')||pre;
      try{await navigator.clipboard.writeText(code.textContent||'');
        btn.textContent='已复制';
        setTimeout(()=>btn.textContent='复制',1500);
      }catch(e){btn.textContent='失败';}
    });
  });
})();

// ===============================================================
// PART 9: Table horizontal scroll detection
// ===============================================================
(function(){
  document.querySelectorAll('.table-wrap').forEach(w=>{
    const c=()=>w.classList.toggle('is-overflow',w.scrollWidth>w.clientWidth+1);
    c(); window.addEventListener('resize',c);
  });
})();

// ===============================================================
// PART 10: Highlighter & Annotation System
// ===============================================================

/* --- State --- */
let annotations = [];
let pendingSelection = null;
let activeAnnotationId = null; // track which highlight we're editing (click-on-highlight flow)

/* --- Init from meta tags --- */
(function initMeta(){
  try{
    const get=name=>{const m=document.querySelector('meta[name="'+name+'"]');return m?m.getAttribute('content').trim():''};
    const typeMap={system:'系统',algorithm:'算法',survey:'综述',empirical:'实证',position:'立场'};
    const t=get('paper-title'),ty=get('paper-type'),a=get('paper-authors'),v=get('paper-venue'),d=get('paper-date'),inst=get('paper-institution'),mt=get('paper-method'),kf=get('paper-key-finding');
    if(t){
      document.title= t;
      const topM=document.querySelector('.top-meta');if(topM)topM.innerHTML='<strong>'+escHtml(t)+'</strong>'+(v?' &middot; '+escHtml(v):'')+(d?' &middot; '+escHtml(d):'');
      const h1=document.querySelector('.section h1');if(h1)h1.textContent=t
    }
    if(ty){const badge=document.querySelector('.top-badge');if(badge)badge.textContent=typeMap[ty]||ty}
    const labels=[['paper-authors','📄 作者',a],['paper-institution','🏫 机构',inst],['paper-method','🔬 方法',mt],['paper-key-finding','🎯 核心',kf]];
    const row=document.querySelector('.meta-row');if(row&&labels.some(l=>l[2])){
      row.innerHTML=labels.filter(l=>l[2]).map(l=>'<span>'+escHtml(l[1])+'：'+escHtml(l[2])+'</span>').join('');
    }
  }catch(e){}
})();

function annotationId(){return 'hl_'+Date.now()+'_'+Math.random().toString(36).slice(2,6)}

/* --- Text offset helpers --- */
function textOffsetOf(ancestor,targetNode,targetOffset){
  const w=document.createTreeWalker(ancestor,NodeFilter.SHOW_TEXT);
  let acc=0,node;
  while((node=w.nextNode())){if(node===targetNode)return acc+targetOffset;acc+=node.textContent.length}
  return-1;
}
function textNodeAtOffset(ancestor,offset){
  const w=document.createTreeWalker(ancestor,NodeFilter.SHOW_TEXT);
  let acc=0,node;
  while((node=w.nextNode())){const len=node.textContent.length;if(offset>=acc&&offset<=acc+len)return{node,off:offset-acc};acc+=len}
  return null;
}

/* --- Serialization --- */
function serializeSelection(){
  const sel=window.getSelection();
  if(!sel||sel.isCollapsed||sel.rangeCount===0)return null;
  const range=sel.getRangeAt(0),contentEl=document.querySelector('.content');
  if(!contentEl.contains(range.startContainer)||!contentEl.contains(range.endContainer))return null;
  const s=textOffsetOf(contentEl,range.startContainer,range.startOffset),e=textOffsetOf(contentEl,range.endContainer,range.endOffset);
  if(Math.abs(e-s)<1)return null;
  // KaTeX check
  let n=range.startContainer;while(n&&n!==contentEl){if(n.classList&&n.classList.contains('katex'))return'KATEX';n=n.parentNode}
  n=range.endContainer;while(n&&n!==contentEl){if(n.classList&&n.classList.contains('katex'))return'KATEX';n=n.parentNode}
  // Use textContent.slice for consistent whitespace across paragraphs (browsers
  // normalize range.toString() whitespace differently for cross-paragraph selections)
  const rawText=contentEl.textContent.slice(s,e).replace(/\s+/g,' ').trim();
  return{startOffset:s,endOffset:e,text:rawText||range.toString().trim()};
}
function getTextNodesInRange(range){
  const nodes=[],iter=document.createNodeIterator(range.commonAncestorContainer,NodeFilter.SHOW_TEXT,{acceptNode:n=>range.intersectsNode(n)?NodeFilter.FILTER_ACCEPT:NodeFilter.FILTER_REJECT});
  let node;while((node=iter.nextNode())){const s=(node===range.startContainer)?range.startOffset:0,e=(node===range.endContainer)?range.endOffset:node.textContent.length;if(e>s)nodes.push({node,start:s,end:e})}
  return nodes;
}
function applyMarkWrapper(range,color,id,hasNote){
  const segs=getTextNodesInRange(range);
  const mkList=[];
  for(const seg of segs){
    const sr=document.createRange();sr.setStart(seg.node,seg.start);sr.setEnd(seg.node,seg.end);
    const mk=document.createElement('mark');mk.className='hl-'+color;mk.dataset.annotationId=id;
    if(hasNote)mk.dataset.note=annotations.find(a=>a.id===id)?.note||'';
    try{sr.surroundContents(mk)}catch(e){const ext=sr.extractContents();mk.appendChild(ext);sr.insertNode(mk)}
    mkList.push(mk);
  }
  if(hasNote&&mkList.length>0)mkList[mkList.length-1].dataset.hasNote='true';
}
function textOffsetToRange(ancestor,so,eo){
  const s=textNodeAtOffset(ancestor,so),e=textNodeAtOffset(ancestor,eo);
  if(!s||!e)return null;const r=document.createRange();r.setStart(s.node,s.off);r.setEnd(e.node,e.off);return r;
}
function stripExistingHighlights(container){
  container.querySelectorAll('mark[class^="hl-"]').forEach(mk=>{
    const p=mk.parentNode;while(mk.firstChild)p.insertBefore(mk.firstChild,mk);p.removeChild(mk);p.normalize();
  });
}
function bindMarkClicks(){
  document.querySelectorAll('mark[class^="hl-"]').forEach(mk=>{
    mk.onclick=function(e){e.stopPropagation();showHighlightPopup(e,this.dataset.annotationId)}
    mk.onmouseenter=function(){
      const id=this.dataset.annotationId;
      document.querySelectorAll('mark[data-annotation-id="'+id+'"]').forEach(m=>m.classList.add('hl-sibling-active'))
    }
    mk.onmouseleave=function(){
      const id=this.dataset.annotationId;
      document.querySelectorAll('mark[data-annotation-id="'+id+'"]').forEach(m=>m.classList.remove('hl-sibling-active'))
    }
  });
}
function restoreHighlights(){
  const ce=document.querySelector('.content');if(!ce)return;
  stripExistingHighlights(ce);
  const sorted=[...annotations].sort((a,b)=>a.startOffset-b.startOffset);
  for(const a of sorted){const r=textOffsetToRange(ce,a.startOffset,a.endOffset);if(r)applyMarkWrapper(r,a.color,a.id,!!a.note)}
  bindMarkClicks();renderNotesList();
}

/* --- Persistence (manual save only — no localStorage) --- */
function saveAnnotations(){window._annotationsPersisted=false;syncAnnotationData()}
function loadAnnotations(){
  /* Annotations survive only via the embedded <script> tag — user must click
     "Save" to persist them. On reload, they load from the saved file. */
  try{
    const tag=document.getElementById('ppr-annotation-data');
    if(tag){const d=JSON.parse(tag.textContent);if(Array.isArray(d)&&d.length>0){annotations=d;restoreHighlights()}}
  }catch(e){}
  }
function syncAnnotationData(){const tag=document.getElementById('ppr-annotation-data');if(tag)tag.textContent=JSON.stringify(annotations)}

/* --- Popup --- */
function showPopup(x,y,forHighlight){
  const pop=document.getElementById('hl-popup');if(!pop)return;
  // Clear swatch selection
  pop.querySelectorAll('.hl-swatch').forEach(s=>s.classList.remove('selected'));
  // On highlight edit: also show delete + edit button
  const existingDivider=pop.querySelector('.hl-divider'),existingBtn=pop.querySelector('.hl-edit-btn');
  if(forHighlight){
    if(!existingDivider){const d=document.createElement('div');d.className='hl-divider';pop.appendChild(d)}
    // Add delete swatch
    if(!pop.querySelector('.hl-swatch.delete')){const ds=document.createElement('span');ds.className='hl-swatch delete';ds.title='删除高亮';ds.onclick=function(e){e.stopPropagation();deleteAnnotation(activeAnnotationId);hidePopup()};pop.appendChild(ds)}
    // Add edit button
    if(!existingBtn){const eb=document.createElement('button');eb.className='hl-edit-btn';eb.textContent='✎ 批注';eb.onclick=function(e){e.stopPropagation();const mk=document.querySelector('mark[data-annotation-id="'+activeAnnotationId+'"]');if(mk){const r=mk.getBoundingClientRect();openStickyEditor(r.right+10,r.top,activeAnnotationId)}hidePopup()};pop.appendChild(eb)}
  } else {
    if(existingDivider)existingDivider.remove();
    const ds=pop.querySelector('.hl-swatch.delete');if(ds)ds.remove();
    if(existingBtn)existingBtn.remove();
  }
  // Position
  pop.style.left=Math.min(x,window.innerWidth-pop.clientWidth-10)+'px';
  pop.style.top=Math.min(y,window.innerHeight-pop.clientHeight-10)+'px';
  pop.classList.add('active');
}
function hidePopup(){const pop=document.getElementById('hl-popup');if(pop)pop.classList.remove('active');activeAnnotationId=null}
function clearSelectionState(){pendingSelection=null;hidePopup();window.getSelection()?.removeAllRanges()}
function showToast(msg,d){const t=document.getElementById('hlToast');if(!t)return;t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),d||2000)}

/* --- Create highlight (step 1: select text, pick color) --- */
function confirmHighlight(color){
  if(!pendingSelection)return;
  const id=annotationId(),ann={id,color,startOffset:pendingSelection.startOffset,endOffset:pendingSelection.endOffset,text:pendingSelection.text,note:'',createdAt:Date.now(),updatedAt:Date.now()};
  annotations.push(ann);saveAnnotations();
  const ce=document.querySelector('.content'),range=textOffsetToRange(ce,ann.startOffset,ann.endOffset);
  if(range){applyMarkWrapper(range,ann.color,ann.id,false);bindMarkClicks()}
  clearSelectionState();renderNotesList();
}

/* --- Show popup for existing highlight (step 2: recolor/delete/edit) --- */
function showHighlightPopup(e,id){
  activeAnnotationId=id;e.stopPropagation();
  // Pre-select current color
  const ann=annotations.find(a=>a.id===id);if(!ann)return;
  const pop=document.getElementById('hl-popup');if(!pop)return;
  pop.querySelectorAll('.hl-swatch').forEach(s=>{s.classList.remove('selected');if(s.dataset.color===ann.color)s.classList.add('selected')});
  showPopup(e.clientX||e.touches?.[0]?.clientX||100,e.clientY||e.touches?.[0]?.clientY||100,true);
}

/* --- Swatch clicks --- */
document.addEventListener('click',function(e){
  const sw=e.target.closest('.hl-swatch');if(!sw||sw.classList.contains('delete'))return;
  const color=sw.dataset.color;if(!color)return;
  if(activeAnnotationId){
    // Recolor existing highlight
    const ann=annotations.find(a=>a.id===activeAnnotationId);if(!ann)return;
    ann.color=color;ann.updatedAt=Date.now();saveAnnotations();
    document.querySelectorAll('mark[data-annotation-id="'+activeAnnotationId+'"]').forEach(mk=>{
      mk.className='hl-'+color;
    });
    renderNotesList();hidePopup();
  } else if(pendingSelection){
    confirmHighlight(color);
  }
});

/* --- Selection handler --- */
function onSelection(e){
  setTimeout(()=>{
    if(activeAnnotationId){/* Don't steal focus from highlight edit */return}
    const r=serializeSelection();if(!r)return;
    if(r==='KATEX'){showPopup(e.clientX||e.changedTouches?.[0]?.clientX||100,e.clientY||e.changedTouches?.[0]?.clientY||100,false);showToast('⚠️ 无法高亮数学公式区域');setTimeout(hidePopup,1800);return}
    pendingSelection=r;showPopup(e.clientX||e.changedTouches?.[0]?.clientX||100,e.clientY||e.changedTouches?.[0]?.clientY||100,false);
  },50);
}
document.addEventListener('mouseup',onSelection);
document.addEventListener('touchend',function(e){setTimeout(()=>onSelection(e),300)});

/* Dismiss popup on outside click */
document.addEventListener('mousedown',function(e){
  if(e.target.closest('#hl-popup')||e.target.closest('.sticky-editor'))return;
  if(pendingSelection&&!activeAnnotationId){clearSelectionState()}
  if(activeAnnotationId&&!e.target.closest('mark[class^="hl-"]')){hidePopup()}
});

/* --- Sticky editor --- */
let stickyEditId=null;
function openStickyEditor(x,y,id){
  stickyEditId=id;const se=document.getElementById('stickyEditor'),ta=document.getElementById('stickyTextarea');
  if(!se||!ta)return;
  const ann=annotations.find(a=>a.id===id);ta.value=ann?ann.note||'':'';
  // Show hidden element first so it has dimensions, then position
  se.classList.add('active');
  const W=260,H=se.clientHeight||200;
  let px=x+10,py=y+10;
  if(px+W>window.innerWidth-10)px=x-W-10;
  if(py+H>window.innerHeight-10)py=y-H-10;
  if(px<10)px=10;if(py<10)py=10;
  se.style.left=px+'px';se.style.top=py+'px';ta.focus();
}
function closeStickyEditor(save){
  if(!stickyEditId)return;
  if(save){
    const ann=annotations.find(a=>a.id===stickyEditId),ta=document.getElementById('stickyTextarea');
    if(ann&&ta){ann.note=ta.value.trim();ann.updatedAt=Date.now();saveAnnotations();
      // Update DOM marks — only last segment gets the pin
      const marks=document.querySelectorAll('mark[data-annotation-id="'+stickyEditId+'"]');
      marks.forEach(mk=>{
        if(ann.note)mk.dataset.note=ann.note;else mk.removeAttribute('data-note');
        mk.removeAttribute('data-has-note');
      });
      if(ann.note&&marks.length>0)marks[marks.length-1].dataset.hasNote='true';
    }
  }
  document.getElementById('stickyEditor').classList.remove('active');stickyEditId=null;renderNotesList();
}
// Auto-save on click outside
document.addEventListener('mousedown',function(e){
  if(stickyEditId&&!e.target.closest('.sticky-editor')&&!e.target.closest('mark[class^="hl-"]')&&!e.target.closest('.note-item-actions')&&!e.target.closest('#hl-popup')){
    closeStickyEditor(true);
  }
});

/* --- Notes panel --- */
function toggleNotesPanel(){
  const p=document.getElementById('notesPanel'),o=document.querySelector('.notes-overlay'),t=document.getElementById('notes-toggle');
  if(!p)return;
  if(window.innerWidth<960){
    p.classList.toggle('open');if(o)o.classList.toggle('active');
    document.body.style.overflow=p.classList.contains('open')?'hidden':'';
  }else{p.classList.toggle('open')}
  if(t)t.textContent=p.classList.contains('open')?'✕':'💡';
  document.body.classList.toggle('has-notes-open',p.classList.contains('open'));
}

function renderNotesList(){
  const list=document.getElementById('notesList'),count=document.getElementById('notesCount'),toggle=document.getElementById('notes-toggle');
  if(!list)return;
  if(annotations.length===0){
    list.innerHTML='<div class="note-empty"><div class="note-empty-icon">📝</div><p>选中文本后高亮</p><p style="font-size:11px;margin-top:4px;opacity:.5">点击高亮区域添加批注</p></div>';
    if(count)count.textContent='0';if(toggle)toggle.classList.remove('has-notes');return;
  }
  if(count)count.textContent=annotations.length;if(toggle)toggle.classList.add('has-notes');
  const sorted=[...annotations].sort((a,b)=>a.startOffset-b.startOffset);
  list.innerHTML=sorted.map(a=>'<div class="note-item" data-id="'+a.id+'" onclick="scrollToAnnotation(\''+a.id+'\')">'+
    '<div class="note-item-color" style="--hl-color:var(--hl-'+a.color+')"></div>'+
    '<div class="note-item-text" title="'+escHtml(a.text)+'">'+escHtml(a.text)+'</div>'+
    (a.note?'<div class="note-item-annotation">'+escHtml(a.note)+'</div>':'')+
    '<div class="note-item-meta"><span class="note-item-time">'+new Date(a.createdAt).toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'})+'</span>'+
    '<div class="note-item-actions" onclick="event.stopPropagation()">'+
    '<button onclick="openStickyEditor(event.clientX,event.clientY,\''+a.id+'\')" title="编辑批注">✎</button>'+
    '<button class="del-btn" onclick="deleteAnnotation(\''+a.id+'\')" title="删除">✕</button></div></div></div>').join('');
}

function escHtml(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML}

function scrollToAnnotation(id){
  const marks=document.querySelectorAll('mark[data-annotation-id="'+id+'"]');if(marks.length>0){marks[0].scrollIntoView({behavior:'smooth',block:'center'});marks.forEach(mk=>{mk.classList.add('hl-flash');setTimeout(()=>mk.classList.remove('hl-flash'),800)})}
  const item=document.querySelector('.note-item[data-id="'+id+'"]');if(item)item.classList.toggle('expanded');
}

function deleteAnnotation(id){
  if(!confirm('删除此批注？'))return;
  annotations=annotations.filter(a=>a.id!==id);saveAnnotations();
  document.querySelectorAll('mark[data-annotation-id="'+id+'"]').forEach(mk=>{const p=mk.parentNode;while(mk.firstChild)p.insertBefore(mk.firstChild,mk);p.removeChild(mk);p.normalize()});
  hidePopup();renderNotesList();
}

async function saveHtml(){
  syncAnnotationData(); // ensures annotations are in the DOM before saving
  const html='<!DOCTYPE html>\n'+document.documentElement.outerHTML;
  const blob=new Blob([html],{type:'text/html;charset=utf-8'});
  // Derive filename from the original file path, not document.title
  let name='reading_note.html';
  try{const p=window.location.pathname;if(p){const m=p.split('/').pop();if(m)name=m}}catch(e){}
  // Try File System Access API — native Save As dialog with location choice
  // Chrome remembers the last-used directory for showSaveFilePicker automatically
  try{
    const h=await window.showSaveFilePicker({suggestedName:name,types:[{description:'HTML',accept:{'text/html':['.html']}}]});
    const w=await h.createWritable();await w.write(blob);await w.close();
    window._annotationsPersisted = true; // save succeeded — suppress beforeunload warning
  }catch(e){
    if(e.name==='AbortError')return; // user cancelled — do nothing
    // Fallback: download via temporary link
    const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;
    a.click();URL.revokeObjectURL(a.href);
    window._annotationsPersisted = true; // fallback download triggered — suppress beforeunload warning
  }
}
function clearAllAnnotationsPrompt(){
  if(!confirm('确定清除所有高亮和批注？此操作不可撤销。'))return;
  annotations=[];saveAnnotations();stripExistingHighlights(document.querySelector('.content'));renderNotesList();
  document.getElementById('notesPanel')?.classList.remove('open');
}

/* --- Init --- */
(function(){
  const wc=()=>{if(document.querySelector('.content')){loadAnnotations()}else setTimeout(wc,200)};setTimeout(wc,300);
  // Warn on close if annotations exist but were not saved to file
  // Skip the warning if the user has already saved the HTML to disk
  // (window._annotationsPersisted is set in saveHtml() after a successful save)
  window.addEventListener('beforeunload',function(e){
    if(annotations.length>0 && !window._annotationsPersisted){
      // Custom Chinese confirm — modern browsers ignore e.returnValue text,
      // but a synchronous confirm() still works in Chromium-based browsers and
      // gives the user a clearer message than the native dialog alone.
      const msg='当前页面有 '+annotations.length+' 条批注尚未保存到本地文件。\n离开后这些批注会丢失。\n\n确定要离开吗？';
      if(!confirm(msg)){e.preventDefault();e.returnValue='';return}
      e.preventDefault();e.returnValue=msg;
    }
  });
})();