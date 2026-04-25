# -*- coding: utf-8 -*-
"""
RED TEAM — Computational stress tests for the sectoral extension.

Tests each vulnerability identified in RED_TEAM_SECTORAL.md:
  RT1: Extreme theta swap (agriculture <-> services)
  RT2: Firm-size heterogeneity within sectors (3x2 = 6 groups)
  RT3: Agriculture informality sensitivity (40%, 50%, 60.7%)
  RT4: Equal K across sectors (K_s = 1/3 each)
  RT5: Sector-specific sigma (agro=0.80, ind=0.40, serv=0.60)
  RT6: Extreme sigma (1.5, 2.0) — "what would break"

Outputs: SECTOR_REDTEAM_RESULTS.csv
"""

import csv
import json
import os
import sys
import copy
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

from src.model.firm_problem import solve_NF
from src.model.efficiency import calibrate_kappa, formal_hours_avg
from src.model.calibration import calibrate_wedge, calibrate_pi_m, calibrate_psi
from src.model.welfare import compensating_variation
from src.sectoral.model.sector_model import (
    load_sectoral_facts, load_national_targets,
    build_sector_params, run_sectoral_simulation, _solve_Areq_multi
)


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


def run_single_test(sectors, targets, test_name, h1=36.0,
                    sigma_sub=1.15, omega=0.622, gamma_F=0.06):
    """Run one test configuration, return results dict."""
    try:
        params, kappa = build_sector_params(sectors, targets,
                                             sigma_sub=sigma_sub, omega=omega,
                                             gamma_F=gamma_F)
        res = run_sectoral_simulation(params, kappa, h1)

        row = {
            "test": test_name,
            "areq_agro": res["sectors"]["agriculture"]["A_req_pct"],
            "areq_ind": res["sectors"]["industry"]["A_req_pct"],
            "areq_serv": res["sectors"]["services"]["A_req_pct"],
            "areq_agg": res["aggregate"]["A_req_pct"],
            "dY_agg": res["aggregate"]["dY_pct"],
            "dCV_agg": res["aggregate"]["dCV_pct"],
            "spread_agro_ind": round(
                res["sectors"]["agriculture"]["A_req_pct"] -
                res["sectors"]["industry"]["A_req_pct"], 4),
            "ranking": _ranking(res),
            "status": "OK",
        }
    except Exception as e:
        row = {
            "test": test_name,
            "areq_agro": None, "areq_ind": None, "areq_serv": None,
            "areq_agg": None, "dY_agg": None, "dCV_agg": None,
            "spread_agro_ind": None,
            "ranking": "ERROR",
            "status": str(e)[:80],
        }
    return row


def _ranking(res):
    """Return sector ranking string by A_req."""
    secs = [(s, r["A_req_pct"]) for s, r in res["sectors"].items()]
    secs.sort(key=lambda x: -x[1])
    return " > ".join(f"{s[:4]}({a:.1f}%)" for s, a in secs)


def build_sector_params_heterogeneous_sigma(sectors, targets, sigma_by_sector,
                                              omega=0.622, gamma_F=0.06):
    """Like build_sector_params but with sector-specific sigma."""
    alpha = targets["ALPHA"]
    eta_I = targets["ETA_I"]
    e_q = targets["E_Q"]
    h0 = targets["H0"]
    h_star = targets["H_STAR"]
    hI = targets["HI"]

    national_theta = np.array([
        targets["THETA_36"], targets["THETA_40"], targets["THETA_44"]
    ])
    h_ref = formal_hours_avg(h0, national_theta)
    kappa = calibrate_kappa(h_ref, h_star, e_q)

    sector_params = {}
    for sname, sdata in sectors.items():
        N_s = sdata["N_s"]
        theta_s = sdata["theta"]
        inf_target = sdata["inf_rate"]
        K_s = sdata["vab_share"]
        sigma_s = sigma_by_sector[sname]
        NF_init = N_s * (1 - inf_target)

        pi_m_s = 0.0
        sol_w0 = solve_NF(N_s, h0, hI, 1.0, K_s, alpha, omega, sigma_s,
                          eta_I, kappa, h_star, 0.0, pi_m_s, 0.0,
                          NF_init, theta_s)
        if sol_w0["informality"] > inf_target + 1e-10:
            pi_m_s = calibrate_pi_m(inf_target, N_s, h0, hI,
                                     1.0, K_s, alpha, omega, sigma_s,
                                     eta_I, kappa, h_star, theta_s)

        tau_s = calibrate_wedge(inf_target, N_s, h0, hI,
                                1.0, K_s, alpha, omega, sigma_s,
                                eta_I, kappa, h_star, pi_m_s, theta_s)

        sector_params[sname] = {
            "A": 1.0, "K": K_s, "alpha": alpha,
            "omega": omega, "sigma_sub": sigma_s,
            "eta_I": eta_I, "kappa": kappa, "h_star": h_star,
            "h0": h0, "hI": hI,
            "N_total": N_s, "formal_wedge": tau_s,
            "pi_m": pi_m_s, "gamma_F": gamma_F,
            "NF_init": NF_init,
            "theta": theta_s,
            "inf_target": inf_target,
            "lambda_s": sdata["lambda_s"],
            "vab_share": sdata["vab_share"],
        }

    return sector_params, kappa


def run_all_tests():
    data_final = os.path.join(PROJECT_ROOT, "data_final")
    output_dir = os.path.join(PROJECT_ROOT, "output", "sectoral", "tables")

    sectors_orig = load_sectoral_facts(data_final)
    targets = load_national_targets(data_final)
    h1 = 36.0
    rows = []

    # ── BASELINE ──
    print("=" * 70)
    print("RED TEAM STRESS TESTS")
    print("=" * 70)
    print("\n[BASELINE] Original configuration...")
    rows.append(run_single_test(sectors_orig, targets, "BASELINE"))

    # ══════════════════════════════════════════════════════════════════════
    # RT1: Extreme theta — swap agriculture <-> services
    # ══════════════════════════════════════════════════════════════════════
    print("\n[RT1a] Theta swap: agriculture <-> services...")
    sectors_rt1a = copy.deepcopy(sectors_orig)
    theta_agro = sectors_rt1a["agriculture"]["theta"].copy()
    theta_serv = sectors_rt1a["services"]["theta"].copy()
    sectors_rt1a["agriculture"]["theta"] = theta_serv
    sectors_rt1a["services"]["theta"] = theta_agro
    rows.append(run_single_test(sectors_rt1a, targets, "RT1a_theta_swap"))

    # RT1b: All sectors have agriculture theta (extreme: all at 44h)
    print("[RT1b] All sectors have agriculture theta...")
    sectors_rt1b = copy.deepcopy(sectors_orig)
    for s in sectors_rt1b:
        sectors_rt1b[s]["theta"] = theta_agro.copy()
    rows.append(run_single_test(sectors_rt1b, targets, "RT1b_all_agro_theta"))

    # RT1c: All sectors have services theta (more part-time)
    print("[RT1c] All sectors have services theta...")
    sectors_rt1c = copy.deepcopy(sectors_orig)
    for s in sectors_rt1c:
        sectors_rt1c[s]["theta"] = theta_serv.copy()
    rows.append(run_single_test(sectors_rt1c, targets, "RT1c_all_serv_theta"))

    # ══════════════════════════════════════════════════════════════════════
    # RT2: Firm-size heterogeneity within sectors (3x2 = 6 groups)
    # ══════════════════════════════════════════════════════════════════════
    print("\n[RT2] Firm-size within sectors (small/large per sector)...")
    rows.append(_run_rt2_firmsize(sectors_orig, targets, h1))

    # ══════════════════════════════════════════════════════════════════════
    # RT3: Agriculture informality sensitivity
    # ══════════════════════════════════════════════════════════════════════
    print("\n[RT3a] Agriculture informality = 40%...")
    sectors_rt3a = copy.deepcopy(sectors_orig)
    sectors_rt3a["agriculture"]["inf_rate"] = 0.40
    sectors_rt3a["agriculture"]["NF_s"] = sectors_rt3a["agriculture"]["N_s"] * 0.60
    sectors_rt3a["agriculture"]["NI_s"] = sectors_rt3a["agriculture"]["N_s"] * 0.40
    rows.append(run_single_test(sectors_rt3a, targets, "RT3a_agro_inf_40pct"))

    print("[RT3b] Agriculture informality = 50%...")
    sectors_rt3b = copy.deepcopy(sectors_orig)
    sectors_rt3b["agriculture"]["inf_rate"] = 0.50
    sectors_rt3b["agriculture"]["NF_s"] = sectors_rt3b["agriculture"]["N_s"] * 0.50
    sectors_rt3b["agriculture"]["NI_s"] = sectors_rt3b["agriculture"]["N_s"] * 0.50
    rows.append(run_single_test(sectors_rt3b, targets, "RT3b_agro_inf_50pct"))

    print("[RT3c] Agriculture informality = 70%...")
    sectors_rt3c = copy.deepcopy(sectors_orig)
    sectors_rt3c["agriculture"]["inf_rate"] = 0.70
    sectors_rt3c["agriculture"]["NF_s"] = sectors_rt3c["agriculture"]["N_s"] * 0.30
    sectors_rt3c["agriculture"]["NI_s"] = sectors_rt3c["agriculture"]["N_s"] * 0.70
    rows.append(run_single_test(sectors_rt3c, targets, "RT3c_agro_inf_70pct"))

    # ══════════════════════════════════════════════════════════════════════
    # RT4: Equal K across sectors
    # ══════════════════════════════════════════════════════════════════════
    print("\n[RT4] Equal K (1/3 each)...")
    sectors_rt4 = copy.deepcopy(sectors_orig)
    for s in sectors_rt4:
        sectors_rt4[s]["vab_share"] = 1.0 / 3.0
    rows.append(run_single_test(sectors_rt4, targets, "RT4_equal_K"))

    # ══════════════════════════════════════════════════════════════════════
    # RT5: Sector-specific sigma
    # ══════════════════════════════════════════════════════════════════════
    print("\n[RT5a] Sector sigma: agro=0.80, ind=0.40, serv=0.60...")
    rows.append(_run_rt5_heterogeneous_sigma(
        sectors_orig, targets, h1,
        {"agriculture": 0.80, "industry": 0.40, "services": 0.60},
        "RT5a_sigma_hetero"))

    print("[RT5b] Sector sigma: agro=0.40, ind=0.80, serv=0.60 (inverted)...")
    rows.append(_run_rt5_heterogeneous_sigma(
        sectors_orig, targets, h1,
        {"agriculture": 0.40, "industry": 0.80, "services": 0.60},
        "RT5b_sigma_inverted"))

    # ══════════════════════════════════════════════════════════════════════
    # RT6: Extreme sigma (breaking point)
    # ══════════════════════════════════════════════════════════════════════
    print("\n[RT6a] sigma_sub = 1.50...")
    rows.append(run_single_test(sectors_orig, targets, "RT6a_sigma_1.5",
                                sigma_sub=1.50))

    print("[RT6b] sigma_sub = 2.00...")
    rows.append(run_single_test(sectors_orig, targets, "RT6b_sigma_2.0",
                                sigma_sub=2.00))

    print("[RT6c] sigma_sub = 0.20 (very low substitution)...")
    rows.append(run_single_test(sectors_orig, targets, "RT6c_sigma_0.2",
                                sigma_sub=0.20))

    # ══════════════════════════════════════════════════════════════════════
    # PRINT SUMMARY
    # ══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 100)
    print("RED TEAM RESULTS SUMMARY (44 -> 36h)")
    print("=" * 100)
    print(f"{'Test':<25s} | {'Agro':>7s} | {'Ind':>7s} | {'Serv':>7s} | "
          f"{'Agg':>7s} | {'Spread':>7s} | {'Ranking'}")
    print("-" * 100)
    for r in rows:
        if r["areq_agro"] is not None:
            print(f"{r['test']:<25s} | {r['areq_agro']:>6.2f}% | "
                  f"{r['areq_ind']:>6.2f}% | {r['areq_serv']:>6.2f}% | "
                  f"{r['areq_agg']:>6.2f}% | {r['spread_agro_ind']:>+6.2f} | "
                  f"{r['ranking']}")
        else:
            print(f"{r['test']:<25s} | {'ERROR':>7s} | {r['status']}")

    # Save
    out_path = os.path.join(output_dir, "SECTOR_REDTEAM_RESULTS.csv")
    fieldnames = ["test", "areq_agro", "areq_ind", "areq_serv",
                   "areq_agg", "dY_agg", "dCV_agg",
                   "spread_agro_ind", "ranking", "status"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved: {out_path}")

    return rows


def _run_rt2_firmsize(sectors_orig, targets, h1):
    """
    RT2: 3 sectors x 2 firm sizes = 6 groups.
    Each sector split into small (59%, inf_target_high) and large (41%, inf_target_low).
    """
    alpha = targets["ALPHA"]
    eta_I = targets["ETA_I"]
    e_q = targets["E_Q"]
    h0 = targets["H0"]
    h_star = targets["H_STAR"]
    hI = targets["HI"]

    national_theta = np.array([
        targets["THETA_36"], targets["THETA_40"], targets["THETA_44"]
    ])
    h_ref = formal_hours_avg(h0, national_theta)
    kappa = calibrate_kappa(h_ref, h_star, e_q)

    # Split each sector into small (59%) and large (41%)
    # Small firms: higher informality (+15pp), gamma_F=0.12
    # Large firms: lower informality (-15pp), gamma_F=0.03
    group_params = {}
    for sname, sdata in sectors_orig.items():
        for size, share, inf_adj, gamma_F, K_adj in [
            ("small", 0.59, +0.15, 0.12, 0.35),
            ("large", 0.41, -0.15, 0.03, 0.65)
        ]:
            gname = f"{sname}_{size}"
            inf_s = min(max(sdata["inf_rate"] + inf_adj, 0.05), 0.90)
            N_g = sdata["N_s"] * share
            K_g = sdata["vab_share"] * K_adj
            NF_init = N_g * (1 - inf_s)
            theta_s = sdata["theta"]

            pi_m_g = 0.0
            sol_w0 = solve_NF(N_g, h0, hI, 1.0, K_g, alpha, 0.80, 0.60,
                              eta_I, kappa, h_star, 0.0, 0.0, 0.0,
                              NF_init, theta_s)
            if sol_w0["informality"] > inf_s + 1e-10:
                pi_m_g = calibrate_pi_m(inf_s, N_g, h0, hI,
                                         1.0, K_g, alpha, 0.80, 0.60,
                                         eta_I, kappa, h_star, theta_s)

            tau_g = calibrate_wedge(inf_s, N_g, h0, hI,
                                    1.0, K_g, alpha, 0.80, 0.60,
                                    eta_I, kappa, h_star, pi_m_g, theta_s)

            group_params[gname] = {
                "A": 1.0, "K": K_g, "alpha": alpha,
                "omega": 0.80, "sigma_sub": 0.60,
                "eta_I": eta_I, "kappa": kappa, "h_star": h_star,
                "h0": h0, "hI": hI,
                "N_total": N_g, "formal_wedge": tau_g,
                "pi_m": pi_m_g, "gamma_F": gamma_F,
                "NF_init": NF_init,
                "theta": theta_s,
                "inf_target": inf_s,
                "lambda_s": sdata["lambda_s"] * share,
                "vab_share": sdata["vab_share"] * K_adj,
                "parent_sector": sname,
            }

    # Solve baseline
    N_total = sum(p["N_total"] for p in group_params.values())
    Y_base = 0.0
    C_base = 0.0
    hrs_base = 0.0
    NI_base = 0.0
    group_baselines = {}
    for gname, pars in group_params.items():
        sol = solve_NF(pars["N_total"], h0, hI, 1.0, pars["K"], alpha,
                       0.80, 0.60, eta_I, kappa, h_star,
                       pars["formal_wedge"], pars["pi_m"],
                       pars["gamma_F"], pars["NF_init"], pars["theta"])
        group_baselines[gname] = sol
        Y_base += sol["Y"]
        C_base += sol["C"]
        hrs_base += sol["hours_total"]
        NI_base += sol["NI"]

    # Solve reform
    Y_reform = 0.0
    C_reform = 0.0
    hrs_reform = 0.0
    NI_reform = 0.0
    for gname, pars in group_params.items():
        sol = solve_NF(pars["N_total"], h1, hI, 1.0, pars["K"], alpha,
                       0.80, 0.60, eta_I, kappa, h_star,
                       pars["formal_wedge"], pars["pi_m"],
                       pars["gamma_F"], pars["NF_init"], pars["theta"])
        Y_reform += sol["Y"]
        C_reform += sol["C"]
        hrs_reform += sol["hours_total"]
        NI_reform += sol["NI"]

    # A_req per parent sector
    sector_areqs = {}
    for parent in ["agriculture", "industry", "services"]:
        groups_s = {g: p for g, p in group_params.items()
                    if p["parent_sector"] == parent}
        Y_target_s = sum(group_baselines[g]["Y"] for g in groups_s)
        areq_s = _solve_Areq_multi_custom(groups_s, h1, Y_target_s, hI,
                                           alpha, eta_I, kappa, h_star)
        sector_areqs[parent] = areq_s

    # Aggregate A_req
    areq_agg = _solve_Areq_multi_custom(group_params, h1, Y_base, hI,
                                         alpha, eta_I, kappa, h_star)

    h_avg_base = hrs_base / N_total
    h_avg_reform = hrs_reform / N_total
    psi = calibrate_psi((1-alpha)*Y_base/(N_total*h_avg_base), h_avg_base, 2.0)
    dcv = compensating_variation(C_base/N_total, h_avg_base,
                                  C_reform/N_total, h_avg_reform, 2.0, psi)
    dY = (Y_reform / Y_base - 1) * 100

    spread = sector_areqs["agriculture"] - sector_areqs["industry"]
    secs = [(s, a) for s, a in sector_areqs.items()]
    secs.sort(key=lambda x: -x[1])
    ranking = " > ".join(f"{s[:4]}({a:.1f}%)" for s, a in secs)

    return {
        "test": "RT2_firmsize_3x2",
        "areq_agro": round(sector_areqs["agriculture"], 4),
        "areq_ind": round(sector_areqs["industry"], 4),
        "areq_serv": round(sector_areqs["services"], 4),
        "areq_agg": round(areq_agg, 4),
        "dY_agg": round(dY, 4),
        "dCV_agg": round(dcv * 100, 4),
        "spread_agro_ind": round(spread, 4),
        "ranking": ranking,
        "status": "OK",
    }


def _solve_Areq_multi_custom(groups, h1, Y_target, hI, alpha, eta_I,
                               kappa, h_star, grid=3001):
    """Multi-group A_req solver."""
    def Y_at(A_mult):
        total = 0.0
        for pars in groups.values():
            sol = solve_NF(
                pars["N_total"], h1, hI,
                pars["A"] * A_mult, pars["K"], alpha,
                pars["omega"], pars["sigma_sub"], eta_I,
                kappa, h_star,
                pars["formal_wedge"], pars["pi_m"],
                pars["gamma_F"], pars["NF_init"], pars["theta"], grid)
            total += sol["Y"]
        return total
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


def _run_rt5_heterogeneous_sigma(sectors_orig, targets, h1,
                                  sigma_by_sector, test_name):
    """RT5: sector-specific sigma."""
    try:
        params, kappa = build_sector_params_heterogeneous_sigma(
            sectors_orig, targets, sigma_by_sector)
        res = run_sectoral_simulation(params, kappa, h1)

        return {
            "test": test_name,
            "areq_agro": res["sectors"]["agriculture"]["A_req_pct"],
            "areq_ind": res["sectors"]["industry"]["A_req_pct"],
            "areq_serv": res["sectors"]["services"]["A_req_pct"],
            "areq_agg": res["aggregate"]["A_req_pct"],
            "dY_agg": res["aggregate"]["dY_pct"],
            "dCV_agg": res["aggregate"]["dCV_pct"],
            "spread_agro_ind": round(
                res["sectors"]["agriculture"]["A_req_pct"] -
                res["sectors"]["industry"]["A_req_pct"], 4),
            "ranking": _ranking(res),
            "status": "OK",
        }
    except Exception as e:
        return {
            "test": test_name,
            "areq_agro": None, "areq_ind": None, "areq_serv": None,
            "areq_agg": None, "dY_agg": None, "dCV_agg": None,
            "spread_agro_ind": None,
            "ranking": "ERROR",
            "status": str(e)[:80],
        }


if __name__ == "__main__":
    run_all_tests()
