"""Work backward in time: fit each year's frames (fitall.py) against terrain and the later mosaics, tighten each pose
against those mosaics (refine.py), then build the year's mosaic (mos.py). python3 chain.py [years...]"""
import subprocess, glob, os, sys, json, numpy as np, cv2
import refine, mos, geo
from cfg import *
D={d['b']:d for d in json.load(open('dl_list.json'))}
steps=[('1998',['county_2003','naip_2012']),('1993',['h1998','county_2003']),('1985',['h1993','h1998']),('1963',['h1985','h1993']),
       ('1956',['h1963','h1985']),('1948',['h1956','h1963']),('1941',['h1948','h1956'])]
def comp(tags):
    out=None
    for t in tags:
        a=refine.load_ref(t)
        if out is None: out=a.copy()
        else: m=out==0; out[m]=a[m]
    return out
def sane(b,pf):
    z=np.load(pf,allow_pickle=True); C=-cv2.Rodrigues(z['rv'])[0].T@z['tv'].ravel(); c=(C[0]+geo.X0,C[1]+geo.Y0,C[2]); d=D[b]
    return np.hypot(c[0]-d['x'],c[1]-d['y'])<3500 and 0.4*d['foot']<c[2]-geo.zat(np.array([c[0]]),np.array([c[1]]))[0]<2.6*d['foot']
for tag,refs in steps:
    if sys.argv[1:] and tag not in sys.argv[1:]: continue
    refs=[r for r in refs if os.path.exists(f'master/{r}_x.tif')]
    subprocess.run([sys.executable,'fitall.py',tag]+refs)      # only frames without a pose are fitted
    ref=comp(refs); frames=[]; used=[]
    ref6=cv2.resize(ref,(ref.shape[1]//2,ref.shape[0]//2),interpolation=cv2.INTER_AREA); ref6[cv2.resize((ref==0).astype(np.uint8),(ref6.shape[1],ref6.shape[0]),interpolation=cv2.INTER_AREA)>0]=0
    for sp in sorted(glob.glob(f'scans/{tag}_*.jpg')):
        b=os.path.basename(sp)[:-4]; pf=f'fit_a/{b}.npz'; p2=f'fit_b/{b}.npz'
        if not os.path.exists(pf): print(b,'no pose',flush=True); continue
        if os.path.exists(p2): frames.append((sp,p2)); used.append(b); continue      # refined in the first build
        r=None
        for cand in [pf]+[q for q in sorted(glob.glob(pf.replace('.npz','.alt*.npz'))) if os.path.getmtime(q)>=os.path.getmtime(pf)-600]:      # each focal length candidate; keep the tightest
            rr=None
            for rf,kw in ((ref,{}),(ref6,dict(refres=RX*2,win=30,search=10,step=150))):
                try: rr=refine.refine(sp,cand,rf,'/tmp/ref_try.npz',verbose=False,**kw)
                except Exception as e: rr=None
                if rr and rr[0]>=60: break
            print('  ',os.path.basename(cand),rr,flush=True)
            if rr and sane(b,'/tmp/ref_try.npz') and (r is None or (rr[0]>1.15*r[0]) or (rr[0]>0.85*r[0] and rr[1]<r[1])): r=rr; os.replace('/tmp/ref_try.npz',p2)
        if r is None:
            print(b,'refine failed, keeping terrain fit',r,flush=True); frames.append((sp,pf)); used.append(b+'*'); continue
        print(b,'refined',r,flush=True); frames.append((sp,p2)); used.append(b)
    import mos2; cov=dict(mos2.mosaic('h'+tag,frames) or {}); cov['used']=used
    json.dump(cov,open(f'master/h{tag}_cov.json','w')); print(tag,'mosaic',cov,flush=True)
