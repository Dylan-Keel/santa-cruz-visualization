import numpy as np, cv2, rasterio, sys, os, json, glob
import geo
from geo import zat, proj, X0, Y0
from cfg import *
hp=lambda a,s=12:cv2.GaussianBlur(a,(0,0),1.0)-cv2.GaussianBlur(a,(0,0),s)
def gray(path):
    a=rasterio.open(path).read()
    return a[0] if a.shape[0]==1 else cv2.cvtColor(np.ascontiguousarray(np.moveaxis(a[:3],0,-1)),cv2.COLOR_RGB2GRAY)
def load_ref(tag):
    g=gray(f'master/{tag}_x.tif')   # VX at RX
    nod=cv2.morphologyEx((g==0).astype(np.uint8),cv2.MORPH_OPEN,np.ones((15,15),np.uint8)).astype(bool)   # only large black areas are no-data; black shadow pixels are image
    g=np.maximum(g,1); g[nod]=0; return g
def refine(scanpath,posefile,ref,out,step=120,win=40,search=14,minscore=0.32,verbose=True,refres=None,hps=12):
    z=dict(np.load(posefile,allow_pickle=True)); cf=z['cf'].tolist() if z['cf'].ndim else float(z['cf'])
    a=geo.load(scanpath,cf); s=1600.0/a.shape[1]; sc=cv2.resize(a,None,fx=s,fy=s,interpolation=cv2.INTER_AREA); h,w=sc.shape
    K=z['K'].copy(); K[0]*=s; K[1]*=s; d=z['d']; rv=z['rv'].copy(); tv=z['tv'].copy()
    R=refres or RX; REF=hp(ref.astype(np.float32),hps); valid=ref>0
    for it,(st,sr) in enumerate(((step,search),(step*0.75,8))):
        xs=np.arange(VX[0]+300,VX[2]-300,st); ys=np.arange(VX[1]+300,VX[3]-300,st)
        GX,GY=np.meshgrid(xs,ys); GX=GX.ravel();GY=GY.ravel(); GZ=zat(GX,GY)
        c=proj(np.c_[GX-X0,GY-Y0,GZ],K,d,rv,tv); ok=(c[:,0]>40)&(c[:,0]<w-40)&(c[:,1]>40)&(c[:,1]<h-40)
        P=[];p=[]; Rr=win+sr
        for X,Y,Z in zip(GX[ok],GY[ok],GZ[ok]):
            cc=int((X-VX[0])/R); rr=int((VX[3]-Y)/R)
            if rr-win<0 or cc-win<0 or rr+win+1>ref.shape[0] or cc+win+1>ref.shape[1]: continue
            if not valid[rr-win:rr+win+1,cc-win:cc+win+1].all(): continue
            tm=REF[rr-win:rr+win+1,cc-win:cc+win+1]
            if tm.std()<4: continue
            xc=VX[0]+(cc+0.5)*R; yc=VX[3]-(rr+0.5)*R
            lx=xc+np.arange(-Rr,Rr+1)*R; ly=yc-np.arange(-Rr,Rr+1)*R; LX,LY=np.meshgrid(lx,ly); LZ=zat(LX,LY)
            q=proj(np.c_[LX.ravel()-X0,LY.ravel()-Y0,LZ.ravel()],K,d,rv,tv).astype('float32').reshape(LX.shape+(2,))
            patch=cv2.remap(sc,q[...,0],q[...,1],cv2.INTER_LINEAR)
            if (patch==0).mean()>0.05: continue
            res=cv2.matchTemplate(hp(patch.astype(np.float32),hps),tm,cv2.TM_CCOEFF_NORMED)
            _,mx,_,lc=cv2.minMaxLoc(res); r2=res.copy(); cv2.circle(r2,lc,4,-1,-1)
            if mx<minscore or mx-r2.max()<0.05: continue
            # template centre (xc,yc) found at patch pixel (lc+win): that scan pixel shows ground point (xc,yc)
            p.append(q[lc[1]+win,lc[0]+win]); P.append([xc-X0,yc-Y0,float(zat(np.array([xc]),np.array([yc]))[0])])
        P=np.array(P,np.float64); p=np.array(p,np.float64)
        if len(P)<25:
            if verbose: print('   few matches',len(P)); return None
        okk,rv2,tv2,inl=cv2.solvePnPRansac(P,p,K,d,rvec=rv.copy(),tvec=tv.copy(),useExtrinsicGuess=True,iterationsCount=5000,reprojectionError=3.0,flags=cv2.SOLVEPNP_ITERATIVE)
        if inl is None or len(inl)<20: return None
        inl=inl.ravel(); rv,tv=rv2,tv2
        flags=cv2.CALIB_USE_INTRINSIC_GUESS|cv2.CALIB_FIX_ASPECT_RATIO|cv2.CALIB_ZERO_TANGENT_DIST|cv2.CALIB_FIX_K2|cv2.CALIB_FIX_K3|cv2.CALIB_FIX_PRINCIPAL_POINT
        if len(inl)<60: flags|=cv2.CALIB_FIX_K1
        try:
            rms,K2,d2,rvs,tvs=cv2.calibrateCamera([P[inl].astype(np.float32)],[p[inl].astype(np.float32)],(w,h),K.copy(),np.zeros(5),flags=flags)
            if 0.94<K2[0,0]/K[0,0]<1.06 and abs(d2.ravel()[0])<0.3: K,rv,tv,d=K2,rvs[0],tvs[0],d2.ravel()
        except Exception as e: pass
        e=np.linalg.norm(proj(P[inl],K,d,rv,tv)-p[inl],axis=1); gsd=R
        if verbose: print(f'   it{it} pts {len(P)} inl {len(inl)} med {np.median(e):.2f} px',flush=True)
    C=-cv2.Rodrigues(rv)[0].T@tv.ravel(); Kf=K.copy(); Kf[0]/=s; Kf[1]/=s
    np.savez(out,K=Kf,d=d,rv=rv,tv=tv,cam=(C[0]+X0,C[1]+Y0,C[2]),cf=z['cf'],inl=len(inl),score=z['score'],med=float(np.median(e)))
    return len(inl),float(np.median(e))
if __name__=='__main__':
    tag,reftag=sys.argv[1],sys.argv[2]; ref=load_ref(reftag); os.makedirs('pose2',exist_ok=True)
    for pf in sorted(glob.glob(f'pose/{tag}*.npz')):
        if pf.endswith('.rej.npz'): continue
        b=os.path.basename(pf)[:-4]; sp=f'scans/{b}.jpg' if os.path.exists(f'scans/{b}.jpg') else f'ucsb/{b}.tif'
        r=refine(sp,pf,ref,f'pose2/{b}.npz'); print(b,'->',r,flush=True)
