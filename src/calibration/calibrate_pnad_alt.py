# -*- coding: utf-8 -*-
"""
calibrate_pnad_alt.py — Sensitivity calibration on PNAD-habitual hours + 44.2% informality.

Addresses JMacro R&R item T1.1 (option B: quantify the alt-calibration in main text).

Rebuilds the national A_req using:
  - PNAD habitual hours theta = (0.143, 0.406, 0.451) instead of DIEESE (0.085, 0.269, 0.646)
  - INF_AGG implied by group-weighted targets

All other parameters unchanged from baseline (including group-specific INF_SMALL/LARGE).
Note: the 44.2% national rate and 0.50/0.20 group rates coexist because the group rates are
defined against DIFFERENT informality concepts. This script re-runs the full pipeline under
the PNAD-habitual theta + DIEESE group inf targets to isolate the theta-effect.
"""
import os, sys, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_all import (
    solve_NF, calibrate_wedge, calibrate_pi_m, formal_hours_avg,
    eff, HOURS_BINS,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Override targets ---
THETA_PNAD = np.array([0.143, 0.406, 0.451])
INF_SMALL = 0.50
INF_LARGE = 0.20

# Unchanged
ALPHA = 0.35
ETA_I = 0.40
E_Q = 0.60
H_STAR = 40.0
HI = 44.0
H0 = 44.0
H1 = 36.0
SIGMA_SUB = 1.326
OMEGA = 0.622
NTOT = 0.59
SHARE_S = 0.59
SHARE_L = 0.41
KSHARE_S = 0.35
KSHARE_L = 0.65
GAMMA_F_S = 0.12
GAMMA_F_L = 0.03


def main():
    h_ref = float(np.dot(THETA_PNAD, HOURS_BINS))
    print(f"h_ref (PNAD habitual)  = {h_ref:.4f}")

    kappa = (1.0 - E_Q) / (2.0 * h_ref * (h_ref - H_STAR))
    print(f"kappa (PNAD)           = {kappa:.6e}")
    print(f"e(36) = {eff(36, kappa, H_STAR):.4f}")
    print(f"e(40) = {eff(40, kappa, H_STAR):.4f}")
    print(f"e(44) = {eff(44, kappa, H_STAR):.4f}")

    N_S = NTOT * SHARE_S
    N_L = NTOT * SHARE_L
    K_S = KSHARE_S
    K_L = KSHARE_L

    groups = {}
    specs = [
        ("Pequenas", N_S, K_S, INF_SMALL, GAMMA_F_S),
        ("Grandes",  N_L, K_L, INF_LARGE, GAMMA_F_L),
    ]

    print("\n[Calibrating wedges + pi_m]")
    for name, Ng, Kg, inf_tgt, gF in specs:
        # Check if wedge=0 already gives informality above target
        sol0 = solve_NF(
            Ng, H0, HI, 1.0, Kg, ALPHA, OMEGA, SIGMA_SUB, ETA_I,
            kappa, H_STAR, 0.0, 0.0, 0.0, Ng*(1-inf_tgt), THETA_PNAD)
        pim = 0.0
        if sol0["informality"] > inf_tgt + 1e-10:
            pim = calibrate_pi_m(
                inf_tgt, Ng, H0, HI, 1.0, Kg, ALPHA, OMEGA, SIGMA_SUB, ETA_I,
                kappa, H_STAR, THETA_PNAD)
        wedge = calibrate_wedge(
            inf_tgt, Ng, H0, HI, 1.0, Kg, ALPHA, OMEGA, SIGMA_SUB, ETA_I,
            kappa, H_STAR, pim, THETA_PNAD)
        ver = solve_NF(
            Ng, H0, HI, 1.0, Kg, ALPHA, OMEGA, SIGMA_SUB, ETA_I,
            kappa, H_STAR, wedge, pim, gF, Ng*(1-inf_tgt), THETA_PNAD)
        print(f"  {name}: wedge={wedge:.4f}, pi_m={pim:.4f}, inf_actual={ver['informality']:.4f}")
        groups[name] = dict(N=Ng, K=Kg, gamma_F=gF, wedge=wedge, pi_m=pim,
                             NF_init=Ng*(1-inf_tgt))

    def aggregate(A, hcap):
        Y_total = 0.0
        I_w = 0.0
        N_sum = 0.0
        for gname, g in groups.items():
            sol = solve_NF(
                g["N"], hcap, HI, A, g["K"], ALPHA, OMEGA, SIGMA_SUB, ETA_I,
                kappa, H_STAR, g["wedge"], g["pi_m"], g["gamma_F"],
                g["NF_init"], THETA_PNAD)
            Y_total += sol["Y"]
            I_w += sol["informality"] * g["N"]
            N_sum += g["N"]
        return Y_total, I_w / N_sum

    Y0, inf0 = aggregate(1.0, H0)
    Y1, inf1 = aggregate(1.0, H1)
    dY = (Y1/Y0 - 1) * 100
    dInf = (inf1 - inf0) * 100
    print(f"\nBaseline Y={Y0:.6f}, aggregated Inf={inf0*100:.2f}%")
    print(f"Reform(A=1) Y={Y1:.6f}, dY={dY:+.2f}%, dInf={dInf:+.2f}pp")

    lo, hi = 1.0, 1.30
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        Ymid, _ = aggregate(mid, H1)
        if Ymid < Y0:
            lo = mid
        else:
            hi = mid
    A_req = (0.5 * (lo + hi) - 1.0) * 100

    print(f"\n*** A_req (PNAD habitual theta) = {A_req:.3f}% ***")
    print(f"*** vs. baseline (DIEESE theta) = 7.26%         ***")

    out = {
        "scenario": "PNAD_habitual",
        "theta": THETA_PNAD.tolist(),
        "h_ref": h_ref,
        "kappa": kappa,
        "wedge_S": float(groups["Pequenas"]["wedge"]),
        "wedge_L": float(groups["Grandes"]["wedge"]),
        "pi_m_S": float(groups["Pequenas"]["pi_m"]),
        "pi_m_L": float(groups["Grandes"]["pi_m"]),
        "A_req_pct": A_req,
        "dY_at_A1_pct": dY,
        "dInf_at_A1_pp": dInf,
        "baseline_inf_pct": inf0 * 100,
    }
    out_path = os.path.join(PROJECT_ROOT, "output", "validation", "calibration_pnad_alt.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
