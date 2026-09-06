"""Sector sensitivities with interior grid points; not an identified set."""

from __future__ import annotations

import argparse
import copy
from itertools import product
import json
from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.sectoral.model.inputs import load_inputs, load_national_targets
from src.sectoral.model.sector_model import build_sector_params, run_sectoral_simulation, _write_csv


def run_sensitivity(data_dir=None, output_dir=None, input_kind="frozen",
                    hypotheses_dir=None, targets_path=None, omega=0.622):
    data_dir = Path(data_dir or PROJECT_ROOT / "data_final")
    hypotheses_dir = Path(hypotheses_dir or PROJECT_ROOT / "data_final")
    output_dir = Path(output_dir or PROJECT_ROOT / "output" / "corrected" / "sectoral_sensitivity")
    output_dir.mkdir(parents=True, exist_ok=True)
    targets = load_national_targets(targets_path or hypotheses_dir / "calibration_targets.csv")
    facts, provenance = load_inputs(data_dir, input_kind, hypotheses_dir)
    overrides = {}
    if input_kind == "reprocessed" and targets_path is None:
        overrides = {"H0": float(max(max(s["hours_bins"]) for s in facts.values())),
                     "H_REF_EFFICIENCY": 42.244}
        targets.update(overrides)
    cases = []
    # Full CES grid includes face points and the strict interior, not only corners.
    for sigma, omega_value, eta in product((1.1, 1.326, 1.6), (0.55, omega, 0.70), (0.30, 0.40, 0.50)):
        cases.append({"experiment": "CES_grid", "sigma": sigma, "omega": omega_value, "eta": eta})
    for e_q in (0.40, 0.60, 0.80):
        cases.append({"experiment": "efficiency_elasticity", "e_q": e_q})
    for peak in (38., 39., 40., 41.):
        cases.append({"experiment": "efficiency_peak", "peak": peak})
    for mixing in (0., 0.5, 1.):
        cases.append({"experiment": "hours_uniform_mixture", "mixing": mixing})
    rows = []
    for index, case in enumerate(cases):
        trial_facts = copy.deepcopy(facts)
        trial_targets = {**targets, "ETA_I": case.get("eta", targets["ETA_I"]),
                         "E_Q": case.get("e_q", targets["E_Q"]),
                         "H_STAR": case.get("peak", targets["H_STAR"])}
        if "mixing" in case:
            # Same observed hours support; mix each sector with a national
            # formal-employment-weighted distribution, not with invented hours.
            support = np.unique(np.concatenate([s["hours_bins"] for s in facts.values()]))
            formal_masses = {s: f["lambda_s"]*(1-f["inf_rate"]) for s, f in facts.items()}
            formal_total = sum(formal_masses.values())
            pooled = np.zeros(len(support))
            for name, f in facts.items():
                loc = np.searchsorted(support, f["hours_bins"])
                np.add.at(pooled, loc, formal_masses[name]/formal_total*f["theta"])
            for name, f in trial_facts.items():
                own = np.zeros(len(support))
                np.add.at(own, np.searchsorted(support, f["hours_bins"]), f["theta"])
                f["hours_bins"] = support
                f["theta"] = (1-case["mixing"])*own + case["mixing"]*pooled
        for mode in ("bilateral", "flat_below"):
            params, kappa = build_sector_params(trial_facts, trial_targets,
                                                case.get("sigma", 1.326), case.get("omega", omega),
                                                efficiency_mode=mode)
            for cap in (40., 36.):
                result = run_sectoral_simulation(params, kappa, cap)
                for name, r in {**result["sectors"], "AGGREGATE": result["aggregate"]}.items():
                    rows.append({
                        "case": index, "experiment": case["experiment"], "input_kind": input_kind,
                        "efficiency_mode": mode, "h0": trial_targets["H0"], "h1": int(cap), "sector": name,
                        "sigma_sub": case.get("sigma", 1.326), "omega": case.get("omega", omega),
                        "eta_I": trial_targets["ETA_I"], "e_q": trial_targets["E_Q"],
                        "peak": trial_targets["H_STAR"], "hours_mixing": case.get("mixing", 0.),
                        "kappa": kappa, "A_req_pct": r["A_req_pct"], "A_req_frozen_pct": r["A_req_frozen_pct"],
                        "dY_pct": r["dY_pct"], "dInf_pp": r["dInf_pp"],
                        "dGHH_pct": r["dGHH_pct"], "CE_pct": r["CE_pct"],
                        "classification": "sensitivity_not_identified_set",
                    })
    _write_csv(output_dir / "SECTOR_SENSITIVITY.csv", rows)
    metadata = {**provenance, "n_cases": len(cases), "n_rows": len(rows),
                "interpretation": "Hypothetical parameter grid with corners, faces and interior points; not an identified set",
                "moment_restrictions": "Informality refitted with normalized wedges at every point. Wage-ratio restrictions not imposed on CES grid.",
                "hours_sensitivity": "Mixtures of own and pooled formal-employment-weighted observed supports; raw support kept",
                "baseline_hours_cap_operation": targets["H0"],
                "explicit_runtime_target_overrides": overrides,
                "efficiency_extrapolation": "Curvature anchored externally at 42.244h extrapolated across observed part-time and long hours; these responses are sensitivity assumptions, not estimated behavior",
                "cases": cases}
    (output_dir / "SECTOR_SENSITIVITY_METADATA.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"New sectoral sensitivity results: {len(cases)} cases, {len(rows)} rows")
    return {"rows": rows, "metadata": metadata}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=PROJECT_ROOT / "data_final")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "output" / "corrected" / "sectoral_sensitivity")
    parser.add_argument("--input-kind", choices=("frozen", "frozen_pnad", "reprocessed"), default="frozen")
    parser.add_argument("--hypotheses-dir", type=Path, default=PROJECT_ROOT / "data_final")
    parser.add_argument("--targets-path", type=Path)
    parser.add_argument("--omega", type=float, default=0.622)
    args = parser.parse_args(argv)
    run_sensitivity(**vars(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
