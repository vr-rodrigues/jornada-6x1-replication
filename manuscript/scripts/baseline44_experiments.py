"""Recompute empirical experiments with formal baseline hours capped at 44.

The immutable replication kernel is imported, never edited. National baseline
inputs, remuneration targets and anchors come from the pinned run's existing
``national_empirical_topcode44`` experiment. Its 64-point empirical sensitivity
design is reproduced with H0=44 and the corresponding hourly target.

For sectors, the observed remuneration bridge is reconstructed from paid-worker
payrolls and hours in the verified PNAD sector summaries: sum formal payrolls /
sum formal hours capped at 44, divided by sum informal payrolls / sum informal
unrestricted hours. Only the same three classified activities modeled are
included. Thus this target deliberately differs from the nationwide target,
which includes unclassified activity. A single common omega is fitted across
the three sectors, separately for each efficiency function; sector wedges are
recalibrated under the existing tau*pi=0 normalization. Neither sector-specific
omega nor capital stocks nor any parameter is fitted to recover old results.

API: compute_baseline44_experiments(replication_root, run_dir=None) returns
dataframes, detailed simulations, provenance and numerical checks, without
writing files. The CLI writes only inside the explicit manuscript output dir.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import argparse
import hashlib
import itertools
import json
import sys
import time

import numpy as np
import pandas as pd

RUN_ID = "20260905_005724_846373"
MODES = ("bilateral", "flat_below")
SECTORS = ("agriculture", "industry", "services")


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _json_default(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(type(value).__name__)


def _simulation_check(sim):
    """Independently check saved levels, representative CE and solver evidence."""
    b, r, results = sim["baseline"], sim["reform"], sim["results"]
    population = sum(p["N_total"] for p in sim["groups"].values())
    psi, nu = sim["psi"], sim["nu_ghh"]
    c0, c1 = b["C"]/population, r["C"]/population
    v = lambda h: psi*h**(1.+nu)/(1.+nu)
    ce = 100.*(c1-c0-v(r["h_avg"])+v(b["h_avg"]))/c0
    ghh = 100.*((c1-v(r["h_avg"]))/(c0-v(b["h_avg"]))-1.)
    d = sim["decomposition"]
    decomp_error = abs(sum(d[k] for k in ("hours_pct", "efficiency_pct", "reallocation_pct"))
                       - 100.*(r["Y"]-b["Y"])/b["Y"])
    kkt = max(s["kkt_violation"] for solutions in
              (b["solutions"], r["solutions"], sim["A_req_details"]["allocations"])
              for s in solutions.values())
    # The default resource closure treats the private wedges as rebated transfers.
    resource_error = max(abs(state["C"]+state["resource_cost"]-state["Y"])
                         for state in (b, r))
    return dict(restoration=abs(sim["A_req_details"]["relative_error"]),
                frozen_restoration=abs(sim["A_req_frozen_details"]["relative_error"]),
                kkt=float(kkt), decomposition=float(decomp_error),
                CE=abs(ce-results["CE_pct"]), GHH=abs(ghh-results["dGHH_pct"]),
                resource_constraint=float(resource_error))


def _observed_sector_bridge(pnad):
    """Return a classified payroll/hours target and auditable sector rows.

    Formal topcoding is performed on paid-worker hours, not the distribution of
    all occupied workers. Informal hours and both payrolls remain unchanged.
    The common monthly-to-weekly conversion 12/52 cancels from the ratio.
    """
    rows = []
    for sector in (*SECTORS, "national"):
        source = pnad["national"] if sector == "national" else pnad["sectors"][sector]
        wages = source["wages"]
        f, i = wages["formal"], wages["informal"]
        row = dict(sector=sector,
            formal_income_monthly_sum=float(f["income_monthly_sum"]),
            informal_income_monthly_sum=float(i["income_monthly_sum"]),
            formal_hours_weekly_sum=float(f["hours_weekly_sum"]),
            formal_hours_weekly_sum_capped44=float(f["hours_weekly_sum_capped44"]),
            informal_hours_weekly_sum=float(i["hours_weekly_sum"]),
            formal_paid_weight=float(f["paid_workers_weighted"]),
            informal_paid_weight=float(i["paid_workers_weighted"]))
        rows.append(row)
    classified = {"sector": "CLASSIFIED_AGGREGATE"}
    for key in rows[0]:
        if key != "sector":
            classified[key] = sum(row[key] for row in rows[:3])
    rows.append(classified)
    for row in rows:
        f_income, i_income = row["formal_income_monthly_sum"], row["informal_income_monthly_sum"]
        f_hours, i_hours = row["formal_hours_weekly_sum_capped44"], row["informal_hours_weekly_sum"]
        if min(f_income, i_income, f_hours, i_hours) <= 0 or not np.isfinite(list(row.values())[1:]).all():
            raise ValueError("Missing/invalid verified paid-worker sector payroll or hours")
        row["hourly_ratio_formal_capped44"] = (f_income/f_hours)/(i_income/i_hours)
        row["hourly_ratio_full_habitual"] = (f_income/row["formal_hours_weekly_sum"])/(i_income/i_hours)
        row["formal_hourly_pay_capped44"] = (12./52.)*f_income/f_hours
        row["informal_hourly_pay"] = (12./52.)*i_income/i_hours
    return float(rows[-1]["hourly_ratio_formal_capped44"]), pd.DataFrame(rows)


def compute_baseline44_experiments(replication_root, run_dir=None):
    """Return national/sectoral frames, details, provenance and passed checks.

    source_hashes keys use forward-slash paths relative to replication_root.
    No input, code, prior run or artifact is modified by this function.
    """
    started = time.perf_counter()
    root = Path(replication_root).resolve()
    run = Path(run_dir).resolve() if run_dir is not None else root/"output/runs"/RUN_ID
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scipy.optimize import brentq
    from src.model import simulation
    from src.model.simulation import run_simulation, simulate_groups
    from src.calibration.corrected_pipeline import result_row
    from src.calibration.wage_bridge import aggregate_bridge, calibrate_omega
    from src.sectoral.model.inputs import load_inputs
    from src.sectoral.model.sector_model import build_sector_params
    if not Path(simulation.__file__).resolve().is_relative_to(root):
        raise RuntimeError("A different replication checkout was already imported")
    source_hashes = {}

    def source(path, csv=False):
        path = Path(path)
        source_hashes[path.relative_to(root).as_posix()] = _digest(path)
        return pd.read_csv(path) if csv else json.loads(path.read_text(encoding="utf-8-sig"))

    folder = run/"national_empirical_topcode44"
    inputs = source(folder/"INPUTS.json")
    canonical_bridges = source(folder/"BRIDGE.json")
    canonical = source(folder/"RESULTS.csv", csv=True)
    pnad_path = root/"data_intermediate/reprocessed/pnad_targets.json"
    pnad = source(pnad_path)
    if (pnad.get("status") not in ("verified_reprocessed", "verified_official_fallback")
            or pnad["metadata"]["year"] != 2024 or pnad["metadata"]["quarter"] != 4):
        raise ValueError("Verified PNAD 2024Q4 inputs are required")
    targets = deepcopy(inputs["targets"])
    if float(targets["H0"]["value"]) != 44.:
        raise ValueError("Expected the canonical formal-baseline-44 experiment")
    theta, bins, specs = inputs["theta"], inputs["hours_bins"], inputs["group_specs"]
    share_basis = inputs["share_basis"]
    costs = bool(inputs["resource_costs"])
    if costs:
        raise ValueError("The principal baseline-44 experiment must preserve rebated wedges")
    ratios = {float(b["target"]) for b in canonical_bridges if b["measure"] == "hourly"}
    if len(ratios) != 1 or len(canonical_bridges) != 2:
        raise ValueError("Both canonical modes must use the same observed hourly target")
    ratio = ratios.pop()
    sector_ratio, observed = _observed_sector_bridge(pnad)
    national_observed = observed.loc[observed.sector.eq("national")].iloc[0]
    observed_ratio_error = abs(ratio-float(national_observed.hourly_ratio_formal_capped44))
    if observed_ratio_error > 1e-10:
        raise ArithmeticError("Reconstructed national paid-hour target differs from canonical base44 target")

    sensitivity_rows, sensitivity_details, numerical = [], {}, []
    for mode, cap in itertools.product(MODES, (40, 36)):
        designs = [("efficiency", {"E_Q":v}, 1.326) for v in (.4, .6, .8, 1.)]
        designs += [("peak", {"H_STAR":v}, 1.326) for v in (38., 39., 40., 41.)]
        designs += [("eta", {"ETA_I":v}, 1.326) for v in (.33, .40, .50)]
        designs += [("sigma", {}, v) for v in (.6, 1., 1.326, 1.5, 2.)]
        for index, (dimension, changes, sigma) in enumerate(designs):
            t = deepcopy(targets)
            t["H1"]["value"] = cap
            for key, value in changes.items():
                t[key]["value"] = value
            bridge = calibrate_omega(t, ratio, sigma_sub=sigma, efficiency_mode=mode,
                theta=theta, hours_bins=bins, group_specs=specs, share_basis=share_basis)
            sim = run_simulation(t, sigma_sub=sigma, omega=bridge["omega"], theta=theta,
                hours_bins=bins, group_specs=specs, efficiency_mode=mode,
                share_basis=share_basis, resource_costs=costs)
            check = _simulation_check(sim)
            check["bridge"] = abs(float(bridge["residual"]))
            numerical.append(check)
            key = f"{mode}_{cap}_{dimension}_{index}"
            sensitivity_details[key] = {"bridge":bridge, "simulation":sim, "checks":check}
            sensitivity_rows.append(result_row(sim, "empirical_sensitivity_topcoded44", cap, mode,
                dimension=dimension, E_Q=t["E_Q"]["value"], h_star=t["H_STAR"]["value"],
                eta_I=t["ETA_I"]["value"], bridge_target=ratio, bridge_residual=bridge["residual"],
                baseline_operator_h0=44., interpretation="Conditional base44 hourly mapping; not an identified set"))
    sensitivity = pd.DataFrame(sensitivity_rows)
    if len(sensitivity) != 64:
        raise ArithmeticError("Expected the original 64-point empirical sensitivity design")
    anchor_errors = []
    for mode, cap in itertools.product(MODES, (40,36)):
        original = canonical.loc[canonical.efficiency_mode.eq(mode) & canonical.hours_cap.eq(cap)].iloc[0]
        central = sensitivity.loc[sensitivity.efficiency_mode.eq(mode) & sensitivity.hours_cap.eq(cap)
            & sensitivity.dimension.eq("efficiency") & np.isclose(sensitivity.E_Q, .6)].iloc[0]
        for key in ("Y0", "Y1", "dY_pct", "A_req_pct", "A_req_frozen_pct", "informality_pct",
                    "dInf_pp", "dGHH_pct", "CE_pct", "omega", "hours_pct", "efficiency_pct",
                    "reallocation_pct"):
            anchor_errors.append(abs(float(original[key])-float(central[key])))

    facts, inherited_provenance = load_inputs(pnad_path.parent, "reprocessed", root/"data_final")
    hypothesis = root/"data_final/SECTORAL_BASELINE_FACTS.csv"
    source_hashes[hypothesis.relative_to(root).as_posix()] = _digest(hypothesis)
    flat_targets = {key:float(value["value"]) for key,value in targets.items()}
    sector_rows, sector_details, sector_parameters, sector_bridges = [], {}, {}, []
    for mode in MODES:
        def at(omega):
            params, _ = build_sector_params(deepcopy(facts), flat_targets, sigma_sub=1.326,
                omega=omega, efficiency_mode=mode, resource_costs=costs)
            sim = simulate_groups(params, 44., 44., next(iter(params.values()))["theta"])
            return aggregate_bridge(sim)["hourly_ratio"]
        omega = brentq(lambda w:at(w)-sector_ratio, .02, .98, xtol=1e-11)
        implied = at(omega)
        bridge = dict(efficiency_mode=mode, sigma_sub=1.326, omega=float(omega),
            target=sector_ratio, implied=float(implied), residual=float(implied-sector_ratio),
            measure="hourly", universe="three classified PNAD sectors; positive paid main-job income",
            formal_hours="min(habitual,44)", informal_hours="habitual, unrestricted",
            aggregation="sum payrolls and paid-worker physical hours before taking formal/informal ratio",
            identification="common omega conditional on sigma, eta and wedge normalization")
        sector_bridges.append(bridge)
        parameters, kappa = build_sector_params(deepcopy(facts), flat_targets, sigma_sub=1.326,
            omega=omega, efficiency_mode=mode, resource_costs=costs)
        sector_parameters[mode] = parameters
        for cap in (40,36):
            aggregate = simulate_groups(parameters, 44., cap, next(iter(parameters.values()))["theta"])
            simulations = {name:simulate_groups({name:p}, 44., cap, p["theta"])
                           for name,p in parameters.items()}
            simulations["AGGREGATE"] = aggregate
            sector_details[f"{mode}_{cap}"] = simulations
            for name, sim in simulations.items():
                check = _simulation_check(sim)
                check["bridge"] = abs(bridge["residual"])
                numerical.append(check)
                b, r, result = sim["baseline"], sim["reform"], sim["results"]
                row = dict(scenario_variant="empirical_bridge_topcoded44", input_kind="reprocessed",
                    efficiency_mode=mode, h0=44., h1=cap, sector=name, sigma_sub=1.326,
                    omega=float(omega), kappa=float(kappa), bridge_target=sector_ratio,
                    hourly_ratio_target=sector_ratio,
                    Y_base=b["Y"], Y_reform=r["Y"], C_base=b["C"], C_reform=r["C"],
                    inf_base=b["inf"], inf_reform=r["inf"], h_avg_base=b["h_avg"],
                    h_avg_reform=r["h_avg"], baseline_operator_h0=44.)
                for key in ("dY_pct", "A_req_pct", "A_req_frozen_pct", "dInf_pp", "dGHH_pct", "CE_pct"):
                    row[key] = result[key]
                for key in ("hours_pct", "efficiency_pct", "reallocation_pct", "total_pct"):
                    row[f"decomp_{key}"] = sim["decomposition"][key]
                row["contribution_to_dY"] = 100.*(r["Y"]-b["Y"])/aggregate["baseline"]["Y"]
                sector_rows.append(row)
    sectors = pd.DataFrame(sector_rows)
    if len(sectors) != 16:
        raise ArithmeticError("Expected four sectors/aggregate x two caps x two modes")
    maxima = {key:max(check[key] for check in numerical) for key in numerical[0]}
    for key, maximum in maxima.items():
        tolerance = 1e-7 if key in ("kkt", "bridge") else 1e-9
        if not np.isfinite(maximum) or maximum > tolerance:
            raise ArithmeticError(f"Numerical check failed: {key}={maximum}")
    if max(anchor_errors) > 1e-8:
        raise ArithmeticError("National base44 canonical anchors changed")
    for relative, before in source_hashes.items():
        if _digest(root/relative) != before:
            raise ArithmeticError(f"Input changed during computation: {relative}")
    checks = dict(status="passed", national_sensitivity_rows=len(sensitivity),
        sectoral_rows=len(sectors), simulations_checked=len(numerical),
        max_errors=maxima, max_national_anchor_error=max(anchor_errors),
        observed_national_target_error=observed_ratio_error,
        elapsed_seconds=time.perf_counter()-started)
    provenance = dict(run_id=run.name, source_hashes=source_hashes,
        source_hash_path_basis="relative to replication_root, forward slashes",
        baseline="formal habitual hours min(h,44); informal habitual hours unchanged",
        reform="formal habitual hours min(h,40) or min(h,36)",
        national_hourly_target=ratio, classified_sector_hourly_target=sector_ratio,
        target_difference_classified_minus_national=sector_ratio-ratio,
        sector_employment_coverage_share=inherited_provenance["employment_coverage_share"],
        sector_target_universe="paid persons in agriculture, industry and services; unclassified activity excluded",
        selection_assumption="pay bridge from positive-income occupied extended to all occupied model workers",
        sector_specific_observed_ratios="reported for audit, not individually fitted; one common omega per efficiency mode",
        efficiency_anchor_hours=flat_targets["H_REF_EFFICIENCY"],
        sector_capital_hypothesis=inherited_provenance["capital_hypothesis"],
        sector_capital_shares={name:float(f["vab_share"]) for name,f in facts.items()},
        gamma=.06, alpha=flat_targets["ALPHA"], eta_I=flat_targets["ETA_I"], sigma=1.326,
        normalization="nonnegative tau,pi and tau*pi=0; recalibrated for each technology specification",
        constraints="fixed capital and total sector employment; no investment, IO or worker-incidence equations",
        resource_closure="wedges rebated; quadratic composition adjustment consumes resources",
        pnad_metadata=pnad["metadata"], sector_input_provenance=inherited_provenance,
        all_results_freshly_executed=True, replication_package_modified=False)
    return dict(national=canonical, sensitivity=sensitivity, sectoral=sectors,
        observed_sector_bridge=observed, sectoral_bridges=sector_bridges,
        sectoral_parameters=sector_parameters, sectoral_details=sector_details,
        sensitivity_details=sensitivity_details, provenance=provenance, checks=checks,
        source_hashes=source_hashes)


def save_results(payload, output_dir):
    """Write the reviewable computation bundle without touching the replication."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    frames = {"NATIONAL_BASE44.csv":"national", "NATIONAL_SENSITIVITY_BASE44.csv":"sensitivity",
              "SECTOR_RESULTS_BASE44.csv":"sectoral", "SECTOR_OBSERVED_BRIDGE_BASE44.csv":"observed_sector_bridge"}
    for name, key in frames.items():
        payload[key].to_csv(out/name, index=False, encoding="utf-8-sig")
    for name,key in (("CHECKS.json","checks"), ("PROVENANCE.json","provenance"),
                     ("SECTOR_BRIDGES.json","sectoral_bridges"),
                     ("SECTOR_PARAMETERS.json","sectoral_parameters"),
                     ("SECTOR_DETAILS.json","sectoral_details"),
                     ("SENSITIVITY_DETAILS.json","sensitivity_details")):
        (out/name).write_text(json.dumps(payload[key], ensure_ascii=False, indent=2,
            default=_json_default, allow_nan=False), encoding="utf-8")
    no_fatigue = payload["sensitivity"].query("dimension == 'efficiency' and E_Q == 1")
    summary = {"checks":payload["checks"], "sectoral_bridges":payload["sectoral_bridges"],
               "national_no_fatigue":no_fatigue[["efficiency_mode","hours_cap","A_req_pct","dY_pct","CE_pct","dGHH_pct"]].to_dict("records"),
               "sectoral":payload["sectoral"][["efficiency_mode","h1","sector","dY_pct","A_req_pct","dInf_pp","CE_pct","dGHH_pct"]].to_dict("records"),
               "sectoral_target_note":payload["provenance"]["sector_target_universe"]}
    (out/"EDITORIAL_SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False,
        indent=2, default=_json_default, allow_nan=False), encoding="utf-8")


def main():
    paper = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replication-root", type=Path, default=(paper.parent/"replication_package" if (paper.parent/"replication_package"/"run_all.py").is_file() else paper.parent))
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=paper/".build_paper/base44_computation")
    args = parser.parse_args()
    payload = compute_baseline44_experiments(args.replication_root, args.run_dir)
    save_results(payload,args.output_dir)
    print(json.dumps(payload["checks"], indent=2, ensure_ascii=False))
    print(payload["sectoral"][["efficiency_mode","h1","sector","A_req_pct","CE_pct"]].to_string(index=False))
    print(f"Saved computation bundle: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
