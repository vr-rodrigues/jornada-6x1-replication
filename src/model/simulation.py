# -*- coding: utf-8 -*-
"""Full simulation loop: baseline -> reform -> A_req -> welfare."""

import csv
import json
import os
import hashlib
import datetime
import numpy as np

from .production import production
from .efficiency import eff, formal_hours_avg, calibrate_kappa
from .firm_problem import solve_NF
from .calibration import calibrate_psi
from .areq_solver import solve_Areq
from .welfare import compensating_variation
from .groups import build_groups


def load_targets(data_final_path):
    """Load calibration_targets.csv into dict."""
    path = os.path.join(data_final_path, "calibration_targets.csv")
    targets = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            targets[row["target_id"]] = {
                "value": float(row["value"]),
                "source": row["source"],
                "notes": row.get("notes", "")
            }
    return targets


def run_simulation(targets, sigma_sub=1.15, omega=0.622, theta=None,
                   group_specs=None):
    """
    Run full calibration + simulation pipeline.

    Returns dict with all results: baseline, reform, A_req, welfare.
    """
    alpha = targets["ALPHA"]["value"]
    h0 = targets["H0"]["value"]
    h1 = targets["H1"]["value"]
    hI = targets["HI"]["value"]
    N_total = targets["N_TOTAL"]["value"]
    nu_ghh = 2.0

    if theta is None:
        theta = np.array([
            targets["THETA_36"]["value"],
            targets["THETA_40"]["value"],
            targets["THETA_44"]["value"],
        ])

    # Build and calibrate groups
    groups, kappa, theta = build_groups(targets, sigma_sub, omega,
                                        group_specs, theta)

    # Solve baseline
    Y_base = 0.0; C_base = 0.0; hrs_base = 0.0; NI_base = 0.0
    baseline_solutions = {}
    for gname, pars in groups.items():
        sol = solve_NF(pars["N_total"], h0, hI, pars["A"], pars["K"],
                       pars["alpha"], pars["omega"], pars["sigma_sub"],
                       pars["eta_I"], pars["kappa"], pars["h_star"],
                       pars["formal_wedge"], pars["pi_m"],
                       pars["gamma_F"], pars["NF_init"], theta)
        baseline_solutions[gname] = sol
        Y_base += sol["Y"]; C_base += sol["C"]
        hrs_base += sol["hours_total"]; NI_base += sol["NI"]

    inf_base = NI_base / N_total
    h_avg_base = hrs_base / N_total

    # Calibrate psi
    w_hourly = (1 - alpha) * Y_base / (N_total * h_avg_base)
    psi = calibrate_psi(w_hourly, h_avg_base, nu_ghh)

    # Solve reform (h0 -> h1, no TFP gain)
    Y_cap = 0.0; C_cap = 0.0; hrs_cap = 0.0; NI_cap = 0.0
    for gname, pars in groups.items():
        sol = solve_NF(pars["N_total"], h1, hI, pars["A"], pars["K"],
                       pars["alpha"], pars["omega"], pars["sigma_sub"],
                       pars["eta_I"], pars["kappa"], pars["h_star"],
                       pars["formal_wedge"], pars["pi_m"],
                       pars["gamma_F"], pars["NF_init"], theta)
        Y_cap += sol["Y"]; C_cap += sol["C"]
        hrs_cap += sol["hours_total"]; NI_cap += sol["NI"]

    inf_cap = NI_cap / N_total
    h_avg_cap = hrs_cap / N_total

    dY = (Y_cap / Y_base - 1) * 100
    dInf = (inf_cap - inf_base) * 100
    Yph_base = Y_base / hrs_base
    Yph_cap = Y_cap / hrs_cap
    dYph = (Yph_cap / Yph_base - 1) * 100

    # A_req
    Areq = solve_Areq(groups, h1, Y_base, theta)

    # Welfare
    c_base_pc = C_base / N_total
    c_cap_pc = C_cap / N_total
    dcv = compensating_variation(c_base_pc, h_avg_base, c_cap_pc, h_avg_cap,
                                 nu_ghh, psi)

    return {
        "sigma_sub": sigma_sub,
        "omega": omega,
        "kappa": kappa,
        "psi": psi,
        "groups": groups,
        "baseline": {
            "Y": Y_base, "C": C_base, "hours": hrs_base,
            "inf": inf_base, "h_avg": h_avg_base,
            "solutions": baseline_solutions,
        },
        "reform": {
            "Y": Y_cap, "C": C_cap, "hours": hrs_cap,
            "inf": inf_cap, "h_avg": h_avg_cap,
        },
        "results": {
            "A_req_pct": round(Areq, 4),
            "dY_pct": round(dY, 4),
            "dInf_pp": round(dInf, 4),
            "dCV_pct": round(dcv * 100, 4),
            "dYph_pct": round(dYph, 4),
            "wage_premium_implied": None,  # computed separately if needed
        },
    }


def welfare_schedule(targets, groups, Y_base, C_base_pc, h_avg_base,
                     inf_base, N_total, theta, nu_ghh=2.0, psi=None,
                     h_range=range(44, 29, -1)):
    """Compute welfare metrics for a range of hours caps."""
    hI = targets["HI"]["value"]
    rows = []
    for h_target in h_range:
        Y_t = 0.0; C_t = 0.0; hrs_t = 0.0; NI_t = 0.0
        for pars in groups.values():
            sol = solve_NF(pars["N_total"], h_target, hI, pars["A"], pars["K"],
                           pars["alpha"], pars["omega"], pars["sigma_sub"],
                           pars["eta_I"], pars["kappa"], pars["h_star"],
                           pars["formal_wedge"], pars["pi_m"],
                           pars["gamma_F"], pars["NF_init"], theta)
            Y_t += sol["Y"]; C_t += sol["C"]
            hrs_t += sol["hours_total"]; NI_t += sol["NI"]

        Areq_t = solve_Areq(groups, h_target, Y_base, theta)
        dY_t = (Y_t / Y_base - 1) * 100
        h_avg_t = hrs_t / N_total
        c_pc_t = C_t / N_total
        dcv_t = compensating_variation(C_base_pc, h_avg_base, c_pc_t, h_avg_t,
                                        nu_ghh, psi)
        dInf_t = (NI_t / N_total - inf_base) * 100

        rows.append({
            "h1": h_target,
            "A_req_pct": round(Areq_t, 4),
            "dY_pct": round(dY_t, 4),
            "dCV_pct": round(dcv_t * 100, 4),
            "dInf_pp": round(dInf_t, 4),
        })
    return rows
