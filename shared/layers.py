"""Raster overlay layers shared by all sites: Topographic Wetness Index, LiDAR canopy height, and legacy tree tops."""
import numpy as _np
_np.in1d=_np.isin
import numpy as np, cv2, rasterio, warnings
from scipy import ndimage as ndi
from matplotlib import colormaps
FT=3.28084
TREE_MIN_M=40.0            # 131 ft
CHM_MAX_M=61.0             # 200 ft, top of the colour ramp
def twi(dem_path):
    """ln(specific catchment area / tan(slope)) on the 10 m 3DEP grid, D-infinity routing. Returns array (nan over water)."""
    warnings.filterwarnings('ignore')
    from pysheds.grid import Grid
    grid=Grid.from_raster(dem_path); dem=grid.read_raster(dem_path)
    cond=grid.resolve_flats(grid.fill_depressions(grid.fill_pits(dem)))
    fdir=grid.flowdir(cond,routing='dinf'); acc=np.array(grid.accumulation(fdir,routing='dinf'),dtype=np.float64)
    z=np.array(dem,dtype=np.float64); gy,gx=np.gradient(cv2.GaussianBlur(z,(0,0),1.0),10.0)
    tanb=np.maximum(np.hypot(gx,gy),0.02)
    t=np.log(((acc+1)*10.0)/tanb); t[z<=0.5]=np.nan
    return t.astype(np.float32)
def sample(arr,origin,res,bounds,vres,interp=cv2.INTER_CUBIC):
    """resample a north-up raster (origin = upper-left x,y; res) onto a view grid"""
    x0,y0,x1,y1=bounds; W=int(round((x1-x0)/vres)); H=int(round((y1-y0)/vres))
    xs=((x0+(np.arange(W)+.5)*vres-origin[0])/res-0.5).astype(np.float32); ys=((origin[1]-(y1-(np.arange(H)+.5)*vres))/res-0.5).astype(np.float32)
    mx,my=np.meshgrid(xs,ys); a=np.nan_to_num(arr,nan=-9999.0).astype(np.float32)
    o=cv2.remap(a,mx,my,cv2.INTER_NEAREST if interp==cv2.INTER_NEAREST else cv2.INTER_LINEAR,borderValue=-9999.0)
    bad=cv2.remap((a<-9000).astype(np.float32),mx,my,cv2.INTER_LINEAR,borderValue=1.0)>0.01
    if interp==cv2.INTER_CUBIC:
        o2=cv2.remap(np.where(a<-9000,0,a),mx,my,cv2.INTER_CUBIC,borderValue=0); o=np.where(bad,np.nan,o2)
    else: o=np.where(bad,np.nan,o)
    return o
def twi_rgba(t,lo,hi):
    """wet end only: transparent below lo, light cyan to deep blue up to hi"""
    f=np.clip((t-lo)/(hi-lo),0,1); f=np.nan_to_num(f,nan=0.0)
    rgb=(colormaps['YlGnBu'](0.25+0.75*f)[...,:3]*255).astype(np.uint8)
    a=(np.clip(f*2.2,0,1)*255).astype(np.uint8); a[np.isnan(t)]=0
    return np.dstack([rgb,a])
def chm_rgba(h):
    """viridis by height through a 256-entry lookup table, in row blocks, so a 1 m grid of a whole watershed fits in memory"""
    lut=(colormaps['viridis'](np.linspace(0,1,256))[:,:3]*255).astype(np.uint8); out=np.zeros(h.shape+(4,),np.uint8)
    for r in range(0,h.shape[0],1000):
        b=np.nan_to_num(h[r:r+1000],nan=0.0); out[r:r+1000,:,:3]=lut[(np.clip(b/CHM_MAX_M,0,1)*255).astype(np.uint8)]
        out[r:r+1000,:,3]=(np.clip((b-2.0)/3.0,0,1)*255).astype(np.uint8)
    return out
def ramp_css(kind):
    if kind=='chm': return ['#%02x%02x%02x'%tuple(int(v*255) for v in colormaps['viridis'](k)[:3]) for k in (0,.25,.5,.75,1)]
    return ['#%02x%02x%02x'%tuple(int(v*255) for v in colormaps['YlGnBu'](0.25+0.75*k)[:3]) for k in (0,.33,.66,1)]
def tree_tops(chm,origin,res=1.0,min_h=TREE_MIN_M):
    """local maxima of the canopy height model at least min_h tall with a real crown around them.
    A top counts when at least 15 of the 81 cells in the 9 m window around it reach 75 percent of its height,
    which rejects single-return spikes, and when it is the highest point within 6 m."""
    h=np.nan_to_num(chm,nan=0.0)
    hs=cv2.GaussianBlur(h,(0,0),0.8)
    mx=ndi.maximum_filter(hs,size=13)
    cand=np.argwhere((hs==mx)&(h>=min_h))
    out=[]
    for r,c in cand:
        if r<5 or c<5 or r>=h.shape[0]-5 or c>=h.shape[1]-5: continue
        w=h[r-4:r+5,c-4:c+5]; top=w.max()
        if (w>=0.75*top).sum()<15: continue
        if top>95: continue                       # taller than any tree here: a tower, cliff artefact or bad ground
        out.append((origin[0]+(c+.5)*res,origin[1]-(r+.5)*res,float(top)))
    return out
def fill_ground(gnd):
    """pyramid fill of the 1 m lowest-ground-return grid (9999 = no ground return)"""
    has=gnd<9000; g=np.where(has,gnd,0).astype(np.float32); w=has.astype(np.float32); out=g.copy(); done=has.copy()
    k=2
    while not done.all() and k<=512:
        gs=cv2.resize(g*1.0,(max(1,g.shape[1]//k),max(1,g.shape[0]//k)),interpolation=cv2.INTER_AREA); ws=cv2.resize(w,(gs.shape[1],gs.shape[0]),interpolation=cv2.INTER_AREA)
        ug=cv2.resize(gs,(g.shape[1],g.shape[0]),interpolation=cv2.INTER_LINEAR); uw=cv2.resize(ws,(g.shape[1],g.shape[0]),interpolation=cv2.INTER_LINEAR); up=ug/np.maximum(uw,1e-6)
        ok=(~done)&(uw>0.05); out[ok]=up[ok]; done|=ok; k*=2
    return out
def chm_from(dsm,gnd):
    cov=dsm>-9000; dtm=fill_ground(gnd); chm=np.where(cov,dsm-dtm,0); chm[chm<0]=0
    med=ndi.median_filter(chm,3); sp=(chm-med)>8; chm[sp]=med[sp]; chm[~cov]=np.nan
    return chm.astype(np.float32),dtm
