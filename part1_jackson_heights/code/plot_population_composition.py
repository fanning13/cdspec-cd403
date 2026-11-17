exec(open('work/01_clean_restaurant_data.py',encoding='utf-8').read().split('print(json.dumps(stats')[0])
import openpyxl,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,FancyBboxPatch,FancyArrowPatch
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import numpy as np
w=openpyxl.load_workbook('work/census.xlsx',read_only=True,data_only=True)
rr=list(w.worksheets[1].values); header=rr[3]; data=[dict(zip(header,r)) for r in rr[4:]]
nta=next(r for r in data if r['GeoID']=='QN0301')
keys=['Hsp','ANH','WNH','BNH','ONH','NH2pl']
labels=['Hispanic / Latino (any race)','Asian, non-Hispanic','White, non-Hispanic','Black, non-Hispanic','Other race, non-Hispanic','Two or more races, non-Hispanic']
colors=['#CE663E','#168D93','#C6A65D','#665595','#6F8573','#B77593']
bg='#F6F2EA';ink='#203B3B';muted='#637572'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'text.color':ink,'axes.labelcolor':ink,'xtick.color':muted,'ytick.color':ink,'figure.facecolor':bg,'axes.facecolor':bg})
def heading(fig,kicker,title,sub):
 fig.text(.06,.95,kicker,fontsize=11,color='#B25635',weight='bold');fig.text(.06,.895,title,fontsize=26,weight='bold');fig.text(.06,.85,sub,fontsize=12,color=muted)
def finish(fig,name,note):
 fig.text(.06,.035,note,fontsize=9,color=muted);fig.savefig(root/name,dpi=180,facecolor=bg);plt.close(fig)
fig=plt.figure(figsize=(12,7.5));heading(fig,'01 / PEOPLE','Many communities, one neighborhood','Jackson Heights NTA QN0301 | 2020 Census | 101,848 residents')
ax=fig.add_axes([.37,.23,.53,.54]); vals=[nta[k+'_20']/nta['Pop_20']*100 for k in keys]
ax.barh(range(6),vals,color=colors,height=.6);ax.set_yticks(range(6),labels,fontsize=11);ax.invert_yaxis();ax.set_xlim(0,62);ax.set_xticks([0,20,40,60],['0%','20%','40%','60%']);ax.spines[['top','right','left','bottom']].set_visible(False);ax.tick_params(length=0,pad=10)
for i,(v,k) in enumerate(zip(vals,keys)):ax.text(v+.7,i,f'{v:.1f}%  |  {nta[k+"_20"]:,}',va='center',fontsize=11)
fig.text(.06,.13,'2010 to 2020: Asian non-Hispanic share rose from 22.4% to 27.1%.',fontsize=13,weight='bold')
fig.text(.06,.09,'Census categories describe populations. They do not identify nationality, language, or food preferences.',fontsize=10)
finish(fig,'01_population.png','Source: NYC DCP, New York City Decennial Census Data (2010 and 2020), QN0301. Shares calculated from counts.')
