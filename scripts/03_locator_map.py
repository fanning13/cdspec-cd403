import geopandas as gpd, matplotlib.pyplot as plt, matplotlib as mpl
from matplotlib.patches import ConnectionPatch, FancyArrow
from matplotlib import font_manager as fm
for f in fm.findSystemFonts(): 
    if 'Inter' in f: fm.fontManager.addfont(f)
mpl.rcParams['font.family']='Inter'
boro=gpd.read_file('boro.geojson').to_crs(2263)
nta=gpd.read_file('nta.geojson').to_crs(2263)
cd=gpd.read_file('cd.geojson'); cd=cd[cd.boro_cd.astype(float).astype(int)==403].to_crs(2263)
bg=gpd.read_file('bg403_an.gpkg').to_crs(2263)
n3=nta[nta.nta2020.isin(['QN0301','QN0302','QN0303'])].copy()
cent=bg.copy(); cent['geometry']=bg.representative_point()
pop=gpd.sjoin(cent,n3[['nta2020','geometry']]).groupby('nta2020')['pop'].sum()
n3['pop']=n3.nta2020.map(pop)
lga=gpd.overlay(cd,n3,how='difference')
WATER='#dfe9ef'; LAND='#f4f2ee'; ACC='#c8553d'
cols={'QN0301':'#e8a87c','QN0302':'#8fb8a8','QN0303':'#d4c26a'}
fig=plt.figure(figsize=(16,9),dpi=150,facecolor='white')
ax1=fig.add_axes([0.02,0.06,0.44,0.80]); ax2=fig.add_axes([0.50,0.06,0.48,0.80])
for ax in (ax1,ax2): ax.set_facecolor(WATER); ax.set_xticks([]); ax.set_yticks([])
for s in ax1.spines.values(): s.set_edgecolor('#bbb')
for s in ax2.spines.values(): s.set_edgecolor(ACC); s.set_linewidth(1.6)
# left: NYC
boro.plot(ax=ax1,color=LAND,edgecolor='#9a9a9a',lw=0.7)
boro[boro.boroname=='Queens'].plot(ax=ax1,color='#ebe6dc',edgecolor='#777',lw=0.9)
cd.plot(ax=ax1,color=ACC,edgecolor='#7a2e1f',lw=0.8)
lab={'Manhattan':(-14000,0),'Bronx':(0,0),'Brooklyn':(0,0),'Queens':(16000,-6000),'Staten Island':(0,0)}
for _,r in boro.iterrows():
    p=r.geometry.representative_point(); dx,dy=lab[r.boroname]
    ax1.text(p.x+dx,p.y+dy,r.boroname.upper(),ha='center',va='center',fontsize=11,color='#555',fontweight='semibold',alpha=.9)
bx=boro.total_bounds; ax1.set_xlim(bx[0]-3000,bx[2]+3000); ax1.set_ylim(bx[1]-3000,bx[3]+3000)
c=cd.total_bounds; pad=2500
ax1.add_patch(plt.Rectangle((c[0]-pad,c[1]-pad),c[2]-c[0]+2*pad,c[3]-c[1]+2*pad,fill=False,ec=ACC,lw=1.6))
# right: CD zoom
zx=(c[0]-pad,c[2]+pad); zy=(c[1]-pad,c[3]+pad)
nta.plot(ax=ax2,color=LAND,edgecolor='#cfcac0',lw=0.6)
n3.plot(ax=ax2,color=n3.nta2020.map(cols),edgecolor='white',lw=1.5)
cd.boundary.plot(ax=ax2,color='#222',lw=2.2)
names={'QN0301':'Jackson Heights','QN0302':'East Elmhurst','QN0303':'North Corona'}
for _,r in n3.iterrows():
    p=r.geometry.representative_point()
    ax2.text(p.x,p.y+700,names[r.nta2020],ha='center',fontsize=15,fontweight='bold',color='#222')
    ax2.text(p.x,p.y-700,f"{int(r['pop']):,} residents",ha='center',fontsize=11.5,color='#333')
ax2.text(0.80,0.82,'Flushing Bay',transform=ax2.transAxes,fontsize=11,color='#6a8797',style='italic',ha='center')
ax2.set_xlim(*zx); ax2.set_ylim(*zy); ax2.set_aspect('equal')
# connectors
for (xa,ya),(xb,yb) in [((c[2]+pad,c[3]+pad),(0,1)),((c[2]+pad,c[1]-pad),(0,0))]:
    fig.add_artist(ConnectionPatch((xa,ya),(xb,yb),coordsA='data',coordsB='axes fraction',axesA=ax1,axesB=ax2,color=ACC,lw=1,alpha=.7))
# north arrows & scale bars
def north(ax,x=0.94,y=0.88):
    ax.annotate('N',xy=(x,y+0.07),xytext=(x,y-0.02),xycoords='axes fraction',ha='center',fontsize=13,fontweight='bold',
                arrowprops=dict(arrowstyle='wedge,tail_width=0.6',color='#222'))
def scale(ax,miles,x0f=0.05,yf=0.05):
    xl=ax.get_xlim(); yl=ax.get_ylim(); L=miles*5280
    x0=xl[0]+(xl[1]-xl[0])*x0f; y0=yl[0]+(yl[1]-yl[0])*yf
    ax.plot([x0,x0+L/2],[y0,y0],color='#222',lw=4,solid_capstyle='butt'); ax.plot([x0+L/2,x0+L],[y0,y0],color='white',lw=4,solid_capstyle='butt')
    ax.plot([x0,x0+L],[y0,y0],color='#222',lw=0.6)
    ax.text(x0,y0+(yl[1]-yl[0])*0.02,'0',fontsize=9,ha='center'); ax.text(x0+L,y0+(yl[1]-yl[0])*0.02,f'{miles:g} mi',fontsize=9,ha='center')
[(a.set_xlabel(''),a.set_ylabel('')) for a in (ax1,ax2)]; north(ax1); north(ax2); scale(ax1,5); scale(ax2,0.5)
fig.text(0.02,0.94,'Where is Queens Community District 3 (CD 403)?',fontsize=24,fontweight='bold',color='#222')
fig.text(0.02,0.905,'Northwestern Queens, New York City · Jackson Heights, East Elmhurst and North Corona · about 179,000 residents (2020 Census)',fontsize=13,color='#555')
fig.text(0.02,0.02,'Sources: NYC Dept. of City Planning — Borough, Community District and 2020 NTA boundaries (NYC Open Data); U.S. Census Bureau 2020 Redistricting Data (P2), aggregated from block groups.',fontsize=9,color='#777')
fig.savefig('/mnt/user-data/outputs/CD403_locator_map.png',dpi=150,facecolor='white')
print(n3[['nta2020','pop']])
