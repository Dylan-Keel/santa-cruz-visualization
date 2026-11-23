"""1 m surface and ground grids for the watershed view box from the 2020 Santa Cruz County USGS 3DEP LiDAR.
Reads each COPC tile from Planetary Computer down to 1 m octree spacing (about 20 points per square metre here) instead of downloading whole tiles."""
import sys, os, json, time, numpy as np, laspy
from pyproj import Transformer
import pystac_client, planetary_computer as pc
sys.path.insert(0,'/home/claude/big'); from cfg import VW
name='big'; x0,y0,x1,y1=VW; res=1.0; W=int((x1-x0)/res); H=int((y1-y0)/res)
os.chdir('/home/claude/lidar')
t=Transformer.from_crs(26910,4326,always_xy=True); lo=t.transform(x0,y0); hi=t.transform(x1,y1)
c=pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1",modifier=pc.sign_inplace)
its=[i for i in c.search(collections=['3dep-lidar-copc'],bbox=[lo[0]-0.002,lo[1]-0.002,hi[0]+0.002,hi[1]+0.002],max_items=2000).items() if 'SantaCruzCounty_2020' in i.id]
import geopandas as gpd
from shapely.geometry import box as _box
_ws=gpd.read_file('/home/claude/big/watershed.geojson').geometry.iloc[0].buffer(400); _tu=Transformer.from_crs(4326,26910,always_xy=True)
def _near(i):
    a=_tu.transform(i.bbox[0],i.bbox[1]); b=_tu.transform(i.bbox[2],i.bbox[3]); return _box(a[0]-30,a[1]-30,b[0]+30,b[1]+30).intersects(_ws)
n0=len(its); its=[i for i in its if _near(i)]; print('tiles near the watershed',len(its),'of',n0,flush=True)     # canopy is built for the watershed plus 400 m
done=set(json.load(open(f'{name}_done.json'))) if os.path.exists(f'{name}_done.json') else set()
if done: dsm=np.load(f'{name}_dsm.npy'); gnd=np.load(f'{name}_gnd.npy')
else:
    dsm=np.full((H,W),-9999,np.float32); gnd=np.full((H,W),9999,np.float32)
    # start from the Scott Creek grids (same 1 m alignment) and skip the tiles that run already read in full
    ob=(564500,4103500,572700,4113600); c0=int(ob[0]-x0); r0=int(y1-ob[3]); od=np.load('scott_dsm.npy',mmap_mode='r'); og=np.load('scott_gnd.npy',mmap_mode='r')
    dsm[r0:r0+od.shape[0],c0:c0+od.shape[1]]=od; gnd[r0:r0+og.shape[0],c0:c0+og.shape[1]]=og
    prev=set(json.load(open('scott_done.json')))
    for i in its:
        a=_tu.transform(i.bbox[0],i.bbox[1]); b=_tu.transform(i.bbox[2],i.bbox[3])
        if i.id in prev and a[0]>ob[0]+30 and a[1]>ob[1]+30 and b[0]<ob[2]-30 and b[1]<ob[3]-30: done.add(i.id)
print(len(its),'tiles',len(done),'done',flush=True)
def save():
    np.save(f'{name}_dsm.npy',dsm); np.save(f'{name}_gnd.npy',gnd); json.dump(sorted(done),open(f'{name}_done.json','w'))
for n,it in enumerate(its):
    if it.id in done: continue
    p=None
    for k in range(4):
        try:
            r=laspy.CopcReader.open(pc.sign(it.assets['data'].href)); h=r.header
            if h.maxs[0]<x0 or h.mins[0]>x1 or h.maxs[1]<y0 or h.mins[1]>y1: p='out'; break
            p=r.query(resolution=1.0); break
        except Exception as e: print('retry',it.id,str(e)[:80],flush=True); time.sleep(5)
    if p is None: print('FAILED',it.id,flush=True); continue
    if isinstance(p,str): done.add(it.id); continue
    ci=((np.asarray(p.x)-x0)/res).astype(np.int32); ri=((y1-np.asarray(p.y))/res).astype(np.int32)
    cl=np.asarray(p.classification); Z=np.asarray(p.z,dtype=np.float32); del p
    ok=(ci>=0)&(ci<W)&(ri>=0)&(ri<H)&(cl!=7)&(cl!=18)
    if ok.sum():
        idx=ri[ok].astype(np.int64)*W+ci[ok]; z=Z[ok]; g=cl[ok]==2; del ci,ri,Z,cl
        o=np.argsort(idx,kind='stable'); idx=idx[o]; z=z[o]; g=g[o]; u,st=np.unique(idx,return_index=True)     # per-cell max and ground min without ufunc.at
        dsm.ravel()[u]=np.maximum(dsm.ravel()[u],np.maximum.reduceat(z,st))
        if g.any():
            ig=idx[g]; zg=z[g]; ug,sg=np.unique(ig,return_index=True); gnd.ravel()[ug]=np.minimum(gnd.ravel()[ug],np.minimum.reduceat(zg,sg))
        del idx,z,g,o
    done.add(it.id)
    if n%6==0: save()
    print(n,it.id[-6:],'pts',int(ok.sum()),flush=True)
save(); print('ALLDONE coverage %.3f'%(dsm>-9000).mean(),flush=True)
