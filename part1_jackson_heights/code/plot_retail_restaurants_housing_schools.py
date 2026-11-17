import sys,json,math,os
from pathlib import Path
sys.path.insert(0,str(Path('work/python_libs').resolve()));os.environ['MPLCONFIGDIR']=str(Path('work').resolve())
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from shapely.geometry import shape,Point
from shapely.ops import transform
load=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
proj=lambda g:transform(lambda x,y:((np.asarray(x)+73.885)*111320*math.cos(math.radians(40.755)),(np.asarray(y)-40.755)*111132),g)
b=proj(shape(load('work/boundary.json')[0]['the_geom']));roads=load('work/verified_roads.json');lots=[]
for r in load('work/pluto_corridor_research.json'):
 p=proj(Point(float(r['longitude']),float(r['latitude'])))
 if b.covers(p):lots.append((r,p))
rest=[proj(shape(f['geometry'])) for f in load('outputs/Jackson_Heights_restaurants.geojson')['features']]
schools={}
for r in load('work/facdb_jackson_heights.json'):
 if r['facgroup']=='SCHOOLS (K-12)' and r.get('address'):schools.setdefault(r['address'],(r,proj(Point(float(r['longitude']),float(r['latitude'])))))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':'#203B3B','axes.labelcolor':'#203B3B'})
def lines(ax,g,**kw):
 if g.is_empty:return
 if hasattr(g,'geoms'):
  for gg in g.geoms:lines(ax,gg,**kw)
 elif g.geom_type=='Polygon':lines(ax,g.boundary,**kw)
 else:ax.plot(*g.xy,**kw)
def base(ax):
 ax.set_facecolor('#F5F1E9')
 for r in roads:
  g=proj(shape(r['the_geom'])).intersection(b)
  if not g.is_empty:lines(ax,g,color='#D6D7CD',lw=.5,zorder=0)
 lines(ax,b.boundary,color='#6C7C73',lw=1)
 x0,y0,x1,y1=b.bounds;ax.set_xlim(x0-100,x1+100);ax.set_ylim(y0-140,y1+80);ax.set_aspect('equal');ax.axis('off')
 for name,y,x in [('Northern Blvd',40.757,-73.885),('37th Avenue',40.7506,-73.881),('Roosevelt Ave',40.7485,-73.880)]:
  p=proj(Point(x,y));ax.text(p.x,p.y,name,fontsize=8,bbox=dict(fc='#F5F1E9',ec='none',alpha=.85),zorder=10)
 ax.plot([x0+80,x0+580],[y0-75,y0-75],color='#203B3B',lw=2);ax.text(x0+330,y0-50,'500 m',ha='center',fontsize=8)
 ax.text(.95,.97,'N ↑',transform=ax.transAxes,ha='right')
fig,axs=plt.subplots(1,2,figsize=(14,9));fig.patch.set_facecolor('#F5F1E9')
for ax in axs:base(ax)
ax=axs[0]
for r,p in lots:
 if float(r.get('retailarea',0) or 0)>0:ax.scatter(p.x,p.y,s=26,marker='s',c='#9D9B5C',alpha=.6,zorder=2)
ax.scatter([p.x for p in rest],[p.y for p in rest],s=9,c='#C85939',zorder=3)
ax.set_title('A · Food follows a commercial framework',loc='left',fontsize=13,pad=14)
ax.legend(handles=[Line2D([],[],marker='s',ls='',color='#9D9B5C',label='Tax lot with recorded retail area'),Line2D([],[],marker='o',ls='',color='#C85939',label='Restaurant record')],loc='lower left',bbox_to_anchor=(0,-.1),frameon=False,fontsize=9)
ax=axs[1]
for r,p in lots:
 n=float(r.get('unitsres',0) or 0)
 if n>0:ax.scatter(p.x,p.y,s=3 if n<10 else 10 if n<50 else 28,c='#358C8E',alpha=.48,linewidths=0)
for r,p in schools.values():ax.scatter(p.x,p.y,s=58,marker='^',c='#805B96',edgecolors='white',lw=.6,zorder=4)
ax.set_title('B · Housing and schools around the corridors',loc='left',fontsize=13,pad=14)
ax.legend(handles=[Line2D([],[],marker='o',ls='',color='#358C8E',markersize=s,label=l) for s,l in [(3,'1–9 residential units / lot'),(5,'10–49 units / lot'),(8,'50+ units / lot')]]+[Line2D([],[],marker='^',ls='',color='#805B96',label='K–12 facility address')],loc='lower left',bbox_to_anchor=(0,-.13),frameon=False,fontsize=9)
fig.suptitle('WHY HERE?  THE LAND USE BEHIND THE FOOD MAP',x=.055,ha='left',fontsize=19,fontweight='bold',y=.97)
fig.text(.055,.91,'Jackson Heights · Same study boundary, two complementary views',fontsize=11)
fig.text(.055,.035,'Sources: DOHMH (21 Oct 2026), NYC PLUTO 26v2, FacDB, CSCL and 2020 NTA.\nPoints represent records, not parcel footprints or zoning boundaries. Housing units are not resident counts.\nSchools are deduplicated by address; operating status, enrollment and entrances require verification. Roosevelt’s south side is outside the study area.',fontsize=9)
fig.subplots_adjust(left=.04,right=.98,bottom=.2,top=.85,wspace=.09);fig.savefig('outputs/Why_Here_Landuse_Context.png',dpi=180);plt.close(fig)
