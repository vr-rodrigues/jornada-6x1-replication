"""Figures and tables consume only the current run's computed records."""
from pathlib import Path
import csv,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

LABELS={
 'original':'Original',
 'code_corrected_frozen_inputs':'Código corrigido / entradas congeladas',
 'bridge_recalibrated_assumed_hourly':'Ponte horária recalibrada / R hipotético',
 'rais_verified_only':'RAIS 2022 verificada / demais entradas congeladas',
 'reprocessed_data':'PNAD 2024T4 reprocessada / ponte horária',
 'reprocessed_data_fixed_omega':'PNAD 2024T4 / omega congelado',
 'single_group_frozen_control':'Controle de um grupo',
 'reprocessed_topcoded44':'PNAD / baseline limitado a 44h',
}
COLORS=['#8e9aaf','#193b5b','#bc6c25','#7b5a96','#137c66','#4f92b7']


def build_assets(rows,output_dir,sector_rows=None):
    out=Path(output_dir);figdir=out/'figures';tabdir=out/'tables'
    figdir.mkdir(parents=True,exist_ok=True);tabdir.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'savefig.facecolor':'white'})
    versions=[v for v in ('original','code_corrected_frozen_inputs','reprocessed_topcoded44','reprocessed_data')
              if any(r['version']==v for r in rows)]
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for mi,mode in enumerate(('bilateral','flat_below')):
        for hi,h in enumerate((40,36)):
            ax=axes[mi,hi]
            data=[next((r for r in rows if r['version']==v and r['hours_cap']==h and r['efficiency_mode']==mode),None) for v in versions]
            valid=[(v,r) for v,r in zip(versions,data) if r is not None]
            ax.barh(range(len(valid)),[r['A_req_pct'] for _,r in valid],color=COLORS[:len(valid)])
            ax.set_yticks(range(len(valid)),[LABELS.get(v,v) for v,_ in valid],fontsize=8)
            ax.invert_yaxis();ax.set_xlabel('A_req, % (composição reotimizada)')
            ax.set_title(f'{h}h · '+('Bilateral' if mode=='bilateral' else 'Fadiga apenas acima do pico'))
            for i,(_,r) in enumerate(valid):ax.text(r['A_req_pct']+.05,i,f"{r['A_req_pct']:.2f}",va='center',fontsize=9)
            ax.set_xlim(0,max(r['A_req_pct'] for _,r in valid)*1.15)
    fig.suptitle('Correções e mudanças de dados em etapas separadas',fontsize=16)
    for suffix in ('png','pdf'):fig.savefig(figdir/f'comparativo_areq.{suffix}',dpi=170)
    plt.close(fig)
    selected=[r for r in rows if r['version'] in ('code_corrected_frozen_inputs','reprocessed_data')]
    if selected:
        fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
        labels=[f"{'PNAD' if r['version']=='reprocessed_data' else 'Congeladas'}\n{r['hours_cap']}h / {'bilateral' if r['efficiency_mode']=='bilateral' else 'fadiga'}" for r in selected]
        x=np.arange(len(selected))
        for key,color,label in [('hours_pct','#193b5b','Horas físicas'),('efficiency_pct','#137c66','Eficiência'),('reallocation_pct','#bc6c25','Realocação')]:
            vals=np.array([r.get(key,0) or 0 for r in selected]);offset={'hours_pct':-.23,'efficiency_pct':0,'reallocation_pct':.23}[key]
            axes[0].bar(x+offset,vals,.23,label=label,color=color)
        axes[0].scatter(x,[r['dY_pct'] for r in selected],color='black',marker='_',s=150,label='Variação total')
        axes[0].set_ylabel('Pontos percentuais de Y0');axes[0].set_title('Horas → eficiência → realocação')
        axes[0].legend(fontsize=8);axes[0].axhline(0,color='#aeb5bc',lw=.7)
        axes[1].bar(x-.17,[r['dGHH_pct'] for r in selected],.34,label='Variação do composto GHH',color='#193b5b')
        axes[1].bar(x+.17,[r['CE_pct'] for r in selected],.34,label='Equivalente de consumo',color='#137c66')
        axes[1].set_ylabel('%');axes[1].set_title('GHH e CE têm denominadores distintos')
        axes[1].axhline(0,color='#aeb5bc',lw=.7);axes[1].legend(fontsize=8)
        for ax in axes:ax.set_xticks(x,labels,fontsize=7)
        for suffix in ('png','pdf'):fig.savefig(figdir/f'decomposicao_bem_estar.{suffix}',dpi=170)
        plt.close(fig)
    # A directly consumable LaTeX table, with all numbers from this run.
    lines=[r'\begin{tabular}{llrrrrrr}',r'\hline',
           r'Versão e eficiência & Teto & $\Delta Y$ & $A_{req}$ & Inf. & GHH & CE & $A_{fixo}$ \\',r'\hline']
    for r in rows:
        label=LABELS.get(r['version'],r['version']).replace('_',r'\_')
        vals=[r.get(k) for k in ('dY_pct','A_req_pct','informality_pct','dGHH_pct','CE_pct','A_req_frozen_pct')]
        vals=['--' if v is None else f'{v:.3f}' for v in vals]
        lines.append(label+(' / B' if r['efficiency_mode']=='bilateral' else ' / F')+f" & {r['hours_cap']} & "+' & '.join(vals)+r' \\')
    lines += [r'\hline',r'\end{tabular}']
    (tabdir/'resultados_corrigidos.tex').write_text('\n'.join(lines),encoding='utf-8')
    if sector_rows:
        (tabdir/'sectoral_current_run.json').write_text(json.dumps(sector_rows,indent=2,ensure_ascii=False),encoding='utf-8')
    return [str(p.relative_to(out)) for p in figdir.iterdir()]+['tables/resultados_corrigidos.tex']
