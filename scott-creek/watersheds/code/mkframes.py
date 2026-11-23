"""Write frames.json and site.json (page text) for the Scott Creek flipbook."""
import json, os, csv, numpy as np, rasterio, geopandas as gpd
from rasterio import features
from rasterio.transform import from_origin
from shapely.geometry import Point
from cfg import *
ws=gpd.read_file('watershed.geojson').geometry.iloc[0]; B=gpd.read_file('basins.geojson')
W,H=size(VW,RW); T_=from_origin(VW[0],VW[3],RW,RW); wm=features.rasterize([(ws,1)],out_shape=(H,W),transform=T_).astype(bool)
bm={n:features.rasterize([(g,1)],out_shape=(H,W),transform=T_).astype(bool) for n,g in zip(B.name,B.geometry)}
def cover(a): return {n:float((a[m]>0).mean()) for n,m in bm.items()}
U='UCSB Library FrameFinder scans, orthorectified here'
Y=[('1941','March 24 and April 12, 1941','flight C-6660, 1:24,000, black and white','about 1 m'),
   ('1948','April 24, 1948','California Division of Forestry flight CDF5, 1:20,000, black and white','about 1 m'),
   ('1956','June 5, 1956','flight CJA, 1:20,000, black and white','about 1 m'),
   ('1963','June 25, 1963','flight CAS-SCR, 1:20,000, black and white','about 1 m'),
   ('1985','April 12, 1985','WAC Corporation flight WAC-85CA, 1:31,680, black and white','about 1.2 m'),
   ('1993','June 11, 1993','USGS National Aerial Photography Program, 1:40,000, black and white','about 1.7 m'),
   ('1998','August 29, 1998','USGS National Aerial Photography Program, 1:40,000, black and white','about 1.7 m')]
F=[]; rows=''; gaps=[]
for tag,date,src,res in Y:
    if not os.path.exists(f'master/h{tag}_w.tif'): continue
    c=json.load(open(f'master/h{tag}_cov.json')); used=[u.rstrip('*').split('_')[-1] for u in c['used']]
    a=rasterio.open(f'master/h{tag}_w.tif').read(1); cv=cover(a); miss=[f"{n} {round((1-v)*100)} percent" for n,v in cv.items() if v<0.985]; note=''
    if miss: note='No coverage for: '+', '.join(miss); gaps.append(f"{tag} ({', '.join(miss)})")
    F.append(dict(id=tag,file='h'+tag,label=tag,year=int(tag),date=date,source=f'{src}. {U}. Frames: '+', '.join(used),res=res,note=note,bw=True))
    rows+=f"<tr><td>{tag}</td><td>{src.split(',')[0]}: {', '.join(used)}</td></tr>"
C='Santa Cruz County orthophoto, natural color (county image service)'
for y in (2003,2007):
    cv=cover(rasterio.open(f'master/county_{y}_w.tif').read().sum(0)); miss=[f"{n} {round((1-v)*100)} percent" for n,v in cv.items() if v<0.985]
    F.append(dict(id=str(y),file=f'county_{y}',label=str(y),year=y,date=f'{y}, flight date not published with the service',source=C,res='view resolution',note=('No coverage for: '+', '.join(miss)) if miss else ''))
    if miss: gaps.append(f"{y} ({', '.join(miss)})")
N='USDA National Agriculture Imagery Program, natural color'
for y,d,r in [(2012,'May 20, 2012','1 m'),(2014,'June 13, 2014','1 m'),(2016,'June 19, 2016','0.6 m'),(2018,'August 4, 2018','0.6 m'),(2020,'May 27, 2020','0.6 m'),(2022,'May 19, 2022','0.6 m')]:
    F.append(dict(id=str(y),file=f'naip_{y}',label=str(y),year=y,date=d,source=N,res=r,note={2020:'Flown about 12 weeks before the CZU Lightning Complex',2022:'First date after the CZU Lightning Complex, 21 months post-fire'}.get(y,'')))
cv=cover(rasterio.open('master/county_2025_w.tif').read().sum(0)); miss=[f"{n} {round((1-v)*100)} percent" for n,v in cv.items() if v<0.985]
F.append(dict(id='2025',file='county_2025',label='2025',year=2025,date='2025, flight date not published with the service',source=C,res='view resolution',note=('No coverage for: '+', '.join(miss)) if miss else ''))
if miss: gaps.append(f"2025 ({', '.join(miss)})")
json.dump(F,open('frames.json','w'),indent=1)
T=list(csv.DictReader(open('legacy_trees.csv'))) if os.path.exists('legacy_trees.csv') else []
P=[Point(float(t['easting_utm10n_m']),float(t['northing_utm10n_m'])) for t in T]; HT=[int(t['height_ft']) for t in T]
cnt={n:[h for p,h in zip(P,HT) if g.contains(p)] for n,g in zip(B.name,B.geometry)}
tree_txt=', '.join(f"{len(v):,} in {n} (tallest {max(v,default=0)} ft)" for n,v in cnt.items()); ntot=sum(len(v) for v in cnt.values())
bas_txt=', '.join(f"{n} ({a:,} ac)" for n,a in zip(B.name,B.acres)); words={15:'Fifteen',16:'Sixteen',17:'Seventeen'}
gap_txt=(' Coverage gaps inside the watersheds: '+'; '.join(gaps)+'.') if gaps else ''
notes=f'''  <h2>What this covers</h2>
  <p><strong>{words.get(len(F),str(len(F)))} dates, March 1941 to 2025.</strong> Every frame is on the same UTM zone 10N grid, so the flip is registered. The view is 11.8 by 12.4 km at 2.5 m per pixel. There is no parcel view and there are no tributary views.</p>
  <p><strong>Four watersheds</strong> are outlined, each delineated from the 10 m elevation model: {bas_txt}. Upper Scott Creek is everything draining to 37.0804 N, 122.2469 W. Mill Creek, Big Creek and Little Creek are each taken above their confluence with Scott Creek. On the map, Upper Scott Creek is the western watershed, Mill Creek is the narrow one beside it, Big Creek is the large eastern one, and Little Creek is the small one at the southeast. Turn on "Start point and confluences" in the legend to mark the four outlets.</p>
  <p><strong>1941 through 1998 are scanned film frames</strong> from the UCSB Library FrameFinder collection. I orthorectified each frame against the 10 m 3DEP elevation model, working backward in time so each year is tightened against the next later year. Measured offsets between adjacent dates are typically 4 to 10 m, more on steep ground, and they accumulate toward the older dates. Seams show where frames meet and tone differs between prints. Black areas have no frame for that year.{gap_txt}</p>
  <p><strong>2003, 2007 and 2025</strong> are Santa Cruz County orthophotos. The county service gives the year and no flight date. 2012 to 2022 are NAIP. Color balance varies by year and I left the tones as delivered. Chips with dashed borders mark black-and-white dates.</p>
  <p><strong>3D views.</strong> Each year is draped on the 10 m elevation model and rendered from three fixed cameras: Upper Scott Creek looking up-valley, Big Creek looking up-valley, and all four watersheds from above the coast. The terrain model is smooth at this resolution, so gullies and road cuts do not show as relief, and steep slopes stretch the photos somewhat. Grey terrain has no photo coverage for that year.</p>
  <p><strong>Gaps.</strong> I found no scanned frames over these watersheds between 1963 and 1985. The collection also holds June 1940 frames along the coast, and 1987, 1989 and February 1993 flights, that I did not process. The oldest frames I could get are from 1941. UC Santa Cruz catalogs 1928 flights, but the ones I found described cover the coastline from Santa Cruz to Davenport and not these watersheds, and I could not open that collection from here to confirm.</p>
  <p>Watershed divides are delineated from the 10 m elevation model. Stream lines are from the National Hydrography Dataset. None of these lines is a survey.</p>
  <p><strong>Fire record.</strong> The optional fire layer shows CAL FIRE historical perimeters. The CZU Lightning Complex (alarm date August 16, 2020; 86,553 acres) is mapped across all four watersheds, so May 2020 and May 2022 bracket it. The Lockheed Fire (August 12, 2009; 7,783 acres) is mapped over about 1,060 acres of Upper Scott Creek and 1,880 acres of Big Creek, bracketed by 2007 and 2012. A perimeter drawn dashed burned after the date on screen. The record misses small and early fires, so the absence of a perimeter before 1950 is not evidence of no fire.</p>
  <h2>Canopy height, tall trees and wetness index</h2>
  <p>These three layers are off when the page opens. Turn them on in the legend and set their transparency with the opacity slider. They are available in every view and do not change with the date on screen. There are no road or stream crossing layers in this flipbook.</p>
  <p><strong>Canopy height</strong> is from the USGS 3DEP LiDAR survey of Santa Cruz County, flown in April 2020 (the tile I checked spans April 1 to 14): highest return minus the LiDAR ground surface on a 1 m grid. Ground under 2 m of cover is left clear. <strong>The survey predates the CZU Lightning Complex by four months, so this is the pre-fire canopy.</strong> It covers the four watersheds and at least 400 m beyond them; parts of the view corners are blank.</p>
  <p><strong>Tall trees</strong> are LiDAR canopy tops at least 200 ft (61 m) tall with a full crown around the top. The Humboldt flipbooks flag tops over 131 ft; that height is ordinary in this forest, so the threshold here is higher. The screen flags {ntot:,} tops inside the watersheds: {tree_txt}. This is a remote screen and not a cruise. Heights are as of April 2020, a top on a steep slope can read tall, and a tree killed or topped in the 2020 fire still shows.</p>
  <p><strong>Topographic Wetness Index</strong> is ln(a / tan &beta;), computed from the 10 m elevation model with D-infinity flow routing. It shows where terrain concentrates drainage: swales, hollows and valley floors. It is not a measurement of soil moisture, and at 10 m it does not resolve road drainage or small gullies.</p>
  <h2>Scanned frames used</h2>
  <p>Flight and frame numbers as indexed in <a href="https://mil.library.ucsb.edu/ap_indexes/FrameFinder/">UCSB Library FrameFinder</a>.</p>
  <div style="overflow-x:auto"><table class="fr"><tbody>{rows}</tbody></table></div>
'''
S=dict(title='Scott Creek Watersheds Flipbook',h1=f"Scott Creek watersheds aerial flipbook, {F[0]['year']} to 2025",
  sub='Upper Scott Creek, Mill Creek, Big Creek and Little Creek, Santa Cruz County, California',notes=notes,
  labels=dict(parcel='Start point and confluences',shed='Watershed divides: Upper Scott, Mill, Big, Little',tree='Tall trees: LiDAR tops over 200 ft'),
  names=dict(w='Watersheds',a='3D Upper Scott Creek',b='3D Big Creek',c='3D all four'),
  cam_notes=dict(a='Looking northeast up Upper Scott Creek from above the coast. Mill Creek is the next valley to the right.',
                 b='Looking northeast up Big Creek. Mill Creek is on the left and Little Creek on the right.',
                 c='Looking northeast at all four watersheds from above the coast: Upper Scott, Mill, Big and Little Creeks from left to right.'),
  rastnote='Canopy height and tall trees are from April 2020 USGS 3DEP LiDAR, flown before the CZU fire. Wetness index is computed from the 10 m elevation model.',slug='scott_creek_watersheds')
json.dump(S,open('site.json','w'),indent=1); print(len(F),'frames |',bas_txt,'|',tree_txt,'| gaps',gaps)
