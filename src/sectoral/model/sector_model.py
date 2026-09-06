"""Three independent sectors using the continuous national model kernel.

Fresh outputs: python src/sectoral/model/sector_model.py --input-kind frozen
Capital shares are explicit hypotheses; no IO, worker incidence or investment.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.model.calibration import calibrate_wedges
from src.model.efficiency import calibrate_kappa
from src.model.areq_solver import solve_Areq
from src.model.simulation import simulate_groups
from src.sectoral.model.inputs import (
    load_inputs, load_national_targets, load_sectoral_facts, validate_sector_facts,
)


def build_sector_params(sectors, targets, sigma_sub=1.326, omega=0.622,
                        gamma_F=0.06, efficiency_mode="bilateral",
                        resource_costs=False, kappa_override=None):
    """Calibrate sector wedges under the national complementarity normalization.

    lambda_s is a total employment share. Omega is never a formal share.
    Curvature uses an external national efficiency anchor, not a new average
    that can fall below the peak in the PNAD data.
    """
    sectors = validate_sector_facts(sectors)
    alpha, eta_I = targets["ALPHA"], targets["ETA_I"]
    h0, h_star = targets["H0"], targets["H_STAR"]
    h_ref = targets.get("H_REF_EFFICIENCY", 42.244)
    if kappa_override is None:
        if h_ref <= h_star and targets["E_Q"] != 1:
            raise ValueError("Efficiency anchor must exceed peak; supply an explicit curvature hypothesis")
        kappa = calibrate_kappa(h_ref, h_star, targets["E_Q"])
    else:
        kappa = float(kappa_override)
    if kappa < 0 or not np.isfinite(kappa):
        raise ValueError("Curvature must be finite and nonnegative")
    parameters = {}
    for name, facts in sectors.items():
        population = targets["N_TOTAL"] * facts["lambda_s"]
        hI = facts.get("hI", targets["HI"])
        inf_target = facts["inf_rate"]
        theta, hours_bins = facts["theta"], facts["hours_bins"]
        K = facts["vab_share"]
        wedges = calibrate_wedges(inf_target, population, h0, hI, 1., K,
                                  alpha, omega, sigma_sub, eta_I, kappa, h_star,
                                  theta, efficiency_mode=efficiency_mode, hours_bins=hours_bins)
        parameters[name] = {
            "A": 1., "K": K, "alpha": alpha, "omega": omega,
            "sigma_sub": sigma_sub, "eta_I": eta_I, "kappa": kappa,
            "h_star": h_star, "h0": h0, "hI": hI,
            "N_total": population, "formal_wedge": wedges["formal_wedge"],
            "pi_m": wedges["pi_m"], "gamma_F": gamma_F,
            "NF_init": population * (1.0 - inf_target),
            "theta": theta, "hours_bins": hours_bins,
            "efficiency_mode": efficiency_mode, "resource_costs": resource_costs,
            "inf_target": inf_target, "lambda_s": facts["lambda_s"],
            "vab_share": facts["vab_share"], "h_ref_efficiency": h_ref,
            "wedge_normalization": wedges["normalization"],
        }
    return parameters, kappa


def _compat_result(simulation):
    baseline, reform = simulation["baseline"], simulation["reform"]
    metrics = dict(simulation["results"])
    metrics.update({
        "Y_base": baseline["Y"], "Y_reform": reform["Y"],
        "C_base": baseline["C"], "C_reform": reform["C"],
        "inf_base": baseline["inf"], "inf_reform": reform["inf"],
        "h_avg_base": baseline["h_avg"], "h_avg_reform": reform["h_avg"],
        "psi": simulation["psi"], "decomposition": simulation["decomposition"],
    })
    return metrics


def run_sectoral_simulation(sector_params, kappa, h1, N_total=None, nu_ghh=2.0):
    """All aggregate and sector diagnostics use the same simulate_groups kernel.

    Sector GHH/CE use sector representative agents, not a social incidence
    decomposition. The employment denominator is derived from group totals.
    """
    population = sum(p["N_total"] for p in sector_params.values())
    if N_total is not None and not np.isclose(N_total, population, rtol=0, atol=1e-10):
        raise ValueError("N_total must equal the sum of sector employment")
    caps = {p["h0"] for p in sector_params.values()}
    if len(caps) != 1:
        raise ValueError("Sectors must share a baseline legal hours cap")
    h0 = next(iter(caps))
    theta = next(iter(sector_params.values()))["theta"]
    aggregate_sim = simulate_groups(sector_params, h0, h1, theta, nu_ghh=nu_ghh)
    aggregate = _compat_result(aggregate_sim)
    sectors = {}
    for name, pars in sector_params.items():
        local_sim = simulate_groups({name: pars}, h0, h1, pars["theta"], nu_ghh=nu_ghh)
        row = _compat_result(local_sim)
        row.update({
            "lambda_s": pars["lambda_s"], "inf_target": pars["inf_target"],
            "tau_s": pars["formal_wedge"], "pi_m": pars["pi_m"],
            "Y_share_of_total": row["Y_base"] / aggregate["Y_base"],
            "contribution_to_dY": 100. * (row["Y_reform"] - row["Y_base"]) / aggregate["Y_base"],
        })
        sectors[name] = row
    return {"aggregate": aggregate, "sectors": sectors, "simulation": aggregate_sim}


def _solve_Areq_multi(sector_params, h1, Y_target, grid=3001):
    """Legacy API wrapper: common A_req solver respects each sector's hours."""
    theta = next(iter(sector_params.values()))["theta"]
    return solve_Areq(sector_params, h1, Y_target, theta, grid=grid)


def _json_default(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def _write_csv(path, rows):
    if not rows:
        raise ValueError(f"Refusing an empty result table: {path}")
    with Path(path).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_sectoral_pipeline(data_dir, output_dir, input_kind="frozen",
                          sigma_sub=1.326, omega=0.622, targets_path=None,
                          hypotheses_dir=None, kappa_override=None,
                          omega_source="explicit technological hypothesis",
                          resource_costs=False, omega_by_mode=None):
    """Recompute 40h/36h and both efficiency functions in an isolated directory."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    hypotheses_dir = Path(hypotheses_dir or PROJECT_ROOT / "data_final")
    explicit_targets = targets_path is not None
    targets_path = Path(targets_path or hypotheses_dir / "calibration_targets.csv")
    targets = load_national_targets(targets_path)
    sectors, provenance = load_inputs(data_dir, input_kind, hypotheses_dir)
    overrides = {}
    if input_kind == "reprocessed" and not explicit_targets:
        overrides = {"H0": float(max(max(s["hours_bins"]) for s in sectors.values())),
                     "H_REF_EFFICIENCY": 42.244}
        targets.update(overrides)
    rows, decomp_rows, scenarios, parameters = [], [], {}, {}
    for mode in ("bilateral", "flat_below"):
        mode_omega = float(omega_by_mode[mode]) if omega_by_mode is not None else float(omega)
        pars, kappa = build_sector_params(sectors, targets, sigma_sub, mode_omega,
                                          efficiency_mode=mode, resource_costs=resource_costs,
                                          kappa_override=kappa_override)
        parameters[mode] = pars
        for h1 in (40., 36.):
            scenario = run_sectoral_simulation(pars, kappa, h1)
            scenarios[f"{mode}_{int(h1)}"] = scenario
            by_sector = {**scenario["sectors"], "AGGREGATE": scenario["aggregate"]}
            for name, metrics in by_sector.items():
                row = {"input_kind": input_kind, "efficiency_mode": mode, "h0": targets["H0"], "h1": int(h1),
                       "sector": name, "sigma_sub": sigma_sub, "omega": mode_omega}
                for key in ("Y_base", "Y_reform", "dY_pct", "A_req_pct", "A_req_frozen_pct",
                            "inf_base", "inf_reform", "dInf_pp", "dGHH_pct", "CE_pct",
                            "C_base", "C_reform", "h_avg_base", "h_avg_reform"):
                    row[key] = metrics[key]
                decomposition = metrics["decomposition"]
                keys = ("hours_pct", "efficiency_pct", "reallocation_pct", "total_pct")
                row.update({f"decomp_{key}": decomposition[key] for key in keys})
                row["contribution_to_dY"] = metrics.get("contribution_to_dY", metrics["dY_pct"])
                rows.append(row)
                decomp_rows.append({"input_kind": input_kind, "efficiency_mode": mode,
                                    "h1": int(h1), "sector": name,
                                    **{key: decomposition[key] for key in keys},
                                    "order": "physical hours -> efficiency -> formal-informal reallocation",
                                    "denominator": metrics["Y_base"]})
    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(), **provenance,
        "targets_path": str(targets_path.resolve()),
        "targets_sha256": hashlib.sha256(targets_path.read_bytes()).hexdigest(),
        "effective_targets": targets,
        "explicit_runtime_target_overrides": overrides,
        "sigma_sub": sigma_sub, "omega": omega, "omega_source": omega_source,
        "omega_by_mode": omega_by_mode,
        "omega_is_not_formal_employment_share": True,
        "efficiency_curvature_anchor_hours": targets.get("H_REF_EFFICIENCY", 42.244),
        "kappa_override": kappa_override,
        "baseline_hours_cap_operation": targets["H0"],
        "habitual_hours_policy_mapping": (
            "Baseline min(h_habitual,H0) preserves all observed hours because H0 is at least max support; H0 is an identity operation, not the legal cap. Reform min(h_habitual,h1) is a policy mapping assumption, not contracted hours data."
            if all(targets["H0"] >= max(s["hours_bins"]) for s in sectors.values())
            else "Baseline min(h_habitual,H0) topcodes observed habitual hours; reform min(h_habitual,h1). Topcoding and statutory mapping are assumptions, not contracted hours data."),
        "efficiency_extrapolation": "The same efficiency curve anchored at 42.244h is extrapolated over the full empirical hours support; long-hours and part-time responses are assumptions, not estimated behavior.",
        "observed_formal_support_by_sector": {
            name: {"min_hours": float(min(s["hours_bins"])), "max_hours": float(max(s["hours_bins"])),
                   "share_above_44h": float(np.asarray(s["theta"])[np.asarray(s["hours_bins"]) > 44].sum())}
            for name, s in sectors.items()},
        "welfare": "representative-agent diagnostics; sector values do not constitute worker incidence",
        "resource_costs": resource_costs,
        "all_results_newly_executed": True, "legacy_output_files_used": [],
    }
    payload = {"metadata": metadata, "rows": rows, "scenarios": scenarios}
    _write_csv(output_dir / "SECTOR_RESULTS.csv", rows)
    _write_csv(output_dir / "SECTOR_DECOMPOSITION.csv", decomp_rows)
    from src.sectoral.model.workers_affected import write_exposure
    write_exposure(sectors, output_dir / "SECTOR_HOURS_EXPOSURE.csv")
    (output_dir / "SECTOR_RESULTS_FULL.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    (output_dir / "SECTOR_PARAMETERS.json").write_text(
        json.dumps({"metadata": metadata, "parameters": parameters}, ensure_ascii=False,
                   indent=2, default=_json_default), encoding="utf-8")
    print(f"New sectoral results: {output_dir / 'SECTOR_RESULTS.csv'} ({len(rows)} rows)")
    return payload


def calibrate_sector_omega(data_dir, targets_path, hypotheses_dir=None, target=None,
                           measure="hourly", efficiency_mode="bilateral", sigma_sub=1.326):
    """Conditional aggregate payroll/hours bridge with sector wedges refitted.

    This imposes a competitive gross-marginal-product pay mapping. It is not
    joint identification of technology and wedges or a causal wage equation.
    """
    from scipy.optimize import brentq
    from src.calibration.wage_bridge import aggregate_bridge

    hypotheses_dir = Path(hypotheses_dir or PROJECT_ROOT / "data_final")
    targets = load_national_targets(targets_path)
    facts, provenance = load_inputs(data_dir, "reprocessed", hypotheses_dir)
    if measure not in ("hourly", "weekly"):
        raise ValueError("Specify hourly or weekly compensation, never effective labor implicitly")
    if target is None:
        key = "aggregate_hourly_payroll_over_hours" if measure == "hourly" else "mean_weekly_per_worker"
        target = provenance["national_wage_ratio_targets"][key]
    if not np.isfinite(target) or target <= 0:
        raise ValueError("A positive remuneration ratio is required")
    h0 = targets["H0"]

    def at(technology_weight):
        params, _ = build_sector_params(facts, targets, sigma_sub, technology_weight,
                                        efficiency_mode=efficiency_mode)
        theta = next(iter(params.values()))["theta"]
        simulation = simulate_groups(params, h0, h0, theta)
        return aggregate_bridge(simulation)[measure + "_ratio"]

    weight = brentq(lambda w: at(w) - target, 0.02, 0.98, xtol=1e-11)
    implied = at(weight)
    if abs(implied - target) > 1e-7:
        raise ArithmeticError("Sector remuneration bridge did not restore the requested moment")
    return {"omega": weight, "sigma_sub": sigma_sub, "efficiency_mode": efficiency_mode,
            "measure": measure, "target": target, "implied": implied, "residual": implied-target,
            "status": "conditional_calibration_not_joint_identification",
            "aggregation": "sum productive payrolls and physical hours across firms before forming formal/informal ratios",
            "assumption": "national observed pay ratio mapped to gross productive marginal products of three classified sectors; tau/pi normalization retained",
            "employment_coverage_share": provenance["employment_coverage_share"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=PROJECT_ROOT / "data_final")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "output" / "corrected" / "sectoral")
    parser.add_argument("--input-kind", choices=("frozen", "frozen_pnad", "reprocessed"), default="frozen")
    parser.add_argument("--hypotheses-dir", type=Path, default=PROJECT_ROOT / "data_final")
    parser.add_argument("--targets-path", type=Path)
    parser.add_argument("--sigma", type=float, default=1.326)
    parser.add_argument("--omega", type=float, default=0.622)
    parser.add_argument("--kappa", type=float)
    parser.add_argument("--resource-costs", action="store_true")
    args = parser.parse_args(argv)
    run_sectoral_pipeline(args.data_dir, args.output_dir, args.input_kind,
                          sigma_sub=args.sigma, omega=args.omega,
                          targets_path=args.targets_path, hypotheses_dir=args.hypotheses_dir,
                          kappa_override=args.kappa, resource_costs=args.resource_costs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
