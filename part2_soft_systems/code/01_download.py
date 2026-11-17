
import json, sys, urllib.parse, urllib.request, pathlib, time, ssl, certifi
CTX = ssl.create_default_context(cafile=certifi.where())
RAW = pathlib.Path(sys.argv[1]); RAW.mkdir(parents=True, exist_ok=True)

def get(url, out):
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "cd403-walktime/1.0"})
            with urllib.request.urlopen(req, timeout=300, context=CTX) as r:
                data = r.read()
            (RAW / out).write_bytes(data); print(out, len(data), "bytes"); return
        except Exception as e:
            print("retry", out, e, file=sys.stderr); time.sleep(5)
    raise SystemExit("failed " + out)

def soda(base, params): return base + "?" + urllib.parse.urlencode(params)

                                                                                    
get("https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/NYC_Community_Districts/FeatureServer/0/query?where=BoroCD%3D403&outFields=*&f=geojson", "cd403.geojson")
                      
get(soda("https://data.cityofnewyork.us/resource/9nt8-h7nd.geojson", {"$where": "nta2020 like 'QN03%'"}), "nta_qn03.geojson")
                                                
get(soda("https://data.ny.gov/resource/i9wp-a4ja.json", {"$limit": 10000}), "subway_entrances.json")
                                                                   
get(soda("https://data.cityofnewyork.us/resource/43nn-pn8j.json", {
    "$select": "camis,dba,boro,building,street,zipcode,cuisine_description,latitude,longitude,community_board,nta,inspection_date,record_date,grade",
    "$where": "boro='Queens'", "$limit": 200000}), "dohmh_queens.json")
                                                                             
get(soda("https://data.cityofnewyork.us/resource/inkn-q76z.geojson", {
    "$where": "within_box(the_geom, 40.800, -73.920, 40.730, -73.825)", "$limit": 60000}), "cscl_box.geojson")
