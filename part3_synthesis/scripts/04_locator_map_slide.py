import geopandas as gpd, matplotlib.pyplot as plt, matplotlib as mpl, numpy as np
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
n3['pop']=n3.nta2020.map(gpd.sjoin(cent,n3[['nta2020','geometry']]).groupby('nta2020')['pop'].sum())
WATER='#dfe9ef'; LAND='#f4f2ee'; ACC='#c8553d'
cols={'QN0301':'#e8a87c','QN0302':'#8fb8a8','QN0303':'#d4c26a'}
W,H=16,9
fig=plt.figure(figsize=(W,H),dpi=150,facecolor=WATER)
ax=fig.add_axes([0,0,1,1]); ax.set_facecolor(WATER); ax.axis('off')
c=cd.total_bounds; cw=c[2]-c[0]; ch=c[3]-c[1]
# extent: height = ch*1.5; width by aspect; CD centered at 68% of width
hy=ch*1.95; wx=hy*W/H; cx=(c[0]+c[2])/2; cy=(c[1]+c[3])/2
x0=cx-0.60*wx; ax.set_xlim(x0,x0+wx); ax.set_ylim(cy-hy*0.58,cy+hy*0.42)
nta.plot(ax=ax,color=LAND,edgecolor='#d6d1c7',lw=0.7)
n3.plot(ax=ax,color=n3.nta2020.map(cols),edgecolor='white',lw=2)
cd.boundary.plot(ax=ax,color='#222',lw=2.6)
names={'QN0301':'Jackson Heights','QN0302':'East Elmhurst','QN0303':'North Corona'}
for _,r in n3.iterrows():
    p=r.geometry.representative_point()
    ax.text(p.x,p.y+500,names[r.nta2020],ha='center',fontsize=19,fontweight='bold',color='#222')
    ax.text(p.x,p.y-650,f"{int(r['pop']):,} residents",ha='center',fontsize=14,color='#333')
ax.text(c[2]-2500,c[3]-300,'Flushing Bay',fontsize=13,color='#6a8797',style='italic',ha='center')
ax.text((c[0]+c[2])/2,c[1]-1400,'Queens Community District 3 (CD 403)',fontsize=13,color='#222',ha='center',fontweight='semibold')
# left fade for text panel
grad=np.ones((10,256,4)); grad[...,:3]=mpl.colors.to_rgb('#f7f6f3'); grad[...,3]=np.clip(np.linspace(1.15,-0.1,256),0,1)
fax=fig.add_axes([0,0,0.48,1]); fax.imshow(grad,aspect='auto',extent=[0,1,0,1]); fax.axis('off')
# inset NYC (top right)
ia=fig.add_axes([0.825,0.60,0.155,0.36]); ia.set_facecolor(WATER)
boro.plot(ax=ia,color=LAND,edgecolor='#9a9a9a',lw=0.5)
boro[boro.boroname=='Queens'].plot(ax=ia,color='#ebe6dc',edgecolor='#777',lw=0.6)
cd.plot(ax=ia,color=ACC,edgecolor='#7a2e1f',lw=0.5)
bx=boro.total_bounds; ia.set_xlim(bx[0]-2000,bx[2]+2000); ia.set_ylim(bx[1]-2000,bx[3]+2000); ia.set_xticks([]); ia.set_yticks([]); ia.set_xlabel(''); ia.set_ylabel('')
for s in ia.spines.values(): s.set_edgecolor('#999'); s.set_linewidth(1)
ia.text(0.5,0.02,'New York City',transform=ia.transAxes,ha='center',va='bottom',fontsize=10,color='#555')
for nm,(dx,dy) in {'Manhattan':(-9000,3000),'Queens':(9000,-7000),'Brooklyn':(0,0),'Bronx':(0,0),'Staten Island':(0,0)}.items():
    p=boro[boro.boroname==nm].geometry.iloc[0].representative_point(); ia.text(p.x+dx,p.y+dy,nm,fontsize=7,ha='center',color='#666')
# north arrow & scale (bottom right)
ax.annotate('N',xy=(0.955,0.20),xytext=(0.955,0.11),xycoords='figure fraction',ha='center',fontsize=15,fontweight='bold',arrowprops=dict(arrowstyle='wedge,tail_width=0.7',color='#222'))
L=0.5*5280; xs=x0+wx*0.80; ys=cy-hy*0.58+hy*0.06
ax.plot([xs,xs+L/2],[ys,ys],color='#222',lw=5,solid_capstyle='butt'); ax.plot([xs+L/2,xs+L],[ys,ys],color='white',lw=5,solid_capstyle='butt'); ax.plot([xs,xs+L],[ys,ys],color='#222',lw=0.6)
ax.text(xs,ys+hy*0.02,'0',fontsize=10,ha='center'); ax.text(xs+L,ys+hy*0.02,'0.5 mi',fontsize=10,ha='center')
fig.text(0.985,0.012,'Sources: NYC DCP boundaries (NYC Open Data); U.S. Census Bureau 2020 (P2).',ha='right',fontsize=8.5,color='#777')
fig.savefig('/home/claude/cdspec-cd403/images/part3_synthesis/CD403_locator_map_slide.png',dpi=150,facecolor=WATER)
