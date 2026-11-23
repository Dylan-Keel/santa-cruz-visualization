"""Wetness index, canopy height and tall-tree layers for the Scott Creek flipbook, for the watershed view and each 3D camera."""
import os, sys, json, numpy as np, geopandas as gpd, cv2
sys.path.insert(0,'/home/claude/big')
import layers, overlays, cfg, cams, geo
from shapely.geometry import Point
d='/home/claude/big'; os.chdir(d)
MIN_M=float(sys.argv[1]) if len(sys.argv)>1 else 61.0
if not os.path.exists('/home/claude/lidar/big_chm.npy'):
    # canopy height in overlapping row strips: the whole 1 m grid for four watersheds does not fit in memory at once
    dsm=np.load('/home/claude/lidar/big_dsm.npy',mmap_mode='r'); gnd=np.load('/home/claude/lidar/big_gnd.npy',mmap_mode='r')
    H_,W_=dsm.shape; out=np.lib.format.open_memmap('/home/claude/lidar/big_chm.npy',mode='w+',dtype=np.float32,shape=(H_,W_)); S_=2400; M_=320
    for r0 in range(0,H_,S_):
        a0=max(0,r0-M_); a1=min(H_,r0+S_+M_); c,_=layers.chm_from(np.array(dsm[a0:a1]),np.array(gnd[a0:a1])); out[r0:min(H_,r0+S_)]=c[r0-a0:r0-a0+min(S_,H_-r0)]; print('chm rows',r0,flush=True)
    out.flush(); del out,dsm,gnd
_tt=layers.tree_tops
layers.tree_tops=lambda chm,origin,res=1.0,min_h=MIN_M: _tt(chm,origin,res,min_h)
C={}
for k,c in cams.CAMS.items():
    X,Y,D=c.ground_map()
    def project(x,y,z,c=c):
        P=np.c_[x,y,geo.zat(np.asarray(x,float),np.asarray(y,float))+np.asarray(z)]-c.C
        zc=P@c.f; xc=P@c.r; yc=P@c.u; return 1600/2+c.fpx*xc/zc, 1200/2-c.fpx*yc/zc, np.linalg.norm(P,axis=1), zc
    C[k]=(X,Y,D,project)
b=cfg.VW; ws=gpd.read_file('watershed.geojson').geometry.iloc[0]
m=overlays.make(dict(dir=d,out=d+'/site/frames',dem=(d+'/ref/dem10.tif',cfg.OX,cfg.OY),chm=('/home/claude/lidar/big_chm.npy',b[0],b[3]),
    views={k:(v,r) for k,(v,r) in cfg.VIEWS.items()},cams=C,watershed=ws,parcel=ws,chm_label='Canopy height, April 2020 LiDAR, pre-fire (0 to 200+ ft)'))
