import json
from pathlib import Path
from shapely.geometry import shape,Point
p=Path("analysis_outputs")
load=lambda f:json.loads(Path(f).read_text(encoding="utf-8-sig"))
b=shape(load(p/"cd403_boundary.geojson")["features"][0]["geometry"])
lots=[r for r in load("raw_data/pluto_26v2_area_extract.json") if b.covers(Point(float(r["longitude"]),float(r["latitude"])))]
retail=[r for r in lots if float(r.get("retailarea",0) or 0)>0]
def street(address):
 s=address.upper().replace("BOULEVARD","BLVD").replace("AVENUE","AVE").replace("37TH","37")
 if "NORTHERN BLVD" in s:return "Northern Boulevard"
 if "ROOSEVELT AVE" in s:return "Roosevelt Avenue"
 if "37 AVE" in s:return "37th Avenue"
 return "Other streets"
from collections import Counter
counts=Counter(street(r.get("address","")) for r in retail)
result={"total_lots":len(lots),"retail_lots":len(retail),"retail_corridors":dict(counts),"three_corridors_retail":len(retail)-counts["Other streets"]}
(p/"CD403_retail_corridor_recomputed.json").write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
