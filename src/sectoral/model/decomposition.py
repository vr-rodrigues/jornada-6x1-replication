# -*- coding: utf-8 -*-
"""
Sectoral decomposition analysis.

Counterfactual: what if all sectors had the same national theta?
This isolates the contribution of sector-specific hours distributions
vs. sector-specific informality to the A_req differences.
"""

import csv
import os
import sys
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

from src.model.firm_problem import solve_NF
from src.model.areq_solver import solve_Areq
from src.sectoral.model.sector_model import (
    load_sectoral_facts, load_national_targets,
    build_sector_params, _solve_Areq_multi
)


def run_decomposition():
    """
    Decomposition analysis: separate the role of informality vs hours.

    Method:
    1. ACTUAL: sector-specific theta_s AND sector-specific inf_s
    2. COUNTERFACTUAL 1: national theta (uniform) + sector-specific inf_s
    3. COUNTERFACTUAL 2: sector-specific theta_s + national inf (uniform)
    4. COUNTERFACTUAL 3: national theta + national inf (= aggregate model)

    Differences:
    - Actual - CF1 = contribution of sector-specific hours
    - Actual - CF2 = contribution of sector-specific informality
    - Actual - CF3 = total heterogeneity effect
    """
    data_final = os.path.join(PROJECT_ROOT, "data_final")
    output_dir = os.path.join(PROJECT_ROOT, "output", "sectoral", "tables")

    sectors = load_sectoral_facts(data_final)
    targets = load_national_targets(data_final)

    national_theta = np.array([
        targets["THETA_36"], targets["THETA_40"], targets["THETA_44"]
    ])
    national_inf = targets.get("INF_AGG", 0.378)

    h1_values = [40.0, 36.0]
    rows = []

    for h1 in h1_values:
        print(f"\n{'='*60}")
        print(f"DECOMPOSITION: 44 -> {int(h1)}h")
        print(f"{'='*60}")

        # 1. ACTUAL (sector-specific theta_s + sector-specific inf_s)
        print("\n[1] Actual (sector-specific theta + sector-specific inf)...")
        params_actual, kappa = build_sector_params(sectors, targets)
        areq_actual = {}
        for sname, pars in params_actual.items():
            group = {sname: pars}
            Y_base_s = solve_NF(
                pars["N_total"], pars["h0"], pars["hI"],
                pars["A"], pars["K"], pars["alpha"],
                pars["omega"], pars["sigma_sub"], pars["eta_I"],
                pars["kappa"], pars["h_star"],
                pars["formal_wedge"], pars["pi_m"],
                pars["gamma_F"], pars["NF_init"], pars["theta"]
            )["Y"]
            areq_actual[sname] = _solve_Areq_single(pars, h1, Y_base_s)

        # 2. CF1: national theta + sector-specific inf
        print("[2] CF1 (national theta + sector-specific inf)...")
        sectors_cf1 = {}
        for sname, sdata in sectors.items():
            sectors_cf1[sname] = {**sdata, "theta": national_theta}
        params_cf1, _ = build_sector_params(sectors_cf1, targets)
        areq_cf1 = {}
        for sname, pars in params_cf1.items():
            Y_base_s = solve_NF(
                pars["N_total"], pars["h0"], pars["hI"],
                pars["A"], pars["K"], pars["alpha"],
                pars["omega"], pars["sigma_sub"], pars["eta_I"],
                pars["kappa"], pars["h_star"],
                pars["formal_wedge"], pars["pi_m"],
                pars["gamma_F"], pars["NF_init"], pars["theta"]
            )["Y"]
            areq_cf1[sname] = _solve_Areq_single(pars, h1, Y_base_s)

        # 3. CF2: sector-specific theta + national inf
        print("[3] CF2 (sector-specific theta + national inf)...")
        sectors_cf2 = {}
        for sname, sdata in sectors.items():
            sectors_cf2[sname] = {**sdata, "inf_rate": national_inf}
        params_cf2, _ = build_sector_params(sectors_cf2, targets)
        areq_cf2 = {}
        for sname, pars in params_cf2.items():
            Y_base_s = solve_NF(
                pars["N_total"], pars["h0"], pars["hI"],
                pars["A"], pars["K"], pars["alpha"],
                pars["omega"], pars["sigma_sub"], pars["eta_I"],
                pars["kappa"], pars["h_star"],
                pars["formal_wedge"], pars["pi_m"],
                pars["gamma_F"], pars["NF_init"], pars["theta"]
            )["Y"]
            areq_cf2[sname] = _solve_Areq_single(pars, h1, Y_base_s)

        # Print decomposition
        print(f"\n{'Sector':>12s} | {'Actual':>8s} | {'CF1(nat.th)':>11s} | "
              f"{'CF2(nat.inf)':>12s} | {'Hours eff':>9s} | {'Inf eff':>8s}")
        print("-" * 75)
        for sname in sectors:
            a = areq_actual[sname]
            c1 = areq_cf1[sname]
            c2 = areq_cf2[sname]
            hours_eff = a - c1  # positive means sector theta raises A_req
            inf_eff = a - c2    # positive means sector inf raises A_req
            print(f"{sname:>12s} | {a:>7.3f}% | {c1:>10.3f}% | "
                  f"{c2:>11.3f}% | {hours_eff:>+8.3f} | {inf_eff:>+7.3f}")

            rows.append({
                "h1": int(h1),
                "sector": sname,
                "areq_actual": round(a, 4),
                "areq_cf1_national_theta": round(c1, 4),
                "areq_cf2_national_inf": round(c2, 4),
                "effect_hours_distribution": round(hours_eff, 4),
                "effect_informality": round(inf_eff, 4),
            })

    # Save
    out_path = os.path.join(output_dir, "SECTOR_DECOMPOSITION.csv")
    fieldnames = ["h1", "sector", "areq_actual",
                   "areq_cf1_national_theta", "areq_cf2_national_inf",
                   "effect_hours_distribution", "effect_informality"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved: {out_path}")


def _solve_Areq_single(pars, h1, Y_target, grid=3001):
    """Solve A_req for a single sector."""
    def Y_at(A_mult):
        sol = solve_NF(
            pars["N_total"], h1, pars["hI"],
            pars["A"] * A_mult, pars["K"], pars["alpha"],
            pars["omega"], pars["sigma_sub"], pars["eta_I"],
            pars["kappa"], pars["h_star"],
            pars["formal_wedge"], pars["pi_m"],
            pars["gamma_F"], pars["NF_init"], pars["theta"], grid)
        return sol["Y"]

    Y1 = Y_at(1.0)
    if Y1 >= Y_target:
        return 0.0

    A_lo, A_hi = 1.0, (Y_target / max(Y1, 1e-15)) * 1.3
    for _ in range(35):
        A_mid = 0.5 * (A_lo + A_hi)
        if Y_at(A_mid) < Y_target:
            A_lo = A_mid
        else:
            A_hi = A_mid
        if (A_hi - A_lo) < 1e-5 * A_lo:
            break
    return 100.0 * (0.5 * (A_lo + A_hi) - 1.0)


if __name__ == "__main__":
    run_decomposition()
