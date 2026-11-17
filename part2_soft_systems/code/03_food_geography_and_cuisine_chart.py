import sys,json,math,collections,csv
from pathlib import Path

import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import shape,Point,LineString,mapping
from shapely.ops import transform
S=Path('analysis_outputs');O=Path('analysis_outputs');O.mkdir(exist_ok=True)
load=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
rest=load(S/'restaurants_cd403_walktime.geojson')['features'];assert len(rest)==502
boundary=shape(load(S/'cd403_boundary.geojson')['features'][0]['geometry'])
ntas=load(S/'nta_qn03.geojson')['features']
sx=111320*math.cos(math.radians(40.755));sy=111132
proj=lambda g:transform(lambda x,y:((np.asarray(x)+73.885)*sx,(np.asarray(y)-40.755)*sy),g)
unproj=lambda g:transform(lambda x,y:(np.asarray(x)/sx-73.885,np.asarray(y)/sy+40.755),g)
def group(c):
 if c in ['Latin American','Peruvian','Colombian','Ecuadorian','Brazilian','Cuban','Dominican','Chilean','Argentinian','Spanish']:return 'Latin American / regional and Spanish'
 if c in ['Mexican','Tex-Mex']:return 'Mexican / Tex-Mex'
 if c in ['Bangladeshi','Indian','Pakistani']:return 'South Asian'
 if c in ['Chinese','Japanese','Thai','Korean','Vietnamese','Asian/Asian Fusion','Filipino','Indonesian']:return 'East / Southeast Asian and fusion'
 return 'Unclassified' if not c else 'Other recorded cuisines'
colors={'Latin American / regional and Spanish':'#CE663E','Mexican / Tex-Mex':'#D6AA36','South Asian':'#168D93','East / Southeast Asian and fusion':'#7967A3','Other recorded cuisines':'#456260','Unclassified':'#B6B7AD'}
for f in rest:
 p=f['properties'];p['Category']=group(p.get('cuisine_description'));p['Name']=p['dba'];p['Details']=f"{p.get('building','')} {p.get('street','')} | {p.get('cuisine_description') or 'Unclassified'} | {p.get('ntaname')} | CAMIS {p.get('camis')} | nearest subway: {p.get('walk_min')} min"
def save(name,features): (O/name).write_text(json.dumps({'type':'FeatureCollection','features':features},ensure_ascii=False),encoding='utf-8')
save('CD403_Restaurant_Cuisines.geojson',rest)
pops={'QN0301':101848,'QN0302':33573,'QN0303':43434}
for f in ntas:
 p=f['properties'];p['Name']=p['ntaname'];p['Category']=p['ntaname'];p['population2020']=pops[p['nta2020']];p['Details']='2020 NTA context; official district total is 179134. NTA and community district boundaries differ slightly.'
save('CD403_Neighborhood_Context.geojson',ntas)
xy=np.array([[proj(shape(f['geometry'])).x,proj(shape(f['geometry'])).y] for f in rest]);b=proj(boundary);xmin,ymin,xmax,ymax=b.bounds
xx=np.arange(xmin-200,xmax+201,25);yy=np.arange(ymin-200,ymax+201,25);X,Y=np.meshgrid(xx,yy);Z=np.zeros_like(X)
for x,y in xy:Z+=np.exp(-((X-x)**2+(Y-y)**2)/(2*120**2))/(2*math.pi*120**2)*1e6
fig,ax=plt.subplots();cs=ax.contour(X,Y,Z,levels=[100,250,500]);lines=[]
for lev,segs in zip(cs.levels,cs.allsegs):
 for pts in segs:
  if len(pts)<2:continue
  g=LineString(pts).intersection(b)
  if not g.is_empty:lines.append({'type':'Feature','properties':{'Category':f'{int(lev)} restaurants/km2','Name':'Restaurant concentration contour','Details':'Equal-weight Gaussian kernel; 120 m bandwidth; 25 m grid. Descriptive concentration, not a significance test.'},'geometry':mapping(unproj(g))})
plt.close(fig)
lines.append({'type':'Feature','properties':{'Category':'Community District 3 boundary','Name':'BoroCD 403'},'geometry':mapping(boundary.boundary)})
save('CD403_Density_Contours_Boundary.geojson',lines)
cs=['37th Avenue','Roosevelt Avenue','Northern Boulevard','Junction Boulevard','Astoria Boulevard','Other streets'];rows=[]
for c in cs:
 rs=[f['properties'] for f in rest if f['properties']['corridor']==c];rows.append({'corridor':c,'n':len(rs),'cuisines':len({r['cuisine_description'] for r in rs if r.get('cuisine_description')}),'groups':dict(collections.Counter(r['Category'] for r in rs))})
fig,ax=plt.subplots(figsize=(13,7));fig.patch.set_facecolor('#F6F2EA');ax.set_facecolor('#F6F2EA');left=np.zeros(len(rows))
for g,col in colors.items():
 v=np.array([r['groups'].get(g,0)/r['n']*100 for r in rows]);ax.barh(range(len(rows)),v,left=left,color=col,label=g,height=.6);left+=v
ax.set_yticks(range(len(rows)),[f"{r['corridor']} (n={r['n']})" for r in rows]);ax.invert_yaxis();ax.set_xlim(0,100);ax.set_xlabel('Share of restaurant records (%)');ax.spines[['top','right','left']].set_visible(False);ax.legend(loc='upper center',bbox_to_anchor=(.44,-.2),ncol=2,frameon=False,fontsize=9)
fig.suptitle('ONE DISTRICT, DIFFERENT FOOD CORRIDORS',x=.04,ha='left',fontsize=19,weight='bold');fig.text(.04,.89,'Queens Community District 3 | 502 cleaned establishment records | Same data and cleaning as Chapter 2',fontsize=11);fig.text(.04,.025,'Source: NYC DOHMH, downloaded 3 Nov 2026; latest record_date 30 Oct 2026. Address-based corridors.\nCuisine groups describe administrative food categories, not the ethnicity of owners or customers. Spanish is grouped explicitly with Latin American/regional.',fontsize=9);fig.subplots_adjust(left=.23,right=.97,top=.82,bottom=.29);fig.savefig(O/'CD403_Corridor_Cuisines.png',dpi=180);plt.close(fig)
summary={'restaurants':len(rest),'classified':sum(bool(f['properties'].get('cuisine_description')) for f in rest),'source_cuisines':len({f['properties']['cuisine_description'] for f in rest if f['properties'].get('cuisine_description')}),'groups':dict(collections.Counter(f['properties']['Category'] for f in rest)),'subareas':dict(collections.Counter(f['properties']['ntaname'] for f in rest)),'corridors':rows,'top_three_count':sum(r['n'] for r in rows if r['corridor'] in ['37th Avenue','Roosevelt Avenue','Northern Boulevard'])}
(O/'CD403_food_geography_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))

