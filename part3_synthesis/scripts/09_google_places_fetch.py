"""Fetch Google Places data (rating, number of ratings, price level, price range, primary type, business status) for the DOHMH restaurants in CD 403.
One Text Search (New) request per restaurant: textQuery = name + address, locationBias circle of 60 m around the DOHMH point, pageSize 3, no paging.
Field mask is limited to the fields we need (rating / priceRange bill at the Enterprise SKU). Hard cap: 600 requests in total over all runs (counter in out/.places_request_count.json).
A network error is retried once (the retry counts toward the cap); an HTTP error is never retried. 403/400/429 stops the run.
Match rule: the returned point is within 80 m of the DOHMH point AND (the names are similar OR the street number matches). Otherwise match_ok = False and no Google data is kept.
The API key is read ONLY from the environment variable GOOGLE_PLACES_API_KEY and is sent in a request header. It is never printed or written.
Output: out/google_places.csv (a snapshot is in ../data/google_places/; Google content, see the notes there). Raw responses are not stored.
Usage: python -I 09_google_places_fetch.py <out_dir> dry    (no requests: show the 5 test restaurants and the queries)
       python -I 09_google_places_fetch.py <out_dir> test   (5 requests: restaurants that also have a hand lookup)
       python -I 09_google_places_fetch.py <out_dir> full   (one request for every restaurant not yet in google_places.csv)
       python -I 09_google_places_fetch.py <out_dir> relax-dry   (no requests: list the unmatched ones that will be re-asked)
       python -I 09_google_places_fetch.py <out_dir> relax  (one more request for each unmatched restaurant whose returned place was 80-200 m away with a similar name.
                                                              Accepted only if within 200 m AND the names are similar (street number alone is NOT enough). Rows that stay unmatched are left as they were.)
"""
import sys, os, re, json, math, time, pathlib, unicodedata, urllib.request, urllib.error
import pandas as pd, geopandas as gpd

OUT = pathlib.Path(sys.argv[1]); MODE = sys.argv[2] if len(sys.argv) > 2 else "dry"
CAP, RADIUS_M, MAX_DIST_M, NAME_SIM = 600, 60.0, 80.0, 0.5
URL = "https://places.googleapis.com/v1/places:searchText"
MASK = ",".join("places." + f for f in ["id", "displayName", "formattedAddress", "location", "rating", "userRatingCount", "priceLevel", "priceRange", "primaryType", "businessStatus"])
COLS = ["camis", "dba", "place_id", "google_name", "rating", "user_rating_count", "price_level", "price_min", "price_max", "primary_type", "business_status", "match_dist_m", "match_ok"]
CSV, COUNTER = OUT / "google_places.csv", OUT / ".places_request_count.json"
STOP = {"inc", "llc", "corp", "co", "ltd", "the", "and", "restaurant", "restaurants", "of", "a", "cafe", "bar", "grill", "deli", "pizza", "kitchen", "food", "foods"}

def tokens(s):
    s = re.sub(r"[^a-z0-9 ]", " ", str(s).lower().replace("&", " and "))
    return {t for t in s.split() if t not in STOP and len(t) > 1}
def name_sim(a, b):
    A, B = tokens(a), tokens(b)
    if not A or not B:                       # name is only stop words: fall back to all words
        A, B = set(re.sub(r"[^a-z0-9 ]", " ", str(a).lower()).split()), set(re.sub(r"[^a-z0-9 ]", " ", str(b).lower()).split())
    return len(A & B) / min(len(A), len(B)) if A and B else 0.0
STOP2 = STOP | {"el", "la", "los", "las", "de", "del", "y", "new", "ny", "nyc", "queens", "bakery"}   # stricter: Spanish articles and generic words do not count (same as the analysis script)
def norm2(s): return re.sub(r"[^a-z0-9 ]", " ", unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().replace("&", " and "))
def name_sim2(a, b):
    A, B = {t for t in norm2(a).split() if t not in STOP2 and len(t) > 1}, {t for t in norm2(b).split() if t not in STOP2 and len(t) > 1}
    if not A or not B: A, B = set(norm2(a).split()), set(norm2(b).split())
    return len(A & B) / min(len(A), len(B)) if A and B else 0.0
def number_match(building, address):
    b = re.sub(r"\s", "", str(building)).lower(); first = str(address).split(",")[0].replace(" ", "").lower()
    return bool(b) and b != "nan" and first.startswith(b) and not first[len(b):len(b) + 1].isdigit()
def dist_m(lat1, lon1, lat2, lon2):
    p = math.pi / 180; a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 12742000 * math.asin(math.sqrt(a))
def pick(row, lat, lon, places, relax=False):
    """Best acceptable place among the returned ones (closest first). Returns (place, dist, ok); if none is ok, the closest one is returned for the log only.
    relax=True: up to 200 m, name must be similar (stricter name rule), street number alone is not enough."""
    best = None
    for p in places:
        loc = p.get("location", {}); d = dist_m(lat, lon, loc.get("latitude", 0), loc.get("longitude", 0))
        name = p.get("displayName", {}).get("text", "")
        if relax: ok = d <= 200.0 and name_sim2(row.dba, name) >= NAME_SIM
        else: ok = d <= MAX_DIST_M and (name_sim(row.dba, name) >= NAME_SIM or number_match(row.building, p.get("formattedAddress", "")))
        cand = (not ok, d, p, ok)
        if best is None or cand[:2] < best[:2]: best = cand
    return (best[2], best[1], best[3]) if best else (None, None, False)
def to_row(row, p, d, ok):
    r = {c: None for c in COLS}; r.update(camis=row.camis, dba=row.dba, match_dist_m=None if d is None else round(d, 1), match_ok=bool(ok))
    if p is None: return r
    r["google_name"] = p.get("displayName", {}).get("text")
    if ok:                                    # keep Google data only for accepted matches
        pr = p.get("priceRange", {}); s, e = pr.get("startPrice", {}), pr.get("endPrice", {})
        r.update(place_id=p.get("id"), rating=p.get("rating"), user_rating_count=p.get("userRatingCount"), price_level=p.get("priceLevel"),
                 price_min=float(s["units"]) if "units" in s else None, price_max=float(e["units"]) if "units" in e else None,
                 primary_type=p.get("primaryType"), business_status=p.get("businessStatus"))
    return r
def used():
    return json.loads(COUNTER.read_text())["n"] if COUNTER.exists() else 0
def bump():
    COUNTER.write_text(json.dumps({"n": used() + 1}))
def post(key, body):
    """One request. Returns (status, dict). Network error: one retry. Key only in a header; nothing about the request is printed."""
    for attempt in (1, 2):
        if used() >= CAP: sys.exit(f"hard cap of {CAP} requests reached, stop")
        bump()
        req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": MASK})
        try:
            with urllib.request.urlopen(req, timeout=30) as r: return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            try: msg = json.loads(e.read()).get("error", {}).get("message", "")[:200]
            except Exception: msg = ""
            return e.code, {"error": msg}
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2: return -1, {"error": "network error twice"}
            time.sleep(2)

r = gpd.read_file(OUT / "restaurants_cd403_walktime.geojson").to_crs("EPSG:4326")
r["lat"], r["lon"] = r.geometry.y, r.geometry.x
done = pd.read_csv(CSV, encoding="utf-8-sig", dtype={"camis": str}) if CSV.exists() else pd.DataFrame(columns=COLS)
todo = r[~r.camis.astype(str).isin(set(done.camis.astype(str)))]
if MODE in ("dry", "test"):                   # 5 places that also have a hand lookup (with a price band), so the match can be sanity-checked
    hand = pd.read_csv(OUT / "price_sample_results.csv", encoding="utf-8-sig"); hand = hand[hand.lo.notna()]
    todo = todo[todo.dba.str.upper().isin(set(hand.name.str.upper()))].drop_duplicates("dba").head(5)
RELAX = MODE in ("relax", "relax-dry")
if RELAX:                                     # unmatched, but the place Google returned was 80-200 m away and has a similar name
    c = done[(done.match_ok != True) & done.google_name.notna() & (done.match_dist_m <= 200)]
    c = c[[name_sim2(a, b) >= NAME_SIM for a, b in zip(c.dba, c.google_name)]]
    todo = r[r.camis.astype(str).isin(set(c.camis))]
print(f"restaurants: {len(r)} | already fetched: {len(done)} | to fetch now: {len(todo)} | requests used so far: {used()} (cap {CAP})")
def query(x): return f"{x.dba} {x.building} {str(x.street).title()}, Queens NY {x.zipcode}"
if MODE in ("dry", "relax-dry"):
    for x in todo.itertuples(): print("would ask:", query(x))
    if RELAX: print(f"after this run the total would be {used() + len(todo)} of {CAP}")
    sys.exit()
key = os.environ.get("GOOGLE_PLACES_API_KEY")
if not key: sys.exit("GOOGLE_PLACES_API_KEY is not set. In PowerShell run:  $env:GOOGLE_PLACES_API_KEY = '...'  then run this script again.")
def merged(rows):
    """done + new rows. In relax mode a row is replaced only if it is now matched; rows that stay unmatched keep their old content."""
    new = pd.DataFrame(rows, columns=COLS)
    if RELAX: new = new[new.match_ok == True]
    return pd.concat([done[~done.camis.isin(new.camis)], new]) if len(done) else new
rows, n0 = [], used()
for x in todo.itertuples():
    body = {"textQuery": query(x), "pageSize": 3, "locationBias": {"circle": {"center": {"latitude": x.lat, "longitude": x.lon}, "radius": 200.0 if RELAX else RADIUS_M}}}
    code, js = post(key, body)
    if code != 200:
        print(f"HTTP {code} for camis {x.camis}: {js.get('error', '')}")
        if code in (400, 401, 403, 429, -1): break
        rows.append(to_row(x, None, None, False)); continue
    p, d, ok = pick(x, x.lat, x.lon, js.get("places", []), relax=RELAX)
    rows.append(to_row(x, p, d, ok)); time.sleep(0.05)
    if len(rows) % 50 == 0: merged(rows).to_csv(CSV, index=False, encoding="utf-8-sig")   # save progress
new = pd.DataFrame(rows, columns=COLS)
all_ = merged(rows)
all_.to_csv(CSV, index=False, encoding="utf-8-sig")
print(f"requests used in this run: {used() - n0} | total so far: {used()} | rows saved: {len(new)} (csv now {len(all_)})")
ok = new[new.match_ok == True]
print(f"matched {len(ok)} of {len(new)}")
pd.set_option("display.width", 250, "display.max_colwidth", 38)
print(new.drop(columns=["place_id"]).to_string(index=False))
print("\nunmatched:", new[new.match_ok != True][["dba", "google_name", "match_dist_m"]].to_string(index=False) if (new.match_ok != True).any() else "none")
print("not OPERATIONAL:", ok[ok.business_status != "OPERATIONAL"][["dba", "business_status"]].to_string(index=False) if (ok.business_status != "OPERATIONAL").any() else "none")
