import pandas as pd, geopandas as gpd, json
geo=pd.read_csv('pl/nygeo2020.pl',sep='|',header=None,dtype=str,encoding='latin-1')
geo=geo[[2,7,8]]; geo.columns=['sumlev','logrecno','geoid']
geo=geo[geo.sumlev=='150']
s1=pd.read_csv('pl/ny000012020.pl',sep='|',header=None,dtype=str,encoding='latin-1')
cols=['fileid','stusab','chariter','cifsn','logrecno']+[f'P1_{i:03d}' for i in range(1,72)]+[f'P2_{i:03d}' for i in range(1,74)]
s1.columns=cols
d=geo.merge(s1,on='logrecno')
d['GEOID']=d.geoid.str.split('US').str[1]
keep={'P2_001':'pop','P2_002':'hisp','P2_005':'white','P2_006':'black','P2_008':'asian'}
d=d[['GEOID']+list(keep)].rename(columns=keep)
for c in keep.values(): d[c]=d[c].astype(int)
bg=gpd.read_file('bg/tl_2020_36_bg.shp'); bg=bg[bg.COUNTYFP=='081']
bg=bg.merge(d,on='GEOID')
cd=gpd.read_file('cd.geojson'); print(cd.columns.tolist()); cd=cd[cd['boro_cd'].astype(float).astype(int)==403]
bg=bg.to_crs(2263); cd=cd.to_crs(2263)
bg['frac']=bg.intersection(cd.union_all()).area/bg.area
sel=bg[bg.frac>0.5].copy()
print(len(sel),'block groups; pop',sel['pop'].sum())
sel.to_file('bg403.gpkg')
