# -*- coding: utf-8 -*-
"""
Sensitivity analysis for the sectoral extension.
Varies sigma_sub and eta_I to check robustness.
"""

import csv
import os
import sys
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

from src.sectoral.model.sector_model import (
    load_sectoral_facts, load_national_targets,
    build_sector_params, run_sectoral_simulation
)


def run_sensitivity():
    data_final = os.path.join(PROJECT_ROOT, "data_final")
    output_dir = os.path.join(PROJECT_ROOT, "output", "sectoral", "tables")

    sectors = load_sectoral_facts(data_final)
    targets = load_national_targets(data_final)

    rows = []
    h1 = 36.0  # Focus on the main scenario

    # ── Sensitivity to sigma_sub ──
    print("=" * 60)
    print("SENSITIVITY: sigma_sub")
    print("=" * 60)

    sigma_values = [1.065, 1.15, 1.23]
    for sigma in sigma_values:
        print(f"\n  sigma_sub = {sigma}...")
        params, kappa = build_sector_params(sectors, targets,
                                             sigma_sub=sigma)
        res = run_sectoral_simulation(params, kappa, h1)

        row = {
            "parameter": "sigma_sub",
            "value": sigma,
            "areq_agriculture": res["sectors"]["agriculture"]["A_req_pct"],
            "areq_industry": res["sectors"]["industry"]["A_req_pct"],
            "areq_services": res["sectors"]["services"]["A_req_pct"],
            "areq_aggregate": res["aggregate"]["A_req_pct"],
            "dY_aggregate": res["aggregate"]["dY_pct"],
            "dCV_aggregate": res["aggregate"]["dCV_pct"],
        }
        rows.append(row)
        print(f"    A_req: agro={row['areq_agriculture']:.2f}%, "
              f"ind={row['areq_industry']:.2f}%, "
              f"serv={row['areq_services']:.2f}%, "
              f"agg={row['areq_aggregate']:.2f}%")

    # ── Sensitivity to eta_I ──
    print(f"\n{'='*60}")
    print("SENSITIVITY: eta_I")
    print("=" * 60)

    eta_values = [0.10, 0.15, 0.25]
    for eta_I in eta_values:
        print(f"\n  eta_I = {eta_I}...")
        # Override eta_I in targets
        targets_mod = dict(targets)
        targets_mod["ETA_I"] = eta_I
        params, kappa = build_sector_params(sectors, targets_mod)
        res = run_sectoral_simulation(params, kappa, h1)

        row = {
            "parameter": "eta_I",
            "value": eta_I,
            "areq_agriculture": res["sectors"]["agriculture"]["A_req_pct"],
            "areq_industry": res["sectors"]["industry"]["A_req_pct"],
            "areq_services": res["sectors"]["services"]["A_req_pct"],
            "areq_aggregate": res["aggregate"]["A_req_pct"],
            "dY_aggregate": res["aggregate"]["dY_pct"],
            "dCV_aggregate": res["aggregate"]["dCV_pct"],
        }
        rows.append(row)
        print(f"    A_req: agro={row['areq_agriculture']:.2f}%, "
              f"ind={row['areq_industry']:.2f}%, "
              f"serv={row['areq_services']:.2f}%, "
              f"agg={row['areq_aggregate']:.2f}%")

    # ── Sensitivity to uniform theta ──
    print(f"\n{'='*60}")
    print("SENSITIVITY: uniform theta (national for all sectors)")
    print("=" * 60)

    national_theta = np.array([
        targets["THETA_36"], targets["THETA_40"], targets["THETA_44"]
    ])
    sectors_uniform = {}
    for sname, sdata in sectors.items():
        sectors_uniform[sname] = {**sdata, "theta": national_theta}

    params, kappa = build_sector_params(sectors_uniform, targets)
    res = run_sectoral_simulation(params, kappa, h1)

    row = {
        "parameter": "uniform_theta",
        "value": "national",
        "areq_agriculture": res["sectors"]["agriculture"]["A_req_pct"],
        "areq_industry": res["sectors"]["industry"]["A_req_pct"],
        "areq_services": res["sectors"]["services"]["A_req_pct"],
        "areq_aggregate": res["aggregate"]["A_req_pct"],
        "dY_aggregate": res["aggregate"]["dY_pct"],
        "dCV_aggregate": res["aggregate"]["dCV_pct"],
    }
    rows.append(row)
    print(f"    A_req: agro={row['areq_agriculture']:.2f}%, "
          f"ind={row['areq_industry']:.2f}%, "
          f"serv={row['areq_services']:.2f}%, "
          f"agg={row['areq_aggregate']:.2f}%")

    # Save
    out_path = os.path.join(output_dir, "SECTOR_SENSITIVITY.csv")
    fieldnames = ["parameter", "value",
                   "areq_agriculture", "areq_industry", "areq_services",
                   "areq_aggregate", "dY_aggregate", "dCV_aggregate"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    run_sensitivity()
