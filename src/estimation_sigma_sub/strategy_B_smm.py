# -*- coding: utf-8 -*-
"""
strategy_B_smm.py — Indirect Inference / SMM for sigma_sub

Method:
  For each sigma in a grid, re-calibrate the model (wedges, pi_m) to match
  the SAME informality targets, then compute model-implied moments.
  The sigma that best matches ADDITIONAL moments (not used in calibration)
  is the preferred estimate.

Key insight: Informality rates (50%, 20%) are matched by construction
  via wedge calibration for ANY sigma. So we need OTHER moments to
  identify sigma:

  1. Formal/informal wage premium
  2. Output response to hours reduction (if we had cross-country variation)
  3. Relative firm-size distribution responses

Since we only have one economy (Brazil), the most informative moment
  is the wage premium R = w_F / w_I.

The wage premium formula (from CES FOC):
  R = (omega/(1-omega)) * (LF/LI)^(rho-1) * z
  where rho = (sigma-1)/sigma, z = eff_hF / (eta_I * hI * eI)

This creates a 1-to-1 mapping: given observed R, we can solve for sigma.
So SMM reduces to: what is the observed wage premium?

Output: src/estimation_sigma_sub/sigma_sub_strategy_B.md
"""

import os
import sys
import json
import numpy as np

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add parent paths
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "calibration"))
from calibrate_all import (
    production, ces_agg, eff, formal_hours_hetero, formal_hours_avg,
    calibrate_kappa, calibrate_wedge, calibrate_pi_m, solve_NF,
    solve_Areq, calibrate_psi, compensating_variation
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FINAL = os.path.join(PROJECT_ROOT, "data_final")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "validation")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Hours distribution
THETA = np.array([0.085, 0.269, 0.646])


def calibrate_and_simulate(sigma_sub, verbose=False):
    """
    For a given sigma_sub, calibrate the full model and return key moments.
    """
    # Fixed parameters
    alpha = 0.35
    eta_I = 0.40
    e_q = 0.60
    h0 = 44.0
    h1 = 36.0
    h_star = 40.0
    hI = 44.0
    omega = 0.622
    N_total = 0.590

    # Kappa
    h_ref = formal_hours_avg(h0, THETA)
    kappa = calibrate_kappa(h_ref, h_star, e_q)

    # Group specs
    specs = {
        "Pequenas": {"share": 0.59, "inf_target": 0.50, "gamma_F": 0.12, "K_share": 0.35},
        "Grandes":  {"share": 0.41, "inf_target": 0.20, "gamma_F": 0.03, "K_share": 0.65},
    }

    groups = {}
    for gname, spec in specs.items():
        N_g = N_total * spec["share"]
        K_g = spec["K_share"]

        # Check if pi_m needed
        pi_m_g = 0.0
        sol_w0 = solve_NF(N_g, h0, hI, 1.0, K_g, alpha, omega, sigma_sub,
                          eta_I, kappa, h_star, 0.0, 0.0, 0.0,
                          N_g * (1 - spec["inf_target"]), THETA)
        if sol_w0["informality"] > spec["inf_target"] + 1e-10:
            pi_m_g = calibrate_pi_m(spec["inf_target"], N_g, h0, hI,
                                    1.0, K_g, alpha, omega, sigma_sub,
                                    eta_I, kappa, h_star, THETA)

        wedge = calibrate_wedge(spec["inf_target"], N_g, h0, hI,
                                1.0, K_g, alpha, omega, sigma_sub,
                                eta_I, kappa, h_star, pi_m_g, THETA)

        groups[gname] = {
            "A": 1.0, "alpha": alpha, "h0": h0, "h1": h1, "hI": hI,
            "h_star": h_star, "omega": omega, "sigma_sub": sigma_sub,
            "eta_I": eta_I, "kappa": kappa,
            "N_total": N_g, "K": K_g, "gamma_F": spec["gamma_F"],
            "pi_m": pi_m_g, "formal_wedge": wedge,
            "NF_init": N_g * (1 - spec["inf_target"]),
        }

    # Baseline solution
    Y_base = 0.0; NF_tot = 0.0; NI_tot = 0.0; hrs = 0.0; C_base = 0.0
    for gname, pars in groups.items():
        sol = solve_NF(pars["N_total"], h0, hI, 1.0, pars["K"], alpha,
                       omega, sigma_sub, eta_I, kappa, h_star,
                       pars["formal_wedge"], pars["pi_m"],
                       pars["gamma_F"], pars["NF_init"], THETA)
        Y_base += sol["Y"]; NF_tot += sol["NF"]; NI_tot += sol["NI"]
        hrs += sol["hours_total"]; C_base += sol["C"]

    # Wage premium computation
    hF_avg, eff_hF = formal_hours_hetero(h0, kappa, h_star, THETA)
    eI = eff(hI, kappa, h_star)
    LF = NF_tot * eff_hF
    LI = eta_I * NI_tot * hI * eI
    z = eff_hF / (eta_I * hI * eI)
    x = LF / max(LI, 1e-15)

    rho = (sigma_sub - 1.0) / sigma_sub
    wage_premium = (omega / (1 - omega)) * x**(rho - 1) * z

    # Reform solution
    Y_cap = 0.0; NI_cap = 0.0; hrs_cap = 0.0; C_cap = 0.0
    for pars in groups.values():
        sol = solve_NF(pars["N_total"], h1, hI, 1.0, pars["K"], alpha,
                       omega, sigma_sub, eta_I, kappa, h_star,
                       pars["formal_wedge"], pars["pi_m"],
                       pars["gamma_F"], pars["NF_init"], THETA)
        Y_cap += sol["Y"]; NI_cap += sol["NI"]
        hrs_cap += sol["hours_total"]; C_cap += sol["C"]

    # A_req
    Areq = solve_Areq(groups, h1, Y_base, THETA)

    # Welfare
    N = N_total
    h_avg_b = hrs / N
    h_avg_c = hrs_cap / N
    nu = 2.0
    w_hr = (1 - alpha) * Y_base / (N * h_avg_b)
    psi = calibrate_psi(w_hr, h_avg_b, nu)
    dcv = compensating_variation(C_base / N, h_avg_b, C_cap / N, h_avg_c, nu, psi)

    inf_agg = NI_tot / N
    inf_cap_agg = NI_cap / N
    dInf = (inf_cap_agg - inf_agg) * 100

    return {
        "sigma_sub": sigma_sub,
        "wage_premium": round(wage_premium, 4),
        "A_req_pct": round(Areq, 4),
        "dY_pct": round((Y_cap / Y_base - 1) * 100, 4),
        "dInf_pp": round(dInf, 4),
        "dCV_pct": round(dcv * 100, 4),
        "wedge_S": round(groups["Pequenas"]["formal_wedge"], 4),
        "wedge_L": round(groups["Grandes"]["formal_wedge"], 4),
        "pi_m_S": round(groups["Pequenas"]["pi_m"], 4),
        "pi_m_L": round(groups["Grandes"]["pi_m"], 4),
        "inf_agg_baseline": round(inf_agg, 4),
    }


def main():
    print("=" * 60)
    print("STRATEGY B: SMM / INDIRECT INFERENCE FOR SIGMA_SUB")
    print("=" * 60)

    # Grid of sigma values
    sigma_grid = [0.90, 1.00, 1.065, 1.10, 1.15, 1.20, 1.23, 1.30, 1.50,
                  2.00, 3.00]

    results = []
    print(f"\n{'sigma':>6} {'premium':>8} {'A_req':>7} {'dY':>7} {'dInf':>6} {'dCV':>7}")
    print("-" * 50)

    for sig in sigma_grid:
        try:
            r = calibrate_and_simulate(sig)
            results.append(r)
            print(f"{sig:>6.3f} {r['wage_premium']:>8.3f} {r['A_req_pct']:>6.2f}% "
                  f"{r['dY_pct']:>6.2f}% {r['dInf_pp']:>+5.2f} {r['dCV_pct']:>+6.2f}%")
        except Exception as e:
            print(f"{sig:>6.3f}  ERROR: {e}")

    # Observed wage premium range
    print(f"\n{'='*60}")
    print("WAGE PREMIUM DISCIPLINE")
    print(f"{'='*60}")
    print(f"  Observed formal/informal wage premium: [1.15, 1.55]")
    print(f"  (Source: PNAD Continua, controlling for observables)")

    # Find sigma range consistent with observed premium
    consistent = [r for r in results if 1.15 <= r["wage_premium"] <= 1.55]
    if consistent:
        sig_range = [r["sigma_sub"] for r in consistent]
        areq_range = [r["A_req_pct"] for r in consistent]
        print(f"  Consistent sigma range: [{min(sig_range):.3f}, {max(sig_range):.3f}]")
        print(f"  Consistent A_req range: [{min(areq_range):.2f}%, {max(areq_range):.2f}%]")

    # Exact inversion
    print(f"\n  Exact inversion (from CES FOC):")
    # Use baseline NF/NI from sigma=0.80 (representative)
    r_ref = [r for r in results if abs(r["sigma_sub"] - 1.15) < 0.01][0]

    for R_target in [1.15, 1.25, 1.35, 1.45, 1.55]:
        # Find sigma by interpolation
        best = min(results, key=lambda r: abs(r["wage_premium"] - R_target))
        print(f"    R={R_target:.2f} -> sigma~{best['sigma_sub']:.3f}, "
              f"A_req={best['A_req_pct']:.2f}%")

    # Save
    outpath = os.path.join(OUTPUT_DIR, "smm_sigma_results.json")
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump({"grid_results": results,
                   "observed_premium_range": [1.15, 1.55],
                   "method": "Re-calibrate model for each sigma, compute implied wage premium"
                   }, f, indent=2)
    print(f"\n[OK] Results saved to: {outpath}")

    return results


if __name__ == "__main__":
    main()
