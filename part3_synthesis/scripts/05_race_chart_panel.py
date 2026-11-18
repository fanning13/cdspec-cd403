# Compact race/ethnicity bar chart sized for a StoryMap sidecar text panel
import matplotlib.pyplot as plt, matplotlib as mpl
from matplotlib import font_manager as fm
for f in fm.findSystemFonts():
    if 'Inter' in f: fm.fontManager.addfont(f)
mpl.rcParams['font.family']='Inter'
# NYC DCP 2020 Census, CD 403 (179,134 residents)
data=[('Hispanic or Latino',63.3,'#cf6a3f'),('Asian',19.2,'#178f94'),('White',9.8,'#c8a65d'),('Black',4.9,'#665796'),('Two or more',1.5,'#b97394'),('Other',1.2,'#6f8576')]
fig,ax=plt.subplots(figsize=(6,4.6),dpi=200); fig.patch.set_facecolor('white')
y=range(len(data))[::-1]
for yy,(lab,v,c) in zip(y,data):
    ax.barh(yy,v,color=c,height=0.66)
    ax.text(v+1.2,yy,f'{v:.1f}%',va='center',fontsize=15,fontweight='semibold',color='#222')
ax.set_yticks(list(y)); ax.set_yticklabels([d[0] for d in data],fontsize=14,color='#222')
ax.set_xlim(0,80); ax.set_xticks([])
for s in ax.spines.values(): s.set_visible(False)
ax.tick_params(length=0)
fig.text(0.03,0.95,'Residents by race and ethnicity, 2020',fontsize=15,fontweight='semibold',color='#222')
fig.text(0.02,0.015,'Groups other than Hispanic or Latino are non-Hispanic. Source: NYC DCP, 2020 Census.',fontsize=9,color='#777')
plt.tight_layout(rect=(0,0.04,1,0.92))
fig.savefig('images/part3_synthesis/CD403_race_panel_chart.png',facecolor='white')
