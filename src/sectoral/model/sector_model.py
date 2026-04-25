# -*- coding: utf-8 -*-
"""
Sectoral extension: 3-sector model (agriculture, industry, services).

Each sector is a standalone instance of the national model with:
  - Sector-specific: lambda_s, inf_rate_s, theta_s, K_s, tau_s
  - Common: alpha, sigma_sub, omega, eta_I, kappa, h*, nu, sigma_ghh

Y = sum_s Y_s (no cross-sector terms, no mobility)
A_req solved per sector and in aggregate.
"""

import csv
import json
import os
import sys
import numpy as np

# Add the project root to path so we can import the national model
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

from src.model.production import production
from src.model.ces_aggregator import ces_agg
from src.model.efficiency import (eff, calibrate_kappa, formal_hours_avg,
                                   formal_hours_hetero)
from src.model.firm_problem import solve_NF
from src.model.calibration import calibrate_wedge, calibrate_pi_m, calibrate_psi
from src.model.areq_solver import solve_Areq
from src.model.welfare import compensating_variation


# ── Load sector data ───────────────────────────────────────────────────────

def load_sectoral_facts(data_final_path):
    """Load SECTORAL_BASELINE_FACTS.csv into dict keyed by sector name."""
    path = os.path.join(data_final_path, "SECTORAL_BASELINE_FACTS.csv")
    sectors = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sectors[row["sector"]] = {
                "name": row["sector_name"],
                "lambda_s": float(row["lambda_s"]),
                "inf_rate": float(row["inf_rate"]),
                "N_s": float(row["N_s"]),
                "NF_s": float(row["NF_s"]),
                "NI_s": float(row["NI_s"]),
                "theta": np.array([
                    float(row["theta_36"]),
                    float(row["theta_40"]),
                    float(row["theta_44"]),
                ]),
                "vab_share": float(row["vab_share"]),
                "yph": float(row["yph_reais_per_hour"]),
            }
    return sectors


def load_national_targets(data_final_path):
    """Load calibration_targets.csv for common parameters."""
    path = os.path.join(data_final_path, "calibration_targets.csv")
    targets = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            targets[row["target_id"]] = float(row["value"])
    return targets


# ── Build sector parameter dicts ───────────────────────────────────────────

def build_sector_params(sectors, targets, sigma_sub=1.15, omega=0.622,
                        gamma_F=0.06):
    """
    Build calibrated parameter dict for each sector.

    Each sector gets:
      - N_total_s from employment data
      - K_s proportional to VAB share
      - theta_s from sectoral hours distribution
      - tau_s calibrated to match sectoral informality
      - pi_m_s calibrated if needed (wedge=0 too much informality)

    Args:
        sectors: dict from load_sectoral_facts()
        targets: dict from load_national_targets()
        sigma_sub: CES substitution elasticity (common)
        omega: CES formal weight (common)
        gamma_F: adjustment cost (common, blended national average)

    Returns:
        sector_params: dict of sector -> parameter dict (compatible with solve_NF)
        kappa: calibrated kappa (common)
    """
    alpha = targets["ALPHA"]
    eta_I = targets["ETA_I"]
    e_q = targets["E_Q"]
    h0 = targets["H0"]
    h_star = targets["H_STAR"]
    hI = targets["HI"]

    # Calibrate kappa from national aggregate theta (for consistency)
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

        # K_s proportional to VAB share (normalized so sum K_s = 1)
        K_s = sdata["vab_share"]

        # A_s = 1.0 (baseline TFP, same for all sectors)
        A_s = 1.0

        # NF_init: starting point for firm problem
        NF_init = N_s * (1 - inf_target)

        # Calibrate pi_m if wedge=0 gives too much informality
        pi_m_s = 0.0
        sol_w0 = solve_NF(N_s, h0, hI, A_s, K_s, alpha, omega, sigma_sub,
                          eta_I, kappa, h_star, 0.0, pi_m_s, 0.0,
                          NF_init, theta_s)
        if sol_w0["informality"] > inf_target + 1e-10:
            pi_m_s = calibrate_pi_m(inf_target, N_s, h0, hI,
                                     A_s, K_s, alpha, omega, sigma_sub,
                                     eta_I, kappa, h_star, theta_s)

        # Calibrate tau_s to match sector informality
        tau_s = calibrate_wedge(inf_target, N_s, h0, hI,
                                A_s, K_s, alpha, omega, sigma_sub,
                                eta_I, kappa, h_star, pi_m_s, theta_s)

        sector_params[sname] = {
            "A": A_s, "K": K_s, "alpha": alpha,
            "omega": omega, "sigma_sub": sigma_sub,
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

        print(f"  {sname:12s}: N={N_s:.4f}, K={K_s:.4f}, "
              f"inf_target={inf_target:.1%}, tau={tau_s:.4f}, "
              f"pi_m={pi_m_s:.4f}")

    return sector_params, kappa


# ── Run simulation ─────────────────────────────────────────────────────────

def run_sectoral_simulation(sector_params, kappa, h1, N_total=0.59,
                            nu_ghh=2.0):
    """
    Run the full sectoral simulation: baseline -> reform -> A_req -> welfare.

    Returns dict with per-sector and aggregate results.
    """
    alpha = list(sector_params.values())[0]["alpha"]

    # ── Baseline ──
    Y_base = 0.0
    C_base = 0.0
    hrs_base = 0.0
    NI_base = 0.0
    sector_baselines = {}

    for sname, pars in sector_params.items():
        sol = solve_NF(pars["N_total"], pars["h0"], pars["hI"],
                       pars["A"], pars["K"], pars["alpha"],
                       pars["omega"], pars["sigma_sub"], pars["eta_I"],
                       pars["kappa"], pars["h_star"],
                       pars["formal_wedge"], pars["pi_m"],
                       pars["gamma_F"], pars["NF_init"], pars["theta"])
        sector_baselines[sname] = sol
        Y_base += sol["Y"]
        C_base += sol["C"]
        hrs_base += sol["hours_total"]
        NI_base += sol["NI"]

    inf_base = NI_base / N_total
    h_avg_base = hrs_base / N_total

    # Calibrate psi from aggregate baseline
    w_hourly = (1 - alpha) * Y_base / (N_total * h_avg_base)
    psi = calibrate_psi(w_hourly, h_avg_base, nu_ghh)

    # ── Reform (h0 -> h1, no TFP gain) ──
    Y_reform = 0.0
    C_reform = 0.0
    hrs_reform = 0.0
    NI_reform = 0.0
    sector_reforms = {}

    for sname, pars in sector_params.items():
        sol = solve_NF(pars["N_total"], h1, pars["hI"],
                       pars["A"], pars["K"], pars["alpha"],
                       pars["omega"], pars["sigma_sub"], pars["eta_I"],
                       pars["kappa"], pars["h_star"],
                       pars["formal_wedge"], pars["pi_m"],
                       pars["gamma_F"], pars["NF_init"], pars["theta"])
        sector_reforms[sname] = sol
        Y_reform += sol["Y"]
        C_reform += sol["C"]
        hrs_reform += sol["hours_total"]
        NI_reform += sol["NI"]

    inf_reform = NI_reform / N_total
    h_avg_reform = hrs_reform / N_total

    # ── A_req per sector ──
    sector_areq = {}
    for sname, pars in sector_params.items():
        # Wrap single sector as a "group" dict for solve_Areq
        group = {sname: pars}
        Y_target_s = sector_baselines[sname]["Y"]
        areq_s = solve_Areq(group, h1, Y_target_s, pars["theta"])
        sector_areq[sname] = areq_s

    # ── Aggregate A_req (all sectors together) ──
    areq_agg = solve_Areq(sector_params, h1, Y_base,
                          list(sector_params.values())[0]["theta"])
    # Note: solve_Areq uses the theta from the first sector for capping.
    # For aggregate A_req, we need a custom solver that respects each sector's theta.
    areq_agg = _solve_Areq_multi(sector_params, h1, Y_base)

    # ── Welfare ──
    c_base_pc = C_base / N_total
    c_reform_pc = C_reform / N_total
    dcv = compensating_variation(c_base_pc, h_avg_base,
                                  c_reform_pc, h_avg_reform,
                                  nu_ghh, psi)

    # ── Aggregate results ──
    dY = (Y_reform / Y_base - 1) * 100
    dInf = (inf_reform - inf_base) * 100

    results = {
        "aggregate": {
            "Y_base": Y_base, "Y_reform": Y_reform,
            "dY_pct": round(dY, 4),
            "inf_base": round(inf_base, 4),
            "inf_reform": round(inf_reform, 4),
            "dInf_pp": round(dInf, 4),
            "h_avg_base": round(h_avg_base, 4),
            "h_avg_reform": round(h_avg_reform, 4),
            "A_req_pct": round(areq_agg, 4),
            "dCV_pct": round(dcv * 100, 4),
            "psi": psi,
        },
        "sectors": {},
    }

    for sname in sector_params:
        base = sector_baselines[sname]
        ref = sector_reforms[sname]
        pars = sector_params[sname]
        dY_s = (ref["Y"] / base["Y"] - 1) * 100
        dInf_s = (ref["informality"] - base["informality"]) * 100

        results["sectors"][sname] = {
            "lambda_s": pars["lambda_s"],
            "inf_target": pars["inf_target"],
            "tau_s": pars["formal_wedge"],
            "pi_m": pars["pi_m"],
            "Y_base": base["Y"],
            "Y_reform": ref["Y"],
            "dY_pct": round(dY_s, 4),
            "inf_base": round(base["informality"], 4),
            "inf_reform": round(ref["informality"], 4),
            "dInf_pp": round(dInf_s, 4),
            "A_req_pct": round(sector_areq[sname], 4),
            "Y_share_of_total": round(base["Y"] / Y_base, 4),
            "contribution_to_dY": round(
                (ref["Y"] - base["Y"]) / Y_base * 100, 4),
        }

    return results


def _solve_Areq_multi(sector_params, h1, Y_target, grid=3001):
    """
    Solve aggregate A_req when each sector has its own theta.
    Finds A_mult such that sum_s Y_s(A_s*A_mult, h1) = Y_target.
    """
    def Y_at(A_mult):
        total = 0.0
        for pars in sector_params.values():
            sol = solve_NF(
                pars["N_total"], h1, pars["hI"],
                pars["A"] * A_mult, pars["K"], pars["alpha"],
                pars["omega"], pars["sigma_sub"], pars["eta_I"],
                pars["kappa"], pars["h_star"],
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


# ── Main entry point ──────────────────────────────────────────────────────

def main():
    """Run the sectoral model for both reform scenarios (44->40 and 44->36)."""
    data_final = os.path.join(PROJECT_ROOT, "data_final")
    output_dir = os.path.join(PROJECT_ROOT, "output", "sectoral", "tables")
    os.makedirs(output_dir, exist_ok=True)

    # Load data
    print("=" * 70)
    print("SECTORAL MODEL — 3-Sector Extension")
    print("=" * 70)

    print("\nLoading data...")
    sectors = load_sectoral_facts(data_final)
    targets = load_national_targets(data_final)

    # Build sector parameters
    print("\nCalibrating sector parameters...")
    sector_params, kappa = build_sector_params(sectors, targets,
                                                sigma_sub=1.15, omega=0.622)

    # Run for both scenarios
    all_rows = []
    for h1 in [40.0, 36.0]:
        print(f"\n{'='*70}")
        print(f"SCENARIO: 44 -> {int(h1)} hours")
        print(f"{'='*70}")

        results = run_sectoral_simulation(sector_params, kappa, h1)

        print(f"\n  Aggregate: A_req={results['aggregate']['A_req_pct']:.3f}%, "
              f"dY={results['aggregate']['dY_pct']:.3f}%, "
              f"dInf={results['aggregate']['dInf_pp']:.3f}pp, "
              f"dCV={results['aggregate']['dCV_pct']:.3f}%")

        for sname, sr in results["sectors"].items():
            print(f"  {sname:12s}: A_req={sr['A_req_pct']:.3f}%, "
                  f"dY={sr['dY_pct']:.3f}%, "
                  f"dInf={sr['dInf_pp']:.3f}pp, "
                  f"Y_share={sr['Y_share_of_total']:.1%}")

            all_rows.append({
                "h1": int(h1),
                "sector": sname,
                "lambda_s": sr["lambda_s"],
                "inf_target": sr["inf_target"],
                "tau_s": round(sr["tau_s"], 4),
                "A_req_pct": sr["A_req_pct"],
                "dY_pct": sr["dY_pct"],
                "dInf_pp": sr["dInf_pp"],
                "Y_base": round(sr["Y_base"], 6),
                "Y_reform": round(sr["Y_reform"], 6),
                "Y_share": sr["Y_share_of_total"],
                "contribution_to_dY": sr["contribution_to_dY"],
            })

        # Add aggregate row
        agg = results["aggregate"]
        all_rows.append({
            "h1": int(h1),
            "sector": "AGGREGATE",
            "lambda_s": 1.0,
            "inf_target": round(agg["inf_base"], 4),
            "tau_s": "",
            "A_req_pct": agg["A_req_pct"],
            "dY_pct": agg["dY_pct"],
            "dInf_pp": agg["dInf_pp"],
            "Y_base": round(agg["Y_base"], 6),
            "Y_reform": round(agg["Y_reform"], 6),
            "Y_share": 1.0,
            "contribution_to_dY": agg["dY_pct"],
        })

    # Save results
    out_path = os.path.join(output_dir, "SECTOR_AREQ_RESULTS.csv")
    fieldnames = ["h1", "sector", "lambda_s", "inf_target", "tau_s",
                   "A_req_pct", "dY_pct", "dInf_pp",
                   "Y_base", "Y_reform", "Y_share", "contribution_to_dY"]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nSaved: {out_path}")

    # Save full results as JSON for downstream use
    json_path = os.path.join(output_dir, "SECTOR_RESULTS_FULL.json")
    with open(json_path, "w", encoding="utf-8") as f:
        # Convert numpy to native Python for JSON
        def convert(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, (np.float64, np.float32)):
                return float(obj)
            if isinstance(obj, (np.int64, np.int32)):
                return int(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        json.dump({
            "kappa": kappa,
            "sigma_sub": 1.15,
            "omega": 0.622,
            "sector_params": {
                s: {k: v for k, v in p.items()}
                for s, p in sector_params.items()
            },
        }, f, indent=2, default=convert)

    print(f"Saved: {json_path}")
    print("\nDONE")


if __name__ == "__main__":
    main()
