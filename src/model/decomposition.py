"""Sequential exact output accounting, using one baseline-output denominator."""
import numpy as np
from .efficiency import eff, hours_distribution
from .ces_aggregator import ces_agg
from .production import production


def output_decomposition(groups,baseline_solutions,reform_solutions,h0,h1,theta):
    """Order: physical hours -> efficiency -> formal/informal reallocation.

    At the physical step each hours bin retains its own baseline efficiency.
    At the efficiency step update efficiency at capped hours, still holding
    baseline employment. The last step changes composition to the optimum.
    Capital and productivity remain fixed. Contributions are order-dependent,
    add exactly in levels, and all percentages divide by baseline output.
    """
    levels = {"baseline":sum(s["Y"] for s in baseline_solutions.values()),
              "physical_hours":0.,"efficiency":0.,
              "reallocation":sum(s["Y"] for s in reform_solutions.values())}
    for name,p in groups.items():
        weights,bins = hours_distribution(p.get("theta",theta),p.get("hours_bins"))
        old,new = np.minimum(bins,h0),np.minimum(bins,h1)
        mode = p.get("efficiency_mode","bilateral")
        e0 = eff(old,p["kappa"],p["h_star"],mode)
        e1 = eff(new,p["kappa"],p["h_star"],mode)
        eI = eff(p["hI"],p["kappa"],p["h_star"],mode)
        base = baseline_solutions[name]
        LI = p["eta_I"]*base["NI"]*p["hI"]*eI
        for key,e in (("physical_hours",e0),("efficiency",e1)):
            LF = base["NF"]*float(np.dot(weights,new*e))
            L = ces_agg(LF,LI,p["omega"],p["sigma_sub"])
            levels[key] += float(production(p["A"],p["K"],p["alpha"],L))
    Y0,YH,YE,Y1 = [levels[k] for k in ("baseline","physical_hours","efficiency","reallocation")]
    result = {"hours_pct":100.*(YH-Y0)/Y0,
              "efficiency_pct":100.*(YE-YH)/Y0,
              "reallocation_pct":100.*(Y1-YE)/Y0,
              "total_pct":100.*(Y1-Y0)/Y0,"levels":levels,
              "order":["physical_hours","efficiency","formal_informal_reallocation"],
              "denominator":"baseline gross output Y0"}
    result["sum_error_pct"] = (result["hours_pct"]+result["efficiency_pct"]
                               +result["reallocation_pct"]-result["total_pct"])
    return result

