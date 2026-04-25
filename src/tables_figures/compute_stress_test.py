# -*- coding: utf-8 -*-
"""
compute_stress_test.py — Pessimistic stress test: post-reform TFP shock.

Motivation: large negative shocks to the economy may themselves depress TFP
(learning-by-doing disruption, organizational slack, hysteresis of
informalization). The baseline model treats A as exogenous; this script runs
the reform (h=44 -> 36) under A_post = A_base * (1 - delta) for delta in
[0, 0.005, 0.01, 0.015, 0.02], reporting how ΔY, ΔInf, ΔCV shift.

Output:
  - data_final/stress_test_results.json
  - output/tables/tab_stress_test.tex

Reference: La Porta & Shleifer (2014); Aghion & Howitt (Schumpeterian
growth with creative-destruction disruption); related hysteresis literature.
"""

import json
import os
import sys
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from src.model.simulation import load_targets, run_simulation
from src.model.groups import build_groups
from src.model.firm_problem import solve_NF
from src.model.areq_solver import solve_Areq
from src.model.welfare import compensating_variation
from src.model.calibration import calibrate_psi
from src.model.efficiency import formal_hours_avg

OUT_DATA = os.path.join(ROOT, "data_final", "stress_test_results.json")
OUT_TAB = os.path.join(ROOT, "output", "tables", "tab_stress_test.tex")

os.makedirs(os.path.dirname(OUT_TAB), exist_ok=True)

DATA_FINAL = os.path.join(ROOT, "data_final")
DELTAS = [0.0, 0.005, 0.010, 0.015, 0.020]
SIGMA = 1.326
OMEGA = 0.622
NU_GHH = 2.0


def solve_reform_at_delta(groups, h1, hI, theta, delta):
    """Solve the reform assuming post-reform A = A_base * (1 - delta)."""
    Y, C, hours, NI = 0.0, 0.0, 0.0, 0.0
    for pars in groups.values():
        A_post = pars["A"] * (1.0 - delta)
        sol = solve_NF(pars["N_total"], h1, hI, A_post, pars["K"],
                       pars["alpha"], pars["omega"], pars["sigma_sub"],
                       pars["eta_I"], pars["kappa"], pars["h_star"],
                       pars["formal_wedge"], pars["pi_m"],
                       pars["gamma_F"], pars["NF_init"], theta)
        Y += sol["Y"]; C += sol["C"]
        hours += sol["hours_total"]; NI += sol["NI"]
    return Y, C, hours, NI


def solve_Areq_at_delta(groups, h1, Y_base, theta, delta):
    """Solve A_req assuming post-reform A = A_base * (1 - delta)."""
    # We want to find multiplier A_req such that
    # sum_g Y_g(A*(1-delta)*(1+A_req), K_g, h1) = Y_base
    # Equivalent to solving with a scaled A_0 = A * (1-delta)
    scaled = {}
    for g, p in groups.items():
        scaled[g] = dict(p)
        scaled[g]["A"] = p["A"] * (1.0 - delta)
    return solve_Areq(scaled, h1, Y_base, theta)


def main():
    print("Loading targets and building groups...")
    targets = load_targets(DATA_FINAL)
    groups, kappa, theta = build_groups(targets, SIGMA, OMEGA)

    alpha = targets["ALPHA"]["value"]
    h0 = targets["H0"]["value"]
    h1 = targets["H1"]["value"]
    hI = targets["HI"]["value"]
    N_total = targets["N_TOTAL"]["value"]

    # Baseline
    print("Solving baseline (h0=44, A=A_base)...")
    Y_base, C_base, hours_base, NI_base = 0.0, 0.0, 0.0, 0.0
    for pars in groups.values():
        sol = solve_NF(pars["N_total"], h0, hI, pars["A"], pars["K"],
                       pars["alpha"], pars["omega"], pars["sigma_sub"],
                       pars["eta_I"], pars["kappa"], pars["h_star"],
                       pars["formal_wedge"], pars["pi_m"],
                       pars["gamma_F"], pars["NF_init"], theta)
        Y_base += sol["Y"]; C_base += sol["C"]
        hours_base += sol["hours_total"]; NI_base += sol["NI"]

    inf_base = NI_base / N_total
    h_avg_base = hours_base / N_total
    w_hourly = (1 - alpha) * Y_base / (N_total * h_avg_base)
    psi = calibrate_psi(w_hourly, h_avg_base, NU_GHH)
    c_base_pc = C_base / N_total

    print(f"  Y_base = {Y_base:.6f}, inf_base = {inf_base:.4f}, h_avg = {h_avg_base:.2f}")

    # Stress grid
    print("\nRunning stress test grid...")
    results = []
    for delta in DELTAS:
        Y, C, hours, NI = solve_reform_at_delta(groups, h1, hI, theta, delta)
        dY_pct = (Y / Y_base - 1) * 100
        dInf_pp = (NI / N_total - inf_base) * 100
        h_avg = hours / N_total
        c_pc = C / N_total
        dCV = compensating_variation(c_base_pc, h_avg_base, c_pc, h_avg,
                                     NU_GHH, psi) * 100
        Areq = solve_Areq_at_delta(groups, h1, Y_base, theta, delta)

        results.append({
            "delta_pct": round(delta * 100, 2),
            "A_post_ratio": round(1 - delta, 4),
            "A_req_pct": round(Areq, 3),
            "dY_pct": round(dY_pct, 3),
            "dInf_pp": round(dInf_pp, 3),
            "dCV_pct": round(dCV, 3),
            "h_avg_post": round(h_avg, 3),
        })
        print(f"  delta={delta*100:+.1f}%  ->  dY={dY_pct:+.2f}%, A_req={Areq:+.2f}%, "
              f"dInf={dInf_pp:+.2f}pp, dCV={dCV:+.2f}%")

    # Save JSON
    summary = {
        "description": (
            "Pessimistic stress test: post-reform TFP is A_post = A_base*(1-delta). "
            "delta=0 is the baseline in the paper. delta in [0.5%, 2%] represents "
            "additional TFP deterioration that could arise from the shock itself "
            "(learning-by-doing disruption, organizational slack, informalization "
            "lock-in). All other calibration is held at the baseline values."
        ),
        "sigma_sub": SIGMA,
        "omega": OMEGA,
        "baseline": {
            "Y": Y_base,
            "inf": inf_base,
            "h_avg": h_avg_base,
            "psi": psi,
        },
        "grid": results,
    }
    with open(OUT_DATA, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Saved JSON to {OUT_DATA}")

    # Generate LaTeX table
    lines = [
        r"% Auto-generated by src/tables_figures/compute_stress_test.py",
        r"% Pessimistic stress test: post-reform TFP = A*(1-delta)",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Pessimistic stress test: reform with post-reform TFP shock.}\label{tab:stress_test}",
        r"\small",
        r"\begin{tabular}{crrrr}",
        r"\hline\hline",
        r"Post-reform TFP shock & $A_{\text{req}}$ & $\Delta Y$ & $\Delta\text{Inf}$ & $\Delta\text{CV}$ \\",
        r"$\delta$ (\%) & (\%) & (\%) & (pp) & (\%) \\",
        r"\hline",
    ]
    for r in results:
        delta_str = (r"\textbf{" + f"{r['delta_pct']:.1f}" + r"} (baseline)"
                     if r['delta_pct'] == 0 else f"{r['delta_pct']:.1f}")
        lines.append(
            f"{delta_str} & ${r['A_req_pct']:+.2f}$ & ${r['dY_pct']:+.2f}$ & "
            f"${r['dInf_pp']:+.3f}$ & ${r['dCV_pct']:+.2f}$ \\\\"
        )
    lines += [
        r"\hline\hline",
        r"\multicolumn{5}{l}{\footnotesize $\delta$ represents a post-reform contraction of TFP beyond the}\\",
        r"\multicolumn{5}{l}{\footnotesize mechanical effect of the hours cap. The $\delta = 0$ row reproduces}\\",
        r"\multicolumn{5}{l}{\footnotesize the main result of Table~\ref{tab:main_results}. Other rows show how}\\",
        r"\multicolumn{5}{l}{\footnotesize outcomes deteriorate if the reform itself depresses TFP by $\delta$.}\\",
        r"\end{tabular}",
        r"\end{table}",
    ]
    with open(OUT_TAB, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[OK] Saved LaTeX table to {OUT_TAB}")


if __name__ == "__main__":
    main()
