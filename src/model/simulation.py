"""Shared national/sectoral simulation, resource accounting and exact diagnostics."""
import csv
import os
from .firm_problem import solve_group
from .calibration import calibrate_psi
from .areq_solver import solve_Areq
from .welfare import ghh_change, consumption_equivalent, ghh_composite
from .groups import build_groups
from .decomposition import output_decomposition


def load_targets(data_final_path):
    targets = {}
    with open(os.path.join(data_final_path,"calibration_targets.csv"),encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            targets[row["target_id"]] = {"value":float(row["value"]),
                                          "source":row["source"],
                                          "notes":row.get("notes","")}
    return targets


def _aggregate(solutions,N_total):
    out = {key:sum(s[field] for s in solutions.values())
           for key,field in (("Y","Y"),("C","C"),("hours","hours_total"),
                             ("NI","NI"),("adjustment_cost","adj"),
                             ("resource_cost","resource_cost"))}
    out.update({"inf":out["NI"]/N_total,"h_avg":out["hours"]/N_total,
                "solutions":solutions})
    return out


def simulate_groups(groups,h0,h1,theta,nu_ghh=2.0):
    """Fixed-capital representative-household accounting for arbitrary groups.

    Welfare uses per-worker consumption and mean physical hours as in the
    original representative-agent specification; it does not identify
    within-household dispersion, wage bargaining or distributional incidence.
    """
    N_total = sum(p["N_total"] for p in groups.values())
    if N_total <= 0:
        raise ValueError("Positive population required")
    baseline_solutions = {g:solve_group(p,h0,theta) for g,p in groups.items()}
    # The comparison explicitly freezes the actual baseline allocation.
    groups = {g:{**p,"NF_frozen":baseline_solutions[g]["NF"]} for g,p in groups.items()}
    reform_solutions = {g:solve_group(p,h1,theta) for g,p in groups.items()}
    baseline = _aggregate(baseline_solutions,N_total)
    reform = _aggregate(reform_solutions,N_total)
    labor_income = sum((1.-groups[g]["alpha"])*s["Y"]
                       for g,s in baseline_solutions.items())
    w_hourly = labor_income/baseline["hours"]
    psi = calibrate_psi(w_hourly,baseline["h_avg"],nu_ghh)
    c0,c1 = baseline["C"]/N_total,reform["C"]/N_total
    ghh = ghh_change(c0,baseline["h_avg"],c1,reform["h_avg"],nu_ghh,psi)
    ce = consumption_equivalent(c0,baseline["h_avg"],c1,reform["h_avg"],nu_ghh,psi)
    baseline["GHH_composite_pc"] = ghh_composite(c0,baseline["h_avg"],nu_ghh,psi)
    reform["GHH_composite_pc"] = ghh_composite(c1,reform["h_avg"],nu_ghh,psi)
    restoration = solve_Areq(groups,h1,baseline["Y"],theta,return_details=True)
    frozen_restoration = solve_Areq(groups,h1,baseline["Y"],theta,
                                    composition="frozen",return_details=True)
    decomposition = output_decomposition(groups,baseline_solutions,reform_solutions,h0,h1,theta)
    results = {"A_req_pct":restoration["A_req_pct"],
               "A_req_frozen_pct":frozen_restoration["A_req_pct"],
               "dY_pct":100.*(reform["Y"]/baseline["Y"]-1.),
               "dInf_pp":100.*(reform["inf"]-baseline["inf"]),
               "dGHH_pct":100.*ghh,"CE_pct":100.*ce,
               # Deprecated compatibility label: percentage change of the
               # composite. New tables must explicitly use dGHH_pct or CE_pct.
               "dCV_pct":100.*ghh,
               "dYph_pct":100.*((reform["Y"]/reform["hours"])/
                                (baseline["Y"]/baseline["hours"])-1.),
               "wage_premium_implied":None}
    return {"groups":groups,"psi":psi,"nu_ghh":nu_ghh,
            "baseline":baseline,"reform":reform,"results":results,
            "decomposition":decomposition,"A_req_details":restoration,
            "A_req_frozen_details":frozen_restoration,
            "welfare_definition":{"dGHH_pct":"100*(GHH1-GHH0)/GHH0",
                                   "CE_pct":"100*(C1-C0-v(h1)+v(h0))/C0",
                                   "dCV_pct":"deprecated alias of dGHH_pct, not CE",
                                   "unit":"per worker; representative mean physical hours",
                                   "incidence":"not identified by this representative-agent model"},
            "resource_constraint":("C + adjustment + tau*NF + pi*NI^2/2 = Y"
                                    if all(p.get("resource_costs",False) for p in groups.values())
                                    else "By group: C=Y-resource_cost. Default C+adjustment=Y; tau and pi are rebated transfers."),
            "capital":"fixed group capital; no endogenous capital adjustment equation"}


def run_simulation(targets,sigma_sub=1.15,omega=.622,theta=None,group_specs=None,
                   efficiency_mode="bilateral",hours_bins=None,share_basis="formal",
                   resource_costs=False,kappa_override=None):
    groups,kappa,theta = build_groups(targets,sigma_sub,omega,group_specs,theta,
                                      efficiency_mode,hours_bins,share_basis,
                                      resource_costs,kappa_override)
    result = simulate_groups(groups,targets["H0"]["value"],targets["H1"]["value"],theta)
    result.update({"sigma_sub":sigma_sub,"omega":omega,"kappa":kappa,
                   "efficiency_mode":efficiency_mode,"theta":theta.tolist(),
                   "share_basis":share_basis})
    return result


def welfare_schedule(targets,groups,Y_base,C_base_pc,h_avg_base,inf_base,
                     N_total,theta,nu_ghh=2.,psi=None,h_range=range(44,29,-1)):
    if psi is None:
        labor_income = sum((1.-p["alpha"])*solve_group(p,targets["H0"]["value"],theta)["Y"]
                           for p in groups.values())
        psi = calibrate_psi(labor_income/(N_total*h_avg_base),h_avg_base,nu_ghh)
    rows = []
    for cap in h_range:
        agg = _aggregate({g:solve_group(p,cap,theta) for g,p in groups.items()},N_total)
        ghh = ghh_change(C_base_pc,h_avg_base,agg["C"]/N_total,agg["h_avg"],nu_ghh,psi)
        ce = consumption_equivalent(C_base_pc,h_avg_base,agg["C"]/N_total,agg["h_avg"],nu_ghh,psi)
        rows.append({"h1":cap,"A_req_pct":solve_Areq(groups,cap,Y_base,theta),
                     "A_req_frozen_pct":solve_Areq(groups,cap,Y_base,theta,composition="frozen"),
                     "dY_pct":100.*(agg["Y"]/Y_base-1.),
                     "dGHH_pct":100.*ghh,"CE_pct":100.*ce,"dCV_pct":100.*ghh,
                     "dInf_pp":100.*(agg["inf"]-inf_base)})
    return rows

