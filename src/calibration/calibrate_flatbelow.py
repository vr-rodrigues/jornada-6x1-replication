"""One-sided fatigue adapter; all optimization lives in src.model."""
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.model.efficiency import eff, calibrate_kappa, HOURS_BINS
from src.model.firm_problem import solve_NF
from src.model.calibration import calibrate_wedge, calibrate_pi_m
from src.model.simulation import load_targets

_t=load_targets(str(ROOT/'data_final'))
THETA=np.array([_t[f'THETA_{h}']['value'] for h in (36,40,44)])
ALPHA,ETA_I,E_Q,H_STAR,HI,H0,H1,NTOT=[_t[k]['value'] for k in ('ALPHA','ETA_I','E_Q','H_STAR','HI','H0','H1','N_TOTAL')]
SIGMA=1.326
OMEGA=0.622  # frozen technology assumption, never an employment-share estimator
INF_S,INF_L=[_t[k]['value'] for k in ('INF_SMALL','INF_LARGE')]
_fs=np.array([_t[k]['value'] for k in ('SHARE_SMALL','SHARE_LARGE')])
_ns=_fs/(1-np.array([INF_S,INF_L]))
SHARE_S,SHARE_L=_ns/_ns.sum()
KSHARE_S,KSHARE_L=0.35,0.65
GAMMA_F_S,GAMMA_F_L=[_t[k]['value'] for k in ('GAMMA_F_SMALL','GAMMA_F_LARGE')]


def eff_flat_below(h,kappa,h_star=H_STAR):
    return eff(h,kappa,h_star,efficiency_mode='flat_below')

def kappa_from_eq(h_ref,h_star,e_q):
    return calibrate_kappa(h_ref,h_star,e_q,efficiency_mode='flat_below')

def solve_NF_flat(N_total,hF,hI,A,K,formal_wedge,pi_m,gamma_F,NF_prev,kappa,theta,grid=4001):
    return solve_NF(N_total,hF,hI,A,K,ALPHA,OMEGA,SIGMA,ETA_I,kappa,H_STAR,
                    formal_wedge,pi_m,gamma_F,NF_prev,theta,grid,
                    efficiency_mode='flat_below')

def calib_wedge(target_inf,N,K,pim,kappa,gamma_F,NF_init):
    return calibrate_wedge(target_inf,N,H0,HI,1.,K,ALPHA,OMEGA,SIGMA,ETA_I,
                           kappa,H_STAR,pim,THETA,efficiency_mode='flat_below')

def calib_pim(target_inf,N,K,kappa,NF_init):
    return calibrate_pi_m(target_inf,N,H0,HI,1.,K,ALPHA,OMEGA,SIGMA,ETA_I,
                          kappa,H_STAR,THETA,efficiency_mode='flat_below')

def main():
    from src.calibration.corrected_pipeline import run_national_cli
    return run_national_cli('flat_below')

if __name__=='__main__': main()
