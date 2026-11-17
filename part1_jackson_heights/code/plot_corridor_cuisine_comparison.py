import sys,json,math,os
from pathlib import Path
sys.path.insert(0,str(Path('work/python_libs').resolve()))
import numpy as np
from collections import Counter
from shapely.geometry import shape
from shapely.ops import transform,unary_union
os.environ['MPLCONFIGDIR']=str(Path('work').resolve())
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path('outputs');load=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
R=[f['properties'] for f in load(O/'Jackson_Heights_restaurants_analyzed.geojson')['features']]
sx=111320*math.cos(math.radians(40.755));sy=111132
proj=lambda g:transform(lambda x,y:((np.asarray(x)+73.885)*sx,(np.asarray(y)-40.755)*sy),g)
b=proj(shape(load('work/boundary.json')[0]['the_geom']))
def corridor(r):
 s=r['street'].strip().upper()
 if 'NORTHERN' in s:return 'Northern Boulevard'
 if s in ['37 AVENUE','37TH AVENUE']:return '37th Avenue'
 if 'ROOSEVELT' in s:return 'Roosevelt Avenue'
 return 'Other streets'
cs=['37th Avenue','Northern Boulevard','Roosevelt Avenue','Other streets']
groups=list(dict.fromkeys(r['map_cuisine_group'] for r in R))
rows=[]
for c in cs:
 rs=[r for r in R if corridor(r)==c];cnt=Counter(r.get('cuisine_description') for r in rs if r.get('cuisine_description'))
 rows.append(dict(corridor=c,n=len(rs),groups=dict(Counter(r['map_cuisine_group'] for r in rs)),top=cnt.most_common(5),cuisines=len(cnt),within5=sum(r['walk_band']=='0-5 min' for r in rs),within10=sum(r['walk_band']!='Over 10 min' for r in rs)))
gstats=[dict(group=g,n=sum(r['map_cuisine_group']==g for r in R),within10=sum(r['map_cuisine_group']==g and r['walk_band']!='Over 10 min' for r in R)) for g in groups]
tr=[]
for f in load(O/'Jackson_Heights_diversity.geojson')['features']:
 p=f['properties'];area=proj(shape(f['geometry'])).area/1e6
 tr.append(dict(tract=p['tract'],population=p['population2020'],restaurants=p['restaurants2026'],area_km2=area,pop_density=p['population2020']/area,rest_density=p['restaurants2026']/area,per1000=p['restaurants2026']/p['population2020']*1000))
def rank(x):return np.array([sum(v<a for v in x)+(sum(v==a for v in x)-1)/2 for a in x])
rho=float(np.corrcoef(rank([t['pop_density'] for t in tr]),rank([t['rest_density'] for t in tr]))[0,1])
roads=[]
for r in load('work/verified_roads.json'):
 if r.get('nonped')=='V' or r.get('rw_type') not in ['1','3','4','5','6','7','9']:continue
 roads.append(proj(shape(r['the_geom'])).intersection(b))
total=unary_union(roads).length/1000
out={'corridors':rows,'cuisine_access':gstats,'tracts':tr,'spearman_density':rho,'street_km_total':total,'population_total':sum(t['population'] for t in tr),'restaurants_total':sum(t['restaurants'] for t in tr)}
(O/'Spatial_Analysis_Extended.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='tracts'},indent=2))
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':'#203B3B','axes.labelcolor':'#203B3B','xtick.color':'#456260','ytick.color':'#456260','font.size':11})
colors={'Latin American / regional':'#CE663E','Mexican':'#D6AA36','South Asian':'#168D93','East / Southeast Asian & Asian fusion':'#7967A3','Other recorded cuisines':'#456260','Unspecified':'#B6B7AD'}
fig,ax=plt.subplots(figsize=(12,5.7));fig.patch.set_facecolor('#F5F1E9');ax.set_facecolor('#F5F1E9')
left=np.zeros(4)
for g,col in colors.items():
 vals=np.array([r['groups'].get(g,0)/r['n']*100 for r in rows]);ax.barh(range(4),vals,left=left,color=col,label=g,height=.57);left+=vals
ax.set_yticks(range(4),[f"{r['corridor']} (n={r['n']})" for r in rows]);ax.invert_yaxis();ax.set_xlim(0,100);ax.set_xlabel('Share of restaurant records (%)');ax.spines[['top','right','left']].set_visible(False)
fig.suptitle('ONE NEIGHBORHOOD, DIFFERENT FOOD CORRIDORS',x=.04,ha='left',fontsize=17,fontweight='bold');ax.legend(loc='upper center',bbox_to_anchor=(.42,-.23),ncol=2,frameon=False,fontsize=9)
fig.text(.04,.025,'DOHMH snapshot: 21 Oct 2026 | Address-based corridors; six display groups, not ethnic identities.',fontsize=9)
fig.subplots_adjust(left=.25,right=.97,top=.86,bottom=.30);fig.savefig(O/'06_Corridor_Comparison.png',dpi=180);plt.close(fig)
