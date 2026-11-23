"""Final mosaics for the historic years: python3 mos2.py <year>...
Same nearest-camera seams as mos.py, with two changes for these flights: the projection is solved on every fourth pixel
and interpolated (the 10 m elevation model has no finer detail to use), and each frame is flat-fielded before tone
matching, because the 1985 and 1941 prints fall off strongly toward the corners."""
import numpy as np, cv2, json, sys, os, rasterio
from rasterio.transform import from_origin
import geo
from geo import zat, proj, X0, Y0
from cfg import *
def ortho_fast(scan,K,d,rv,tv,bounds,res,sub=4):
    x0,y0,x1,y1=bounds; W=int(round((x1-x0)/res)); H=int(round((y1-y0)/res))
    xs=x0+(np.arange(0,W+sub,sub)+.5)*res; ys=y1-(np.arange(0,H+sub,sub)+.5)*res
    LX,LY=np.meshgrid(xs,ys); LZ=zat(LX,LY); q=np.zeros(LX.shape+(2,),np.float32)
    for r0 in range(0,LX.shape[0],100):
        s=slice(r0,r0+100); q[s]=proj(np.c_[LX[s].ravel()-X0,LY[s].ravel()-Y0,LZ[s].ravel()],K,d,rv,tv).reshape(LX[s].shape+(2,))
    # node (i,j) sits at pixel centre (j*sub, i*sub); upsample the map to every pixel
    M=np.float32([[1/sub,0,0],[0,1/sub,0]])
    mx=cv2.warpAffine(q[...,0],M,(W,H),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REPLICATE)
    my=cv2.warpAffine(q[...,1],M,(W,H),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REPLICATE)
    h,w=scan.shape; ok=(mx>2)&(mx<w-3)&(my>2)&(my<h-3)      # valid where the ground point falls inside the print, so black shadow pixels are kept
    return np.maximum(cv2.remap(scan,mx,my,cv2.INTER_CUBIC),1)*ok, ok
def flat(o,vv,res,sig_m=900.0,gain=0.85):
    k=max(1,int(round(60/res))); s=cv2.resize(o,(o.shape[1]//k,o.shape[0]//k),interpolation=cv2.INTER_AREA); w=cv2.resize(vv.astype(np.float32),(s.shape[1],s.shape[0]),interpolation=cv2.INTER_AREA)
    sg=sig_m/(res*k); lo=cv2.GaussianBlur(s*w,(0,0),sg)/np.maximum(cv2.GaussianBlur(w,(0,0),sg),1e-3)
    lo=cv2.resize(lo,(o.shape[1],o.shape[0]),interpolation=cv2.INTER_LINEAR); m=float(o[vv].mean())
    return np.clip(o*(m/np.maximum(lo,8))**gain,1,255)
def mosaic(tag,frames):
    scans=[]
    for path,pf in frames:
        z=dict(np.load(pf,allow_pickle=True)); cf=z['cf'].tolist() if z['cf'].ndim else float(z['cf']); scans.append((geo.load(path,cf),z))
    cov={}
    for k,(v,r) in ALLV.items():
        W,H=size(v,r); xs=v[0]+(np.arange(W,dtype=np.float32)+.5)*r; ys=v[3]-(np.arange(H,dtype=np.float32)+.5)*r
        best=np.full((H,W),1e12,np.float32); out=np.zeros((H,W),np.float32); L=[]
        for a,z in scans:
            o,ok=ortho_fast(a,z['K'],z['d'],z['rv'],z['tv'],v,r); o=o.astype(np.float32)
            e=max(3,int(40/r))|1; vv=cv2.erode(ok.astype(np.uint8),np.ones((e,e),np.uint8)).astype(bool)
            if vv.sum()<1000: continue
            L.append([flat(o,vv,r).astype(np.uint8),vv,(float(z['cam'][0]),float(z['cam'][1]))])
        if not L: cov[k]=0; continue
        L.sort(key=lambda l:-l[1].sum()); c0=L[0][2]; L=[L[0]]+sorted(L[1:],key=lambda l:(l[2][0]-c0[0])**2+(l[2][1]-c0[1])**2)
        for i,(o,vv,cm) in enumerate(L):     # outward from the largest frame, each one tone-matched to what is already placed
            o=o.astype(np.float32); d2=(xs[None,:]-cm[0])**2+(ys[:,None]-cm[1])**2; ov=vv&(best<1e11)
            if i>0 and ov.sum()>20000: a_,b_=o[ov].std(),out[ov].std(); o=(o-o[ov].mean())*(b_/max(a_,1e-3))+out[ov].mean()
            m=vv&(d2<best); out[m]=o[m]; best[m]=d2[m]
        lo,hi=np.percentile(out[best<1e11][::7],[0.7,99.5]); out=(out-lo)/(hi-lo)*235+10        # one contrast stretch for the whole year
        out=np.clip(out,1,255).astype(np.uint8); out[best>=1e11]=0; cov[k]=float((best<1e11).mean())
        with rasterio.open(f'master/{tag}_{k}.tif','w',driver='GTiff',width=W,height=H,count=1,dtype='uint8',crs='EPSG:26910',transform=from_origin(v[0],v[3],r,r),compress='deflate') as ds: ds.write(out,1)
        cv2.imwrite(f'master/{tag}_{k}_th.jpg',cv2.resize(out,(W//4,H//4),interpolation=cv2.INTER_AREA))
    return cov
if __name__=='__main__':
    for y in sys.argv[1:]:
        c=json.load(open(f'master/h{y}_cov.json')); fr=[]
        for u in c['used']: b=u.rstrip('*'); fr.append((f'scans/{b}.jpg',f"{'fit_a' if u.endswith('*') else 'fit_b'}/{b}.npz"))
        cov=mosaic('h'+y,fr); c.update(cov); json.dump(c,open(f'master/h{y}_cov.json','w')); print(y,cov,flush=True)
