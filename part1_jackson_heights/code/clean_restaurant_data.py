import sys,json,csv,math
from pathlib import Path
sys.path.insert(0,str(Path('work/python_libs').resolve()))
from shapely.geometry import shape,Point,mapping
from collections import Counter
root=Path('outputs');root.mkdir(exist_ok=True)
b=json.load(open('work/boundary.json',encoding='utf-8-sig'))[0]
boundary=shape(b['the_geom'])
raw=json.load(open('work/restaurants_raw.json',encoding='utf-8-sig'))
latest={}
for r in sorted(raw,key=lambda r:(r.get('inspection_date',''),r.get('cuisine_description',''),r.get('dba',''))):latest[r['camis']]=r
rows=[r for r in latest.values() if boundary.covers(Point(float(r['longitude']),float(r['latitude'])))]
rows.sort(key=lambda r:r.get('dba',''))
counts=Counter(r.get('cuisine_description','Unspecified') for r in rows)
streets=Counter(r['street'].strip() for r in rows)
tracts=json.load(open('work/tracts.json',encoding='utf-8-sig'))
for r in rows:
 p=Point(float(r['longitude']),float(r['latitude']))
 r['tract2020']=next((t['ct2020'] for t in tracts if shape(t['the_geom']).covers(p)),'')
 r['nta2020']='QN0301'
cols=['camis','dba','building','street','zipcode','cuisine_description','latitude','longitude','inspection_date','nta2020','tract2020']
with open(root/'Jackson_Heights_restaurants.csv','w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(rows)
json.dump({'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':[float(r['longitude']),float(r['latitude'])]},'properties':r} for r in rows]},open(root/'Jackson_Heights_restaurants.geojson','w'),indent=2)
json.dump({'type':'FeatureCollection','features':[{'type':'Feature','geometry':b['the_geom'],'properties':{k:v for k,v in b.items() if k!='the_geom'}}]},open(root/'Jackson_Heights_boundary.geojson','w'))
stats={'raw_rows':len(raw),'bbox_unique':len(latest),'restaurants':len(rows),'cuisine_categories':len(counts),'cuisines':counts.most_common(),'streets':streets.most_common(),'tracts':len(tracts),'bounds':boundary.bounds,'uninspected':sum(r['inspection_date'].startswith('1900') for r in rows)}
json.dump(stats,open(root/'analysis_summary.json','w'),indent=2)
print(json.dumps(stats,indent=2))
