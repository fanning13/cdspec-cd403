# Restaurants on the three main food corridors, grouped like the StoryMap icon map
import json, collections
d=json.load(open('part2_soft_systems/analysis_outputs/CD403_Restaurant_Cuisines.geojson'))
G={'Latin American':['Latin American','Mexican','Spanish','Peruvian','Tex-Mex','Brazilian','Tapas','Caribbean'],
   'American, pizza, bakery & café':['American','Bakery Products/Desserts','Pizza','Juice, Smoothies, Fruit Salads','Hamburgers','Chicken','Coffee/Tea','Frozen Desserts','Donuts','Sandwiches','Pancakes/Waffles'],
   'East & Southeast Asian':['Chinese','Asian/Asian Fusion','Japanese','Thai','Chinese/Cuban'],
   'South Asian':['Bangladeshi','Indian','Pakistani']}
def grp(c):
    for k,v in G.items():
        if c in v: return k
    return 'Other or not listed'
out=[]; summ={}
for f in d['features']:
    p=f['properties']
    if p['corridor'] in ('Roosevelt Avenue','37th Avenue','Northern Boulevard'):
        g=grp(p['cuisine_description'])
        out.append({'type':'Feature','geometry':f['geometry'],'properties':{'name':p['dba'],'address':f"{p['building']} {p['street'].title()}",'cuisine':p['cuisine_description'] or 'Not listed','food_group':g,'corridor':p['corridor'],'walk_min':p['walk_min'],'nearest_station':p['nearest_station']}})
        summ.setdefault(p['corridor'],collections.Counter())[g]+=1
json.dump({'type':'FeatureCollection','features':out},open('part3_synthesis/data/restaurants/main_corridors_restaurants.geojson','w'))
json.dump({k:dict(v) for k,v in summ.items()},open('part3_synthesis/data/restaurants/main_corridors_summary.json','w'),indent=1)
for k,v in summ.items(): print(k,sum(v.values()),v.most_common())
