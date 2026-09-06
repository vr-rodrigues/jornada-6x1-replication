"""Conditional CES bridge using payrolls aggregated across heterogeneous firms.
Default: fix sigma=1.326, calibrate omega. This is not joint identification.
"""
from pathlib import Path
import sys,json,argparse
from scipy.optimize import brentq
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.model.simulation import load_targets,run_simulation
from src.calibration.wage_bridge import aggregate_bridge,calibrate_omega

def wage_premium_at(sigma_sub,omega,eta_I,measure='hourly',efficiency_mode='bilateral'):
    t=load_targets(str(ROOT/'data_final')); t['ETA_I']['value']=eta_I
    th=[t[f'THETA_{h}']['value'] for h in (36,40,44)]
    sim=run_simulation(t,sigma_sub=sigma_sub,omega=omega,efficiency_mode=efficiency_mode)
    return aggregate_bridge(sim,th)[measure+'_ratio']

def sigma_for_R(R_target,omega,eta_I,sig_lo=.3,sig_hi=5.,tol=1e-9,maxit=100,measure='hourly'):
    return brentq(lambda s:wage_premium_at(s,omega,eta_I,measure)-R_target,sig_lo,sig_hi,xtol=tol,maxiter=maxit)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ratio',type=float,default=1.4,help='Assumed target, not a verified MNR estimate')
    p.add_argument('--output',type=Path,default=ROOT/'output'/'corrected'/'wage_bridge.json')
    a=p.parse_args(); t=load_targets(str(ROOT/'data_final'))
    out={'ratio_source':'Legacy 1.4 hypothesis, not direct identification from MNR wage-posting model',
         'calibrations':[calibrate_omega(t,a.ratio,measure=m,efficiency_mode=e) for e in ('bilateral','flat_below') for m in ('hourly','weekly')]}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2),encoding='utf-8');print(a.output)

if __name__=='__main__': main()
