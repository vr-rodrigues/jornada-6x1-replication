"""Classify accounting identities without behavioral-validation claims."""
from pathlib import Path
import json,sys,argparse
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.model.simulation import load_targets,run_simulation
from src.calibration.wage_bridge import aggregate_bridge

def audit(targets=None):
    t=targets or load_targets(str(ROOT/'data_final'))
    th=np.array([t[f'THETA_{h}']['value'] for h in (36,40,44)])
    sim=run_simulation(t,sigma_sub=1.326,omega=.622)
    return {'moments':[
        {'moment':'mean_formal_hours','value':float(th@[36,40,44]),'classification':'accounting_identity_given_hours_weights'},
        {'moment':'formal_share_above_36','value':float(th[1:].sum()),'classification':'accounting_identity_given_hours_weights'},
        {'moment':'informality_by_group','classification':'calibration_target_not_validation'},
        {'moment':'aggregate_informality','value':sim['baseline']['inf'],'classification':'accounting_implication_of_shares_and_group_targets'},
        {'moment':'formal_payroll_share','value':aggregate_bridge(sim,th)['formal_payroll_share'],'classification':'conditional_model_implication; no independent comparable observed target verified'}],
        'sectoral_dispersion':'Size groups are not sectors. No zero-dispersion validation is defined without a mapping.',
        'hours_comparison':'Habitual and contracted hours are distinct concepts, not behavioral out-of-sample validation.',
        'identification':'Sensitivity box is not an identified set: no likelihood, confidence region or complete moment restrictions imposed.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'output'/'corrected'/'audit_fit_moments.json')
    a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(audit(),indent=2),encoding='utf-8');print(a.output)

if __name__=='__main__': main()
