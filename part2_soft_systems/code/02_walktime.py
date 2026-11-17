









import json, sys, pathlib, math, re
import pandas as pd, geopandas as gpd, networkx as nx
from shapely.geometry import MultiLineString
from shapely.ops import unary_union, substring
from shapely.strtree import STRtree

RAW, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
CRS = "EPSG:26918"                   
SPEED = 80.0                           
BINS = [(0, 400, "within 5 min"), (400, 800, "5-10 min"), (800, math.inf, "beyond 10 min")]
BAND = 35                                                                  

                                     
cd = gpd.read_file(RAW / "cd403.geojson").to_crs(CRS)
cd_poly = cd.geometry.iloc[0]
nta = gpd.read_file(RAW / "nta_qn03.geojson").to_crs(CRS)[["nta2020", "ntaname", "geometry"]]
print("CD 403 area km2:", round(cd_poly.area / 1e6, 2), "| NTAs:", list(nta.ntaname))

                                      
rows = json.load(open(RAW / "dohmh_queens.json"))
df = pd.DataFrame(rows)
df["inspection_date"] = df["inspection_date"].fillna("")
df = df.sort_values(["camis", "inspection_date", "record_date"]).groupby("camis", as_index=False).last()
df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce"); df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
df = df[(df.latitude > 40.4) & (df.longitude < -73.5)]
rest = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326").to_crs(CRS)
                                                                                                                   
                                                                                                                   
                                                                                              
inside = rest.within(cd_poly)
print("points inside CD 403 polygon:", int(inside.sum()), "| inside but community_board!=403:", int((inside & (rest.community_board != "403")).sum()),
      "| community_board==403 outside polygon:", int((~inside & (rest.community_board == "403")).sum()),
      "(max distance m:", round(rest[~inside & (rest.community_board == "403")].distance(cd_poly).max(), 1), ")")
rest = rest[rest.community_board == "403"].copy()
rest = gpd.sjoin(rest, nta, how="left", predicate="within").drop(columns="index_right")
miss = rest.nta2020.isna()
if miss.any():                                              
    near = gpd.sjoin_nearest(rest.loc[miss, ["geometry"]], nta, how="left")
    rest.loc[miss, "nta2020"] = near.nta2020.values; rest.loc[miss, "ntaname"] = near.ntaname.values
print("restaurants in CD 403:", len(rest), "| assigned to nearest NTA because on boundary line:", int(miss.sum()))

                                                     
                                                                                                                      
                                                                                                                          
                                                                                                                          
STOP = {"DBA", "NEW", "GRAND", "THE", "EL", "LA", "LOS", "LAS", "LE", "INC", "LLC", "NYC", "NY"}
def name_key(dba):
    words = [w for w in re.sub(r"[^A-Z0-9 ]", " ", str(dba).upper()).split() if w not in STOP]
    return words[0] if words else str(dba).upper()
rest["xy"] = rest.geometry.x.round(1).astype(str) + "," + rest.geometry.y.round(1).astype(str)
rest["name_key"] = rest.dba.map(name_key)
rest = rest.sort_values(["inspection_date", "record_date"])
dup = rest.duplicated(["xy", "name_key"], keep="last")
removed = rest[dup][["camis", "dba", "building", "street", "inspection_date"]]
print("duplicate permit records removed:", len(removed)); print(removed.to_string(index=False))
removed.to_csv(OUT / "removed_duplicate_permits.csv", index=False)
rest = rest[~dup].drop(columns=["xy", "name_key"]).copy()
print("restaurants in CD 403 after cleaning:", len(rest))

def corridor(street):
    s = str(street).upper().replace(".", "").strip()
    s = s.replace("BOULEVARD", "BLVD").replace("AVENUE", "AVE")
    s = s.replace("37TH", "37").replace("31ST", "31")
    if s.startswith("ROOSEVELT AVE"): return "Roosevelt Avenue"
    if s.startswith("37 AVE"): return "37th Avenue"
    if s.startswith("NORTHERN BLVD"): return "Northern Boulevard"
    if s.startswith("JUNCTION BLVD"): return "Junction Boulevard"
    if s.startswith("ASTORIA BLVD"): return "Astoria Boulevard"
    return "Other streets"
rest["corridor"] = rest["street"].map(corridor)

                                           
ent = pd.DataFrame(json.load(open(RAW / "subway_entrances.json")))
ent = ent[ent.entry_allowed == "YES"].copy()
ent["lat"] = pd.to_numeric(ent.entrance_latitude); ent["lon"] = pd.to_numeric(ent.entrance_longitude)
ent = gpd.GeoDataFrame(ent, geometry=gpd.points_from_xy(ent.lon, ent.lat), crs="EPSG:4326").to_crs(CRS)
ent = ent[ent.distance(cd_poly) <= 1200].reset_index(drop=True)
print("entry-allowed subway entrances within 1.2 km of CD 403:", len(ent), "| stations:", sorted(ent.stop_name.unique()))

                                          
cscl = gpd.read_file(RAW / "cscl_box.geojson").to_crs(CRS)
WALKABLE_RW = {"1", "3", "4", "5", "6", "7", "10"}                                                                
elig = cscl[cscl.rw_type.isin(WALKABLE_RW) & (cscl.nonped != "V") & (cscl.status == "2")].copy()
print("CSCL segments in box:", len(cscl), "| walkable:", len(elig))

def key(x, y, lvl): return (round(x, 1), round(y, 1), str(lvl))
G = nx.Graph(); seg_geoms, seg_uv, seg_name = [], [], []
for r in elig.itertuples():
    parts = list(r.geometry.geoms) if isinstance(r.geometry, MultiLineString) else [r.geometry]
    for ln in parts:
        (x0, y0), (x1, y1) = ln.coords[0][:2], ln.coords[-1][:2]
        u, v = key(x0, y0, r.from_level_code), key(x1, y1, r.to_level_code)
        L = ln.length
        if G.has_edge(u, v): L = min(L, G[u][v]["w"])
        G.add_edge(u, v, w=L)
        seg_geoms.append(ln); seg_uv.append((u, v)); seg_name.append(r.stname_label)
tree = STRtree(seg_geoms)
print("graph nodes:", G.number_of_nodes(), "edges:", G.number_of_edges(), "| largest component share:",
      round(max(len(c) for c in nx.connected_components(G)) / G.number_of_nodes(), 3))

def snap(pt):
    i = int(tree.nearest(pt)); ln = seg_geoms[i]
    along = ln.project(pt); conn = pt.distance(ln.interpolate(along))
    return i, along, conn, ln.length

sources = {}
for r in ent.itertuples():
    i, along, conn, L = snap(r.geometry); u, v = seg_uv[i]; n = ("E", r.Index)
    G.add_edge(n, u, w=conn + along); G.add_edge(n, v, w=conn + (L - along)); sources[n] = r.Index
dist, paths = nx.multi_source_dijkstra(G, list(sources), weight="w")

                                               
recs = []
for r in rest.itertuples():
    i, along, conn, L = snap(r.geometry); u, v = seg_uv[i]
    cand = []
    if u in dist: cand.append((conn + along + dist[u], u))
    if v in dist: cand.append((conn + (L - along) + dist[v], v))
    if not cand: recs.append((math.inf, None, None, seg_name[i], conn)); continue
    d, node = min(cand); ent_idx = sources[paths[node][0]]
    recs.append((d, ent.loc[ent_idx, "stop_name"], ent.loc[ent_idx, "daytime_routes"], seg_name[i], conn))
rest["walk_m"] = [x[0] for x in recs]; rest["nearest_station"] = [x[1] for x in recs]
rest["routes"] = [x[2] for x in recs]; rest["snapped_street"] = [x[3] for x in recs]; rest["connector_m"] = [round(x[4], 1) for x in recs]
rest["walk_min"] = (rest.walk_m / SPEED).round(1)
rest["walk_bin"] = pd.cut(rest.walk_m, bins=[-1, 400, 800, math.inf], labels=[b[2] for b in BINS])
print("unreachable restaurants:", int((rest.walk_m == math.inf).sum()), rest.loc[rest.walk_m == math.inf, ["dba", "building", "street", "snapped_street"]].values.tolist())

                                    
order = [b[2] for b in BINS]
def summarise(by):
    t = pd.crosstab(rest[by], rest.walk_bin).reindex(columns=order, fill_value=0)
    t["total"] = t.sum(axis=1)
    for c in order: t[c + " %"] = (100 * t[c] / t["total"]).round(1)
    return t
by_nta = summarise("ntaname"); by_nta.loc["All CD 403"] = summarise("boro").loc["Queens"]
by_cor = summarise("corridor"); by_cor.loc["All CD 403"] = by_nta.loc["All CD 403"]
by_nta_cor = pd.crosstab([rest.ntaname, rest.corridor], rest.walk_bin).reindex(columns=order, fill_value=0); by_nta_cor["total"] = by_nta_cor.sum(axis=1)
by_nta.to_csv(OUT / "summary_by_subarea.csv"); by_cor.to_csv(OUT / "summary_by_corridor.csv"); by_nta_cor.to_csv(OUT / "summary_by_subarea_corridor.csv")
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 20)
print("\n== by sub-area ==\n", by_nta); print("\n== by corridor ==\n", by_cor); print("\n== sub-area x corridor ==\n", by_nta_cor)
print("\nmedian walk minutes by sub-area:\n", rest.groupby("ntaname").walk_min.median())

cols = ["camis", "dba", "building", "street", "zipcode", "cuisine_description", "community_board", "nta2020", "ntaname", "corridor",
        "nearest_station", "routes", "snapped_street", "connector_m", "walk_m", "walk_min", "walk_bin", "inspection_date"]
out = rest[cols + ["geometry"]].copy(); out["walk_m"] = out.walk_m.round(1); out["walk_bin"] = out.walk_bin.astype(str)
out.drop(columns="geometry").to_csv(OUT / "restaurants_cd403_walktime.csv", index=False)
out.to_crs("EPSG:4326").to_file(OUT / "restaurants_cd403_walktime.geojson", driver="GeoJSON")

                                            
def reach(D):
    pieces = []
    for ln, (u, v) in zip(seg_geoms, seg_uv):
        L = ln.length; du, dv = dist.get(u, math.inf), dist.get(v, math.inf)
        a = min(L, max(0.0, D - du)); b = min(L, max(0.0, D - dv))
        if a + b >= L: pieces.append(ln); continue
        if a > 0: pieces.append(substring(ln, 0, a))
        if b > 0: pieces.append(substring(ln, L - b, L))
    return unary_union(pieces).buffer(BAND)
shed = gpd.GeoDataFrame({"minutes": [5, 10], "metres": [400, 800]}, geometry=[reach(400), reach(800)], crs=CRS)
shed.to_crs("EPSG:4326").to_file(OUT / "walkshed_5_10min.geojson", driver="GeoJSON")
clip = shed.copy(); clip["geometry"] = clip.geometry.intersection(cd_poly)
clip.to_crs("EPSG:4326").to_file(OUT / "walkshed_5_10min_clipped_cd403.geojson", driver="GeoJSON")
ent[["stop_name", "daytime_routes", "entrance_type", "entry_allowed", "geometry"]].to_crs("EPSG:4326").to_file(OUT / "subway_entrances_used.geojson", driver="GeoJSON")
cd.to_crs("EPSG:4326").to_file(OUT / "cd403_boundary.geojson", driver="GeoJSON"); nta.to_crs("EPSG:4326").to_file(OUT / "nta_qn03.geojson", driver="GeoJSON")
elig[["stname_label", "rw_type", "geometry"]].to_crs("EPSG:4326").to_file(OUT / "walkable_streets.geojson", driver="GeoJSON")

                                          
ex = rest[rest.walk_m < math.inf].copy()
picks = []
for name in ["AREPA LADY", "NEPALI", "MOJITOS"]:
    m = ex[ex.dba.str.contains(name, na=False)]
    if len(m): picks.append(m.iloc[0])
for b in order:
    m = ex[ex.walk_bin == b].sort_values("walk_m")
    if len(m): picks.append(m.iloc[len(m) // 2])
print("\n== worked examples ==")
for p in picks:
    print(f"{p.dba} | {p.building} {p.street} | {p.ntaname} | snapped to {p.snapped_street} (connector {p.connector_m} m) | nearest entrance {p.nearest_station} ({p.routes}) | {p.walk_m:.0f} m = {p.walk_min} min -> {p.walk_bin}")
