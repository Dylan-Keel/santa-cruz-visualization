"""Stand-in for modern.py export when the county image service is down: regrid the Santa Cruz County orthophotos already
fetched for the first Scott Creek build onto this site's views. Covers everything west of easting 575,200."""
import numpy as np, rasterio, sys
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from cfg import *
import modern
for y in sys.argv[1:]:
    for k,(v,r) in ALLV.items():
        W,H=size(v,r); T=from_origin(v[0],v[3],r,r); out=np.zeros((3,H,W),'uint8')
        for src in ('w','x'):
            with rasterio.open(f'/home/claude/scott/master/county_{y}_{src}.tif') as s:
                tmp=np.zeros((3,H,W),'uint8'); reproject(rasterio.band(s,[1,2,3]),tmp,dst_transform=T,dst_crs='EPSG:26910',resampling=Resampling.cubic if src=='w' else Resampling.bilinear)
                cov=np.zeros((H,W),'uint8'); reproject(np.ones((s.height,s.width),'uint8'),cov,src_transform=s.transform,src_crs=s.crs,dst_transform=T,dst_crs='EPSG:26910',resampling=Resampling.nearest)
                m=(cov>0)&(out.sum(0)==0); out[:,m]=np.maximum(tmp[:,m],1)
        modern.save(f'county_{y}',k,out); print(y,k,'cov %.3f'%((out.sum(0)>0).mean()),flush=True)
