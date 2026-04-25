# -*- coding: utf-8 -*-
"""
asymmetric_eh.py — A_req under asymmetric efficiency e(h) below vs above h* = 40.

Addresses JMacro R&R item T2.2.

Baseline: e(h) = exp(-kappa*(h-40)^2)  symmetric.
Alternatives tested:
  (A) Flat below 40: e(h)=1 for h<=40, exp(-kappa*(h-40)^2) for h>40
      (no efficiency loss from shorter hours)
  (B) Half-curvature below: kappa_below = 0.5*kappa, kappa_above = kappa
  (C) Double-curvature below: kappa_below = 2*kappa, kappa_above = kappa
"""
import os, sys, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_all import (
    calibrate_wedge, calibrate_pi_m, HOURS_BINS,
    production, ces_agg, formal_hours_avg,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

THETA = np.array([0.085, 0.269, 0.646])
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
INF_S = 0.50
INF_L = 0.20


def make_eff(scenario, kappa):
    """Return a vectorizable efficiency function."""
    if scenario == "symmetric":
        return lambda h: np.exp(-kappa * (np.asarray(h) - H_STAR)**2)
    if scenario == "flat_below":
        return lambda h: np.where(np.asarray(h) <= H_STAR, 1.0,
                                   np.exp(-kappa * (np.asarray(h) - H_STAR)**2))
    if scenario == "half_below":
        return lambda h: np.where(np.asarray(h) <= H_STAR,
                                   np.exp(-0.5*kappa * (np.asarray(h) - H_STAR)**2),
                                   np.exp(-kappa * (np.asarray(h) - H_STAR)**2))
    if scenario == "double_below":
        return lambda h: np.where(np.asarray(h) <= H_STAR,
                                   np.exp(-2.0*kappa * (np.asarray(h) - H_STAR)**2),
                                   np.exp(-kappa * (np.asarray(h) - H_STAR)**2))
    raise ValueError(scenario)


def solve_NF_custom(N_total, hF, hI, A, K, formal_wedge, pi_m, gamma_F,
                    NF_prev, effF, effI, theta, grid=3001):
    NF_grid = np.linspace(0, N_total, grid)
    NI_grid = N_total - NF_grid

    h_capped = np.minimum(HOURS_BINS, hF)
    eff_hF = float(np.dot(theta, h_capped * effF(h_capped)))

    LF = NF_grid * eff_hF
    LI = ETA_I * NI_grid * hI * effI(hI)
    L = ces_agg(LF, LI, OMEGA, SIGMA_SUB)
    Y = production(A, K, ALPHA, L)
    adj = 0.5 * gamma_F * (NF_grid - NF_prev)**2
    phi = 0.5 * pi_m * NI_grid**2
    obj = Y - formal_wedge * NF_grid - phi - adj
    j = int(np.argmax(obj))
    return dict(NF=NF_grid[j], NI=NI_grid[j], Y=Y[j],
                 informality=NI_grid[j]/max(N_total, 1e-15))


def run_scenario(scenario):
    h_ref = float(np.dot(THETA, HOURS_BINS))
    kappa = (1.0 - E_Q) / (2.0 * h_ref * (h_ref - H_STAR))
    effF = make_eff(scenario, kappa)
    effI = effF

    N_S = NTOT * SHARE_S
    N_L = NTOT * SHARE_L
    K_S = KSHARE_S
    K_L = KSHARE_L

    # Calibrate wedges using the standard module (which uses symmetric internally).
    # The wedges are a baseline-fit object, so we keep them fixed across scenarios
    # (only reform-counterfactual efficiency differs). This mimics how the paper
    # treats e(h) as a model primitive independent of the wedge calibration.
    # To avoid re-solving wedges under each e(h), we compute *relative* A_req
    # holding wedges at their symmetric calibration.
    from calibrate_all import solve_NF as _solve_NF_sym
    # Symmetric wedges (standard calibration)
    groups = {}
    for name, Ng, Kg, inf_tgt, gF in [
        ("S", N_S, K_S, INF_S, GAMMA_F_S),
        ("L", N_L, K_L, INF_L, GAMMA_F_L),
    ]:
        sol0 = _solve_NF_sym(Ng, H0, HI, 1.0, Kg, ALPHA, OMEGA, SIGMA_SUB, ETA_I,
                             kappa, H_STAR, 0.0, 0.0, 0.0, Ng*(1-inf_tgt), THETA)
        pim = 0.0
        if sol0["informality"] > inf_tgt + 1e-10:
            pim = calibrate_pi_m(inf_tgt, Ng, H0, HI, 1.0, Kg, ALPHA, OMEGA,
                                 SIGMA_SUB, ETA_I, kappa, H_STAR, THETA)
        wedge = calibrate_wedge(inf_tgt, Ng, H0, HI, 1.0, Kg, ALPHA, OMEGA,
                                SIGMA_SUB, ETA_I, kappa, H_STAR, pim, THETA)
        groups[name] = dict(N=Ng, K=Kg, gamma_F=gF, wedge=wedge, pi_m=pim,
                             NF_init=Ng*(1-inf_tgt))

    def agg(A, hcap):
        Y = 0.0
        for g in groups.values():
            sol = solve_NF_custom(
                g["N"], hcap, HI, A, g["K"], g["wedge"], g["pi_m"],
                g["gamma_F"], g["NF_init"], effF, effI, THETA)
            Y += sol["Y"]
        return Y

    Y0 = agg(1.0, H0)
    lo, hi = 1.0, 1.40
    for _ in range(70):
        mid = 0.5*(lo+hi)
        if agg(mid, H1) < Y0: lo = mid
        else: hi = mid
    Areq = (0.5*(lo+hi) - 1.0) * 100
    return Areq


def main():
    scenarios = ["symmetric", "flat_below", "half_below", "double_below"]
    results = {}
    print(f"{'scenario':>14} {'A_req':>8}")
    for s in scenarios:
        a = run_scenario(s)
        results[s] = a
        print(f"{s:>14} {a:>7.3f}%")
    out_path = os.path.join(PROJECT_ROOT, "output", "validation", "asymmetric_eh.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
