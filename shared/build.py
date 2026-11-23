"""Assemble a flipbook site from masters. Run from a site directory holding cfg.py, cams.py, frames.json, site.json."""
import sys, os, json, datetime, numpy as np, rasterio, geopandas as gpd
sys.path.insert(0,os.getcwd()); sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from shapely.geometry import box
import r3d, cams
from cfg import *
F=json.load(open('frames.json')); S=json.load(open('site.json'))
os.makedirs('site/frames',exist_ok=True)
force=set(sys.argv[1:])
def rgb(path):
    a=rasterio.open(path).read(); a=a[:3] if a.shape[0]>=3 else np.repeat(a[:1],3,0); return Image.fromarray(np.moveaxis(a,0,-1))
for f in F:
    fid=f['id']
    for k,(v,r) in VIEWS.items():
        out=f'site/frames/{k}_{fid}.jpg'
        if os.path.exists(out) and fid not in force: continue
        im=rgb(f"master/{f['file']}_{k}.tif"); W,H=im.size; q=84
        im.save(out,quality=q,optimize=True,progressive=True)
        while os.path.getsize(out)>3.6e6 and q>62: q-=4; im.save(out,quality=q,optimize=True,progressive=True)
        im.resize((W//2,H//2),Image.LANCZOS).save(f'site/frames/{k}s_{fid}.jpg',quality=80,optimize=True,progressive=True)
    for k,c in cams.CAMS.items():
        out=f'site/frames/{k}_{fid}.jpg'
        if os.path.exists(out) and fid not in force: continue
        X,Y,D=c.ground_map(); im=Image.fromarray(r3d.render(f['file'],X,Y,D))
        im.save(out,quality=86,optimize=True,progressive=True); im.resize((1200,900),Image.LANCZOS).save(f'site/frames/{k}s_{fid}.jpg',quality=80,optimize=True,progressive=True)
    print(fid,flush=True)
parcel=gpd.read_file('parcel.geojson').to_crs(26910).geometry.iloc[0]
ws=gpd.read_file('watershed.geojson').to_crs(26910).geometry.iloc[0].simplify(6); wsb=ws.buffer(0)
nhd=gpd.read_file('nhd_utm.geojson'); fg=gpd.read_file('fires.geojson').set_crs(26910,allow_override=True)
PAL=['#ff8a3d','#ff4d6d','#d98cff','#8be28b','#f2a6c8','#ffe066','#7fe0d6','#c9c9c9','#ffb3a1','#b6c7ff']
fg=fg.sort_values('YEAR_').reset_index(drop=True)
def fmeta(i,f):
    dt=(datetime.datetime(1970,1,1)+datetime.timedelta(milliseconds=float(f.ALARM_DATE))).strftime('%B %-d, %Y') if f.ALARM_DATE==f.ALARM_DATE and f.ALARM_DATE else str(int(f.YEAR_))
    nm=(f.FIRE_NAME or 'Unnamed').title().replace('Coop.','Co-op').replace('L.m.','L.M.').replace('Czu','CZU'); return dict(year=int(f.YEAR_),name=nm,date=dt,acres=round(float(f.GIS_ACRES)),color=PAL[i%len(PAL)])
OM=json.load(open('overlay_meta.json')) if os.path.exists('overlay_meta.json') else dict(views={},rasters=[])
ov={}
for k,(v,r) in VIEWS.items():
    x0,y0,x1,y1=v; bb=box(*v); W,H=size(v,r)
    def path(g):
        out=[]
        for gg in getattr(g,'geoms',[g]):
            if gg.is_empty: continue
            if gg.geom_type=='Polygon':
                for ring in [gg.exterior]+list(gg.interiors): out.append('M'+' L'.join(f'{(x-x0)/r:.1f} {(y1-y)/r:.1f}' for x,y,*_ in ring.coords)+'Z')
            elif gg.geom_type in('LineString','LinearRing'): out.append('M'+' L'.join(f'{(x-x0)/r:.1f} {(y1-y)/r:.1f}' for x,y,*_ in gg.coords))
            elif hasattr(gg,'geoms'): out.append(path(gg))
        return ' '.join(out)
    st=' '.join(path(g.intersection(wsb).intersection(bb.buffer(50))) for g in nhd.geometry if g.intersects(wsb))
    fires=[]
    for i,f in fg.iterrows():
        g=f.geometry.buffer(0)
        if g.intersection(bb).area<2000: continue
        m=fmeta(i,f); m['d']=path(g.intersection(bb.buffer(200))); fires.append(m)
    ov[k]=dict(name=S['names'][k],w=W,h=H,res=r,parcel=path(parcel),watershed=path(ws),streams=st,fires=fires,**OM['views'].get(k,{}))
for k,c in cams.CAMS.items():
    X,Y,D=c.ground_map(); fires=[]
    for i,f in fg.iterrows():
        d=c.path3d(f.geometry.buffer(0).boundary,D)
        if len(d)<40: continue
        m=fmeta(i,f); m['d']=d; fires.append(m)
    st=' '.join(c.path3d(g.intersection(wsb),D) for g in nhd.geometry if g.intersects(wsb))
    ov[k]=dict(name=S['names'][k],w=r3d.W,h=r3d.H,res=None,parcel=c.path3d(parcel,D),watershed=c.path3d(ws,D),streams=st,fires=fires,note=S['cam_notes'][k],**OM['views'].get(k,{}))
labels=dict(S['labels']); 
if OM.get('rasters'): labels.setdefault('tree','Legacy trees: LiDAR tops over 131 ft'); labels.setdefault('rastnote',S.get('rastnote',''))
data=dict(frames=[dict(id=f['id'],label=f['label'],year=f['year'],date=f['date'],source=f['source'],res=f['res'],note=f.get('note',''),bw=f.get('bw',False)) for f in F],views=ov,order=list(VIEWS)+list(cams.CAMS),rasters=OM.get('rasters',[]),labels=labels,slug=S.get('slug','flipbook'))
json.dump(data,open('site/data.json','w'))
tpl=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'page.tpl')).read()
html=tpl.replace('__DATA__',json.dumps(data)).replace('__TITLE__',S['title']).replace('__H1__',S['h1']).replace('__SUB__',S['sub']).replace('__NOTES__',S['notes'])
open('site/index.html','w').write(html)
tot=sum(os.path.getsize('site/frames/'+f) for f in os.listdir('site/frames')); print('files',len(os.listdir('site/frames')),'MB',round(tot/1e6,1),'html kB',len(html)//1000)
