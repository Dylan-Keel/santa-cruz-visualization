"""Modern orthoimagery onto the site grids: NAIP (Planetary Computer), Santa Cruz County tile caches, Esri World Imagery."""
import requests, numpy as np, rasterio, io, time, sys, collections, os, math
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from PIL import Image
from cfg import *
VIEWS=dict(ALLV)
def save(name,k,a):
    v,r=VIEWS[k]; W,H=size(v,r)
    with rasterio.open(f'master/{name}_{k}.tif','w',driver='GTiff',width=W,height=H,count=3,dtype='uint8',crs='EPSG:26910',transform=from_origin(v[0],v[3],r,r),compress='jpeg',photometric='ycbcr',tiled=True,jpeg_quality=92) as d: d.write(a[:3])
def tiles(url,k,extra,T=1500):
    v,r=VIEWS[k]; W,H=size(v,r); out=np.zeros((3,H,W),'uint8')
    for i in range(0,H,T):
        for j in range(0,W,T):
            h=min(T,H-i); w=min(T,W-j); bb=(v[0]+j*r,v[3]-(i+h)*r,v[0]+(j+w)*r,v[3]-i*r)
            for t in range(5):
                try:
                    q=requests.get(url,params=dict(bbox=','.join(map(str,bb)),bboxSR=26910,imageSR=26910,size=f'{w},{h}',f='image',**extra),timeout=240)
                    a=np.asarray(Image.open(io.BytesIO(q.content)).convert('RGB')); out[:,i:i+h,j:j+w]=np.moveaxis(a,-1,0); break
                except Exception as e: print('retry',str(e)[:80],flush=True); time.sleep(3)
    return out
if len(sys.argv)>1 and sys.argv[1]=='export':      # python3 modern.py export <name> <MapServer url>
    for k in VIEWS:
        a=tiles(sys.argv[3]+'/export',k,dict(format='jpg')); save(sys.argv[2],k,a); print(sys.argv[2],k,(a.sum(0)>0).mean(),flush=True)
if len(sys.argv)>1 and sys.argv[1]=='pc':
    import pystac_client, planetary_computer as pc
    from pyproj import Transformer
    tr=Transformer.from_crs(26910,4326,always_xy=True); lo=tr.transform(VX[0],VX[1]); hi=tr.transform(VX[2],VX[3])
    c=pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1",modifier=pc.sign_inplace)
    by=collections.defaultdict(list)
    for it in c.search(collections=["naip"],bbox=[lo[0],lo[1],hi[0],hi[1]]).items(): by[it.datetime.year].append(it)
    for y,its in sorted(by.items()):
        print(y,[(i.id,str(i.datetime.date()),i.properties.get('gsd')) for i in its],flush=True)
        if len(sys.argv)>2 and str(y) not in sys.argv[2:]: continue
        if os.path.exists(f'master/naip_{y}_x.tif'): continue
        for k,(v,r) in VIEWS.items():
            W,H=size(v,r); T=from_origin(v[0],v[3],r,r); out=np.zeros((3,H,W),'uint8')
            for it in its:
                with rasterio.open(it.assets['image'].href) as s:
                    tmp=np.zeros((3,H,W),'uint8'); reproject(rasterio.band(s,[1,2,3]),tmp,dst_transform=T,dst_crs='EPSG:26910',resampling=Resampling.cubic)
                    m=(tmp.sum(0)>0)&(out.sum(0)==0); out[:,m]=tmp[:,m]
            save(f'naip_{y}',k,out); print(y,k,'cov',(out.sum(0)>0).mean(),flush=True)
