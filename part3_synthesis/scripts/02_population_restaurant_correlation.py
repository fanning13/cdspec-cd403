import pandas as pd, geopandas as gpd, numpy as np, json
from scipy.stats import spearmanr, pearsonr
bg=gpd.read_file('bg403.gpkg')
r=pd.DataFrame(json.load(open('rest.json')))
r=r.dropna(subset=['latitude']); r=r[r.latitude.astype(float)>40]
r=r.drop_duplicates('camis')
print('restaurants',len(r))
g=gpd.GeoDataFrame(r,geometry=gpd.points_from_xy(r.longitude.astype(float),r.latitude.astype(float)),crs=4326).to_crs(2263)
def grp(c):
    c=str(c).lower()
    if any(k in c for k in ['latin','spanish','mexican','tex-mex','peruvian','colombian','ecuador','caribbean','brazil','tapas','chilean','argentin']): return 'Latin'
    if any(k in c for k in ['bangladeshi','indian','pakistani','nepal','tibetan','afghan','himalay']): return 'SouthAsian'
    if any(k in c for k in ['chinese','japanese','korean','thai','asian','vietnam','filipino','indonesian','sushi']): return 'EastSEAsian'
    return 'Other'
g['grp']=g.cuisine_description.map(grp)
bg['area_ha']=bg.area/107639.1
bg['dens']=bg['pop']/bg.area_ha
for c in ['hisp','asian','white','black']: bg['p_'+c]=bg[c]/bg['pop'].clip(lower=1)
sh=bg[['p_hisp','p_asian','p_white','p_black']].clip(lower=1e-9)
bg['diversity']=1-(bg[['p_hisp','p_asian','p_white','p_black']]**2).sum(axis=1)
j=gpd.sjoin_nearest(g,bg[['GEOID','geometry']],how='left')  # nearest BG (handles boundary streets)
cnt=j.groupby('GEOID').size()
bg['n']=bg.GEOID.map(cnt).fillna(0)
bg['n_per_ha']=bg.n/bg.area_ha
print('BG stats: pop median',bg['pop'].median(),'area median ha',round(bg.area_ha.median(),1),'restaurants per BG median',bg.n.median(),'zeros',(bg.n==0).sum())
print('\n== Block group level (n=%d) Spearman with restaurant density =='%len(bg))
for v in ['dens','p_hisp','p_asian','p_white','p_black','diversity']:
    rho,p=spearmanr(bg[v],bg.n_per_ha); print(f'{v:10s} rho={rho:+.2f} p={p:.3f}')
# 400m around each restaurant vs random points: resident composition
# hex/grid analysis with areal weighting
from shapely.geometry import box
cdg=gpd.read_file('cd.geojson'); cdg=cdg[cdg.boro_cd.astype(float).astype(int)==403].to_crs(2263)
xmin,ymin,xmax,ymax=cdg.total_bounds; s=1312 # 400m
cells=[box(x,y,x+s,y+s) for x in np.arange(xmin,xmax,s) for y in np.arange(ymin,ymax,s)]
gr=gpd.GeoDataFrame(geometry=cells,crs=2263); gr=gr[gr.intersects(cdg.union_all())]
gr=gr[gr.intersection(cdg.union_all()).area/gr.area>0.5].reset_index(drop=True)
ov=gpd.overlay(bg[['pop','hisp','asian','white','black','geometry']].assign(a0=bg.area),gr.reset_index(),how='intersection')
w=ov.area/ov.a0
for c in ['pop','hisp','asian','white','black']: ov[c]=ov[c]*w
agg=ov.groupby('index')[['pop','hisp','asian','white','black']].sum()
gr=gr.join(agg)
gr['n']=gpd.sjoin(g,gr,predicate='within').groupby('index_right').size().reindex(gr.index).fillna(0)
for c in ['hisp','asian','white','black']: gr['p_'+c]=gr[c]/gr['pop']
print('\n== 400m grid (n=%d) Spearman with restaurant count =='%len(gr))
for v in ['pop','p_hisp','p_asian','p_white','p_black']:
    rho,p=spearmanr(gr[v],gr.n,nan_policy='omit'); print(f'{v:10s} rho={rho:+.2f} p={p:.3f}')
# cuisine match: share of restaurants of group vs resident share in nearest BG
print('\n== Cuisine group vs residents of restaurant\'s own block group ==')
j2=j.merge(bg[['GEOID','p_hisp','p_asian']],on='GEOID')
print(j2.groupby('grp')[['p_hisp','p_asian']].mean().round(3), '\ncounts',j2.grp.value_counts().to_dict())
print('district resident share hisp %.3f asian %.3f'%(bg.hisp.sum()/bg['pop'].sum(),bg.asian.sum()/bg['pop'].sum()))
bg.to_file('bg403_an.gpkg'); gr.to_file('grid400.gpkg'); g.to_file('rest.gpkg')
