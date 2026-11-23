import numpy as np, cv2, json, rasterio, os, sys
from shapely.geometry import LineString
from PIL import Image
import geo
from geo import zat
from cfg import *
W,H=1600,1200
class Cam:
    def __init__(s,name,pos,az,pitch,hfov):
        s.name=name; s.C=np.array(pos,float); a=np.radians(az); p=np.radians(pitch)
        s.f=np.array([np.sin(a)*np.cos(p),np.cos(a)*np.cos(p),-np.sin(p)])
        s.r=np.array([np.cos(a),-np.sin(a),0.]); s.u=np.cross(s.r,s.f); s.fpx=(W/2)/np.tan(np.radians(hfov)/2)
    def ground_map(s):
        fn=f'v3d/gmap_{s.name}.npz'
        if os.path.exists(fn):
            z=np.load(fn); return z['X'],z['Y'],z['D']
        I,J=np.meshgrid(np.arange(W)+.5,np.arange(H)+.5)
        d=s.f[None,None,:]*s.fpx+s.r[None,None,:]*(I-W/2)[...,None]+s.u[None,None,:]*(H/2-J)[...,None]; d/=np.linalg.norm(d,axis=2,keepdims=True)
        d=d.reshape(-1,3); n=len(d)
        hit=np.zeros(n,bool); tlo=np.zeros(n); thi=np.zeros(n); t=100.0; tprev=np.full(n,100.0)
        while t<17000:
            P=s.C+d*t; inb=(P[:,0]>OX+100)&(P[:,0]<OX+17900)&(P[:,1]>OY-17900)&(P[:,1]<OY-100)
            zt=np.where(inb,zat(P[:,0],P[:,1]),-1e9)
            new=(~hit)&inb&(P[:,2]<=zt)
            tlo[new]=tprev[new]; thi[new]=t; hit|=new
            tprev[~hit]=t; t+=max(4.0,t*0.005)
        for _ in range(10):
            tm=(tlo+thi)/2; P=s.C+d*tm[:,None]; below=P[:,2]<=zat(P[:,0],P[:,1]); thi=np.where(below,tm,thi); tlo=np.where(below,tlo,tm)
        tm=(tlo+thi)/2; P=s.C+d*tm[:,None]
        X=np.where(hit,P[:,0],np.nan).reshape(H,W).astype(np.float32); Y=np.where(hit,P[:,1],np.nan).reshape(H,W).astype(np.float32); D=np.where(hit,tm,np.inf).reshape(H,W).astype(np.float32)
        np.savez(fn,X=X,Y=Y,D=D); return X,Y,D
    def project(s,x,y):
        z=zat(np.asarray(x,float),np.asarray(y,float))+3.0; P=np.c_[x,y,z]-s.C
        zc=P@s.f; xc=P@s.r; yc=P@s.u; i=W/2+s.fpx*xc/zc; j=H/2-s.fpx*yc/zc; return i,j,np.linalg.norm(P,axis=1),zc
    def path3d(s,geom,D,step=6.0):
        out=[]; lines=[]
        if geom is None or geom.is_empty: return ''
        for g in getattr(geom,'geoms',[geom]):
            if g.geom_type=='Polygon': lines+= [LineString(g.exterior.coords)]+[LineString(i.coords) for i in g.interiors]
            elif g.geom_type=='LineString': lines.append(g)
            elif g.geom_type=='LinearRing': lines.append(LineString(g.coords))
        for ln in lines:
            if ln.length<step: continue
            pts=np.array([ln.interpolate(q).coords[0][:2] for q in np.arange(0,ln.length+step,step)])
            ok0=(pts[:,0]>OX+100)&(pts[:,0]<OX+17900)&(pts[:,1]>OY-17900)&(pts[:,1]<OY-100)
            i,j,dist,zc=s.project(pts[:,0],pts[:,1])
            ok=ok0&(zc>30)&(i>=0)&(i<W)&(j>=0)&(j<H)
            ii=np.clip(np.nan_to_num(i).astype(int),0,W-1); jj=np.clip(np.nan_to_num(j).astype(int),0,H-1)
            vis=ok&(dist<=D[jj,ii]+np.maximum(25,dist*0.012))
            seg=[]
            for k in range(len(pts)):
                if vis[k]: seg.append(f'{i[k]:.1f} {j[k]:.1f}')
                else:
                    if len(seg)>1: out.append('M'+' L'.join(seg))
                    seg=[]
            if len(seg)>1: out.append('M'+' L'.join(seg))
        return ' '.join(out)
_hs=None
def hill(X,Y):
    global _hs
    if _hs is None:
        gy,gx=np.gradient(geo.dem,10.0); nn=np.sqrt(gx*gx+gy*gy+1); a=np.radians(315); e=np.radians(45)
        _hs=np.clip((-gx*np.sin(a)*np.cos(e)+gy*np.cos(a)*np.cos(e)+np.sin(e))/nn,0,1).astype(np.float32)
    c=((X-OX)/10-0.5).astype(np.float32); rr=((OY-Y)/10-0.5).astype(np.float32)
    return cv2.remap(_hs,np.nan_to_num(c),np.nan_to_num(rr),cv2.INTER_LINEAR)
def tex(fid,k):
    fn=f'master/{fid}_{k}.tif'
    if not os.path.exists(fn): return None
    a=rasterio.open(fn).read(); a=a[:3] if a.shape[0]>=3 else np.repeat(a[:1],3,0)
    return np.ascontiguousarray(np.moveaxis(a,0,-1))
def render(fid,X,Y,D,order=('p','w','x')):
    hit=np.isfinite(D); img=np.zeros((H,W,3),np.float32); has=np.zeros((H,W),bool)
    for k in order:
        t=tex(fid,k)
        if t is None: continue
        v,r=ALLV[k]; c=((X-v[0])/r-0.5); rr=((v[3]-Y)/r-0.5)
        # mild pre-blur when the texture is much finer than the view sampling
        col=cv2.remap(t,np.nan_to_num(c,nan=-9).astype(np.float32),np.nan_to_num(rr,nan=-9).astype(np.float32),cv2.INTER_LINEAR,borderValue=0).astype(np.float32)
        Wt,Ht=size(v,r); inb=(c>0.5)&(c<Wt-1.5)&(rr>0.5)&(rr<Ht-1.5)
        m=(col.sum(2)>24)&hit&(~has)&inb; img[m]=col[m]; has|=m
    grey=(70+120*hill(X,Y))[...,None]*np.array([1.0,1.0,1.02],np.float32)
    img=np.where(has[...,None],img,grey)
    haze=np.clip((D-3000)/16000,0,0.45)[...,None]; img=img*(1-haze)+np.array([176,188,196],np.float32)*haze
    jj=np.linspace(0,1,H)[:,None,None]; sky=np.array([150,170,186],np.float32)*(1-jj)+np.array([206,214,220],np.float32)*jj
    img=np.where(hit[...,None],img,np.broadcast_to(sky,img.shape))
    return np.clip(img,0,255).astype(np.uint8)
