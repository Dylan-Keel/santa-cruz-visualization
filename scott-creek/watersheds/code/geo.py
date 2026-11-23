import numpy as np, cv2, rasterio, json, os, sys
from rasterio.transform import from_origin
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
from cfg import *
dem=rasterio.open('ref/dem10.tif').read(1); NDEM=dem.shape[0]
X0,Y0=CEN
G=10.0
def zat(X,Y):
    c=(np.asarray(X)-OX)/10.0-0.5; r=(OY-np.asarray(Y))/10.0-0.5
    c=c.astype('float32').ravel(); r=r.astype('float32').ravel(); n=c.size; pad=(-n)%1000
    c=np.pad(c,(0,pad)).reshape(-1,1000); r=np.pad(r,(0,pad)).reshape(-1,1000)
    o=np.concatenate([cv2.remap(dem,c[i:i+20000],r[i:i+20000],cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE) for i in range(0,len(c),20000)])
    return o.ravel()[:n].reshape(np.shape(X))
def proj(P,K,d,rv,tv): return cv2.projectPoints(P,rv,tv,K,d)[0].reshape(-1,2)
def ortho(scan,K,d,rv,tv,bounds,res,interp=cv2.INTER_CUBIC):
    x0,y0,x1,y1=bounds; W=int(round((x1-x0)/res)); H=int(round((y1-y0)/res))
    xs=x0+(np.arange(W)+.5)*res; ys=y1-(np.arange(H)+.5)*res
    out=np.zeros((H,W),scan.dtype)
    for r0 in range(0,H,160):
        LX,LY=np.meshgrid(xs,ys[r0:r0+160]); LZ=zat(LX,LY)
        q=proj(np.c_[LX.ravel()-X0,LY.ravel()-Y0,LZ.ravel()],K,d,rv,tv).astype('float32')
        out[r0:r0+160]=cv2.remap(scan,q[:,0].reshape(LX.shape),q[:,1].reshape(LX.shape),interp)
    return out
def init_pose(cx,cy,mpp,rotdeg,f,w,h):
    t=np.radians(rotdeg); c,s_=np.cos(t),np.sin(t)
    R=np.array([[c,-s_,0],[s_,c,0],[0,0,1.]])@np.array([[1,0,0],[0,-1,0],[0,0,-1.]])
    Z0=float(zat(np.array([cx]),np.array([cy]))[0]); C=np.array([cx-X0,cy-Y0,Z0+f*mpp])
    K=np.array([[f,0,w/2],[0,f,h/2],[0,0,1.]])
    return K,np.zeros(5),cv2.Rodrigues(R)[0],(-R@C).reshape(3,1)
def hillshade(az,alt):
    gy,gx=np.gradient(dem,10.0); az=np.radians(az); alt=np.radians(alt)
    nx=-gx; ny=gy; nz=np.ones_like(dem); nn=np.sqrt(nx*nx+ny*ny+nz*nz)
    return np.clip((nx*np.sin(az)*np.cos(alt)+ny*np.cos(az)*np.cos(alt)+nz*np.sin(alt))/nn,0,1).astype(np.float32)
hp=lambda a,s=12:cv2.GaussianBlur(a,(0,0),1.0)-cv2.GaussianBlur(a,(0,0),s)
_H={}
def HSF(az,alt,s=15):
    k=(az,alt)
    if k not in _H: _H[k]=hp(hillshade(az,alt)*255,s)
    return _H[k]
def score(scan,K,d,rv,tv,HS,b):
    o=ortho(scan,K,d,rv,tv,b,G).astype(np.float32); m=o>0
    if m.mean()<0.2: return -1
    r0=int((OY-b[3])/G); c0=int((b[0]-OX)/G)
    if r0<0 or c0<0: return -1
    r=HS[r0:r0+o.shape[0],c0:c0+o.shape[1]]
    if r.shape!=o.shape: return -1
    a=hp(o,15)[m]; bb=r[m]; a=a-a.mean(); bb=bb-bb.mean(); return float((a*bb).sum()/np.sqrt((a*a).sum()*(bb*bb).sum()+1e-9))
def dense(scan,K,d,rv,tv,HS,b,step,win,search,minscore,gap):
    h,w=scan.shape; wp=[];ip=[]
    xs=np.arange(b[0]-1500,b[2]+1500,step); ys=np.arange(b[1]-1500,b[3]+1500,step)
    GX,GY=np.meshgrid(xs,ys); GX=GX.ravel().astype(float);GY=GY.ravel().astype(float)
    ok=(GX>OX+600)&(GX<OX+NDEM*10-600)&(GY>OY-NDEM*10+600)&(GY<OY-600); GX=GX[ok];GY=GY[ok]; GZ=zat(GX,GY)
    c=proj(np.c_[GX-X0,GY-Y0,GZ],K,d,rv,tv); ok=(c[:,0]>20)&(c[:,0]<w-20)&(c[:,1]>20)&(c[:,1]<h-20)
    R=win+search
    for X,Y,Z in zip(GX[ok],GY[ok],GZ[ok]):
        lx=X+np.arange(-R,R+1)*G; ly=Y-np.arange(-R,R+1)*G; LX,LY=np.meshgrid(lx,ly); LZ=zat(LX,LY)
        q=proj(np.c_[LX.ravel()-X0,LY.ravel()-Y0,LZ.ravel()],K,d,rv,tv).astype('float32').reshape(LX.shape+(2,))
        patch=cv2.remap(scan,q[...,0],q[...,1],cv2.INTER_CUBIC)
        if (patch==0).mean()>0.15: continue
        cc=int((X-OX)/G); rr=int((OY-Y)/G); tm=HS[rr-win:rr+win+1,cc-win:cc+win+1]
        if tm.shape!=(2*win+1,2*win+1) or tm.std()<5: continue
        res=cv2.matchTemplate(hp(patch.astype(np.float32),15),tm,cv2.TM_CCOEFF_NORMED)
        _,mx,_,lc=cv2.minMaxLoc(res); r2=res.copy(); cv2.circle(r2,lc,5,-1,-1)
        if mx<minscore or mx-r2.max()<gap: continue
        ip.append(q[R+lc[1]-search,R+lc[0]-search]); wp.append([X-X0,Y-Y0,Z])
    return np.array(wp,np.float64),np.array(ip,np.float64)
REFS=None
def fit(a,cx,cy,mpp,rot,verbose=True,ffs=(0.67,0.92,1.33),wide=True):
    """a: cropped gray scan (small, ~1200 px). mpp: metres per pixel of a."""
    scan=a; h,w=scan.shape
    half=mpp*max(a.shape)/2; b=(int(cx-half),int(cy-half),int(cx+half),int(cy+half))
    best=None
    for az,alt in (((135,50),(180,50),(225,50),(200,35),(160,35),(110,40),(250,40)) if REFS is None else list(REFS)):
        HS=HSF(az,alt) if REFS is None else REFS[(az,alt)]
        for sgn in (1,-1):
            for ff in ffs:
                for ms in (0.92,1.0,1.08):
                    K,d,rv,tv=init_pose(cx,cy,mpp*ms,sgn*rot,ff*w,w,h); s=score(scan,K,d,rv,tv,HS,b)
                    if best is None or s>best[0]: best=(s,K,d,rv,tv,(az,alt),ff,sgn,ms)
    s0,_,_,_,_,sun,ff,sgn,ms=best; HS=HSF(*sun) if REFS is None else REFS[sun]
    sh=350 if wide else 150
    for dr in (-5,0,5):
        for dx in (-sh,0,sh):
            for dy in (-sh,0,sh):
                K,d,rv,tv=init_pose(cx+dx,cy+dy,mpp*ms,sgn*rot+dr,ff*w,w,h); s=score(scan,K,d,rv,tv,HS,b)
                if s>best[0]: best=(s,K,d,rv,tv,sun,ff,sgn,ms)
    s,K,d,rv,tv,sun,ff=best[:7]; HS=HSF(*sun) if REFS is None else REFS[sun]
    if verbose: print('init score %.3f sun %s f/w %.2f'%(s,sun,ff),flush=True)
    ninl=0; med=99
    ws=min(1.0,max(0.5,(2*half)/4500.0))
    for it,(step,win,search,ms) in enumerate([(int(250*ws),int(45*ws),int(30*ws),0.3),(int(200*ws),int(35*ws),int(15*ws),0.35),(int(150*ws),int(30*ws),8,0.35)]):
        P,p=dense(scan,K,d,rv,tv,HS,b,step,win,search,ms,0.04)
        if len(P)<15:
            if verbose: print('  too few matches',len(P))
            break
        ok,rv2,tv2,inl=cv2.solvePnPRansac(P,p,K,d,rvec=rv.copy(),tvec=tv.copy(),useExtrinsicGuess=True,iterationsCount=5000,reprojectionError=6.0,flags=cv2.SOLVEPNP_ITERATIVE)
        if inl is None or len(inl)<12: break
        inl=inl.ravel(); rv,tv=rv2,tv2
        flags=cv2.CALIB_USE_INTRINSIC_GUESS|cv2.CALIB_FIX_ASPECT_RATIO|cv2.CALIB_ZERO_TANGENT_DIST|cv2.CALIB_FIX_K1|cv2.CALIB_FIX_K2|cv2.CALIB_FIX_K3|cv2.CALIB_FIX_PRINCIPAL_POINT
        try:
            rms,K2,d2,rvs,tvs=cv2.calibrateCamera([P[inl].astype(np.float32)],[p[inl].astype(np.float32)],(w,h),K.copy(),np.zeros(5),flags=flags)
            if 0.5<K2[0,0]/K[0,0]<2: K,rv,tv=K2,rvs[0],tvs[0]
        except Exception as e: pass
        e=np.linalg.norm(proj(P[inl],K,d,rv,tv)-p[inl],axis=1); ninl=len(inl); med=float(np.median(e))
        s=score(scan,K,d,rv,tv,HS,b)
        if verbose:
            C=-cv2.Rodrigues(rv)[0].T@tv.ravel(); print(f'  iter {it}: pts {len(P)} inl {ninl} med {med:.2f} px  f/w {K[0,0]/w:.2f}  cam {C[0]+X0:.0f},{C[1]+Y0:.0f},{C[2]:.0f}  score {s:.3f}',flush=True)
    C=-cv2.Rodrigues(rv)[0].T@tv.ravel()
    return dict(K=K,d=d,rv=rv,tv=tv,inl=ninl,med=med,score=s,cam=(C[0]+X0,C[1]+Y0,C[2]),sun=sun,wh=(w,h))
WFIT=1200
def load(path,cf):
    im=Image.open(path).convert('L'); a=np.asarray(im); H,W=a.shape
    if isinstance(cf,(int,float)): cf=(cf,cf,cf,cf)   # left, top, right, bottom fractions
    return a[int(H*cf[1]):int(H*(1-cf[3])),int(W*cf[0]):int(W*(1-cf[2]))]
def fit_file(path,cx,cy,foot,rot,cf=0.08,**kw):
    """foot: ground width covered by the cropped frame (m)."""
    a=load(path,cf); s=WFIT/a.shape[1]; small=cv2.resize(a,None,fx=s,fy=s,interpolation=cv2.INTER_AREA)
    f=fit(small,cx,cy,foot/WFIT,rot,**kw)
    K=f['K'].copy(); sx=a.shape[1]/small.shape[1]; sy=a.shape[0]/small.shape[0]
    K[0,0]*=sx; K[1,1]*=sy; K[0,2]*=sx; K[1,2]*=sy; f['K_full']=K; f['cf']=cf
    return f
def best_fit(path,cx,cy,foot,rot,cf=0.08,tries=((1,0,0),(0.9,0,0),(1.1,0,0),(1,300,300),(1,-300,-300),(0.95,300,-300),(1.05,-300,300),(1.2,0,0),(0.82,0,0)),verbose=False):
    f=None
    for mf,dx,dy in tries:
        try: g=fit_file(path,cx+dx,cy+dy,foot*mf,rot,cf,verbose=verbose)
        except Exception as e: print('fit error',str(e)[:100],flush=True); continue
        if f is None or (g['inl'],g['score'])>(f['inl'],f['score']): f=g
        if f['inl']>=60 and f['score']>0.15: break
    return f

def image_ref(path,view,res):
    """resample an ortho (gray, 0 = nodata) onto the DEM grid and high-pass it, for use in REFS"""
    a=rasterio.open(path).read(1).astype(np.float32); out=np.zeros(dem.shape,np.float32)
    b=cv2.resize(a,(int(round(a.shape[1]*res/10)),int(round(a.shape[0]*res/10))),interpolation=cv2.INTER_AREA)   # any view resolution onto the 10 m grid
    r0=int((OY-view[3])/10); c0=int((view[0]-OX)/10); out[r0:r0+b.shape[0],c0:c0+b.shape[1]]=b
    m=out>0; f=hp(out,15); f[~cv2.erode(m.astype(np.uint8),np.ones((9,9),np.uint8)).astype(bool)]=0
    return f
