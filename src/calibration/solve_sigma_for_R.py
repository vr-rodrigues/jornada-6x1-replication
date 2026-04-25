# -*- coding: utf-8 -*-
"""
solve_sigma_for_R.py — Invert the CES wage-premium R(sigma) for a target R.

Given (omega, eta_I, theta, h0, hI, h_star, e_q, alpha, group structure),
recalibrate wedges/pi_m at each sigma in a dense grid and compute the
model-implied formal/informal wage premium R. Then find the sigma that
yields R = R_target.

Used to map R in {1.15, 1.40, 1.55} -> sigma_sub.
"""
import os
import sys
import json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_all import (
    solve_NF, calibrate_wedge, calibrate_pi_m, formal_hours_avg,
    formal_hours_hetero, eff, HOURS_BINS, calibrate_kappa,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

THETA = np.array([0.085, 0.269, 0.646])
ALPHA = 0.35
E_Q = 0.60
H_STAR = 40.0
HI = 44.0
H0 = 44.0
NTOT = 0.59
SHARE_S = 0.59
SHARE_L = 0.41
KSHARE_S = 0.35
KSHARE_L = 0.65
INF_S = 0.50
INF_L = 0.20


def wage_premium_at(sigma_sub, omega, eta_I):
    """Recalibrate at (sigma_sub, omega, eta_I) and return implied wage premium R."""
    h_ref = formal_hours_avg(H0, THETA)
    kappa = calibrate_kappa(h_ref, H_STAR, E_Q)

    groups_specs = [
        ("S", NTOT * SHARE_S, KSHARE_S, INF_S),
        ("L", NTOT * SHARE_L, KSHARE_L, INF_L),
    ]
    NF_tot = 0.0
    NI_tot = 0.0
    for _, Ng, Kg, inf_tgt in groups_specs:
        # pi_m
        sol0 = solve_NF(Ng, H0, HI, 1.0, Kg, ALPHA, omega, sigma_sub, eta_I,
                        kappa, H_STAR, 0.0, 0.0, 0.0, Ng * (1 - inf_tgt), THETA)
        pi_m = 0.0
        if sol0["informality"] > inf_tgt + 1e-10:
            pi_m = calibrate_pi_m(inf_tgt, Ng, H0, HI, 1.0, Kg, ALPHA, omega,
                                  sigma_sub, eta_I, kappa, H_STAR, THETA)
        wedge = calibrate_wedge(inf_tgt, Ng, H0, HI, 1.0, Kg, ALPHA, omega,
                                sigma_sub, eta_I, kappa, H_STAR, pi_m, THETA)
        sol = solve_NF(Ng, H0, HI, 1.0, Kg, ALPHA, omega, sigma_sub, eta_I,
                       kappa, H_STAR, wedge, pi_m, 0.0,
                       Ng * (1 - inf_tgt), THETA)
        NF_tot += sol["NF"]
        NI_tot += sol["NI"]

    hF_avg, eff_hF = formal_hours_hetero(H0, kappa, H_STAR, THETA)
    eI = eff(HI, kappa, H_STAR)
    z = eff_hF / (eta_I * HI * eI)
    LF = NF_tot * eff_hF
    LI = eta_I * NI_tot * HI * eI
    x = LF / max(LI, 1e-15)
    rho = (sigma_sub - 1.0) / sigma_sub
    R = (omega / (1 - omega)) * x ** (rho - 1) * z
    return R


def sigma_for_R(R_target, omega, eta_I, sig_lo=0.30, sig_hi=2.00, tol=1e-4, maxit=60):
    """Bisection: find sigma s.t. R(sigma) = R_target."""
    def f(s):
        return wage_premium_at(s, omega, eta_I) - R_target

    f_lo = f(sig_lo)
    f_hi = f(sig_hi)
    # R is typically decreasing in sigma (higher substitution -> smaller premium gap).
    # Check and bracket.
    if f_lo * f_hi > 0:
        # Extend range
        for s_try in [0.10, 0.20, 2.5, 3.0, 4.0, 5.0]:
            f_try = f(s_try)
            if f_lo * f_try < 0:
                sig_hi = s_try
                f_hi = f_try
                break
            if f_try * f_hi < 0:
                sig_lo = s_try
                f_lo = f_try
                break
    # Monotone bisection (assume f(sig_lo) and f(sig_hi) have opposite signs)
    a, b = sig_lo, sig_hi
    fa, fb = f_lo, f_hi
    if fa * fb > 0:
        raise RuntimeError(f"Cannot bracket R={R_target} in [{sig_lo},{sig_hi}] "
                           f"(f_lo={fa}, f_hi={fb})")
    for _ in range(maxit):
        m = 0.5 * (a + b)
        fm = f(m)
        if abs(fm) < tol:
            return m
        if fa * fm < 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
    return 0.5 * (a + b)


def main():
    omega = float(os.environ.get("OMEGA", "0.622"))
    eta_I = float(os.environ.get("ETA_I", "0.40"))
    R_targets = [1.15, 1.40, 1.55]

    print(f"Solving sigma(R) for omega={omega}, eta_I={eta_I}")
    print(f"{'R':>6} {'sigma':>8} {'R_check':>8}")
    print("-" * 26)
    out = {"omega": omega, "eta_I": eta_I, "grid": []}
    for R_t in R_targets:
        sig = sigma_for_R(R_t, omega, eta_I)
        R_check = wage_premium_at(sig, omega, eta_I)
        print(f"{R_t:>6.2f} {sig:>8.4f} {R_check:>8.4f}")
        out["grid"].append({"R": R_t, "sigma": sig, "R_check": R_check})

    op = os.path.join(PROJECT_ROOT, "output", "validation", "sigma_for_R_map.json")
    os.makedirs(os.path.dirname(op), exist_ok=True)
    with open(op, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved: {op}")


if __name__ == "__main__":
    main()
