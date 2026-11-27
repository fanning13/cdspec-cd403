"""Google Places data for CD 403 restaurants: do restaurants UNDER the elevated 7 train (Roosevelt Ave) differ from those AWAY from it in rating, review count and price?
Input: out/google_places.csv (from 09_google_places_fetch.py; Google content), out/restaurants_cd403_walktime.geojson, out/segments_v2.geojson, out/price_sample_results.csv (hand lookups, for a check).
Under = address street is Roosevelt Avenue and the point is within 30 m of a Roosevelt Ave segment. Away = at least 200 m from any Roosevelt Ave segment (same rule as 30_price_sample.py (not in this repo)). The rest are left out of the under/away tests.
Samples (fixed before looking at any under/away result):
  main  = matched (match_ok) AND OPERATIONAL AND the Google name agrees with the DOHMH name (token overlap >= 0.5 after dropping Spanish articles and generic words). Matches made only by street number are dropped.
  loose = matched AND OPERATIONAL (the match rule of the fetch script, as is). Shown as a robustness check. In both, a Google place that matched two DOHMH records is counted once.
Subsets: all places | no chains | no chains, no bars, no bakeries. Each is tested plainly and within cuisine group (stratified permutation test).
Measures (all reported, none picked): rating, review count, price level (1-4), price lower bound, price upper bound, price midpoint, share of places with a price band.
Price bands come from Google's priceRange. They are wide (for example $20-70). Open-ended bands ($100+) have a lower bound but no upper bound or midpoint, so they drop out of those two.
Test: permutation test of the difference in means (10,000 shuffles of the under/away labels, two-sided). No correction for the many tests: read p-values as a guide, not as proof.
Output: out/google_places_tests.csv, out/google_places_by_corridor.csv, out/google_places_by_group.csv.
Usage: python -I 10_google_places_analysis.py <out_dir>
"""
import sys, re, pathlib, unicodedata
import numpy as np, pandas as pd, geopandas as gpd
OUT = pathlib.Path(sys.argv[1]); CRS = "EPSG:26918"; NPERM = 10000
rng = np.random.default_rng(7)
pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_colwidth", 40)

def group(c):
    c = str(c).lower()
    if any(k in c for k in ["latin", "mexican", "spanish", "tex-mex", "peruvian", "caribbean", "colombian", "salvadoran", "ecuadorian", "brazilian", "cuban", "chilean", "argentin"]): return "Latin American"
    if any(k in c for k in ["indian", "bangladeshi", "pakistani", "afghan", "nepal", "tibetan", "himalayan", "sri lank", "south asian"]): return "South Asian"
    if any(k in c for k in ["chinese", "japanese", "korean", "thai", "asian", "filipino", "vietnam", "indonesian", "malaysian", "sushi"]): return "East/SE Asian"
    if any(k in c for k in ["american", "pizza", "hamburger", "chicken", "sandwich", "donut", "coffee", "bakery", "ice cream", "juice", "steak", "seafood", "delicatessen"]): return "American/fast food"
    return "Other"
CHAIN = ["STARBUCKS", "MCDONALD", "DUNKIN", "SUBWAY", "BURGER KING", "WENDY", "KFC", "DOMINO", "PAPA JOHN", "POPEYES", "CHIPOTLE", "TACO BELL", "PIZZA HUT", "FIVE GUYS", "SHAKE SHACK", "CHICK-FIL", "BASKIN", "TIM HORTON", "7-ELEVEN", "APPLEBEE", "IHOP", "DENNY", "PANERA", "COLD STONE", "COFFEE BEAN",
         "WINGSTOP", "RAISING CANE", "PARIS BAGUETTE", "POTBELLY", "CAFFE BENE", "CARVEL"]   # list of 30_price_sample.py (not in this repo) + 6 more chains seen in this data
STOP = {"inc", "llc", "corp", "corporation", "co", "ltd", "the", "and", "of", "a", "restaurant", "restaurants", "cafe", "bar", "grill", "deli", "pizza", "kitchen", "food", "foods", "bakery",
        "el", "la", "los", "las", "de", "del", "y", "new", "ny", "nyc", "queens"}
def norm(s): return re.sub(r"[^a-z0-9 ]", " ", unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().replace("&", " and "))
def sim(a, b):
    A, B = {t for t in norm(a).split() if t not in STOP and len(t) > 1}, {t for t in norm(b).split() if t not in STOP and len(t) > 1}
    if not A or not B: A, B = set(norm(a).split()), set(norm(b).split())
    return len(A & B) / min(len(A), len(B)) if A and B else 0.0

# ---- build the table -------------------------------------------------------------------------------------------------------------------
r = gpd.read_file(OUT / "restaurants_cd403_walktime.geojson").to_crs(CRS)
seg = gpd.read_file(OUT / "segments_v2.geojson").to_crs(CRS)
roos = seg[seg.name.fillna("").str.upper().str.contains("ROOSEVELT")].geometry.union_all()
r["d_roos"] = r.geometry.distance(roos)
on_roos = r.street.fillna("").str.upper().str.contains("ROOSEVELT")
r["side"] = np.where(on_roos & (r.d_roos <= 30), "under", np.where(r.d_roos >= 200, "away", "between"))
r["cgroup"] = r.cuisine_description.map(group)
g = pd.read_csv(OUT / "google_places.csv", encoding="utf-8-sig", dtype={"camis": str}).drop(columns=["dba"])
d = pd.DataFrame(r.drop(columns="geometry")).merge(g, on="camis", how="left")
d["match_ok"] = d.match_ok.fillna(False).astype(bool)
d["sim"] = [sim(a, b) if isinstance(b, str) else 0.0 for a, b in zip(d.dba.fillna(""), d.google_name)]
d["oper"] = d.business_status.eq("OPERATIONAL")
d["level"] = d.price_level.map({"PRICE_LEVEL_INEXPENSIVE": 1, "PRICE_LEVEL_MODERATE": 2, "PRICE_LEVEL_EXPENSIVE": 3, "PRICE_LEVEL_VERY_EXPENSIVE": 4})
d["lo"], d["hi"] = d.price_min, d.price_max; d["mid"] = (d.lo + d.hi) / 2; d["has"] = d.lo.notna().astype(float)
d["chain"] = d.dba.fillna("").str.upper().apply(lambda s: any(c in s for c in CHAIN))
pt = d.primary_type.fillna("")
d["bar"] = pt.str.contains("bar$|^bar|night_club|pub|beer_garden|sports_bar", regex=True)
d["bakery"] = pt.isin(["bakery", "cake_shop", "pastry_shop"]) | d.cuisine_description.fillna("").str.contains("Bakery", case=False)
SAMPLES = {"main": d.match_ok & d.oper & (d.sim >= 0.5), "loose": d.match_ok & d.oper}
def sample(name):
    s = d[SAMPLES[name]]; return s[~s.place_id.duplicated()].copy()
S = sample("main")

# ---- 1. match quality and coverage -------------------------------------------------------------------------------------------------------
print(f"DOHMH restaurants: {len(d)} | matched (fetch rule): {int(d.match_ok.sum())} ({d.match_ok.mean():.1%}) | unmatched: {int((~d.match_ok).sum())}")
print(f"matched but not OPERATIONAL: {int((d.match_ok & ~d.oper).sum())} {d[d.match_ok & ~d.oper].business_status.value_counts().to_dict()}")
print(f"matched by street number only (Google name differs, token overlap < 0.5): {int((d.match_ok & (d.sim < 0.5)).sum())}")
print(f"main sample: {len(S)} places | loose sample: {len(sample('loose'))} | Google places matched by two DOHMH records (second one dropped): {int((d.match_ok & d.oper & (d.sim >= 0.5) & d.place_id.duplicated()).sum())}")
print("side counts, DOHMH:", d.side.value_counts().to_dict(), "| main sample:", S.side.value_counts().to_dict())
def cov(x):
    return pd.Series({"dohmh": len(x), "matched": int(x.match_ok.sum()), "main": int(x.main.sum()), "rating": int(x[x.main].rating.notna().sum()), "price band": int(x[x.main].has.sum()),
                      "share with band (main)": round(x[x.main].has.mean(), 2) if x.main.any() else np.nan})
d["main"] = d.index.isin(S.index)
print("\ncoverage by corridor:"); print(d.groupby("corridor").apply(cov, include_groups=False).to_string())
print("\ncoverage by side:"); print(d.groupby("side").apply(cov, include_groups=False).to_string())
print("\ncoverage by cuisine group:"); print(d.groupby("cgroup").apply(cov, include_groups=False).to_string())
um = d[~d.match_ok]
near = um[um.google_name.notna() & (um.match_dist_m <= 200) & (um.sim >= 0.5)]
print(f"\nunmatched: {len(um)} | of these, {len(near)} have a similar-name place returned between 80 and 200 m (probably the same business, DOHMH point is off; Google data was not kept for them)")

# ---- 2. sanity check against the hand lookups ----------------------------------------------------------------------------------------------
h = pd.read_csv(OUT / "price_sample_results.csv", encoding="utf-8-sig"); h = h[h.lo.notna()].copy()
h["building"] = h.address.str.split().str[0]; h["key"] = h.name.str.upper() + "|" + h.building
d["key"] = d.dba.str.upper() + "|" + d.building.astype(str)
m = h.merge(d[d.main][["key", "lo", "hi", "google_name"]], on="key", suffixes=("_hand", "_api"))
same = (m.lo_hand == m.lo_api) & (m.hi_hand == m.hi_api)
print(f"\nhand lookups with a band: {len(h)} | found in the API main sample: {len(m)} | same band: {int(same.sum())} | different: {int((~same).sum())}")
if (~same).any(): print(m[~same][["name", "lo_hand", "hi_hand", "lo_api", "hi_api"]].to_string(index=False))

# ---- 3. under vs away tests --------------------------------------------------------------------------------------------------------------
MEAS = [("rating", "rating"), ("review count", "user_rating_count"), ("price level (1-4)", "level"), ("price lower bound $", "lo"), ("price upper bound $", "hi"), ("price midpoint $", "mid"), ("share with a price band", "has")]
def plain(u, a):
    x = np.concatenate([u, a]); k = len(u); diff = u.mean() - a.mean()
    P = x[rng.random((NPERM, len(x))).argsort(axis=1)]; sh = P[:, :k].mean(1) - P[:, k:].mean(1)
    return diff, (np.sum(np.abs(sh) >= abs(diff) - 1e-12) + 1) / (NPERM + 1)
def within(v, s, gr):
    """stratified: shuffle the under/away labels inside each cuisine group; statistic = weighted mean of the within-group differences"""
    num, den, parts = 0.0, 0.0, []
    for _, idx in pd.DataFrame({"v": v, "s": s, "g": gr}).groupby("g"):
        u, a = idx[idx.s == "under"].v.to_numpy(), idx[idx.s == "away"].v.to_numpy()
        if len(u) and len(a): parts.append((u, a, len(u) * len(a) / (len(u) + len(a))))
    if not parts: return np.nan, np.nan
    W = sum(w for *_, w in parts); diff = sum(w * (u.mean() - a.mean()) for u, a, w in parts) / W; sh = np.zeros(NPERM)
    for u, a, w in parts:
        x = np.concatenate([u, a]); P = x[rng.random((NPERM, len(x))).argsort(axis=1)]; sh += w * (P[:, :len(u)].mean(1) - P[:, len(u):].mean(1)) / W
    return diff, (np.sum(np.abs(sh) >= abs(diff) - 1e-12) + 1) / (NPERM + 1)
SUBS = {"all places": lambda x: x, "no chains": lambda x: x[~x.chain], "no chains, bars, bakeries": lambda x: x[~x.chain & ~x.bar & ~x.bakery]}
rows = []
for sname in ["main", "loose"]:
    base = sample(sname); base = base[base.side.isin(["under", "away"])]
    for subname, f in SUBS.items():
        x = f(base); print(f"\n=== sample: {sname} | subset: {subname} | under n={int((x.side == 'under').sum())}, away n={int((x.side == 'away').sum())} ===")
        out = []
        for lab, col in MEAS:
            y = x[x[col].notna()]; u, a = y[y.side == "under"][col].to_numpy(float), y[y.side == "away"][col].to_numpy(float)
            if len(u) < 3 or len(a) < 3: out.append({"measure": lab, "n_under": len(u), "n_away": len(a)}); continue
            diff, p = plain(u, a); wd, wp = within(y[col].to_numpy(float), y.side.to_numpy(), y.cgroup.to_numpy())
            out.append({"measure": lab, "n_under": len(u), "n_away": len(a), "mean_under": u.mean(), "mean_away": a.mean(), "diff": diff, "p": p, "median_under": np.median(u), "median_away": np.median(a), "diff_within_group": wd, "p_within_group": wp})
        o = pd.DataFrame(out); print(o.round({"mean_under": 2, "mean_away": 2, "diff": 2, "median_under": 1, "median_away": 1, "diff_within_group": 2, "p": 3, "p_within_group": 3}).to_string(index=False))
        rows.append(o.assign(sample=sname, subset=subname))
pd.concat(rows).to_csv(OUT / "google_places_tests.csv", index=False, encoding="utf-8-sig")
print("\nby cuisine group, under vs away (main sample, all places): mean price midpoint $ (n) | mean rating (n)")
b = S[S.side.isin(["under", "away"])]
for gname, x in b.groupby("cgroup"):
    f = lambda col, s: (f"{x[(x.side == s) & x[col].notna()][col].mean():.1f} ({int(((x.side == s) & x[col].notna()).sum())})" if ((x.side == s) & x[col].notna()).any() else "- (0)")
    print(f"  {gname:20s} price mid: under {f('mid', 'under')} vs away {f('mid', 'away')} | rating: under {f('rating', 'under')} vs away {f('rating', 'away')}")

# ---- 4. rating and price by corridor and cuisine group -----------------------------------------------------------------------------------
def summ(x):
    return pd.Series({"n": len(x), "rating_mean": x.rating.mean(), "rating_median": x.rating.median(), "reviews_median": x.user_rating_count.median(), "n_band": int(x.has.sum()), "share_band": x.has.mean(),
                      "mid_mean": x.mid.mean(), "mid_median": x.mid.median(), "lo_median": x.lo.median(), "hi_median": x.hi.median()})
for key, name in [("corridor", "google_places_by_corridor.csv"), ("cgroup", "google_places_by_group.csv")]:
    t = S.groupby(key).apply(summ, include_groups=False).round(2); t.to_csv(OUT / name, encoding="utf-8-sig")
    print(f"\nmain sample by {key}:"); print(t.to_string())
cg = S.groupby(["corridor", "cgroup"]).apply(summ, include_groups=False).round(2)
cg.to_csv(OUT / "google_places_by_corridor_group.csv", encoding="utf-8-sig")
for col in ["mid_mean", "rating_mean"]:
    pv = cg[col].where(cg.n_band >= 5 if col == "mid_mean" else cg.n >= 5).unstack("cgroup")
    print(f"\n{col} by corridor x cuisine group (cells with fewer than 5 places with data left blank):"); print(pv.round(2).to_string())
print("\nsaved: google_places_tests.csv, google_places_by_corridor.csv, google_places_by_group.csv, google_places_by_corridor_group.csv")
