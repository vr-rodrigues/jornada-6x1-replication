"""Conditional national formalization-cost experiments for the 40h/36h panels.

This separates computation from ``original_transition_figure.py`` while
preserving the audited replication kernel and empirical inputs.
Formal habitual hours start at min(observed,44). Both counterfactual caps use
the SAME baseline at each sigma, with omega fitted to the canonical hourly
remuneration target and tau/pi recalibrated under tau>=0, pi>=0, tau*pi=0.
Only the counterfactual private formalization cost changes:
tau_cap=(1-r)*tau, r in [0,1]. No post-shock calibration is performed. Baseline
output, pi, gamma, NF_init, and omega remain fixed while composition is solved
again in EVERY evaluation of the productivity-restoration root.

The output preserves the old CSV column names, including
``wedge_relief_national`` (a fraction), and adds the 36h panel. The plot-facing
label should say "redução do custo de formalização", not an observed tax rate.
The cost is national and private, not a firm-size observation or an identified
fiscal subsidy. Its accounting treatment follows canonical resource_costs.

There are 44 sigma values, 61 reductions, and two caps (5,368 rows). Signed
A_req and max(0,A_req) are both reported. Additional thresholds solve output
restoration at A=1 and A=1.01 directly; infeasible targets are recorded without
extending r beyond [0,1]. Feasible minima use the CES product-maximizing
composition and the private FOC, with an explicit bounded numerical check.

API: compute_transition_map(inputs, replication_root, anchor_rows=None)
returns (DataFrame, JSON-serializable checks). ``inputs`` combines canonical
INPUTS.json with a ``bridges`` list from BRIDGE.json. No input is modified.
The CLI writes CSV/checks only when --output-dir is supplied; plotting belongs
to the paper figure module, which can use a common scale for both panels.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import argparse
import json
import sys
import time

import numpy as np
import pandas as pd
from scipy.optimize import brentq, minimize_scalar
from scipy.special import expit

from paper_config import PRIMARY_VERSION, PRIMARY_H0, PRIMARY_FOLDER


CAPS = (40., 36.)
SIGMAS = np.unique(np.r_[np.linspace(.4, 2.5, 43), 1.326])
RELIEFS = np.linspace(0., 1., 61)


def _anchors(anchor_rows):
    if anchor_rows is None:
        return pd.DataFrame()
    frame = (anchor_rows.copy() if isinstance(anchor_rows, pd.DataFrame)
             else pd.DataFrame(anchor_rows))
    for key, value in (("version", PRIMARY_VERSION), ("efficiency_mode", "bilateral")):
        if key in frame:
            frame = frame.loc[frame[key].eq(value)]
    if "sigma_sub" in frame:
        frame = frame.loc[np.isclose(frame.sigma_sub.astype(float), 1.326)]
    if "hours_cap" not in frame:
        raise ValueError("Canonical anchors must specify hours_cap")
    frame = frame.loc[frame.hours_cap.astype(float).isin(CAPS)]
    if len(frame) != 2 or frame.hours_cap.astype(float).nunique() != 2:
        raise ValueError("Require exactly one bilateral canonical anchor per cap")
    return frame


def compute_transition_map(inputs, replication_root, anchor_rows=None):
    """Compute both panels and the feasible 0%/1% productivity frontiers.

    With one positive mixed CES, the gross-output maximum is interior and has
    x/(N-x)=(omega/(1-omega))**sigma*(qF/qI)**(sigma-1). This maximum does not
    depend on A. At that x, the output derivative is zero, so the private FOC
    requires tau_star=pi*(N-x)-gamma*(x-NF_init). Reducing tau monotonically
    raises the private choice x. Therefore clipping 1-tau_star/tau to [0,1]
    gives the reduction that maximizes gross output for every positive A,
    and hence minimizes the restoring A. This also permits an interior
    minimum; monotonic A_req across the entire domain is not assumed.
    """
    started = time.perf_counter()
    replication_root = Path(replication_root).resolve()
    if str(replication_root) not in sys.path:
        sys.path.insert(0, str(replication_root))
    from src.model import firm_problem
    from src.model.groups import build_groups
    from src.model.areq_solver import solve_Areq
    from src.calibration.wage_bridge import calibrate_omega
    if not Path(firm_problem.__file__).resolve().is_relative_to(replication_root):
        raise RuntimeError("A different replication checkout was already imported")
    solve_group = firm_problem.solve_group

    targets = deepcopy(inputs["targets"])
    specs = deepcopy(inputs["group_specs"])
    theta = np.asarray(inputs["theta"], dtype=float)
    bins = np.asarray(inputs["hours_bins"], dtype=float)
    if len(specs) != 1 or not np.isclose(next(iter(specs.values()))["share"], 1.):
        raise ValueError("The empirical transition panels require one national group")
    if (theta.shape != bins.shape or not np.isfinite(theta).all()
            or not np.isfinite(bins).all() or np.any(theta < 0)
            or not np.isclose(theta.sum(), 1., atol=1e-10, rtol=0)):
        raise ValueError("Require a valid complete weighted hours distribution")
    h0 = float(targets["H0"]["value"])
    if not np.isclose(h0, PRIMARY_H0) or not np.isclose(h0, 44.):
        raise ValueError("The transition panels must use the explicit 44h baseline")
    share_basis = inputs.get("share_basis", "formal")
    resource_costs = bool(inputs.get("resource_costs", False))
    anchors = _anchors(anchor_rows)
    bridge = next((b for b in inputs.get("bridges", [])
                   if b.get("efficiency_mode") == "bilateral"), None)
    if bridge is not None:
        if bridge.get("measure") != "hourly":
            raise ValueError("Require the canonical hourly remuneration bridge")
        ratio = float(bridge["target"])
    elif len(anchors) == 2 and "implied_hourly_ratio" in anchors:
        values = anchors.implied_hourly_ratio.to_numpy(float)
        if not np.allclose(values, values[0], atol=1e-10, rtol=0):
            raise ValueError("Both caps must have the same baseline bridge target")
        ratio = float(values[0])
    else:
        raise ValueError("Supply canonical bridges or anchors with implied_hourly_ratio")
    if not np.isfinite(ratio) or ratio <= 0:
        raise ValueError("Hourly remuneration target must be positive and finite")

    rows, frontiers, bridge_errors, baseline_errors, auxiliary_points = [], [], [], [], []
    central = {}
    min_optimizer_errors = []
    for sigma in SIGMAS:
        fitted = calibrate_omega(targets, ratio, sigma_sub=float(sigma), measure="hourly",
            efficiency_mode="bilateral", theta=theta, hours_bins=bins,
            group_specs=specs, share_basis=share_basis)
        bridge_errors.append(abs(float(fitted["residual"])))
        groups, _, _ = build_groups(targets, sigma_sub=float(sigma), omega=fitted["omega"],
            group_specs=specs, theta=theta, efficiency_mode="bilateral", hours_bins=bins,
            share_basis=share_basis, resource_costs=resource_costs)
        group_name, p0 = next(iter(groups.items()))
        baseline = solve_group(p0, h0, theta)
        y0, population, nf0 = baseline["Y"], p0["N_total"], baseline["NF"]
        i0 = baseline["NI"] / population
        baseline_errors.append(abs(i0-float(next(iter(specs.values()))["inf_target"])))
        tau0, pi0 = float(p0["formal_wedge"]), float(p0["pi_m"])
        if tau0 <= 0 or pi0 < 0 or abs(tau0*pi0) > 1e-12:
            raise ArithmeticError("Fractional cost reduction requires positive baseline tau and complementarity")
        for cap in CAPS:
            def treated_at(relief):
                treated = deepcopy(groups)
                p = treated[group_name]
                p["formal_wedge"] = tau0*(1.-float(relief))
                p["NF_frozen"] = nf0
                return treated

            # At fixed composition the private cost does not enter gross output.
            frozen = solve_Areq(treated_at(0.), cap, y0, theta,
                                composition="frozen", return_details=True)
            cache = {}

            def evaluate(relief):
                relief = float(relief)
                if not 0 <= relief <= 1:
                    raise ValueError("No extrapolation beyond 0--100% cost reduction")
                if relief in cache:
                    return cache[relief]
                treated = treated_at(relief)
                reform = solve_group(treated[group_name], cap, theta)
                detail = solve_Areq(treated, cap, y0, theta, return_details=True)
                compensated = detail["allocations"][group_name]
                kkt = max(s["kkt_violation"] for s in (baseline, reform, compensated))
                row = dict(efficiency_mode="bilateral", sigma_sub=float(sigma),
                    wedge_relief_national=relief, omega=float(fitted["omega"]),
                    hourly_ratio_target=ratio, hourly_ratio_implied=float(fitted["implied"]),
                    bridge_residual=float(fitted["residual"]), baseline_operator_h0=h0,
                    hours_cap=cap, tau_national=tau0, tau_national_cap=tau0*(1.-relief),
                    pi_national=pi0, Y0=float(y0), Y1=float(reform["Y"]),
                    dY_pct=100.*(reform["Y"]/y0-1.), A_req_pct=float(detail["A_req_pct"]),
                    A_req_signed_pct=float(detail["A_req_pct"]),
                    A_req_nonnegative_pct=float(detail["nonnegative_gain_pct"]),
                    A_req_frozen_pct=float(frozen["A_req_pct"]),
                    baseline_informality_pct=100.*i0,
                    informality_pct=100.*reform["NI"]/population,
                    dInf_pp=100.*(reform["NI"]/population-i0),
                    restoration_residual=float(detail["relative_error"]),
                    frozen_restoration_residual=float(frozen["relative_error"]),
                    max_kkt_violation=float(kkt), baseline_NF=float(nf0),
                    reform_NF=float(reform["NF"]), compensated_NF=float(compensated["NF"]),
                    NF_init=float(p0["NF_init"]), gamma_F=float(p0["gamma_F"]))
                cache[relief] = row
                return row

            panel_rows = [evaluate(r) for r in RELIEFS]
            rows.extend(panel_rows)
            ref = solve_group(treated_at(0.)[group_name], cap, theta)
            qF, qI = ref["eff_hF"], p0["eta_I"]*ref["hI"]*ref["eI"]
            log_odds = float(sigma)*np.log(fitted["omega"]/(1.-fitted["omega"]))
            log_odds += (float(sigma)-1.)*np.log(qF/qI)
            x_product = float(population*expit(log_odds))
            tau_product = pi0*(population-x_product)-p0["gamma_F"]*(x_product-p0["NF_init"])
            unrestricted_relief = float(1.-tau_product/tau0)
            r_min = float(np.clip(unrestricted_relief, 0., 1.))
            minimum_point = evaluate(r_min)
            if minimum_point["A_req_pct"] > min(r["A_req_pct"] for r in panel_rows)+1e-9:
                raise ArithmeticError("Analytical feasible minimum exceeds a grid value")

            thresholds = {}
            for target_pct in (0., 1.):
                multiplier = 1.+target_pct/100.
                def target_residual(relief):
                    p = treated_at(relief)[group_name]
                    return solve_group(p, cap, theta, multiplier)["Y"]/y0-1.
                residual0, residual_min = target_residual(0.), target_residual(r_min)
                if residual0 >= -1e-12:
                    root = 0.
                    state = "already_met_without_cost_reduction"
                elif residual_min < -1e-12:
                    thresholds[str(int(target_pct))] = dict(status="unattainable_on_0_1",
                        target_A_req_pct=target_pct, minimum_relief_fraction=None,
                        minimum_relief_pct=None, minimum_A_req_pct=minimum_point["A_req_pct"],
                        remaining_A_req_gap_pp=minimum_point["A_req_pct"]-target_pct,
                        max_output_residual_at_target_A=float(residual_min))
                    continue
                else:
                    root = float(brentq(target_residual, 0., r_min, xtol=1e-12, rtol=1e-12))
                    state = "attainable"
                point = evaluate(root)
                residual = float(target_residual(root))
                if state == "attainable" and (abs(residual)>1e-9
                        or abs(point["A_req_pct"]-target_pct)>1e-7):
                    raise ArithmeticError("Cost-reduction threshold failed independent output restoration")
                thresholds[str(int(target_pct))] = dict(status=state,
                    target_A_req_pct=target_pct, minimum_relief_fraction=root,
                    minimum_relief_pct=100.*root, output_residual_at_target_A=residual, point=point)

            minimum = dict(relief_fraction=r_min, relief_pct=100.*r_min,
                A_req_pct=minimum_point["A_req_pct"],
                A_req_nonnegative_pct=minimum_point["A_req_nonnegative_pct"],
                product_maximizing_NF=x_product, required_relief_unrestricted=unrestricted_relief,
                location="interior" if 0<r_min<1 else "boundary", point=minimum_point,
                method="CES product maximum and private FOC, restricted to [0,1]")
            frontier = dict(sigma_sub=float(sigma), hours_cap=cap, minimum=minimum,
                thresholds=thresholds,
                grid_max_upward_A_req_step=float(np.max(np.diff([r["A_req_pct"] for r in panel_rows]))))
            frontiers.append(frontier)
            if np.isclose(sigma, 1.326, atol=1e-12, rtol=0):
                # Separate bounded optimization checks the central analytical result.
                opt = minimize_scalar(lambda r:evaluate(r)["A_req_pct"], bounds=(0.,1.),
                                      method="bounded", options={"xatol":1e-11})
                opt_best = min(evaluate(0.)["A_req_pct"], evaluate(1.)["A_req_pct"], float(opt.fun))
                min_optimizer_errors.append(abs(opt_best-minimum_point["A_req_pct"]))
                central[str(int(cap))] = dict(frontier,
                    probes=[evaluate(r) for r in (0.,.1,.2,.5,1.)],
                    bounded_optimizer_relief=float(opt.x), bounded_optimizer_A_req_pct=float(opt.fun),
                    minimum_crosscheck_error=abs(opt_best-minimum_point["A_req_pct"]))
            auxiliary_points.extend(cache.values())

    frame = pd.DataFrame(rows)
    numeric = frame.select_dtypes("number").to_numpy()
    if len(frame) != len(SIGMAS)*len(RELIEFS)*len(CAPS) or not np.isfinite(numeric).all():
        raise ArithmeticError("Incomplete or non-finite two-panel transition map")
    if frame.duplicated(["hours_cap", "sigma_sub", "wedge_relief_national"]).any():
        raise ArithmeticError("Duplicate transition-map grid points")
    anchor_errors = {}
    for cap in CAPS:
        actual = frame.loc[np.isclose(frame.sigma_sub,1.326)
            & np.isclose(frame.wedge_relief_national,0.) & frame.hours_cap.eq(cap)].iloc[0]
        errors = {}
        if len(anchors):
            expected = anchors.loc[anchors.hours_cap.astype(float).eq(cap)].iloc[0]
            for key in ("omega", "Y0", "Y1", "dY_pct", "A_req_pct", "A_req_frozen_pct",
                        "baseline_informality_pct", "informality_pct", "dInf_pp"):
                if key in expected:
                    errors[key] = abs(float(actual[key])-float(expected[key]))
        if bridge is not None:
            errors["canonical_omega"] = abs(float(actual.omega)-float(bridge["omega"]))
        anchor_errors[str(int(cap))] = errors
    max_anchor = max((v for item in anchor_errors.values() for v in item.values()),default=0.)
    all_points = pd.DataFrame(auxiliary_points)
    maxima = dict(max_restoration_residual=float(all_points.restoration_residual.abs().max()),
        max_frozen_restoration_residual=float(all_points.frozen_restoration_residual.abs().max()),
        max_kkt_violation=float(all_points.max_kkt_violation.max()),
        max_bridge_residual=max(bridge_errors), max_baseline_informality_error=max(baseline_errors),
        max_anchor_error=max_anchor, max_minimum_optimizer_error=max(min_optimizer_errors))
    shared_baseline_keys = ["omega", "Y0", "tau_national", "pi_national", "baseline_NF",
                            "NF_init", "gamma_F", "hourly_ratio_target"]
    if frame.groupby("sigma_sub")[shared_baseline_keys].nunique().to_numpy().max() != 1:
        raise ArithmeticError("Baseline state changed between caps or cost reductions")
    if frame.groupby(["sigma_sub","hours_cap"]).A_req_frozen_pct.nunique().max() != 1:
        raise ArithmeticError("Frozen gross-product compensation changed with private cost")
    if (maxima["max_restoration_residual"] > 1e-9
            or maxima["max_frozen_restoration_residual"] > 1e-9
            or maxima["max_kkt_violation"] > 1e-7 or maxima["max_bridge_residual"] > 1e-7
            or maxima["max_baseline_informality_error"] > 1e-9
            or max_anchor > 1e-8 or maxima["max_minimum_optimizer_error"] > 1e-8):
        raise ArithmeticError("Transition experiments failed numerical/bridge/anchor checks")
    checks = dict(status="passed", scenarios=len(frame), scenarios_per_cap=len(SIGMAS)*len(RELIEFS),
        sigma_columns=len(SIGMAS), relief_rows=len(RELIEFS), sigma_grid=SIGMAS.tolist(),
        relief_grid=RELIEFS.tolist(), hours_caps=list(CAPS), efficiency_mode="bilateral",
        group="national_PNAD", baseline="formal_habitual_hours_capped44; informal_hours_observed",
        baseline_operator_h0=h0,
        wedge_change="tau_cap=(1-relief)*tau; pi, gamma, NF_init, omega and baseline output unchanged",
        normalization="baseline tau>=0, pi>=0, tau*pi=0; not separate identification",
        bridge="hourly target fixed; omega and baseline costs recalibrated at each sigma",
        intervention="conditional static national private formalization cost; not identified fiscal policy",
        resource_costs=resource_costs, plotted_measure="signed A_req_pct",
        nonnegative_counterpart="A_req_nonnegative_pct=max(0,A_req_pct)",
        frozen_compensation_invariant_to_relief=True, baseline_shared_across_caps=True,
        thresholds_method="direct root of Y(A=1+target_pct/100,H,r)/Y0-1 on feasible [0,r_min]",
        minimum_method="gross-product CES maximum and private FOC; central bounded-optimizer crosscheck",
        anchor_errors=anchor_errors, central_by_cap=central, frontier_by_sigma=frontiers,
        min_A_req_pct=float(frame.A_req_pct.min()), max_A_req_pct=float(frame.A_req_pct.max()),
        elapsed_seconds=time.perf_counter()-started, **maxima)
    return frame, checks


def main():
    paper = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replication-root",type=Path,default=(paper.parent/"replication_package" if (paper.parent/"replication_package"/"run_all.py").is_file() else paper.parent))
    parser.add_argument("--run-id",default="20260905_005724_846373")
    parser.add_argument("--output-dir",type=Path)
    args = parser.parse_args()
    folder = args.replication_root/"output"/"runs"/args.run_id/PRIMARY_FOLDER
    inputs = json.loads((folder/"INPUTS.json").read_text(encoding="utf-8-sig"))
    inputs["bridges"] = json.loads((folder/"BRIDGE.json").read_text(encoding="utf-8-sig"))
    frame, checks = compute_transition_map(inputs,args.replication_root,pd.read_csv(folder/"RESULTS.csv"))
    if args.output_dir is not None:
        args.output_dir.mkdir(parents=True,exist_ok=True)
        frame.to_csv(args.output_dir/"transition_map.csv",index=False,encoding="utf-8-sig")
        (args.output_dir/"transition_map_checks.json").write_text(
            json.dumps(checks,ensure_ascii=False,indent=2),encoding="utf-8")
        (args.output_dir/"transition_map_summary.json").write_text(json.dumps(
            {key:checks[key] for key in ("status","scenarios","central_by_cap","min_A_req_pct",
                                        "max_A_req_pct","elapsed_seconds")},
            ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({key:checks[key] for key in ("status","scenarios","sigma_columns","relief_rows",
        "hours_caps","min_A_req_pct","max_A_req_pct","max_restoration_residual",
        "max_kkt_violation","max_anchor_error","elapsed_seconds")},indent=2))


if __name__ == "__main__":
    main()
