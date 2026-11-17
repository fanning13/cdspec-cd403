






import sys, pathlib, math, json
import pandas as pd, geopandas as gpd, networkx as nx
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from shapely.geometry import MultiLineString, LineString
from shapely.strtree import STRtree

OUT = pathlib.Path("analysis_outputs")
plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "svg.fonttype": "none"})

SURF, INK, INK2, MUTED, HAIR = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
                                                                                                  
BINS = ["within 5 min", "5-10 min", "beyond 10 min"]
FILL = {"within 5 min": "#104281", "5-10 min": "#2a78d6", "beyond 10 min": "#86b6ef"}
LABEL_INK = {"within 5 min": "#ffffff", "5-10 min": "#ffffff", "beyond 10 min": INK}
LEGEND = {"within 5 min": "Within 5 minutes (up to 400 m)", "5-10 min": "5 to 10 minutes (400-800 m)", "beyond 10 min": "Beyond 10 minutes"}
SOURCE = ("Walking distance along NYC Street Centerline from each restaurant to the nearest entry-allowed subway entrance, at 80 m per minute. "
          "Restaurants: NYC DOHMH inspection records, one per establishment, community board 403, snapshot 30 Oct 2026. Entrances: MTA. Original analysis.")

def wrap(text, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width: lines.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    return "\n".join(lines + [cur])

def segmented_rows(rows, title, subtitle, fname, group_break=None):

    W_IN = 10; row_h = 0.6; top = 1.6; bottom = 0.75
    H_IN = top + bottom + row_h * len(rows) + (0.25 if group_break else 0)
    fig = plt.figure(figsize=(W_IN, H_IN), dpi=200, facecolor=SURF)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W_IN); ax.set_ylim(0, H_IN); ax.axis("off")
    px = W_IN / (W_IN * 200)                       
                 
    ax.text(0.5, H_IN - 0.42, title, fontsize=14.5, fontweight="semibold", color=INK, va="center", ha="left")
    ax.text(0.5, H_IN - 0.78, subtitle, fontsize=9.5, color=INK2, va="center", ha="left")
                                       
    y = H_IN - 1.15
    for b, x in zip(BINS, (0.5, 3.1, 5.55)):
        ax.add_patch(FancyBboxPatch((x, y - 0.07), 0.14, 0.14, boxstyle="round,pad=0,rounding_size=0.02", fc=FILL[b], ec="none"))
        ax.text(x + 0.21, y, LEGEND[b], fontsize=8.8, color=INK2, va="center", ha="left")
          
    bar_x0, bar_x1 = 3.05, W_IN - 0.5; bar_w = bar_x1 - bar_x0; bar_h = 28 * px; gap = 2 * px
    y = H_IN - top - 0.2
    for i, (label, n, counts) in enumerate(rows):
        if group_break is not None and i == group_break:
            y -= 0.25; ax.plot([0.5, bar_x1], [y + row_h * 0.5 + 0.1] * 2, color=HAIR, lw=0.8, solid_capstyle="butt")
        bold = "semibold" if (group_break is not None and i >= group_break) else "normal"
        ax.text(bar_x0 - 0.18, y + 0.055, label, fontsize=10, color=INK, va="center", ha="right", fontweight=bold)
        ax.text(bar_x0 - 0.18, y - 0.14, f"n = {n}", fontsize=8, color=MUTED, va="center", ha="right")
        x = bar_x0
        for b in BINS:
            share = counts.get(b, 0) / n
            w = share * bar_w
            if w <= 0: continue
            w_draw = max(w - gap, 0)
            ax.add_patch(FancyBboxPatch((x, y - bar_h / 2), w_draw, bar_h, boxstyle="round,pad=0,rounding_size=0.02", fc=FILL[b], ec="none"))
            txt = f"{share * 100:.0f}%"
            if w_draw >= 0.42:                           
                ax.text(x + 0.09, y, txt, fontsize=8.6, color=LABEL_INK[b], va="center", ha="left", fontweight="semibold")
            x += w
        y -= row_h
    ax.text(0.5, 0.52, wrap(SOURCE, 175), fontsize=7.2, color=MUTED, va="center", ha="left", linespacing=1.4)
    fig.savefig(OUT / fname, dpi=200, facecolor=SURF); fig.savefig(OUT / fname.replace(".png", ".svg"), facecolor=SURF); plt.close(fig)
    print("wrote", fname)


cor = pd.read_csv(OUT / "summary_by_corridor.csv", index_col=0)
def rows_from(t, order):
    return [(name, int(t.loc[name, "total"]), {b: int(t.loc[name, b]) for b in BINS}) for name in order]

segmented_rows(rows_from(cor, ["Roosevelt Avenue", "37th Avenue", "Junction Boulevard", "Northern Boulevard", "Astoria Boulevard", "Other streets", "All CD 403"]),
               "Two food corridors sit under the train, two sit well beyond it",
               "Share of restaurants by walking time to the nearest subway entrance, by corridor (street in the recorded address), Community District 3.",
               "chart2_by_corridor.png", group_break=6)

