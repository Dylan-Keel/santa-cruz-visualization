"""Fit a camera pose to each scanned frame: python3 fitall.py <tag> <ref mosaic tags...> [-- part n]
1. Coarse: slide the frame (four orientations, three scales) over hillshades of the 10 m elevation model and over
   later-date mosaics, within 3 km of the UCSB FrameFinder centre point.
2. Fine: dense template matches against the winning reference, then a perspective camera solve on the terrain."""
import geo, json, sys, os, glob, numpy as np, time, cv2
from geo import *
args=[a for a in sys.argv[1:] if a not in('-v','-f')]; part,n=0,1
if '--' in args: i=args.index('--'); part,n=int(args[i+1]),int(args[i+2]); args=args[:i]
ONLY=[a[5:] for a in args if a.startswith('only=')]; args=[a for a in args if not a.startswith('only=')]; tag,refs=args[0],args[1:]
D={d['b']:d for d in json.load(open('dl_list.json'))}
R={s:geo.HSF(*s) for s in ((150,45),(215,45))}
for i,t in enumerate(refs): R[('img',i)]=geo.image_ref(f'master/{t}_x.tif',VX,RX)
CF={'1941':(0.26,0.07,0.115,0.13)}.get(tag,0.05)
g=20.0; hp2=lambda a,s=15:cv2.GaussianBlur(a,(0,0),1.0)-cv2.GaussianBlur(a,(0,0),s)
RC={k:cv2.resize(v,None,fx=.5,fy=.5,interpolation=cv2.INTER_AREA) for k,v in R.items()}
rng=np.random.default_rng(0)
RC={k:(v+rng.normal(0,0.6*v[v!=0].std(),v.shape)*(cv2.GaussianBlur((np.abs(v)<1e-3).astype(np.float32),(0,0),3)>0.5)).astype(np.float32) for k,v in RC.items()}   # noise over flat water and no-data so they cannot win the correlation
def coarse(a,x,y,foot,rad=3000,angles=(0,)):
    out=[]
    for sc in (1.0,0.88,1.14,0.78,1.3):
        wpx=int(foot*sc/g); t0=cv2.resize(a,(wpx,int(wpx*a.shape[0]/a.shape[1])),interpolation=cv2.INTER_AREA).astype(np.float32)
        for k4 in [(q,ang) for q in range(4) for ang in angles]:
            tb=np.ascontiguousarray(np.rot90(t0,k4[0]))
            if k4[1]: hh,ww=tb.shape; tb=cv2.warpAffine(tb,cv2.getRotationMatrix2D((ww/2,hh/2),k4[1],1.0),(ww,hh),borderMode=cv2.BORDER_REFLECT)
            t=hp2(tb); m=int(min(t.shape)*(0.12 if foot<6000 else 0.25)) if len(angles)==1 else int(min(t.shape)*0.2); t=t[m:-m,m:-m]; th,tw=t.shape
            c0=int((x-OX)/g); r0=int((OY-y)/g); rr=int(rad/g)
            ra,rb=r0-th//2-rr,r0+th//2+rr+th%2; ca,cb=c0-tw//2-rr,c0+tw//2+rr+tw%2
            ra,ca=max(ra,0),max(ca,0); rb,cb=min(rb,900),min(cb,900)
            if rb-ra<th+10 or cb-ca<tw+10: continue
            for k,ref in RC.items():
                res=cv2.matchTemplate(ref[ra:rb,ca:cb],t,cv2.TM_CCOEFF_NORMED); _,mx,_,lc=cv2.minMaxLoc(res)
                z=(mx-res.mean())/(res.std()+1e-6)
                out.append((z,mx,k,sc,k4,OX+(ca+lc[0]+tw/2)*g,OY-(ra+lc[1]+th/2)*g))
    out.sort(key=lambda o:-o[0]); return out
FFS=dict([('1998',(0.74,)),('1993',(0.74,)),('1985',(0.74,1.02))]).get(tag,(0.74,1.02,1.48))
def fit2(scan,cx,cy,mpp,key,verbose=False,rots=(0,90,180,270)):
    h,w=scan.shape; HS=R[key]; half=mpp*max(scan.shape)/2; b=(int(cx-half),int(cy-half),int(cx+half),int(cy+half)); best=None
    for rot in rots:
        K,d,rv,tv=init_pose(cx,cy,mpp,rot,0.9*w,w,h); s=score(scan,K,d,rv,tv,HS,b)
        if best is None or s>best[0]: best=(s,rot)
    s0,rot=best; out=None; alts=[]
    ws=min(1.0,max(0.5,(2*half)/4500.0)); st=max(1.0,(2*half)/5000.0)
    for ff in FFS:
        K,d,rv,tv=init_pose(cx,cy,mpp,rot,ff*w,w,h); ninl=0; med=99; s=s0
        for it,(step,win,search,ms,tol) in enumerate([(int(250*st),int(45*ws),int(30*ws),0.3,6.0),(int(200*st),int(35*ws),int(15*ws),0.35,4.0),(int(150*st),int(30*ws),8,0.35,3.0)]):
            P,p=dense(scan,K,d,rv,tv,HS,b,step,win,search,ms,0.04)
            if len(P)<15: break
            ok,rv2,tv2,inl=cv2.solvePnPRansac(P,p,K,d,rvec=rv.copy(),tvec=tv.copy(),useExtrinsicGuess=True,iterationsCount=5000,reprojectionError=tol,flags=cv2.SOLVEPNP_ITERATIVE)
            if inl is None or len(inl)<12: break
            inl=inl.ravel(); rv,tv=rv2,tv2
            e=np.linalg.norm(proj(P[inl],K,d,rv,tv)-p[inl],axis=1); ninl=len(inl); med=float(np.median(e)); s=score(scan,K,d,rv,tv,HS,b)
        C=-cv2.Rodrigues(rv)[0].T@tv.ravel()
        r=dict(K=K,d=d,rv=rv,tv=tv,inl=ninl,med=med,score=s,cam=(C[0]+X0,C[1]+Y0,C[2]),sun=key,rot=rot,s0=s0,ff=ff)
        if verbose: print('   ff',ff,'inl',ninl,'med',round(med,2),'score',round(s,3),'cam',[round(c) for c in r['cam']],flush=True)
        if out is None or (r['inl'],r['score'])>(out['inl'],out['score']): out=r
        alts.append(r)
    out['alts']=[a for a in alts if a is not out and a['inl']>=0.6*out['inl']]
    return out
for path in [p_ for p_ in sorted(glob.glob(f'scans/{tag}_*.jpg'))[part::n] if not ONLY or any(o in p_ for o in ONLY)]:
    b=os.path.basename(path)[:-4]; out=f'fit_a/{b}.npz'
    if b not in D or '.alt' in b or (os.path.exists(out) and '-f' not in sys.argv): continue
    d=D[b]; t0=time.time(); cf_=(0.04,0.10,0.04,0.05) if 'C_7054' in b else CF; a=geo.load(path,cf_); foot=d['foot']*(a.shape[1]/(a.shape[1]/(1-(CF[0]+CF[2] if isinstance(CF,tuple) else 2*CF))))
    if tag=='1941': foot=5100.0 if 'C_6660' in b else 3540.0*0.9
    diag='C_7054' in b      # flight line runs along the coast, so the prints are not square to north
    C=coarse(a,d['x'],d['y'],foot,angles=(0,15,30,45,60,75) if diag else (0,)); best=None; seen=[]
    for z,mx,key,sc,k4,cx,cy in C[:12]:
        if any(abs(cx-u)<300 and abs(cy-v)<300 and abs(sc-w_)<0.05 and key==kk for u,v,w_,kk in seen): continue
        seen.append((cx,cy,sc,key))
        if len(seen)>4: break
        s=640/a.shape[1]; small=cv2.resize(a,None,fx=s,fy=s,interpolation=cv2.INTER_AREA)
        f=fit2(small,cx,cy,foot*sc/640,key,verbose='-v' in sys.argv,rots=tuple(range(0,360,15)) if diag else (0,90,180,270)); f['z']=z; f['sc']=sc
        if best is None or (f['inl'],f['score'])>(best['inl'],best['score']): best=f
        if best['inl']>=70 and best['score']>0.18: break
    f=best
    if f is None: print(b,'FAILED',flush=True); continue
    K=f['K'].copy(); sx=a.shape[1]/640; K[0]*=sx; K[1]*=sx
    h=f['cam'][2]-geo.zat(np.array([f['cam'][0]]),np.array([f['cam'][1]]))[0]
    ok=((f["inl"]>=35 and f["score"]>0.10) or (f["score"]==-1 and f["inl"]>=150)) and 0.4*d['foot']<h<2.6*d['foot'] and np.hypot(f['cam'][0]-d['x'],f['cam'][1]-d['y'])<3500
    print(b,'rot',f['rot'],'inl',f['inl'],'med %.2f'%f['med'],'score %.3f'%f['score'],'ref',f['sun'],'z %.1f sc %.2f'%(f['z'],f['sc']),'cam %.0f %.0f %.0f'%f['cam'],'pred',d['x'],d['y'],'h/foot %.2f ff %.2f'%(h/d['foot'],f['ff']),'tried',len(seen),'sec',round(time.time()-t0),'OK' if ok else 'REJECT',flush=True)
    for j,al in enumerate(f['alts'] if ok else []):
        Ka=al['K'].copy(); Ka[0]*=sx; Ka[1]*=sx; np.savez(out.replace('.npz',f'.alt{j}.npz'),K=Ka,d=al['d'],rv=al['rv'],tv=al['tv'],cam=al['cam'],cf=cf_,inl=al['inl'],score=al['score'],med=al['med'],rot=al['rot'])
    np.savez(out if ok else out.replace('.npz','.rej.npz'),K=K,d=f['d'],rv=f['rv'],tv=f['tv'],cam=f['cam'],cf=cf_,inl=f['inl'],score=f['score'],med=f['med'],rot=f['rot'])
