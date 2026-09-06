"""Audited experiments: numerical/accounting, bridge, then data changes."""
from pathlib import Path
from copy import deepcopy
import argparse, csv, json, itertools, sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.model.simulation import load_targets,run_simulation
from src.calibration.wage_bridge import aggregate_bridge,calibrate_omega


def json_default(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    if isinstance(x,Path):return str(x)
    raise TypeError(type(x).__name__)


def save_json(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,default=json_default,allow_nan=False),encoding='utf-8')


def save_csv(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:raise ValueError(f'Empty result: {path}')
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)


def result_row(sim,version,h,mode,**extra):
    b,r=sim['baseline'],sim['reform'];v=sim['results']
    d=sim.get('decomposition',v.get('decomposition',{}))
    return dict(version=version,efficiency_mode=mode,hours_cap=h,
                sigma_sub=sim['sigma_sub'],omega=sim['omega'],kappa=sim['kappa'],
                Y0=b['Y'],Y1=r['Y'],C0=b['C'],C1=r['C'],
                dY_pct=v['dY_pct'],A_req_pct=v['A_req_pct'],
                A_req_frozen_pct=v['A_req_frozen_pct'],
                baseline_informality_pct=100*b['inf'],informality_pct=100*r['inf'],
                dInf_pp=v['dInf_pp'],dGHH_pct=v['dGHH_pct'],CE_pct=v['CE_pct'],
                hours_pct=d.get('hours_pct'),efficiency_pct=d.get('efficiency_pct'),
                reallocation_pct=d.get('reallocation_pct'),decomposition_total_pct=d.get('total_pct'),
                **extra)


def run_version(targets,version,output_dir,*,omega=.622,group_specs=None,theta=None,
                hours_bins=None,share_basis='formal',bridge_target=None,
                bridge_measure='hourly',modes=('bilateral','flat_below'),note='',caps=(40,36),resource_costs=False):
    out=Path(output_dir);rows=[];details={};bridges=[]
    th=theta if theta is not None else [targets[f'THETA_{h}']['value'] for h in (36,40,44)]
    for mode in modes:
        om=omega
        if bridge_target is not None:
            bridge=calibrate_omega(targets,bridge_target,measure=bridge_measure,
                                   efficiency_mode=mode,theta=th,hours_bins=hours_bins,
                                   group_specs=group_specs,share_basis=share_basis)
            om=bridge['omega'];bridges.append(dict(efficiency_mode=mode,**bridge))
        for h in caps:
            t=deepcopy(targets);t['H1']['value']=h
            sim=run_simulation(t,sigma_sub=1.326,omega=om,group_specs=group_specs,
                               theta=th,efficiency_mode=mode,hours_bins=hours_bins,share_basis=share_basis,
                               resource_costs=resource_costs)
            bridge_check=aggregate_bridge(sim,th,hours_bins)
            rows.append(result_row(sim,version,h,mode,input_note=note,
                        implied_hourly_ratio=bridge_check['hourly_ratio'],
                        implied_weekly_ratio=bridge_check['weekly_ratio']))
            details[f'{mode}_{h}']=sim
    save_csv(out/'RESULTS.csv',rows);save_json(out/'RESULTS_FULL.json',details)
    save_json(out/'INPUTS.json',dict(targets=targets,theta=th,hours_bins=hours_bins,
                                  group_specs=group_specs,share_basis=share_basis,note=note,resource_costs=resource_costs))
    if bridges:save_json(out/'BRIDGE.json',bridges)
    return rows,details,bridges


def run_sensitivities(targets,output_dir):
    """Interior-inclusive parameter experiments, not an identified region."""
    rows=[]
    for mode,h,sigma,omega,eta in itertools.product(
            ('bilateral','flat_below'),(40,36),(0.6,1.,1.116,1.326,1.469,2.),(.58,.622,.66),(.33,.40,.50)):
        t=deepcopy(targets);t['H1']['value']=h;t['ETA_I']['value']=eta
        sim=run_simulation(t,sigma_sub=sigma,omega=omega,efficiency_mode=mode)
        bridge=aggregate_bridge(sim,[t[f'THETA_{hh}']['value'] for hh in (36,40,44)])
        rows.append(result_row(sim,'sensitivity',h,mode,dimension='CES_grid',eta_I=eta,
                    E_Q=t['E_Q']['value'],h_star=t['H_STAR']['value'],
                    hourly_ratio=bridge['hourly_ratio'],
                    passes_assumed_R_interval=1.15<=bridge['hourly_ratio']<=1.55,
                    restrictions_note='R interval is a hypothesis; other empirical restrictions not imposed'))
    theta0=np.array([targets[f'THETA_{h}']['value'] for h in (36,40,44)])
    for mode,h in itertools.product(('bilateral','flat_below'),(40,36)):
        experiments=[]
        for eq in (0.4,0.5,0.6,0.8,1.0):experiments.append(('efficiency',{'E_Q':eq},theta0))
        for peak in (38.,39.,40.,41.,42.):experiments.append(('peak',{'H_STAR':peak},theta0))
        for delta in (-.05,-.025,0.,.025,.05):
            experiments.append(('hours_distribution',{},theta0+np.array([delta,0,-delta])))
        for eta in (.25,.33,.4,.5,.6):experiments.append(('informal_efficiency',{'ETA_I':eta},theta0))
        for dimension,changes,th in experiments:
            t=deepcopy(targets);t['H1']['value']=h
            for key,value in changes.items():t[key]['value']=value
            sim=run_simulation(t,sigma_sub=1.326,omega=.622,theta=th,efficiency_mode=mode)
            rows.append(result_row(sim,'sensitivity',h,mode,dimension=dimension,
                        E_Q=t['E_Q']['value'],h_star=t['H_STAR']['value'],eta_I=t['ETA_I']['value'],
                        theta_36=th[0],theta_40=th[1],theta_44=th[2]))
    save_csv(Path(output_dir)/'SENSITIVITY.csv',rows)
    save_json(Path(output_dir)/'SENSITIVITY_DESIGN.json',{
        'label':'conditional sensitivity grid, not identified set','points':len(rows),
        'fixed':'Each point recalibrates tau/pi to the same conditional group targets. Capital and total employment fixed.',
        'interior':'Includes interior sigma, omega, eta, peak, elasticity and hours weights.',
        'wage_constraint':'CES grid records whether the hourly ratio is in an assumed 1.15-1.55 interval; the whole box need not pass.',
        'external_evidence':'E_Q and peak are transport assumptions, not Brazilian estimates from Pencavel.'})
    return rows


def run_national_cli(mode):
    p=argparse.ArgumentParser()
    p.add_argument('--data-dir',type=Path,default=ROOT/'data_final')
    p.add_argument('--output-dir',type=Path,default=ROOT/'output'/'corrected'/mode)
    a=p.parse_args()
    return run_version(load_targets(str(a.data_dir)),'code_corrected_frozen_inputs',a.output_dir,modes=(mode,))


def run_empirical_sensitivity(targets,specs,theta,bins,ratio_target,output_dir):
    """Recalibrate the remuneration bridge at each empirical sensitivity point."""
    rows=[]
    for mode,h in itertools.product(('bilateral','flat_below'),(40,36)):
        designs=[('efficiency',{'E_Q':v},1.326) for v in (.4,.6,.8,1.)]
        designs += [('peak',{'H_STAR':v},1.326) for v in (38.,39.,40.,41.)]
        designs += [('eta',{'ETA_I':v},1.326) for v in (.33,.40,.50)]
        designs += [('sigma',{},v) for v in (.6,1.,1.326,1.5,2.)]
        for dimension,changes,sigma in designs:
            t=deepcopy(targets);t['H1']['value']=h
            for k,v in changes.items():t[k]['value']=v
            bridge=calibrate_omega(t,ratio_target,sigma_sub=sigma,efficiency_mode=mode,
                                   theta=theta,hours_bins=bins,group_specs=specs)
            sim=run_simulation(t,sigma_sub=sigma,omega=bridge['omega'],theta=theta,hours_bins=bins,
                               group_specs=specs,efficiency_mode=mode)
            rows.append(result_row(sim,'empirical_sensitivity',h,mode,dimension=dimension,
                E_Q=t['E_Q']['value'],h_star=t['H_STAR']['value'],eta_I=t['ETA_I']['value'],
                bridge_target=ratio_target,bridge_residual=bridge['residual'],
                interpretation='Conditional on hourly remuneration mapping; not an identified set'))
    save_csv(Path(output_dir)/'EMPIRICAL_SENSITIVITY.csv',rows)
    return rows
