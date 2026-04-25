# -*- coding: utf-8 -*-
"""
Run the sectoral model with empirical PNAD parameters and compare
with estimated-parameter results.
"""

import csv
import os
import sys
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

from src.sectoral.model.sector_model import (
    load_national_targets, build_sector_params, run_sectoral_simulation
)


def load_empirical_facts(data_final_path):
    """Load SECTORAL_PNAD_EMPIRICAL.csv into dict matching sector_model format."""
    emp_path = os.path.join(data_final_path, "SECTORAL_PNAD_EMPIRICAL.csv")
    orig_path = os.path.join(data_final_path, "SECTORAL_BASELINE_FACTS.csv")

    # Load empirical PNAD data
    empirical = {}
    with open(emp_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["sector"] != "NATIONAL":
                empirical[row["sector"]] = row

    # Load original for vab_share and yph (not available from PNAD)
    original = {}
    with open(orig_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            original[row["sector"]] = row

    N_total = 0.59  # employment rate from calibration

    sectors = {}
    for sname in ["agriculture", "industry", "services"]:
        emp = empirical[sname]
        orig = original[sname]
        lambda_s = float(emp["lambda_s"])
        inf_rate = float(emp["inf_rate"])
        N_s = lambda_s * N_total
        NF_s = N_s * (1 - inf_rate)
        NI_s = N_s * inf_rate

        sectors[sname] = {
            "name": orig["sector_name"],
            "lambda_s": lambda_s,
            "inf_rate": inf_rate,
            "N_s": N_s,
            "NF_s": NF_s,
            "NI_s": NI_s,
            "theta": np.array([
                float(emp["theta_36"]),
                float(emp["theta_40"]),
                float(emp["theta_44"]),
            ]),
            "vab_share": float(orig["vab_share"]),
            "yph": float(orig["yph_reais_per_hour"]),
        }

    return sectors


def main():
    data_final = os.path.join(PROJECT_ROOT, "data_final")
    output_dir = os.path.join(PROJECT_ROOT, "output", "sectoral", "tables")

    print("=" * 70)
    print("SECTORAL MODEL WITH EMPIRICAL PNAD PARAMETERS")
    print("=" * 70)

    # Load empirical data
    sectors = load_empirical_facts(data_final)
    targets = load_national_targets(data_final)

    print("\nEmpirical parameters (from PNAD Q4 2024):")
    for sname, sd in sectors.items():
        print(f"  {sname:12s}: lambda={sd['lambda_s']:.3f}, "
              f"inf={sd['inf_rate']:.1%}, "
              f"theta=[{sd['theta'][0]:.3f}, {sd['theta'][1]:.3f}, "
              f"{sd['theta'][2]:.3f}]")

    # Build sector parameters
    print("\nCalibrating sector parameters...")
    sector_params, kappa = build_sector_params(sectors, targets,
                                                sigma_sub=1.326, omega=0.622)

    # Run for both scenarios
    all_rows = []
    for h1 in [40.0, 36.0]:
        print(f"\n{'='*70}")
        print(f"SCENARIO: 44 -> {int(h1)} hours (EMPIRICAL)")
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

    # Save empirical results
    out_path = os.path.join(output_dir, "SECTOR_AREQ_EMPIRICAL.csv")
    fieldnames = ["h1", "sector", "lambda_s", "inf_target", "tau_s",
                   "A_req_pct", "dY_pct", "dInf_pp",
                   "Y_base", "Y_reform", "Y_share", "contribution_to_dY"]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nSaved: {out_path}")

    # ── Comparison: estimated vs empirical ──
    print(f"\n{'='*70}")
    print("COMPARISON: Estimated vs Empirical A_req")
    print(f"{'='*70}")

    est_path = os.path.join(output_dir, "SECTOR_AREQ_RESULTS.csv")
    estimated = {}
    with open(est_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (int(row["h1"]), row["sector"])
            estimated[key] = float(row["A_req_pct"])

    emp_results = {}
    for row in all_rows:
        key = (row["h1"], row["sector"])
        emp_results[key] = row["A_req_pct"]

    print(f"\n{'Scenario':>10s}  {'Sector':>12s}  {'Estimated':>10s}  "
          f"{'Empirical':>10s}  {'Diff':>8s}")
    print("-" * 60)

    for h1 in [40, 36]:
        for s in ["agriculture", "industry", "services", "AGGREGATE"]:
            key = (h1, s)
            if key in estimated and key in emp_results:
                est = estimated[key]
                emp = emp_results[key]
                diff = emp - est
                print(f"  44->{h1:2d}h  {s:>12s}  {est:>9.3f}%  "
                      f"{emp:>9.3f}%  {diff:>+7.3f}pp")
        print()

    print("DONE")


if __name__ == "__main__":
    main()
