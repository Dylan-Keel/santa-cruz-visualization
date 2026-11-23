"""Make the flat, hosted copy of a flipbook: python3 stage.py <site dir> <output dir>.
Frames sit beside index.html, and the save button uses a plain browser download."""
import sys, os, shutil, re
src,out=sys.argv[1],sys.argv[2]; os.makedirs(out,exist_ok=True)
h=open(f'{src}/site/index.html').read()
a=h.index('/*SAVE-BEGIN*/'); b=h.index('/*SAVE-END*/')+len('/*SAVE-END*/')
save='''$('save').onclick=async()=>{
  const msg=$('msg'), f=F[idx], v=V[view]; play(false);
  msg.textContent='Preparing full-resolution frame';
  try{
    const c=await renderStill(await loadImg('frames/'+view+'_'+f.id+'.jpg'));
    const blob=await new Promise(r=>c.toBlob(r,'image/jpeg',0.93));
    const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=(DATA.slug||'flipbook')+'_'+v.name.toLowerCase().replace(/[^a-z0-9]+/g,'_')+'_'+f.id+'.jpg';
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(a.href),5000);
    msg.textContent='Saved '+f.label+' at '+c.width+' by '+c.height+' pixels.';
  }catch(e){ msg.textContent='Could not save this frame. Press and hold the image to save the screen-size frame instead.'; }
};'''
h=(h[:a]+save+h[b:]).replace("'frames/","'")
assert 'frames/' not in h.replace('site/frames','')
open(f'{out}/index.html','w').write(h)
n=0
for f in os.listdir(f'{src}/site/frames'):
    if f.endswith(('.jpg','.webp')): shutil.copy(f'{src}/site/frames/{f}',f'{out}/{f}'); n+=1
print(out,n,'files',round(sum(os.path.getsize(f'{out}/{f}') for f in os.listdir(out))/1e6,1),'MB')
