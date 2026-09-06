"""Execute only archived original code; emit freshly calculated comparisons.

Run in its own interpreter so corrected modules cannot contaminate imports.
"""
from pathlib import Path
import argparse, sys, json, math
import numpy as np


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--archive',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    root=Path(args.archive)/'baseline_run'
    sys.path.insert(0,str(root))
    sys.path.insert(0,str(root/'src'/'calibration'))
    from src.model.simulation import load_targets, run_simulation
    import calibrate_flatbelow as flat
    targets=load_targets(str(root/'data_final'))
    rows=[]
    # Original unified module uses a grid and total-employment interpretation.
    for h in (40,36):
        targets['H1']['value']=h
        sim=run_simulation(targets,sigma_sub=1.326,omega=0.622)
        b,r=sim['baseline'],sim['reform']
        n=targets['N_TOTAL']['value']
        v0=sim['psi']*b['h_avg']**3/3
        v1=sim['psi']*r['h_avg']**3/3
        rows.append(dict(version='original',efficiency_mode='bilateral',hours_cap=h,
                         sigma_sub=1.326,omega=0.622,Y0=b['Y'],Y1=r['Y'],
                         dY_pct=100*(r['Y']/b['Y']-1),A_req_pct=sim['results']['A_req_pct'],
                         baseline_informality_pct=100*b['inf'],informality_pct=100*r['inf'],
                         dInf_pp=100*(r['inf']-b['inf']),
                         dGHH_pct=sim['results']['dCV_pct'],
                         CE_pct=100*((r['C']-b['C'])/n-v1+v0)/(b['C']/n),
                         metric_note='GHH from original; CE newly evaluated from original allocations; no original level decomposition'))
    theta=flat.THETA
    k=flat.kappa_from_eq(float(np.dot(theta,flat.HOURS_BINS)),flat.H_STAR,flat.E_Q)
    gs=[]
    for N,K,inf,gamma in ((flat.NTOT*flat.SHARE_S,flat.KSHARE_S,flat.INF_S,flat.GAMMA_F_S),
                          (flat.NTOT*flat.SHARE_L,flat.KSHARE_L,flat.INF_L,flat.GAMMA_F_L)):
        nf=N*(1-inf)
        pi=flat.calib_pim(inf,N,K,k,nf)
        tau=flat.calib_wedge(inf,N,K,pi,k,gamma,nf)
        gs.append((N,K,pi,tau,gamma,nf))
    def agg(A,h):
        Y=C=NI=hours=0.
        for N,K,pi,tau,gamma,nf in gs:
            s=flat.solve_NF_flat(N,h,flat.HI,A,K,tau,pi,gamma,nf,k,theta)
            Y+=s['Y']; C+=s['Y']-.5*gamma*(s['NF']-nf)**2; NI+=s['NI']
            hours+=s['NF']*np.dot(theta,np.minimum(flat.HOURS_BINS,h))+s['NI']*flat.HI
        return dict(Y=Y,C=C,inf=NI/flat.NTOT,h_avg=hours/flat.NTOT)
    b=agg(1,44)
    psi=(1-flat.ALPHA)*b['Y']/(flat.NTOT*b['h_avg'])/b['h_avg']**2
    for h in (40,36):
        r=agg(1,h)
        lo,hi=1.,1.3
        for _ in range(80):
            m=(lo+hi)/2
            if agg(m,h)['Y']<b['Y']: lo=m
            else: hi=m
        v0=psi*b['h_avg']**3/3; v1=psi*r['h_avg']**3/3
        ce=((r['C']-b['C'])/flat.NTOT-v1+v0)/(b['C']/flat.NTOT)
        ghh=(r['C']/flat.NTOT-v1)/(b['C']/flat.NTOT-v0)-1
        rows.append(dict(version='original',efficiency_mode='flat_below',hours_cap=h,
                         sigma_sub=flat.SIGMA,omega=flat.OMEGA,Y0=b['Y'],Y1=r['Y'],
                         dY_pct=100*(r['Y']/b['Y']-1),A_req_pct=100*((lo+hi)/2-1),
                         baseline_informality_pct=100*b['inf'],informality_pct=100*r['inf'],
                         dInf_pp=100*(r['inf']-b['inf']),dGHH_pct=100*ghh,CE_pct=100*ce,
                         metric_note='Original flat solver; GHH and CE reconstructed from original allocations'))
    Path(args.output).write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Fresh original comparison:',args.output)


if __name__=='__main__': main()
