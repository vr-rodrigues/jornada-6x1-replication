# -*- coding: utf-8 -*-
"""
clean_and_merge.py — Merge all data sources into calibration_targets.csv

Reads:
  - data_intermediate/pnad_targets.json (SIDRA/IBGE)
  - data_intermediate/pwt_targets.json (PWT 10.01)
  - data_intermediate/rais_targets.json (RAIS/CAGED)

Produces:
  - data_final/calibration_targets.csv (all calibration targets with provenance)
"""

import json
import os
import sys
import csv
import hashlib
import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Paths
# ============================================================
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INTERMEDIATE_DIR = os.path.join(PROJECT_ROOT, "data_intermediate")
FINAL_DIR = os.path.join(PROJECT_ROOT, "data_final")
os.makedirs(FINAL_DIR, exist_ok=True)


def load_json(filename):
    path = os.path.join(INTERMEDIATE_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    print("=" * 60)
    print("CLEAN AND MERGE -- calibration_targets.csv")
    print("=" * 60)

    # Load all sources
    pnad = load_json("pnad_targets.json")
    pwt = load_json("pwt_targets.json")
    rais = load_json("rais_targets.json")

    # ================================================================
    # Build calibration targets
    # ================================================================
    targets = []

    def add(target_id, name, value, unit, source, variable, notes=""):
        targets.append({
            "target_id": target_id,
            "name": name,
            "value": value,
            "unit": unit,
            "source": source,
            "variable": variable,
            "notes": notes
        })

    # --- From PNAD: Informality ---
    inf = pnad.get("informality_rate", {})
    inf_rate = inf.get("avg_last_4_quarters") or inf.get("latest_quarter_value")
    add("INF_AGG", "Informality rate (aggregate)",
        inf_rate / 100 if inf_rate else 0.376,
        "proportion", "PNAD Continua Trimestral, Tabela 4093, IBGE",
        "Taxa de informalidade (v12466)",
        f"Avg last 4 quarters: {inf.get('avg_last_4_quarters')}%; Latest: {inf.get('latest_quarter_value')}%")

    # --- From RAIS: Informality by firm size ---
    inf_by_size = rais.get("informality_by_size", {})
    add("INF_SMALL", "Informality rate (small firms, <=49 employees)",
        inf_by_size.get("small_le49_informality", 0.50),
        "proportion", "PNAD Continua / RAIS cross-reference",
        "Estimated from position in occupation x firm size",
        "Target for wedge calibration (tau_S)")

    add("INF_LARGE", "Informality rate (large firms, 50+ employees)",
        inf_by_size.get("large_ge50_informality", 0.20),
        "proportion", "PNAD Continua / RAIS cross-reference",
        "Estimated from position in occupation x firm size",
        "Target for wedge calibration (tau_L)")

    # --- From RAIS: Employment share by firm size ---
    add("SHARE_SMALL", "Small firms employment share (formal sector)",
        rais.get("small_le49_share_formal", 0.59),
        "proportion", "RAIS 2022, Ministerio do Trabalho",
        "Share of formal employment in firms with <=49 employees",
        "RAIS-based, formal employment only (not PNAD all-workers)")

    add("SHARE_LARGE", "Large firms employment share (formal sector)",
        rais.get("large_ge50_share_formal", 0.41),
        "proportion", "RAIS 2022, Ministerio do Trabalho",
        "Share of formal employment in firms with 50+ employees",
        "Complement of SHARE_SMALL")

    # --- From RAIS: Formal cost wedge ---
    cost = rais.get("formal_cost_wedge", {})
    add("GAMMA_F_SMALL", "Formal cost wedge (small firms)",
        cost.get("gamma_F_small", 0.12),
        "proportion", "CLT/FGTS legislation + calibration",
        "Effective marginal cost of formalization for small firms",
        "Calibrated to reproduce INF_SMALL via wedge bisection")

    add("GAMMA_F_LARGE", "Formal cost wedge (large firms)",
        cost.get("gamma_F_large", 0.03),
        "proportion", "CLT/FGTS legislation + calibration",
        "Effective marginal cost of formalization for large firms",
        "Calibrated to reproduce INF_LARGE via wedge bisection")

    # --- From PWT: Capital share ---
    add("ALPHA", "Capital share (Gollin-adjusted)",
        pwt.get("alpha_gollin_adjusted", 0.35),
        "proportion", "PWT 10.01 + Gollin (2002, JPE)",
        f"labsh_raw={pwt.get('labsh_latest', 0.578)}, alpha_raw={pwt.get('alpha_pwt_raw', 0.422)}",
        "Gollin correction for self-employment income")

    add("LABSH_RAW", "Labor share (PWT raw)",
        pwt.get("labsh_latest", 0.578),
        "proportion", f"PWT 10.01, Brazil, {pwt.get('labsh_year', 2019)}",
        "labsh variable from PWT",
        "Before Gollin adjustment")

    # --- Hours distribution (from DIEESE, hardcoded in legacy) ---
    add("THETA_36", "Hours bin weight: <=36h workers",
        0.085, "proportion",
        "DIEESE Tabela 7 / PNAD Continua",
        "Share of formal workers in <=36h bin",
        "Mapped from DIEESE <=39h category")

    add("THETA_40", "Hours bin weight: 40h workers",
        0.269, "proportion",
        "DIEESE Tabela 7 / PNAD Continua",
        "Share of formal workers in 40h bin",
        "Mapped from DIEESE 40h category")

    add("THETA_44", "Hours bin weight: >=41h workers",
        0.646, "proportion",
        "DIEESE Tabela 7 / PNAD Continua",
        "Share of formal workers in >=41h (44h) bin",
        "Mapped from DIEESE >=41h category")

    # --- External parameters ---
    add("ETA_I", "Relative efficiency of informal labor",
        0.60, "proportion",
        "Literature: La Porta & Shleifer (2014), Ulyssea (2018)",
        "Productivity gap formal vs informal",
        "Standard in Brazilian informality literature")

    add("E_Q", "Hours-output elasticity at h_ref",
        0.60, "elasticity",
        "Pencavel (2015, Economic Journal)",
        "Elasticity of output w.r.t. hours at reference formal hours",
        "d ln(h*e(h))/d ln(h) at h_ref=42.24")

    add("N_TOTAL", "Total employment (normalized)",
        0.590, "normalized",
        "PNAD Continua, employment-to-population ratio",
        "Baseline total employment (formal+informal), normalized",
        "Approximate employment-to-population ratio for working-age")

    # --- Model parameters (not from data, but documented) ---
    add("H0", "Baseline weekly hours cap (formal)",
        44.0, "hours/week", "CLT Art. 58",
        "Legal maximum weekly hours in Brazil (pre-reform)",
        "Statutory limit")

    add("H1", "Reform weekly hours cap",
        36.0, "hours/week", "PEC 6x1 proposal",
        "Proposed new maximum weekly hours",
        "Main policy counterfactual")

    add("H_STAR", "Peak-efficiency hours",
        40.0, "hours/week", "Pencavel (2015), Collewet & Sauermann (2017)",
        "Hours at which per-hour efficiency is maximized",
        "Consistent with international evidence")

    add("HI", "Informal sector hours",
        44.0, "hours/week", "Model assumption",
        "Hours worked by informal workers (not subject to cap)",
        "Assumption: informals work the pre-reform maximum")

    # ================================================================
    # Write CSV
    # ================================================================
    outpath = os.path.join(FINAL_DIR, "calibration_targets.csv")
    fieldnames = ["target_id", "name", "value", "unit", "source", "variable", "notes"]
    with open(outpath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(targets)

    # Hash
    with open(outpath, "r", encoding="utf-8") as f:
        content = f.read()
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

    print(f"\n[OK] calibration_targets.csv salvo em: {outpath}")
    print(f"     {len(targets)} targets")
    print(f"     SHA-256: {sha}")
    print(f"     Timestamp: {datetime.datetime.now().isoformat()}")

    # Print summary table
    print(f"\n{'ID':<16} {'Value':>10}  {'Source'}")
    print("-" * 70)
    for t in targets:
        val = t["value"]
        val_str = f"{val:.4f}" if isinstance(val, float) else str(val)
        src_short = t["source"][:40]
        print(f"{t['target_id']:<16} {val_str:>10}  {src_short}")

    return targets


if __name__ == "__main__":
    main()
