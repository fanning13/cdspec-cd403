"""Intro slide 1 background: CD 403 locator map, v2.

Layout rules for a StoryMaps sidecar (text panel sits on the left ~40%):
- every map element lives in the right 58% of the frame and inside a 7% top/bottom margin,
  so nothing is hidden by the panel or cropped on wide/short screens;
- neighborhoods are clipped to the CD boundary (no white gaps);
- each neighborhood gets one landmark that hints at its character.
Run from repo root: python part3_synthesis/scripts/08_locator_map_slide_v2.py
"""
import os
import matplotlib.patheffects as pe
import geopandas as gpd, matplotlib.pyplot as plt, matplotlib as mpl, numpy as np
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch
from shapely.geometry import Point

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
D = lambda *p: os.path.join(ROOT, 'data', *p)
for f in fm.findSystemFonts():
    if 'Inter' in f: fm.fontManager.addfont(f)
mpl.rcParams['font.family'] = 'Inter'

boro = gpd.read_file(D('boundaries', 'boroughs.geojson')).to_crs(2263)
nta = gpd.read_file(D('boundaries', 'nta_2020.geojson')).to_crs(2263)
cd = gpd.read_file(D('boundaries', 'community_districts.geojson'))
cd = cd[cd.boro_cd.astype(float).astype(int) == 403].to_crs(2263)
CDG = cd.geometry.iloc[0]
bg = gpd.read_file(D('census', 'cd403_blockgroups_2020.gpkg')).to_crs(2263)

names = {'QN0301': 'Jackson Heights', 'QN0302': 'East Elmhurst', 'QN0303': 'North Corona'}
n3 = nta[nta.nta2020.isin(names)].copy()
n3['geometry'] = n3.geometry.intersection(CDG)
cent = bg.copy(); cent['geometry'] = bg.representative_point()
popcol = 'pop' if 'pop' in bg.columns else [c for c in bg.columns if c.lower().startswith('pop')][0]
n3['pop'] = n3.nta2020.map(gpd.sjoin(cent, n3[['nta2020', 'geometry']]).groupby('nta2020')[popcol].sum())
lga = nta[nta.ntaname.str.contains('LaGuardia', case=False)]

WATER = '#dce7ee'; LAND = '#f3f1ec'; EDGE = '#d9d3c8'; INK = '#1f2328'; ACC = '#c8553d'
cols = {'QN0301': '#e9a77c', 'QN0302': '#8db7a6', 'QN0303': '#d6c36b'}
tags = {'QN0301': 'Garden apartments & Little India',
        'QN0302': 'Family homes beside LaGuardia',
        'QN0303': 'Latino hub, Louis Armstrong’s home'}

W, H = 16, 9
fig = plt.figure(figsize=(W, H), dpi=150, facecolor=WATER)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(WATER); ax.axis('off')

# Frame: CD sits in x 0.44-0.80 of the width, vertically centred with margin
c = CDG.bounds; cw = c[2] - c[0]; ch = c[3] - c[1]
wx = cw / 0.36; hy = wx * H / W
x0 = c[0] - 0.44 * wx; y0 = (c[1] + c[3]) / 2 - hy * 0.50
ax.set_xlim(x0, x0 + wx); ax.set_ylim(y0, y0 + hy)

nta.plot(ax=ax, color=LAND, edgecolor=EDGE, lw=0.6)
if len(lga):
    lga.plot(ax=ax, color='#ebe8e2', edgecolor='#d3cdc2', lw=0.6)
n3.plot(ax=ax, color=n3.nta2020.map(cols), edgecolor='white', lw=2.2)
cd.boundary.plot(ax=ax, color=INK, lw=2.6)

# Neighborhood labels: name / residents / one-line character tag
offs = {'QN0301': (900, -900), 'QN0302': (300, 500), 'QN0303': (-500, -700)}
fs = {'QN0301': 20, 'QN0302': 19, 'QN0303': 16}
for _, r in n3.iterrows():
    p = r.geometry.representative_point(); dx, dy = offs[r.nta2020]
    x, y = p.x + dx, p.y + dy
    ax.text(x, y + 420, names[r.nta2020], ha='center', fontsize=fs[r.nta2020], fontweight='bold', color=INK)
    ax.text(x, y - 330, f"{int(r['pop']):,} residents", ha='center', fontsize=12.5, color='#333')
    if r.nta2020 != 'QN0303':
        ax.text(x, y - 930, tags[r.nta2020], ha='center', fontsize=11, color='#3d3d3d', style='italic')
# North Corona is small: its tag sits outside, below the district edge
nc = n3[n3.nta2020 == 'QN0303'].geometry.iloc[0]
ax.text(nc.centroid.x + 600, nc.bounds[1] - 1150, tags['QN0303'], ha='center', fontsize=11, color='#3d3d3d', style='italic')

# Landmarks (lon, lat)
marks = [('Little India · 74th St', -73.8913, 40.7470, (-200, -700), 'center'),
         ('Louis Armstrong House', -73.8615, 40.7546, (2350, -120), 'left'),
         ('LaGuardia Airport', -73.8740, 40.7769, (0, 500), 'center')]
for lab, lon, lat, (dx, dy), ha in marks:
    pt = gpd.GeoSeries([Point(lon, lat)], crs=4326).to_crs(2263).iloc[0]
    if ha == 'left':
        ax.plot([pt.x, pt.x + dx - 120], [pt.y, pt.y + dy + 120], color=ACC, lw=1, zorder=4)
    ax.scatter(pt.x, pt.y, s=46, color=ACC, edgecolor='white', lw=1.4, zorder=5)
    ax.text(pt.x + dx, pt.y + dy, lab, ha=ha, fontsize=10.5, color=ACC, fontweight='semibold', zorder=5,
            path_effects=[pe.withStroke(linewidth=3, foreground='white')])
fb = gpd.GeoSeries([Point(-73.8470, 40.7640)], crs=4326).to_crs(2263).iloc[0]
ax.text(fb.x, fb.y, 'Flushing Bay', fontsize=12, color='#62808f', style='italic', ha='center')
ax.text((c[0] + c[2]) / 2, c[1] - 1500, 'Queens Community District 3 · CD 403', fontsize=13,
        color=INK, ha='center', fontweight='semibold')

# Soft fade on the left for the text panel
grad = np.ones((10, 256, 4)); grad[..., :3] = mpl.colors.to_rgb('#f6f5f2')
grad[..., 3] = np.clip(np.linspace(1.0, -0.2, 256), 0, 1)
fax = fig.add_axes([0, 0, 0.42, 1]); fax.imshow(grad, aspect='auto', extent=[0, 1, 0, 1]); fax.axis('off')

# NYC inset, top-right but inside the safe area
ia = fig.add_axes([0.83, 0.60, 0.135, 0.31]); ia.set_facecolor(WATER)
boro.plot(ax=ia, color=LAND, edgecolor='#a3a3a3', lw=0.5)
boro[boro.boroname == 'Queens'].plot(ax=ia, color='#ebe5d9', edgecolor='#7a7a7a', lw=0.6)
cd.plot(ax=ia, color=ACC, edgecolor='#7a2e1f', lw=0.5)
bx = boro.total_bounds; ia.set_xlim(bx[0] - 2000, bx[2] + 2000); ia.set_ylim(bx[1] - 2000, bx[3] + 2000)
ia.set_xticks([]); ia.set_yticks([]); ia.set_xlabel(''); ia.set_ylabel('')
for s in ia.spines.values(): s.set_edgecolor('#9a9a9a'); s.set_linewidth(1)
for nm, (dx, dy) in {'Manhattan': (-9000, 3000), 'Queens': (9000, -7000), 'Brooklyn': (0, 0),
                     'Bronx': (0, 0), 'Staten Island': (0, 0)}.items():
    p = boro[boro.boroname == nm].geometry.iloc[0].representative_point()
    ia.text(p.x + dx, p.y + dy, nm, fontsize=7.5, ha='center', color='#5e5e5e')
ia.text(0.5, 1.03, 'Where CD 403 sits in NYC', transform=ia.transAxes, ha='center', fontsize=9.5, color='#444')

# North arrow + scale bar (bottom right, inside margins)
ax.annotate('N', xy=(0.93, 0.25), xytext=(0.93, 0.165), xycoords='figure fraction', ha='center',
            fontsize=14, fontweight='bold', arrowprops=dict(arrowstyle='wedge,tail_width=0.6', color=INK))
L = 0.5 * 5280; xs = x0 + wx * 0.83; ys = y0 + hy * 0.10
ax.plot([xs, xs + L / 2], [ys, ys], color=INK, lw=5, solid_capstyle='butt')
ax.plot([xs + L / 2, xs + L], [ys, ys], color='white', lw=5, solid_capstyle='butt')
ax.plot([xs, xs + L], [ys, ys], color=INK, lw=0.6)
ax.text(xs, ys + hy * 0.02, '0', fontsize=9.5, ha='center'); ax.text(xs + L, ys + hy * 0.02, '0.5 mi', fontsize=9.5, ha='center')
fig.text(0.965, 0.06, 'Sources: NYC DCP boundaries (NYC Open Data); U.S. Census Bureau 2020.',
         ha='right', fontsize=8, color='#777')

out = os.path.join(REPO, 'images', 'part3_synthesis', 'CD403_locator_map_slide_v2.png')
fig.savefig(out, dpi=150, facecolor=WATER)
print(out)
