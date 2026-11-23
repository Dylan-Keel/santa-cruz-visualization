"""Download the selected UCSB FrameFinder scans and store them as grayscale (or color) JPEGs no wider than 7000 px."""
import json, os, requests, sys, time
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
by=json.load(open('ref/flights.json'))
SEL={'1941':('C_6660',['444','440','441'],5500),
     '1948':('CDF5',['1-68','1-92','1-93','1-94','4-7','4-8','4-9','4-10','4-11','4-12','2-36','2-38'],4570),
     '1956':('CJA_1956',['4R-166','4R-178','4R-179','4R-180','4R-182','9R-54','9R-53','9R-52','9R-51','9R-50','9R-49','9R-48'],4570),
     '1963':('CAS_SCR',['1-24','1-42','1-43','1-44','1-46','1-48','1-60','1-62','1-64','1-66','1-67'],4570),
     '1985':('WAC_85CA',['13-22','13-24','13-63','13-64','13-65','13-66','13-68'],7240),
     '1993':('NAPP_2C',['6354-35'],9140),
     '1998':('NAPP_3C',['10532-86'],9140)}      # frames added for Big Creek; the Scott Creek frames are already in scans/
L=[]
for tag in (sys.argv[1:] or list(SEL)):
    fl,frames,foot=SEL[tag]
    for fr in frames:
        f=[x for x in by[fl] if x['frame']==fr][0]; b=f"{tag}_{fl}_{fr}"; out=f'scans/{b}.jpg'
        L.append(dict(tag=tag,title=f"{fl}_{fr}",b=b,x=f['x'],y=f['y'],foot=foot,url=f['url']))
        if os.path.exists(out): continue
        for k in range(3):
            try:
                with requests.get(f['url'],stream=True,timeout=600) as r, open('/tmp/dl.tif','wb') as o:
                    for ch in r.iter_content(1<<22): o.write(ch)
                im=Image.open('/tmp/dl.tif'); W,H=im.size; mode=im.mode
                if mode.startswith('I') or mode=='F':
                    import numpy as np
                    a=np.asarray(im).astype('float32'); lo,hi=np.percentile(a[::8,::8],[0.2,99.8]); im=Image.fromarray(np.clip((a-lo)/(hi-lo)*255,0,255).astype('uint8'))
                if max(W,H)>7000: im=im.resize((int(W*7000/max(W,H)),int(H*7000/max(W,H))),Image.LANCZOS)
                im=im.convert('RGB' if mode in('RGB','RGBA','CMYK') else 'L'); im.save(out,quality=92); print(b,W,H,mode,'->',im.size,flush=True); break
            except Exception as e: print('retry',b,str(e)[:100],flush=True); time.sleep(5)
old=json.load(open('dl_list.json')) if os.path.exists('dl_list.json') else []
json.dump([o for o in old if o['b'] not in {l['b'] for l in L}]+L,open('dl_list.json','w'),indent=0)
