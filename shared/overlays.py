"""Make the raster overlay layers (wetness index, canopy height) and legacy tree markers for one site, for every 2D and 3D view."""
import os, sys, json, importlib, numpy as np, cv2, rasterio, geopandas as gpd
from PIL import Image
from shapely.geometry import Point
import layers
FT=3.28084
def png(path,rgba,maxw):
    im=Image.fromarray(rgba,'RGBA')
    if im.size[0]>maxw: im=im.resize((maxw,int(round(im.size[1]*maxw/im.size[0]))),Image.LANCZOS)
    im.save(path.replace('.png','.webp'),'WEBP',quality=82,method=5)
def drape(rgba,origin,res,X,Y):
    c=((X-origin[0])/res-0.5).astype(np.float32); r=((origin[1]-Y)/res-0.5).astype(np.float32)
    o=cv2.remap(rgba,np.nan_to_num(c,nan=-9),np.nan_to_num(r,nan=-9),cv2.INTER_LINEAR,borderValue=(0,0,0,0))
    o[~np.isfinite(X)]=0; return o
def make(S):
    """S: dict with dir, dem (path, ox, oy), chm (npy path, x0, y1), views {k:(bounds,res)}, cams {k:(X,Y,D,project)}, watershed, parcel, out"""
    out=S['out']; os.makedirs(out,exist_ok=True)
    t=layers.twi(S['dem'][0]); dox,doy=S['dem'][1],S['dem'][2]
    ws=S['watershed']; from rasterio import features; from rasterio.transform import from_origin
    m=features.rasterize([(ws,1)],out_shape=t.shape,transform=from_origin(dox,doy,10,10)).astype(bool)
    lo,hi=np.nanpercentile(t[m],[60,99.5]); print('twi lo/hi',lo,hi,flush=True)
    chm=np.load(S['chm'][0]); cx0,cy1=S['chm'][1],S['chm'][2]
    tops=layers.tree_tops(chm,(cx0,cy1)); print('tree tops',len(tops),flush=True)
    # ground-coordinate rasters for draping: twi at 5 m (smoothed up from 10 m), chm at 1 m
    twi5=cv2.resize(np.nan_to_num(t,nan=-50),None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC); twi5[cv2.resize(np.isnan(t).astype(np.uint8),None,fx=2,fy=2,interpolation=cv2.INTER_NEAREST)>0]=np.nan
    twi_rgba=layers.twi_rgba(twi5,lo,hi); chm_rgba=layers.chm_rgba(chm)
    V={}
    for k,(b,res) in S['views'].items():
        W=int(round((b[2]-b[0])/res)); H=int(round((b[3]-b[1])/res)); vr=max(res,(b[2]-b[0])/2400.0)
        a=layers.sample(t,(dox,doy),10.0,b,vr); png(f'{out}/o_twi_{k}.png',layers.twi_rgba(a,lo,hi),2400)
        hres=max(res,(b[2]-b[0])/3000.0)
        h=layers.sample(chm,(cx0,cy1),1.0,b,hres,interp=cv2.INTER_LINEAR); png(f'{out}/o_chm_{k}.png',layers.chm_rgba(h),3000)
        s=1.0 if (b[2]-b[0])<2000 else 0.7
        tr=[[round((x-b[0])/res,1),round((b[3]-y)/res,1),round(z*FT),s] for x,y,z in tops if b[0]<x<b[2] and b[1]<y<b[3]]
        V[k]=dict(rast=['chm','twi'],trees=tr); print(k,'trees',len(tr),flush=True)
    for k,(X,Y,D,project) in S['cams'].items():
        png(f'{out}/o_twi_{k}.png',drape(twi_rgba,(dox,doy),5.0,X,Y),1600); png(f'{out}/o_chm_{k}.png',drape(chm_rgba,(cx0,cy1),1.0,X,Y),1600)
        tr=[]
        if tops:
            T=np.array(tops); i,j,dist,zc=project(T[:,0],T[:,1],T[:,2])
            Hh,Ww=D.shape
            for n in range(len(T)):
                if not (zc[n]>30 and 0<=i[n]<Ww and 0<=j[n]<Hh): continue
                ii=int(np.clip(i[n],0,Ww-1)); jj=int(np.clip(j[n],0,Hh-1))
                # visible if the tree top is not behind terrain: compare with the ground hit a little below the top pixel
                jg=int(np.clip(jj+3,0,Hh-1))
                if dist[n]<=D[jg,ii]+max(60,dist[n]*0.03): tr.append([round(float(i[n]),1),round(float(j[n]),1),round(T[n,2]*FT),round(float(np.clip(1600.0/dist[n],0.35,1.6)),2)])
        V[k]=dict(rast=['chm','twi'],trees=tr); print(k,'trees',len(tr),flush=True)
    pg=S['parcel']; npar=sum(1 for x,y,z in tops if pg.contains(Point(x,y))); nws=sum(1 for x,y,z in tops if ws.contains(Point(x,y)))
    meta=dict(views=V,n_parcel=npar,n_ws=nws,n_all=len(tops),tallest_ft=round(max([z for x,y,z in tops],default=0)*FT),
              tallest_parcel_ft=round(max([z for x,y,z in tops if pg.contains(Point(x,y))],default=0)*FT),
              rasters=[dict(id='chm',label=S.get('chm_label','Canopy height, 2018 LiDAR (0 to 200+ ft)'),ramp=layers.ramp_css('chm')),dict(id='twi',label='Topographic Wetness Index (wetter is darker)',ramp=layers.ramp_css('twi'))])
    json.dump(meta,open(f"{S['dir']}/overlay_meta.json",'w'))
    import csv
    with open(f"{S['dir']}/legacy_trees.csv",'w',newline='') as f:
        w=csv.writer(f); w.writerow(['easting_utm10n_m','northing_utm10n_m','longitude','latitude','height_m','height_ft','in_parcel','in_watershed'])
        from pyproj import Transformer; tt=Transformer.from_crs(26910,4326,always_xy=True)
        for x,y,z in sorted(tops,key=lambda q:-q[2]):
            lo_,la_=tt.transform(x,y); w.writerow([round(x,1),round(y,1),round(lo_,6),round(la_,6),round(z,1),round(z*FT),int(pg.contains(Point(x,y))),int(ws.contains(Point(x,y)))])
    print('parcel tops',npar,'watershed tops',nws,flush=True); return meta
def site(name):
    if name=='cooskie':
        d='/home/claude/work'; os.chdir(d); sys.path.insert(0,d); import r3d
        X,Y,D=r3d.ground_map()
        def project(x,y,z):
            P=np.c_[x,y,r3d.zat(np.asarray(x,float),np.asarray(y,float))+np.asarray(z)]-r3d.CAM
            zc=P@r3d.f; xc=P@r3d.r; yc=P@r3d.u; return r3d.W/2+r3d.fpx*xc/zc, r3d.H/2-r3d.fpx*yc/zc, np.linalg.norm(P,axis=1), zc
        return dict(dir=d,out=d+'/site/frames',dem=(d+'/ref/dem10.tif',384000,4468000),chm=('/home/claude/lidar/cooskie_chm.npy',392000,4459400),
            views={'w':((392000,4456700,394400,4459400),1.0),'p':((392580,4457500,393700,4459040),0.5)},cams={'d':(X,Y,D,project)},
            watershed=gpd.read_file(d+'/watershed.geojson').to_crs(26910).geometry.iloc[0],parcel=gpd.read_file(d+'/parcel.geojson').to_crs(26910).geometry.iloc[0])
    d={'fox':'/home/claude/mad','fourmile':'/home/claude/fm'}[name]; os.chdir(d); sys.path.insert(0,d)
    import cfg, cams, geo
    C={}
    for k,c in cams.CAMS.items():
        X,Y,D=c.ground_map()
        def project(x,y,z,c=c):
            P=np.c_[x,y,geo.zat(np.asarray(x,float),np.asarray(y,float))+np.asarray(z)]-c.C
            zc=P@c.f; xc=P@c.r; yc=P@c.u; return 1600/2+c.fpx*xc/zc, 1200/2-c.fpx*yc/zc, np.linalg.norm(P,axis=1), zc
        C[k]=(X,Y,D,project)
    b=cfg.VW
    return dict(dir=d,out=d+'/site/frames',dem=(d+'/ref/dem10.tif',cfg.OX,cfg.OY),chm=(f'/home/claude/lidar/{name}_chm.npy',b[0],b[3]),
        views={k:(v,r) for k,(v,r) in cfg.VIEWS.items()},cams=C,watershed=gpd.read_file(d+'/watershed.geojson').to_crs(26910).geometry.iloc[0],parcel=gpd.read_file(d+'/parcel.geojson').to_crs(26910).geometry.iloc[0])
if __name__=='__main__':
    for n in sys.argv[1:]: make(site(n))
