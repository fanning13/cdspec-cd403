"""Small horizontal bar charts (one per food corridor) for the StoryMap sidecar panels."""
import json, os
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
summary = json.load(open(os.path.join(ROOT, "data/restaurants/main_corridors_summary.json")))
out_dir = os.path.join(REPO, "images/part3_synthesis")

ORDER = ["Latin American", "American, pizza, bakery & café", "East & Southeast Asian",
         "South Asian", "Other or not listed"]
COLORS = {"Latin American": "#d9622b", "American, pizza, bakery & café": "#c9a227",
          "East & Southeast Asian": "#2f7f8f", "South Asian": "#7b5ea7",
          "Other or not listed": "#9a9a9a"}
SLUG = {"Roosevelt Avenue": "roosevelt", "37th Avenue": "37th", "Northern Boulevard": "northern"}

for street, counts in summary.items():
    vals = [counts.get(g, 0) for g in ORDER]
    total = sum(vals)
    fig, ax = plt.subplots(figsize=(5.2, 2.6), dpi=200)
    y = range(len(ORDER))[::-1]
    ax.barh(list(y), vals, color=[COLORS[g] for g in ORDER], height=0.62)
    for yi, v in zip(y, vals):
        ax.text(v + 1, yi, f"{v}  ({v/total:.0%})", va="center", fontsize=8.5, color="#333")
    ax.set_yticks(list(y)); ax.set_yticklabels(ORDER, fontsize=9, color="#222")
    ax.set_xlim(0, 75); ax.set_xticks([])
    for s in ["top", "right", "bottom"]:
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color("#bbb")
    fig.text(0.01, 0.95, f"{street}: {total} restaurants by food group", fontsize=10.5,
             color="#111", fontweight="bold", va="top")
    fig.text(0.01, 0.01, "Source: NYC DOHMH restaurant inspections (cuisine as recorded), 2026",
             fontsize=6.5, color="#777")
    fig.tight_layout(rect=(0, 0.04, 1, 0.9))
    fig.savefig(os.path.join(out_dir, f"CD403_corridor_{SLUG[street]}_chart.png"), facecolor="white")
    plt.close(fig)
print("done")
