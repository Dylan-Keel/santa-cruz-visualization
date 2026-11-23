<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
/* Layout idea: a light table. One dark surface, the photograph is the only bright thing, controls sit in a single strip under it. */
:root{
  color-scheme:dark;
  --table:#14171a; --panel:#1d2226; --line:#333b41; --ink:#e6e9e4; --dim:#98a39f;
  --parcel:#ffd23f; --shed:#5fd4ff; --stream:#7aa8ff; --creek:#9fe8c8;
  --display:"IBM Plex Mono",ui-monospace,Menlo,monospace; --body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--table);color:var(--ink);font-family:var(--body);font-size:15px;line-height:1.45}
main{max-width:1180px;margin:0 auto;padding:14px 16px 40px;display:flex;flex-direction:column;gap:12px}
header{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:10px 20px}
h1{font-family:var(--display);font-weight:500;font-size:17px;letter-spacing:.02em;margin:0;text-wrap:balance}
header p{margin:2px 0 0;color:var(--dim);font-size:13px}
.tabs{display:flex;border:1px solid var(--line);border-radius:6px;overflow:hidden}
.tabs{flex-wrap:wrap}
.tabs button{background:transparent;border:0;color:var(--dim);font:500 14px var(--body);padding:8px 12px;cursor:pointer}
.tabs button[aria-pressed="true"]{background:var(--ink);color:var(--table)}
.work{display:grid;grid-template-columns:minmax(0,1fr);gap:12px}
@media(min-width:900px){.work{grid-template-columns:minmax(0,1fr) 300px;align-items:start}}
.stage{position:relative;background:#000;border:1px solid var(--line);border-radius:4px;overflow:hidden;touch-action:none;cursor:grab;width:100%;max-height:82vh;margin:0 auto}
body.wide main{max-width:none;padding-left:10px;padding-right:10px}
body.wide .work{grid-template-columns:minmax(0,1fr)}
body.wide .side{flex-direction:row;flex-wrap:wrap;align-items:flex-start}
body.wide .side>*{flex:1 1 300px}
body.wide .stage{max-height:88vh}
@media(orientation:landscape) and (max-height:520px){body.wide .stage{max-height:96vh}}
.stage.drag{cursor:grabbing}
.layer{position:absolute;inset:0;transform-origin:0 0;will-change:transform}
.layer img{position:absolute;inset:0;width:100%;height:100%;display:block;visibility:hidden;user-select:none;-webkit-user-drag:none}
.layer img.on{visibility:visible}
.layer img.rast{visibility:visible;opacity:.6;display:none;image-rendering:auto}
.layer img.rast.on{display:block}
.ramp{display:inline-block;flex:none;width:30px;height:10px;border-radius:2px;margin-right:8px;border:1px solid #0006}
.tri{display:inline-block;flex:none;width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-bottom:11px solid #ff4fd8;margin:0 17px 0 7px}
label.op{gap:8px} label.op input{flex:1;min-width:80px}
.layer svg path.o-tree{fill:#ff4fd8;stroke:#1a0716;stroke-width:.25}
.layer svg{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
.layer svg path{fill:none;vector-effect:non-scaling-stroke;stroke-linejoin:round}
.o-parcel{stroke:var(--parcel);stroke-width:2}
.o-shed{stroke:var(--shed);stroke-width:1.6;stroke-dasharray:7 5}
.o-stream{stroke:var(--stream);stroke-width:1.3;opacity:.9}
.o-creek{stroke:var(--creek);stroke-width:2.2}
.layer svg path.o-fire{stroke-width:2.4;fill-opacity:0}
.layer svg path.o-fire.later{stroke-dasharray:3 6;fill-opacity:0;opacity:.75}
.layer svg text.later{opacity:.6}
.layer svg text{font-family:var(--body);font-weight:600;paint-order:stroke;stroke:#0b1014;stroke-width:4px;stroke-linejoin:round;text-anchor:middle}
.badge{position:absolute;left:10px;top:10px;background:rgba(10,12,14,.78);padding:6px 10px;border-radius:4px;pointer-events:none}
.badge b{font:500 26px/1 var(--display);display:block;font-variant-numeric:tabular-nums}
.badge span{font-size:12px;color:var(--dim)}
.scale[hidden],.north[hidden]{display:none}
.scale{position:absolute;right:10px;bottom:10px;background:rgba(10,12,14,.78);padding:5px 8px 6px;border-radius:4px;font:12px var(--display);pointer-events:none;text-align:center}
.scale i{display:block;height:5px;border:1.5px solid var(--ink);border-top:0;margin-top:3px}
.north{position:absolute;right:10px;top:10px;background:rgba(10,12,14,.78);padding:4px 8px;border-radius:4px;font:12px var(--display);pointer-events:none}
.loading{position:absolute;left:10px;bottom:10px;font:12px var(--display);color:var(--dim);background:rgba(10,12,14,.78);padding:4px 8px;border-radius:4px}
.side{display:flex;flex-direction:column;gap:12px}
.box{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:12px;display:flex;flex-direction:column;gap:10px}
.row{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
button.ctl{background:transparent;border:1px solid var(--line);color:var(--ink);font:500 14px var(--body);padding:9px 12px;border-radius:6px;cursor:pointer;min-width:44px}
button.ctl.main{background:var(--ink);color:var(--table);border-color:var(--ink);min-width:92px}
button:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--shed);outline-offset:2px}
select{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:6px;padding:8px;font:14px var(--body)}
input[type=range]{width:100%;accent-color:var(--ink)}
.years{display:flex;flex-wrap:wrap;gap:6px}
.years button{background:transparent;border:1px solid var(--line);color:var(--dim);font:13px var(--display);padding:6px 8px;border-radius:4px;cursor:pointer;font-variant-numeric:tabular-nums}
.years button.bw{border-style:dashed}
.years button[aria-current="true"]{background:var(--ink);color:var(--table);border-color:var(--ink)}
ul.fl{list-style:none;margin:0;padding:0 0 0 26px;display:flex;flex-direction:column;gap:5px;font-size:13px;color:var(--dim)}ul.fl li{display:flex;gap:8px;align-items:center}
label.t{display:flex;align-items:center;gap:8px;font-size:14px;cursor:pointer}
label.t input{width:18px;height:18px;accent-color:var(--ink)}
.sw{display:inline-block;width:18px;height:0;border-top:2px solid}
.meta{font-size:13px;color:var(--dim);margin:0}
.meta strong{color:var(--ink);font-weight:500}
.msg{font-size:13px;color:var(--parcel);min-height:1.2em;margin:0}
h2{font:500 12px var(--display);letter-spacing:.08em;text-transform:uppercase;color:var(--dim);margin:0}
.notes{max-width:68ch;color:var(--dim);font-size:14px;display:flex;flex-direction:column;gap:8px}
.notes p{margin:0}.notes strong{color:var(--ink);font-weight:500}
.notes a{color:var(--shed)}
table.fr{border-collapse:collapse;font:13px var(--display)}table.fr td{padding:5px 12px 5px 0;border-top:1px solid var(--line);vertical-align:top}table.fr a{margin-right:10px;white-space:nowrap}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
</head>
<body>
<main>
<header>
  <div>
    <h1>__H1__</h1>
    <p>__SUB__</p>
  </div>
  <div class="tabs" role="group" aria-label="View" id="tabs"></div>
</header>
<div class="work">
  <div id="hold" style="position:relative">
    <div class="stage" id="stage">
      <div class="layer" id="layer"></div>
      <div class="badge"><b id="yr">1993</b><span id="dt"></span></div>
      <div class="north" id="north">N ↑</div>
      <div class="scale"><span id="sclabel"></span><i id="scbar"></i></div>
      <div class="loading" id="loading" hidden>loading</div>
    </div>
  </div>
  <div class="side">
    <div class="box">
      <button class="ctl" id="rot" hidden style="margin-bottom:8px">Rotate view</button>
      <div class="row">
        <button class="ctl" id="prev" aria-label="Previous frame">◀</button>
        <button class="ctl main" id="play">Play</button>
        <button class="ctl" id="next" aria-label="Next frame">▶</button>
        <select id="speed" aria-label="Playback speed">
          <option value="2000" selected>Slow</option><option value="1100">Medium</option><option value="500">Fast</option>
        </select>
      </div>
      <input type="range" id="scrub" min="0" max="21" value="0" step="1" aria-label="Frame">
      <div class="years" id="years"></div>
      <p class="meta" id="meta"></p>
    </div>
    <div class="box">
      <h2>Legend</h2>
      <label class="t"><input type="checkbox" id="ov-parcel"><span class="sw" style="border-color:var(--parcel)"></span><span id="lab-parcel"></span></label>
      <label class="t"><input type="checkbox" id="ov-shed" checked><span class="sw" style="border-color:var(--shed);border-top-style:dashed"></span><span id="lab-shed"></span></label>
      <label class="t"><input type="checkbox" id="ov-stream" checked><span class="sw" style="border-color:var(--stream)"></span>Streams (National Hydrography Dataset)</label>
      <label class="t"><input type="checkbox" id="ov-fire"><span class="sw" style="border-color:#ff8a3d"></span>Fire perimeters (CAL FIRE)</label>
      <ul class="fl" id="firelist"></ul>
      <p class="meta">A dashed fire outline burned after the date on screen.</p>
      <label class="t"><input type="checkbox" id="ov-chm"><span class="ramp" id="ramp-chm"></span><span id="lab-chm"></span></label>
      <label class="t"><input type="checkbox" id="ov-tree"><span class="tri"></span><span id="lab-tree"></span></label>
      <label class="t"><input type="checkbox" id="ov-twi"><span class="ramp" id="ramp-twi"></span><span id="lab-twi"></span></label>
      <label class="t op"><span>Layer opacity</span><input type="range" id="rop" min="20" max="100" value="60" step="5" aria-label="Layer opacity"></label>
      <p class="meta" id="rastnote"></p>
      <p class="meta" id="note3d" hidden></p>
    </div>
    <div class="box">
      <h2>Stills</h2>
      <div class="row">
        <button class="ctl main" id="save">Save this frame</button>
        <button class="ctl" id="zoomreset">Reset zoom</button>
      </div>
      <label class="t"><input type="checkbox" id="burn" checked>Include legend layers in the still</label>
      <p class="msg" id="msg" role="status"></p>
      <p class="meta">Stills save at full resolution: <span id="fullres"></span>. Pinch, scroll or drag the image to zoom and pan. Zooming in swaps in the full-resolution frame.</p>
    </div>
  </div>
</div>
<div class="notes">
__NOTES__
</div>
</main>
<script>
const DATA=__DATA__;
const F=DATA.frames, V=DATA.views; const FC=['#ff8a3d','#ff4d6d','#ffd166','#d98cff'];
let view='w', idx=0, timer=null, hiTimer=null;
let Z={s:1,x:0,y:0};
const $=id=>document.getElementById(id);
const stage=$('stage'), layer=$('layer');
function build(){
  const v=V[view];
  layout();
  layer.innerHTML='';
  let pending=F.length; $('loading').hidden=false;
  F.forEach((f,i)=>{
    const im=new Image(); im.alt=f.date+' aerial image'; im.draggable=false; im.dataset.i=i;
    im.onload=im.onerror=()=>{ if(--pending<=0) $('loading').hidden=true; };
    im.src='frames/'+view+'s_'+f.id+'.jpg'; layer.appendChild(im);
  });
  const hi=new Image(); hi.id='hi'; hi.alt=''; hi.draggable=false; layer.appendChild(hi);
  RAST.forEach(r=>{ if(!(v.rast&&v.rast.includes(r.id))) return; const im=new Image(); im.className='rast'; im.alt=''; im.draggable=false; im.dataset.r=r.id; im.dataset.src='frames/o_'+r.id+'_'+view+'.webp'; layer.appendChild(im); });
  const ns='http://www.w3.org/2000/svg'; const svg=document.createElementNS(ns,'svg');
  svg.setAttribute('viewBox','0 0 '+v.w+' '+v.h); svg.setAttribute('preserveAspectRatio','none');
  [['o-stream',v.streams,'ov-stream'],['o-shed',v.watershed,'ov-shed'],['o-parcel',v.parcel,'ov-parcel']].forEach(([c,d,t])=>{
    const p=document.createElementNS(ns,'path'); p.setAttribute('class',c); p.setAttribute('d',d); p.dataset.t=t; svg.appendChild(p);
  });
  v.fires.forEach((f,i)=>{ const p=document.createElementNS(ns,'path'); p.setAttribute('class','o-fire'); p.setAttribute('d',f.d); p.style.stroke=f.color; p.dataset.t='ov-fire'; p.dataset.year=f.year; svg.appendChild(p); });
  if(v.trees&&v.trees.length){ const p=document.createElementNS(ns,'path'); p.setAttribute('class','o-tree'); p.setAttribute('d',treePath(v)); p.dataset.t='ov-tree'; svg.appendChild(p); }
  layer.appendChild(svg);
  $('firelist').innerHTML=v.fires.length?v.fires.map((f,i)=>'<li><span class="sw" style="border-color:'+f.color+'"></span>'+f.year+' '+f.name+' Fire, '+f.date+', '+f.acres.toLocaleString()+' acres</li>').join(''):'<li>No recorded perimeters in this view</li>';
  $('fullres').textContent=v.w+' by '+v.h+' pixels'+(v.res?', '+v.res+' m per pixel':'');
  resetZoom(); show(idx); scalebar();
}
function treePath(v){ const s=v.w/170/Math.min(v.res&&v.res<1?1.1:1.9,Math.max(1,Math.sqrt(v.trees.length/250))); return v.trees.map(t=>{ const k=s*(t[3]||1); return 'M'+(t[0]-k*0.6).toFixed(1)+' '+(t[1]+k*0.5).toFixed(1)+' L'+t[0]+' '+(t[1]-k*0.7).toFixed(1)+' L'+(t[0]+k*0.6).toFixed(1)+' '+(t[1]+k*0.5).toFixed(1)+'Z'; }).join(' '); }
function overlays(){ const yr=F[idx].year;
  layer.querySelectorAll('img.rast').forEach(im=>{ const on=$('ov-'+im.dataset.r).checked; if(on&&!im.src) im.src=im.dataset.src; im.classList.toggle('on',on); im.style.opacity=$('rop').value/100; }); layer.querySelectorAll('svg path').forEach(p=>{ p.style.display=$(p.dataset.t).checked?'':'none'; if(p.dataset.year){ const later=+p.dataset.year>yr; p.classList.toggle('later',later); } }); }
function show(i){
  idx=(i+F.length)%F.length; const f=F[idx];
  layer.querySelectorAll('img[data-i]').forEach(im=>im.classList.toggle('on',+im.dataset.i===idx));
  const hi=$('hi'); if(hi){ hi.classList.remove('on'); hi.removeAttribute('src'); }
  $('yr').textContent=f.label; $('dt').textContent=f.date; $('scrub').value=idx;
  document.querySelectorAll('#years button').forEach((b,k)=>b.setAttribute('aria-current',k===idx?'true':'false'));
  $('meta').innerHTML='<strong>'+f.date+'</strong>. '+f.source+'. Source resolution '+f.res+'.'+(f.note?' '+f.note+'.':'');
  overlays(); wantHi();
}
function wantHi(){
  clearTimeout(hiTimer);
  if(Z.s<1.4||timer) return;
  const want=idx, v=view;
  hiTimer=setTimeout(()=>{ const hi=$('hi'); if(!hi) return;
    hi.onload=()=>{ if(want===idx&&v===view) hi.classList.add('on'); };
    hi.src='frames/'+view+'_'+F[idx].id+'.jpg'; },250);
}
function play(on){
  if(on&&!timer){ timer=setInterval(()=>show(idx+1),+$('speed').value); $('play').textContent='Pause'; }
  else if(!on&&timer){ clearInterval(timer); timer=null; $('play').textContent='Play'; wantHi(); }
}
function scalebar(){
  const v=V[view]; if(!v.res) return; const pxPerM=stage.clientWidth/(v.w*v.res)*Z.s;
  const opts=[1000,500,200,100,50,20,10]; let m=opts.find(o=>o*pxPerM<=stage.clientWidth*0.3)||10;
  $('scbar').style.width=(m*pxPerM)+'px'; $('sclabel').textContent=m>=1000?(m/1000)+' km':m+' m';
}
let ROT=false;
function layout(){
  const v=V[view], a=v.w/v.h, wide=a>1.6, hold=$('hold'), st=stage.style;
  document.body.classList.toggle('wide',wide);
  const can=wide&&innerHeight>innerWidth; $('rot').hidden=!can; if(!can) ROT=false;
  $('rot').textContent=ROT?'Unrotate view':'Rotate view';
  if(ROT){ const Wc=hold.clientWidth, h0=Math.min(Wc,innerHeight*0.92/a), w0=h0*a;
    hold.style.height=w0+'px'; st.aspectRatio='auto'; st.width=w0+'px'; st.height=h0+'px'; st.maxWidth='none'; st.maxHeight='none'; st.margin='0';
    st.position='absolute'; st.top='0'; st.left=((Wc-h0)/2+h0)+'px'; st.transformOrigin='0 0'; st.transform='rotate(90deg)';
  } else { hold.style.height=''; ['width','height','maxHeight','margin','position','top','left','transformOrigin','transform'].forEach(k=>st[k]='');
    st.aspectRatio=v.w+' / '+v.h; st.maxWidth='calc('+(wide?88:82)+'vh * '+a.toFixed(4)+')'; }
}
function apply(){
  const w=stage.clientWidth,h=stage.clientHeight;
  Z.s=Math.min(12,Math.max(1,Z.s));
  Z.x=Math.min(0,Math.max(w-w*Z.s,Z.x)); Z.y=Math.min(0,Math.max(h-h*Z.s,Z.y));
  stage.style.touchAction=Z.s>1.01?'none':'pan-y'; layer.style.transform='translate('+Z.x+'px,'+Z.y+'px) scale('+Z.s+')'; scalebar(); wantHi();
}
function zoomAt(cx,cy,k){ const s0=Z.s; const s1=Math.min(12,Math.max(1,s0*k)); Z.x=cx-(cx-Z.x)*(s1/s0); Z.y=cy-(cy-Z.y)*(s1/s0); Z.s=s1; apply(); }
function resetZoom(){ Z={s:1,x:0,y:0}; apply(); }
const P=new Map(); let pd=0;
function loc(e){ const r=stage.getBoundingClientRect(); return ROT?[e.clientY-r.top,r.right-e.clientX]:[e.clientX-r.left,e.clientY-r.top]; }
stage.addEventListener('pointerdown',e=>{ stage.setPointerCapture(e.pointerId); P.set(e.pointerId,loc(e)); stage.classList.add('drag'); if(P.size===2){ const a=[...P.values()]; pd=Math.hypot(a[0][0]-a[1][0],a[0][1]-a[1][1]); } });
stage.addEventListener('pointermove',e=>{ if(!P.has(e.pointerId)) return; const prev=P.get(e.pointerId), cur=loc(e); P.set(e.pointerId,cur);
  if(P.size===1){ Z.x+=cur[0]-prev[0]; Z.y+=cur[1]-prev[1]; apply(); }
  else if(P.size===2){ const a=[...P.values()]; const d=Math.hypot(a[0][0]-a[1][0],a[0][1]-a[1][1]); if(pd>0) zoomAt((a[0][0]+a[1][0])/2,(a[0][1]+a[1][1])/2,d/pd); pd=d; } });
['pointerup','pointercancel'].forEach(t=>stage.addEventListener(t,e=>{ P.delete(e.pointerId); if(!P.size) stage.classList.remove('drag'); pd=0; }));
stage.addEventListener('wheel',e=>{ e.preventDefault(); const c=loc(e); zoomAt(c[0],c[1],e.deltaY<0?1.2:1/1.2); },{passive:false});
stage.addEventListener('dblclick',e=>{ const c=loc(e); if(Z.s>1.05) resetZoom(); else zoomAt(c[0],c[1],3); });
window.addEventListener('resize',()=>{ layout(); apply(); });
$('rot').onclick=()=>{ ROT=!ROT; layout(); resetZoom(); if(ROT) $('hold').scrollIntoView({block:'start'}); };
F.forEach((f,i)=>{ const b=document.createElement('button'); b.textContent=f.label; if(f.bw){ b.className='bw'; b.title='Black and white'; } b.onclick=()=>{ play(false); show(i); }; $('years').appendChild(b); });
$('scrub').max=F.length-1;
$('scrub').oninput=e=>{ play(false); show(+e.target.value); };
$('prev').onclick=()=>{ play(false); show(idx-1); };
$('next').onclick=()=>{ play(false); show(idx+1); };
$('play').onclick=()=>play(!timer);
$('speed').onchange=()=>{ if(timer){ play(false); play(true); } };
$('zoomreset').onclick=resetZoom;
['ov-parcel','ov-shed','ov-stream','ov-fire','ov-chm','ov-tree','ov-twi'].forEach(id=>$(id).onchange=overlays); $('rop').oninput=overlays;
const ORDER=DATA.order; const RAST=DATA.rasters||[]; const L=DATA.labels||{};
$('lab-parcel').textContent=L.parcel||'Parcel boundary'; $('lab-shed').textContent=L.shed||'Watershed boundary';
[['chm','ov-chm'],['twi','ov-twi']].forEach(([id,cb])=>{ const r=RAST.find(x=>x.id===id); if(r){ $('lab-'+id).textContent=r.label; $('ramp-'+id).style.background='linear-gradient(90deg,'+r.ramp.join(',')+')'; } else $(cb).closest('label').hidden=true; });
if(L.tree) $('lab-tree').textContent=L.tree; else $('ov-tree').closest('label').hidden=true;
if(!RAST.length){ $('rop').closest('label').hidden=true; } $('rastnote').textContent=L.rastnote||'';
ORDER.forEach(k=>{ const b=document.createElement('button'); b.id='tab-'+k; b.textContent=V[k].name; b.setAttribute('aria-pressed',k===view); b.onclick=()=>setView(k); $('tabs').appendChild(b); });
function setView(v){ view=v; ORDER.forEach(k=>$('tab-'+k).setAttribute('aria-pressed',v===k)); const flat=!!V[v].res; document.querySelector('.scale').hidden=document.querySelector('.north').hidden=!flat; $('note3d').hidden=flat; $('note3d').textContent=V[v].note||''; build(); }
document.addEventListener('keydown',e=>{ if(['INPUT','SELECT','BUTTON'].includes(e.target.tagName)&&e.key===' ') return;
  if(e.key===' '){ e.preventDefault(); play(!timer); } if(e.key==='ArrowRight'){ play(false); show(idx+1); } if(e.key==='ArrowLeft'){ play(false); show(idx-1); } });
function loadImg(src){ return new Promise((ok,no)=>{ const im=new Image(); im.onload=()=>ok(im); im.onerror=no; im.src=src; }); }
async function renderStill(im){
  const f=F[idx], v=V[view], W=im.naturalWidth, H=im.naturalHeight, k=W/v.w;
  const c=document.createElement('canvas'); c.width=W; c.height=H; const g=c.getContext('2d'); g.drawImage(im,0,0,W,H);
  if($('burn').checked){ for(const r of RAST){ if(v.rast&&v.rast.includes(r.id)&&$('ov-'+r.id).checked){ try{ const o=await loadImg('frames/o_'+r.id+'_'+view+'.webp'); g.globalAlpha=$('rop').value/100; g.drawImage(o,0,0,W,H); g.globalAlpha=1; }catch(e){} } } }
  if($('burn').checked){ g.save(); g.scale(k,k); g.lineJoin='round'; const lw=v.w/600;
    const draw=(id,d,col,w,dash)=>{ if(!$(id).checked) return; g.setLineDash(dash||[]); g.strokeStyle=col; g.lineWidth=w; g.stroke(new Path2D(d)); };
    draw('ov-stream',v.streams,'#7aa8ff',lw*1.3);
    if($('ov-fire').checked) v.fires.forEach((f2,i)=>{ g.setLineDash(f2.year>f.year?[lw*3,lw*6]:[]); g.strokeStyle=f2.color; g.lineWidth=lw*2.4; g.stroke(new Path2D(f2.d)); });
    draw('ov-shed',v.watershed,'#5fd4ff',lw*1.6,[lw*7,lw*5]); draw('ov-parcel',v.parcel,'#ffd23f',lw*2);
    if($('ov-tree').checked&&v.trees&&v.trees.length){ g.setLineDash([]); g.fillStyle='#ff4fd8'; g.strokeStyle='#1a0716'; g.lineWidth=lw*0.12; const tp=new Path2D(treePath(v)); g.fill(tp); g.stroke(tp); }
    g.restore(); }
  // year, date, north arrow and scale bar only
  const u=W/100, box=(x,y,w,h)=>{ g.fillStyle='rgba(10,12,14,.78)'; g.fillRect(x,y,w,h); };
  g.textBaseline='alphabetic'; g.textAlign='left';
  g.font='500 '+(u*3.2)+'px monospace'; const wy=g.measureText(f.label).width; g.font=(u*1.5)+'px sans-serif'; const wd=g.measureText(f.date).width;
  box(u,u,Math.max(wy,wd)+u*1.6,u*6.6); g.fillStyle='#e6e9e4'; g.font='500 '+(u*3.2)+'px monospace'; g.fillText(f.label,u*1.8,u*4.4); g.fillStyle='#98a39f'; g.font=(u*1.5)+'px sans-serif'; g.fillText(f.date,u*1.8,u*6.6);
  if(v.res){ g.font=(u*1.6)+'px monospace'; const wn=g.measureText('N \u2191').width; box(W-u*2.2-wn,u,wn+u*1.2,u*2.8); g.fillStyle='#e6e9e4'; g.fillText('N \u2191',W-u*1.6-wn,u*3);
  const pxm=W/(v.w*v.res), m=[1000,500,200,100,50].find(o=>o*pxm<=W*0.3)||50, bw=m*pxm, lab=m>=1000?(m/1000)+' km':m+' m';
  box(W-bw-u*2.6,H-u*5,bw+u*1.6,u*4); g.fillStyle='#e6e9e4'; g.textAlign='center'; g.fillText(lab,W-u*1.8-bw/2,H-u*2.9); g.textAlign='left';
  g.strokeStyle='#e6e9e4'; g.lineWidth=u*0.18; g.beginPath(); g.moveTo(W-bw-u*1.8,H-u*2.4); g.lineTo(W-bw-u*1.8,H-u*1.7); g.lineTo(W-u*1.8,H-u*1.7); g.lineTo(W-u*1.8,H-u*2.4); g.stroke(); }
  return c;
}
/*SAVE-BEGIN*/
let downloads=null;
(async()=>{ try{ if(window.claude&&window.claude.use) downloads=await window.claude.use('downloads'); }catch(e){} })();
$('save').onclick=async()=>{
  const msg=$('msg'), f=F[idx], v=V[view]; play(false);
  if(!downloads){ msg.textContent='Saving is not available in this view. Open the page in a browser, or press and hold the image to save the screen-size frame.'; return; }
  msg.textContent='Preparing full-resolution frame';
  try{
    const c=await renderStill(await loadImg('frames/'+view+'_'+f.id+'.jpg'));
    const blob=await new Promise(r=>c.toBlob(r,'image/jpeg',0.93));
    await downloads.save({filename:(DATA.slug||'flipbook')+'_'+v.name.toLowerCase().replace(/[^a-z0-9]+/g,'_')+'_'+f.id+'.jpg',data:blob});
    msg.textContent='Saved '+f.label+' at '+c.width+' by '+c.height+' pixels.';
  }catch(e){ msg.textContent=(e&&e.code==='declined')?'Save cancelled.':'Could not save this frame'+(e&&e.code?' ('+e.code+')':'')+'. Press and hold the image to save the screen-size frame instead.'; }
};
/*SAVE-END*/
build();
</script>
</body>
</html>
