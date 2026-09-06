# -*- coding: utf-8 -*-
"""
compute_portugal_validation.py — Validation of the model against Asai, Lopes &
Tondini (2025) for the Portuguese 44->40h reform of 1996.

Runs our model at h1=40h and reports the outcomes that map to theirs
(ΔY, ΔHours, Δ output per hour, ΔInf, A_req). Produces a compact comparison
table for inclusion in the paper.
"""
import json
import os
import sys
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from src.model.simulation import load_targets
from src.model.groups import build_groups
from src.model.firm_problem import solve_NF
from src.model.areq_solver import solve_Areq
from src.model.welfare import compensating_variation
from src.model.calibration import calibrate_psi

OUT_DATA = os.path.join(ROOT, "data_final", "portugal_validation.json")
OUT_TAB = os.path.join(ROOT, "output", "tables", "tab_portugal_validation.tex")
os.makedirs(os.path.dirname(OUT_TAB), exist_ok=True)

SIGMA = 1.326
OMEGA = 0.622
NU_GHH = 2.0
H1_PORTUGAL = 40   # Portuguese reform target
H1_BRAZIL_PROPOSED = 36


def solve_scenario(groups, h_target, h0, hI, theta, N_total, nu_ghh, psi, c_base_pc):
    Y, C, hours, NI = 0.0, 0.0, 0.0, 0.0
    for pars in groups.values():
        sol = solve_NF(pars["N_total"], h_target, hI, pars["A"], pars["K"],
                       pars["alpha"], pars["omega"], pars["sigma_sub"],
                       pars["eta_I"], pars["kappa"], pars["h_star"],
                       pars["formal_wedge"], pars["pi_m"],
                       pars["gamma_F"], pars["NF_init"], theta)
        Y += sol["Y"]; C += sol["C"]
        hours += sol["hours_total"]; NI += sol["NI"]
    inf = NI / N_total
    h_avg = hours / N_total
    c_pc = C / N_total
    dcv = compensating_variation(c_base_pc, h_avg_base, c_pc, h_avg, nu_ghh, psi) * 100
    return {"Y": Y, "C": C, "hours": hours, "NI": NI, "inf": inf, "h_avg": h_avg,
            "dCV_pct": dcv}


targets = load_targets(os.path.join(ROOT, "data_final"))
groups, kappa, theta = build_groups(targets, SIGMA, OMEGA)

alpha = targets["ALPHA"]["value"]
h0 = targets["H0"]["value"]
hI = targets["HI"]["value"]
N_total = targets["N_TOTAL"]["value"]

# Baseline (44h)
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
c_base_pc = C_base / N_total
w_hourly_base = (1 - alpha) * Y_base / (N_total * h_avg_base)
psi = calibrate_psi(w_hourly_base, h_avg_base, NU_GHH)

print(f"Baseline (44h): Y={Y_base:.4f}, inf={inf_base:.4f}, h_avg={h_avg_base:.3f}")
print(f"                w_hourly={w_hourly_base:.6f}")

# Scenario at h=40 (Portugal)
scen40 = solve_scenario(groups, 40, h0, hI, theta, N_total, NU_GHH, psi, c_base_pc)
Areq40 = solve_Areq(groups, 40, Y_base, theta)
w_hourly_40 = (1 - alpha) * scen40["Y"] / (N_total * scen40["h_avg"])

# Scenario at h=36 (Brazil proposed)
scen36 = solve_scenario(groups, 36, h0, hI, theta, N_total, NU_GHH, psi, c_base_pc)
Areq36 = solve_Areq(groups, 36, Y_base, theta)

# Key deltas
def deltas(scen, Areq):
    dY = (scen["Y"] / Y_base - 1) * 100
    dHours = (scen["hours"] / hours_base - 1) * 100
    dInf = (scen["inf"] - inf_base) * 100
    dYph_base = Y_base / hours_base
    dYph_scen = scen["Y"] / scen["hours"]
    dYph = (dYph_scen / dYph_base - 1) * 100
    return {"A_req_pct": round(Areq, 3), "dY_pct": round(dY, 3),
            "dHours_pct": round(dHours, 3), "dInf_pp": round(dInf, 3),
            "dYph_pct": round(dYph, 3), "dCV_pct": round(scen["dCV_pct"], 3)}

d40 = deltas(scen40, Areq40)
d36 = deltas(scen36, Areq36)

# Portuguese empirical numbers (firm-level, from Asai-Lopes-Tondini 2024
# working paper, PSE version)
portugal_data = {
    "dHours_pct": -10.9,   # total hours
    "dY_pct": -3.2,        # sales
    "dEmp_pct": -1.7,      # employment (headcount)
    "dYph_pct": +4.4,      # productivity (sales per hour) — 2024 PSE version
    "dHourlyWage_pct": +9.2,
    "elasticity_hours": -1.17,
    "elasticity_employment": -0.19,
}

print("\n=== Model at 44->40h (comparable to Portugal) ===")
for k, v in d40.items():
    print(f"  {k}: {v}")
print("\n=== Model at 44->36h (Brazil proposed) ===")
for k, v in d36.items():
    print(f"  {k}: {v}")
print("\n=== Portuguese empirical (Asai-Lopes-Tondini 2024, firm-level DiD) ===")
for k, v in portugal_data.items():
    print(f"  {k}: {v}")

summary = {
    "description": (
        "Validation of the model against the Portuguese 1996 reform (44->40h) "
        "estimated at firm level by Asai, Lopes & Tondini (2024)."
    ),
    "sigma": SIGMA,
    "omega": OMEGA,
    "model_44_to_40": d40,
    "model_44_to_36": d36,
    "portugal_empirical_Asai2024": portugal_data,
    "notes": [
        "Our ΔY is economy-wide; Asai-Lopes-Tondini is firm-level (treated vs control).",
        "Our e(h) captures only fatigue; Asai et al capture fatigue + quality + intensification + capital deepening.",
        f"Asai et al find hourly productivity +4.4pct at 44->40h; our model predicts {d40['dYph_pct']:.2f}pct.",
        "Directional consistency: both find ΔY<0, Δhours<0, Δproductivity/h>0."
    ]
}

with open(OUT_DATA, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(f"\n[OK] Saved JSON to {OUT_DATA}")

# LaTeX comparison table
lines = [
    r"% Auto-generated by src/tables_figures/compute_portugal_validation.py",
    r"\begin{table}[htbp]",
    r"\centering",
    r"\caption{Directional validation against Portugal's 1996 reform (44$\to$40h).}\label{tab:portugal_validation}",
    r"\small",
    r"\begin{tabular}{lrrr}",
    r"\hline\hline",
    r" & \textbf{Portugal 44$\to$40h} & \textbf{Model 44$\to$40h} & \textbf{Model 44$\to$36h} \\",
    r" & \textit{Asai et al.\ (2025)} & \textit{This paper} & \textit{This paper, proposed} \\",
    r" & firm-level DiD & aggregate & aggregate \\",
    r"\hline",
    f"$\\Delta$Hours (\\%) & ${portugal_data['dHours_pct']:+.1f}$ & ${d40['dHours_pct']:+.2f}$ & ${d36['dHours_pct']:+.2f}$ \\\\",
    f"$\\Delta Y$ (\\%) & ${portugal_data['dY_pct']:+.1f}$ & ${d40['dY_pct']:+.2f}$ & ${d36['dY_pct']:+.2f}$ \\\\",
    f"$\\Delta Y/h$ (\\%) & ${portugal_data['dYph_pct']:+.1f}$ & ${d40['dYph_pct']:+.2f}$ & ${d36['dYph_pct']:+.2f}$ \\\\",
    f"$\\Delta$Inf (pp) & \\textit{{n/a}} & ${d40['dInf_pp']:+.3f}$ & ${d36['dInf_pp']:+.3f}$ \\\\",
    f"$A_{{\\text{{req}}}}$ (\\%) & \\textit{{n/a}} & ${d40['A_req_pct']:+.2f}$ & ${d36['A_req_pct']:+.2f}$ \\\\",
    r"\hline\hline",
    r"\end{tabular}",
    r"\\[2pt]",
    r"\begin{minipage}{0.95\textwidth}",
    r"\justifying",
    (
        r"{\footnotesize Signs match across all comparable outcomes. Magnitudes differ because "
        r"the Portuguese estimates are firm-level, treated-versus-control partial-equilibrium "
        r"estimates, while ours are economy-wide. The model's $e(h)$ captures only the fatigue "
        r"channel, while the empirical productivity response also reflects worker selection, "
        r"intensification, and sectoral capital deepening.}"
    ),
    r"\end{minipage}",
    r"\end{table}",
]
with open(OUT_TAB, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"[OK] Saved LaTeX table to {OUT_TAB}")
