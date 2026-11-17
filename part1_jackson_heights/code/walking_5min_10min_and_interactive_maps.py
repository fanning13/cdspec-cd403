import sys,json,math,heapq,os,zipfile,html
from pathlib import Path
sys.path.insert(0,str(Path('work/python_libs').resolve()))
os.environ['MPLCONFIGDIR']=str(Path('work').resolve())
import numpy as np
from shapely.geometry import shape,Point,LineString,mapping
from shapely.ops import transform,unary_union,substring
from shapely.strtree import STRtree
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageDraw
from collections import defaultdict,Counter
O=Path('outputs'); W=Path('work')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
sx=111320*math.cos(math.radians(40.755));sy=111132
def proj(g):return transform(lambda x,y:((np.asarray(x)+73.885)*sx,(np.asarray(y)-40.755)*sy),g)
def unproj(g):return transform(lambda x,y:(np.asarray(x)/sx-73.885,np.asarray(y)/sy+40.755),g)
b=proj(shape(load(W/'boundary.json')[0]['the_geom']))
rest=load(O/'Jackson_Heights_restaurants.geojson')['features']
rp=[proj(shape(f['geometry'])) for f in rest]
roads=[];graph=defaultdict(list)
def key(c,l):return (round(c[0],1),round(c[1],1),l)
for r in load(W/'verified_roads.json'):
 if r.get('nonped')=='V' or r.get('rw_type') not in ['1','3','4','5','6','7','9']:continue
 for g in proj(shape(r['the_geom'])).geoms:
  u=key(g.coords[0],r.get('from_level_code','13'));v=key(g.coords[-1],r.get('to_level_code','13'))
  if g.length<.05:continue
  roads.append((g,u,v,r));graph[u].append((v,g.length));graph[v].append((u,g.length))
tree=STRtree([x[0] for x in roads]);dist={};q=[];seeds=defaultdict(list);entr=[]
for r in load(W/'verified_mta.json'):
 if r.get('entry_allowed')!='YES':continue
 p=proj(shape(r['entrance_georeference']));i=int(tree.nearest(p));g,u,v,_=roads[i];a=g.project(p);off=p.distance(g)
 if off>100:continue
 entr.append((r,p,off));seeds[i].append((a,off))
 for n,d in [(u,a+off),(v,g.length-a+off)]:
  if d<dist.get(n,1e99):dist[n]=d;heapq.heappush(q,(d,n))
while q:
 d,n=heapq.heappop(q)
 if d!=dist[n]:continue
 for m,c in graph[n]:
  if d+c<dist.get(m,1e99):dist[m]=d+c;heapq.heappush(q,(d+c,m))
def route(p):
 i=int(tree.nearest(p));g,u,v,_=roads[i];a=g.project(p);off=p.distance(g)
 d=min(dist.get(u,1e99)+a,dist.get(v,1e99)+g.length-a,*[c+abs(a-s) for s,c in seeds[i]])+off
 return d,off
reach={}
for limit in [400,800]:
 lines=[]
 for i,(g,u,v,r) in enumerate(roads):
  intervals=[(0,min(g.length,limit-dist.get(u,1e99))),(max(0,g.length-limit+dist.get(v,1e99)),g.length)]
  intervals += [(max(0,s-(limit-c)),min(g.length,s+(limit-c))) for s,c in seeds[i] if c<limit]
  for a,z in intervals:
   if z>a:lines.append(substring(g,a,z))
 reach[limit]=unary_union(lines).intersection(b)
retail=[]
seen=set()
for r in load(W/'verified_pluto.json'):
 if not r.get('latitude') or not r.get('longitude') or float(r.get('retailarea',0))<=0 or r['bbl'] in seen:continue
 p=proj(Point(float(r['longitude']),float(r['latitude'])))
 if b.covers(p):retail.append((r,p));seen.add(r['bbl'])
for f,p in zip(rest,rp):
 d,off=route(p);f['properties']['estimated_walk_minutes']=round(d/80,1) if d<1e8 else None;f['properties']['network_snap_m']=round(off,1)
 f['properties']['walk_band']='0-5 min' if d<=400 else '5-10 min' if d<=800 else 'Over 10 min'
def category(c):
 if c in ['Latin American','Peruvian','Colombian','Ecuadorian','Brazilian','Cuban','Dominican','Chilean','Argentinian']:return 'Latin American / regional'
 if c=='Mexican':return 'Mexican'
 if c in ['Bangladeshi','Indian','Pakistani']:return 'South Asian'
 if c in ['Chinese','Japanese','Thai','Korean','Vietnamese','Asian/Asian Fusion','Filipino','Indonesian']:return 'East / Southeast Asian & Asian fusion'
 if not c:return 'Unspecified'
 return 'Other recorded cuisines'
cats={'Latin American / regional':'CE663E','Mexican':'D6AA36','South Asian':'168D93','East / Southeast Asian & Asian fusion':'7967A3','Other recorded cuisines':'456260','Unspecified':'B6B7AD'}
for f in rest:f['properties']['map_cuisine_group']=category(f['properties'].get('cuisine_description'))
stats={'restaurants':len(rest),'retail_lots':len(retail),'walk_bands':dict(Counter(f['properties']['walk_band'] for f in rest)),'restaurant_snap_max_m':max(route(p)[1] for p in rp),'entrance_snap_max_m':max(x[2] for x in entr),'cuisine_groups':dict(Counter(f['properties']['map_cuisine_group'] for f in rest))}
for lim in [400,800]:
 stats[str(lim)]={'restaurants':sum(route(p)[0]<=lim for p in rp),'retail_lots':sum(route(p)[0]<=lim for _,p in retail),'reachable_street_km':round(reach[lim].length/1000,2)}
stats['method']='CSCL pedestrian-eligible streets, bridges, tunnels, paths and steps; vehicle-only segments and alleys excluded. Bidirectional endpoint graph with elevation codes and 0.1m coordinate rounding. Entrances and destinations snapped to nearest eligible segment, connector distance included. 80m/min; no crossing waits, accessibility or schedules. Shaded street bands use 35m cartographic buffers, not parcel-level accessibility polygons.'
(O/'map_analysis.json').write_text(json.dumps(stats,indent=2))
(O/'Jackson_Heights_restaurants_analyzed.geojson').write_text(json.dumps({'type':'FeatureCollection','features':rest}))
def esc(x):return html.escape(str(x))
def color(hex,a=255):return f'{a:02x}'+hex[4:6]+hex[2:4]+hex[:2]
def coords(seq):return ' '.join(f'{x:.7f},{y:.7f},0' for x,y in seq)
def geom(g):
 g=unproj(g)
 def make(g):
  if g.geom_type=='Point':return '<Point><coordinates>'+coords([(g.x,g.y)])+'</coordinates></Point>'
  if g.geom_type in ['LineString','LinearRing']:return '<LineString><tessellate>1</tessellate><coordinates>'+coords(g.coords)+'</coordinates></LineString>'
  if g.geom_type=='Polygon':return '<Polygon><tessellate>1</tessellate><outerBoundaryIs><LinearRing><coordinates>'+coords(g.exterior.coords)+'</coordinates></LinearRing></outerBoundaryIs>'+''.join('<innerBoundaryIs><LinearRing><coordinates>'+coords(r.coords)+'</coordinates></LinearRing></innerBoundaryIs>' for r in g.interiors)+'</Polygon>'
  return '<MultiGeometry>'+''.join(make(p) for p in g.geoms if not p.is_empty)+'</MultiGeometry>'
 return make(g)
class KML:
 def __init__(self,title):self.title=title;self.styles=[];self.folders=[];self.icons={}
 def style(self,id,hex,fill=0,width=1,icon=False,size=.6):
  s=f'<Style id="{id}"><LineStyle><color>{color(hex)}</color><width>{width}</width></LineStyle><PolyStyle><color>{color(hex,fill)}</color><outline>{int(width>0)}</outline></PolyStyle><LabelStyle><scale>0</scale></LabelStyle>'
  if icon:
   im=Image.new('RGBA',(32,32));d=ImageDraw.Draw(im);d.ellipse((3,3,29,29),fill='#'+hex,outline='white',width=3);p=W/f'{id}.png';im.save(p);self.icons[f'icons/{id}.png']=p
   s+=f'<IconStyle><scale>{size}</scale><Icon><href>icons/{id}.png</href></Icon><hotSpot x="0.5" y="0.5" xunits="fraction" yunits="fraction"/></IconStyle>'
  self.styles.append(s+'</Style>')
 def folder(self,name,features,visible=1):
  self.folders.append(f'<Folder><name>{esc(name)}</name><visibility>{visible}</visibility>'+''.join(f'<Placemark><name>{esc(n)}</name><description>{esc(d)}</description><styleUrl>#{s}</styleUrl>{geom(g)}</Placemark>' for n,d,s,g in features)+'</Folder>')
 def save(self,file):
  text='<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>'+esc(self.title)+'</name>'+''.join(self.styles)+''.join(self.folders)+'</Document></kml>'
  with zipfile.ZipFile(O/file,'w',zipfile.ZIP_DEFLATED) as z:
   z.writestr('doc.kml',text)
   for name,p in self.icons.items():z.write(p,name)
  return text
m1=KML('Where Is the Table Set? | Jackson Heights')
for i,(c,h) in enumerate(cats.items()):m1.style('c'+str(i),h,icon=True,size=.55)
popfeats=[]
for i,h in enumerate(['EEEDE6','DCDDD1','C3CABD','A5B5A5']):m1.style('p'+str(i),h,fill=170,width=0)
for f in load(O/'Jackson_Heights_diversity.geojson')['features']:
 g=proj(shape(f['geometry']));p=f['properties'];density=p['population2020']/(g.area/1e6);idx=sum(density>v for v in [25000,40000,55000]);p['population_per_km2']=round(density)
 popfeats.append((f"Tract {p['tract']}",f"2020 population: {p['population2020']:,}; density: {density:,.0f} residents/km². NYC DCP Census 2020. Population is context, not a proxy for cuisine.",'p'+str(idx),g))
m1.folder('Population density | pale to dark: <25k / 25-40k / 40-55k / >55k per km²',popfeats)
x0,y0,x1,y1=b.bounds;xs=np.arange(x0-200,x1+200,25);ys=np.arange(y0-200,y1+200,25);X,Y=np.meshgrid(xs,ys);Z=np.zeros(X.shape)
for p in rp:Z+=np.exp(-((X-p.x)**2+(Y-p.y)**2)/(2*120**2))/(2*math.pi*120**2)*1e6
fig,ax=plt.subplots();cs=ax.contour(X,Y,Z,levels=[100,250,500],colors='black');cont=[]
for j,level in enumerate(cs.levels):
 m1.style('d'+str(j),'986F46',width=[1,1.7,2.3][j])
 for seg in cs.allsegs[j]:
  if len(seg)>1:
   g=LineString(seg).intersection(b)
   if not g.is_empty:cont.append((f'Density contour: {int(level)} / km²','Gaussian kernel density, bandwidth 120m; indicative restaurant concentration, not a count within a fixed area. Boundary edge effects remain.','d'+str(j),g))
plt.close(fig);m1.folder('Restaurant density contours | 100 / 250 / 500 per km²',cont)
for i,c in enumerate(cats):
 feats=[]
 for f,p in zip(rest,rp):
  a=f['properties']
  if a['map_cuisine_group']==c:feats.append((a['dba'],f"Cuisine: {a.get('cuisine_description','Unspecified')}\nAddress: {a.get('building','')} {a.get('street','')}\nCAMIS: {a['camis']}\nDOHMH snapshot 21 Oct 2026; latest inspection record, not verified operating status.",'c'+str(i),p))
 m1.folder(f'{c} ({len(feats)})',feats)
m1.style('boundary','203B3B',width=2);m1.folder('Study boundary | Jackson Heights QN0301',[('Jackson Heights','NYC DCP 2020 Neighborhood Tabulation Area QN0301.','boundary',b.boundary)])
m1.save('Map_1_Food_Geography.kmz')
m2=KML('What Holds the Table Together? | Jackson Heights')
m2.style('w10','85BFC6',fill=85,width=0);m2.style('w5','268B99',fill=120,width=0)
for lim,id in [(800,'w10'),(400,'w5')]:m2.folder(f'{lim//80}-minute estimated walk | street network',[(f'{lim//80}-minute network reach',stats['method'],id,reach[lim].buffer(35).intersection(b).simplify(2))])
m2.style('retail','C7A257',icon=True,size=.38);m2.folder('Retail premises | PLUTO retail area > 0',[(r['address'],f"Retail floor area: {float(r['retailarea']):,.0f} sq ft. PLUTO 26v2. Tax-lot centroid; does not identify a specific shop entrance.",'retail',p) for r,p in retail])
m2.style('park','68976B',fill=190,width=1)
parks=[]
for r in load(W/'verified_enfh-gkve.json'):
 g=proj(shape(r['multipolygon']));name=r.get('name311','')
 if b.intersects(g) and any(s in name for s in ['Travers','Northern Playground','Playground Ninety','Rory Staunton','Mall Thirty','Elmjack']):parks.append((name,'NYC Parks properties; public-space context, not a measured social-activity count.','park',g.intersection(b)))
p=load(W/'verified_k5k6-6jex.json');p=p if isinstance(p,list) else [p]
for r in p:parks.append(('Diversity Plaza','NYC DOT pedestrian plaza.','park',proj(shape(r['the_geom']))))
m2.folder('Public spaces | parks and Diversity Plaza',parks)
m2.style('open','4A8762',width=4);openlines=[]
for r in load(W/'verified_uiay-nctu.json'):
 g=proj(shape(r['the_geom'])).intersection(b)
 if not g.is_empty:openlines.append(('34th Avenue Open Street','Geometry: DOT 2024 inventory. DOT 2026 program identifies 69th St to Junction Blvd. Hours and operation vary; this is a spatial reference.','open',g))
m2.folder('34th Avenue Open Street',openlines)
m2.style('food','CE663E',icon=True,size=.52);m2.folder('Restaurants | click for estimated walk time',[(f['properties']['dba'],f"Cuisine: {f['properties'].get('cuisine_description','Unspecified')}\nEstimated nearest-entry walk: {f['properties']['estimated_walk_minutes']} min\nNetwork connector: {f['properties']['network_snap_m']}m. 80m/min; no wait times.",'food',p) for f,p in zip(rest,rp)])
m2.style('subway','203B3B',icon=True,size=.8);m2.folder('Subway entrances | entry permitted',[(r['stop_name'],f"Routes: {r.get('daytime_routes','')}\nMTA entrance inventory 2024; entry allowed. Connector to network: {off:.1f}m.",'subway',p) for r,p,off in entr if p.distance(b)<120])
m2.style('boundary','203B3B',width=2);m2.folder('Study boundary | QN0301',[('Jackson Heights','NYC DCP 2020 NTA QN0301','boundary',b.boundary)])
m2.save('Map_2_Transit_Public_Space.kmz')
print(json.dumps(stats,indent=2))
