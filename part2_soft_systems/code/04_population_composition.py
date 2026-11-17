import sys,json
from pathlib import Path

import openpyxl,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
w=openpyxl.load_workbook('raw_data/census_2020.xlsx',read_only=True,data_only=True)
r=list(w.worksheets[1].values);data=[dict(zip(r[3],x)) for x in r[4:]]
d=next(x for x in data if x['GeoType']=='CD' and str(x['GeoID'])=='403')
keys=['Hsp','ANH','WNH','BNH','ONH','NH2pl'];labels=['Hispanic / Latino (any race)','Asian, non-Hispanic','White, non-Hispanic','Black, non-Hispanic','Other race, non-Hispanic','Two or more races, non-Hispanic'];colors=['#CE663E','#168D93','#C6A65D','#665595','#6F8573','#B77593']
values=[d[k+'_20']/d['Pop_20']*100 for k in keys]
fig,ax=plt.subplots(figsize=(12,7));fig.set_facecolor('#F6F2EA');ax.set_facecolor('#F6F2EA');fig.subplots_adjust(left=.32,right=.92,top=.73,bottom=.18)
ax.barh(range(6),values,color=colors,height=.6);ax.set_yticks(range(6),labels);ax.invert_yaxis();ax.set_xlim(0,75);ax.set_xticks([0,20,40,60],['0%','20%','40%','60%']);ax.spines[['top','right','left','bottom']].set_visible(False);ax.tick_params(length=0,pad=10)
for i,v in enumerate(values):ax.text(v+.8,i,f'{v:.1f}% | {d[keys[i]+"_20"]:,}',va='center')
fig.text(.06,.92,'PEOPLE / QUEENS COMMUNITY DISTRICT 3',fontsize=12,color='#B25635',weight='bold');fig.text(.06,.85,'Many communities, one district',fontsize=26,color='#203B3B',weight='bold');fig.text(.06,.79,'CD 403 | Jackson Heights, East Elmhurst and North Corona | 179,134 residents',fontsize=12)
fig.text(.06,.08,'Source: NYC DCP, 2020 Census, Community District 403 table. Percentages calculated from counts.',fontsize=10);fig.text(.06,.04,'Census groups describe residents; they do not identify restaurant ownership, workers or customers.',fontsize=10)
fig.savefig('analysis_outputs/CD403_Population_Composition.png',dpi=180);plt.close(fig)
Path('analysis_outputs/CD403_population_summary.json').write_text(json.dumps({'population2020':d['Pop_20'],'groups':[{ 'label':l,'count':d[k+'_20'],'percent':v} for k,l,v in zip(keys,labels,values)]},indent=2))
print(d['Pop_20'],values)
