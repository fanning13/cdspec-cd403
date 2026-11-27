"""'Three ways to arrive': compare the three main food streets of CD 403 (Roosevelt Avenue, 37th Avenue, Northern Boulevard) and show how Google ratings change with distance from Roosevelt Avenue (the 7 train viaduct).
Sample: DOHMH restaurants matched to a Google place (google_places.csv, match_ok), ONE ROW PER GOOGLE PLACE (two DOHMH permits at one place count once).
Street of a restaurant = the 'corridor' field of restaurants_cd403_walktime.geojson (street of the recorded address).
Distance from the viaduct = straight-line metres from the restaurant to the nearest street segment named Roosevelt Ave.
Tests: Kruskal-Wallis for the three streets; permutation tests (10,000 shuffles) for differences of means; Fisher's exact test for shares.
Outputs (all in <out_dir>): three_streets_table.csv, viaduct_bands.csv, three_streets_tests.txt, chart_three_streets.png, chart_viaduct_rating.png
The two CSV files hold only aggregates.
Usage: python -I 11_three_streets.py <out_dir>
"""
import sys, pathlib, warnings
import numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import kruskal, fisher_exact
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
warnings.filterwarnings("ignore")
OUT = pathlib.Path(sys.argv[1]); rng = np.random.default_rng(11)
STREETS = ["Roosevelt Avenue", "37th Avenue", "Northern Boulevard"]
def group(c):
    c = str(c).lower()
    if any(k in c for k in ["latin", "mexican", "spanish", "tex-mex", "peruvian", "caribbean", "colombian", "salvadoran", "ecuadorian", "brazilian", "cuban", "chilean", "argentin"]): return "Latin American"
    return "Other"
def perm(a, b, n=10000):
    """difference of means a - b and its two-sided permutation p value"""
    a, b = np.asarray(a, float), np.asarray(b, float); a, b = a[~np.isnan(a)], b[~np.isnan(b)]; obs = a.mean() - b.mean(); z = np.concatenate([a, b]); c = 0
    for _ in range(n):
        rng.shuffle(z); c += abs(z[:len(a)].mean() - z[len(a):].mean()) >= abs(obs)
    return obs, c / n, len(a), len(b)

r = gpd.read_file(OUT / "restaurants_cd403_walktime.geojson").to_crs("EPSG:26918"); r["camis"] = r.camis.astype(str)
g = pd.read_csv(OUT / "google_places.csv", dtype={"camis": str}, encoding="utf-8-sig"); g = g[g.match_ok == True]
m = r.merge(g[["camis", "place_id", "rating", "user_rating_count", "price_min", "price_max", "primary_type"]], on="camis").drop_duplicates("place_id").copy()
m["price"] = (m.price_min + m.price_max) / 2; m["latin"] = m.cuisine_description.map(group) == "Latin American"
m["night"] = m.primary_type.fillna("").str.contains("bar|night_club|pub")
seg = gpd.read_file(OUT / "segments_v2.geojson").to_crs("EPSG:26918")
roos = seg[seg["name"].fillna("").str.upper().str.contains("ROOSEVELT")].geometry.union_all()
m["d"] = m.geometry.distance(roos)
L = []; say = lambda s: (print(s), L.append(s))
say(f"DOHMH records {len(r)} | matched Google places, one row per place: {len(m)} | with a price range: {int(m.price.notna().sum())}")

# ---- 1. three streets -------------------------------------------------------------------------------------------------------------------
t = m[m.corridor.isin(STREETS)]
tab = t.groupby("corridor").agg(places=("camis", "size"), walk_min_median=("walk_min", "median"), latin_pct=("latin", lambda s: 100 * s.mean()), rating_mean=("rating", "mean"),
    reviews_median=("user_rating_count", "median"), price_places=("price", "count"), price_mid_median=("price", "median"), price30_pct=("price", lambda s: 100 * (s.dropna() >= 30).mean()),
    night_pct=("night", lambda s: 100 * s.mean())).loc[STREETS]
tab["restaurants_dohmh"] = r.corridor.value_counts().reindex(STREETS).values
tab.round(2).to_csv(OUT / "three_streets_table.csv"); say(tab.round(2).to_string())
R, A, N = [t[t.corridor == c] for c in STREETS]
say("rating, Kruskal-Wallis across the three streets: p = %.4f" % kruskal(R.rating.dropna(), A.rating.dropna(), N.rating.dropna()).pvalue)
for name, (x, y) in {"Roosevelt - 37th": (R, A), "Roosevelt - Northern": (R, N), "37th - Northern": (A, N)}.items():
    say("  rating %-21s %+.2f (p = %.4f, n = %d, %d)" % ((name,) + perm(x.rating, y.rating)))
    say("  price  %-21s %+.2f (p = %.4f, n = %d, %d)" % ((name,) + perm(x.price, y.price)))
say("reviews (log), Northern - other two: %+.2f (p = %.4f, n = %d, %d)  -> not used as a finding if p > 0.05" % perm(np.log(N.user_rating_count), np.log(pd.concat([R, A]).user_rating_count)))
say("bars and night clubs: Roosevelt %d/%d, 37th %d/%d, Northern %d/%d | Fisher Roosevelt vs 37th p = %.4f" % (R.night.sum(), len(R), A.night.sum(), len(A), N.night.sum(), len(N),
    fisher_exact([[R.night.sum(), len(R) - R.night.sum()], [A.night.sum(), len(A) - A.night.sum()]])[1]))
top = m.sort_values("user_rating_count", ascending=False).head(5)
say("five most-reviewed places, by street: " + ", ".join(f"{c} ({int(n):,} reviews, {w:.1f} min from subway)" for c, n, w in zip(top.corridor, top.user_rating_count, top.walk_min)))

# ---- 2. distance from the viaduct -------------------------------------------------------------------------------------------------------
BANDS = ["On Roosevelt Ave", "30 to 150 m", "150 to 300 m", "300 to 600 m", "Over 600 m"]
m["band"] = pd.cut(m.d, [-1, 30, 150, 300, 600, 1e6], labels=BANDS)
bands = m.groupby("band").agg(places=("camis", "size"), rating_mean=("rating", "mean"), price_places=("price", "count"), price_mid_median=("price", "median"), latin_pct=("latin", lambda s: 100 * s.mean()))
bands.round(2).to_csv(OUT / "viaduct_bands.csv"); say("\n" + bands.round(2).to_string())
on, near = m[m.band == BANDS[0]], m[m.band.isin(BANDS[1:3])]
say("on Roosevelt vs 30 to 300 m: rating %+.2f (p = %.4f, n = %d, %d)" % perm(on.rating, near.rating)); say("on Roosevelt vs 30 to 300 m: price  %+.2f (p = %.4f, n = %d, %d)" % perm(on.price, near.price))
la = m[m.latin]
say("Latin American places only, on Roosevelt vs elsewhere: rating %+.2f (p = %.4f, n = %d, %d)" % perm(la[la.band == BANDS[0]].rating, la[la.band != BANDS[0]].rating))
say("Latin American places only, on Roosevelt vs elsewhere: price  %+.2f (p = %.4f, n = %d, %d)" % perm(la[la.band == BANDS[0]].price, la[la.band != BANDS[0]].price))
(OUT / "three_streets_tests.txt").write_text("\n".join(L), encoding="utf-8")

# ---- charts (static PNG for the story) --------------------------------------------------------------------------------------------------
SURF, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
COL = {"Roosevelt Avenue": "#2a78d6", "37th Avenue": "#eb6834", "Northern Boulevard": "#1baf7a"}     # categorical slots 1-3 (validated for all pairs)
plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 11, "axes.edgecolor": AXIS, "axes.linewidth": 1, "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": MUTED,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF})
def clean(ax):
    for s in ["top", "right", "left"]: ax.spines[s].set_visible(False)
    ax.tick_params(length=0); ax.yaxis.grid(True, color=GRID, linewidth=1); ax.set_axisbelow(True)
SRC = "Sources: Google Places API (ratings, price ranges, place types; fetched Nov 2026), NYC DOHMH restaurant records. One point per Google place."

# chart A: rating by distance from Roosevelt Avenue (single series: line + dots, value axis does not start at zero because the marks are dots)
fig, ax = plt.subplots(figsize=(8.4, 4.9), dpi=200); clean(ax)
x = np.arange(len(BANDS)); y = bands.rating_mean.values
ax.plot(x, y, color=COL["Roosevelt Avenue"], linewidth=2, solid_capstyle="round", solid_joinstyle="round", zorder=2)
ax.scatter(x, y, s=95, color=COL["Roosevelt Avenue"], edgecolor=SURF, linewidth=2, zorder=3)
for i in [0, int(np.argmax(y))]: ax.annotate(f"{y[i]:.2f}", (x[i], y[i]), xytext=(0, 12), textcoords="offset points", ha="center", fontsize=12, fontweight="bold", color=INK)
ax.set_xticks(x); ax.set_xticklabels([f"{b}\n{int(n)} places" for b, n in zip(BANDS, bands.places)]); ax.set_ylim(3.9, 4.35); ax.set_yticks([3.9, 4.0, 4.1, 4.2, 4.3]); ax.set_xlim(-0.5, len(BANDS) - 0.5)
ax.set_xlabel("Distance from Roosevelt Avenue, where the 7 train runs overhead", labelpad=10)
fig.suptitle("One block from the train, the ratings go up", x=0.06, y=0.975, ha="left", fontsize=15, fontweight="bold")
fig.text(0.06, 0.885, "Average Google rating (out of 5) of restaurants in Community District 3, by distance from Roosevelt Avenue", fontsize=10.5, color=INK2)
fig.text(0.06, 0.02, SRC, fontsize=8, color=MUTED)
fig.subplots_adjust(left=0.07, right=0.97, top=0.82, bottom=0.25); fig.savefig(OUT / "chart_viaduct_rating.png"); plt.close(fig)

# chart B: the three streets, three small panels (each panel has its own measure and its own axis)
fig, axes = plt.subplots(1, 3, figsize=(10.4, 4.9), dpi=200)
short = {"Roosevelt Avenue": "Roosevelt\nAvenue", "37th Avenue": "37th\nAvenue", "Northern Boulevard": "Northern\nBoulevard"}
panels = [("rating_mean", "Average Google rating", "{:.2f}", (3.8, 4.4), "dot"), ("price30_pct", "Places with a price range of $30 or more", "{:.0f}%", (0, 30), "bar"), ("night_pct", "Bars and night clubs", "{:.0f}%", (0, 30), "bar")]
for ax, (col, title, fmt, lim, kind) in zip(axes, panels):
    clean(ax); v = tab[col].values; xs = np.arange(3)
    if kind == "bar":
        ax.bar(xs, v, width=0.34, color=[COL[s] for s in STREETS], zorder=2); ax.spines["bottom"].set_color(AXIS); ax.set_yticks([0, 10, 20, 30]); ax.set_yticklabels(["0", "10%", "20%", "30%"])
    else:
        ax.scatter(xs, v, s=150, color=[COL[s] for s in STREETS], edgecolor=SURF, linewidth=2, zorder=3); ax.set_yticks([3.8, 4.0, 4.2, 4.4])
    for xi, vi in zip(xs, v): ax.annotate(fmt.format(vi), (xi, vi), xytext=(0, 9 if kind == "bar" else 13), textcoords="offset points", ha="center", fontsize=11.5, fontweight="bold", color=INK)
    ax.set_ylim(*lim); ax.set_xlim(-0.6, 2.6); ax.set_xticks(xs); ax.set_xticklabels([short[s] for s in STREETS]); ax.set_title(title, loc="left", fontsize=10.5, color=INK2, pad=12)
fig.suptitle("Three streets, three kinds of table", x=0.05, y=0.975, ha="left", fontsize=15, fontweight="bold")
fig.text(0.05, 0.885, "Median walk to the subway: Roosevelt Avenue 1.9 min, 37th Avenue 4.6 min, Northern Boulevard 12.3 min", fontsize=10.5, color=INK2)
fig.text(0.05, 0.02, SRC, fontsize=8, color=MUTED)
fig.subplots_adjust(left=0.06, right=0.98, top=0.76, bottom=0.2, wspace=0.28); fig.savefig(OUT / "chart_three_streets.png"); plt.close(fig)
print("saved charts and tables in", OUT)
