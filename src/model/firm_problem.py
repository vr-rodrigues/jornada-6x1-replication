"""Continuous concave formal/informal choice with checked FOCs and boundaries.

The private objective is Y-tau*NF-pi*NI**2/2-gamma*(NF-NF_prev)**2/2.
Default resource accounting treats tau and pi payments as transfers rebated
to the representative household. Adjustment is a real resource cost:
C + adjustment = Y. With resource_costs=True, tau*NF and pi*NI**2/2 are
also destroyed resources. Neither specification identifies incidence.
"""
import numpy as np
from scipy.optimize import brentq
from .production import production
from .ces_aggregator import ces_agg, ces_marginals
from .efficiency import eff, formal_hours_hetero


def informal_cost(NI, pi_m):
    return 0.5 * pi_m * NI**2


def production_marginals(NF, NI, hF_eff, hI_eff, eta_I, A, K, alpha,
                         omega, sigma_sub):
    """Holding the other workforce fixed: productive revenue per worker/week."""
    LF, LI = NF * hF_eff, eta_I * NI * hI_eff
    L = ces_agg(LF, LI, omega, sigma_sub)
    Y = float(production(A, K, alpha, L))
    if A == 0:
        return {"Y": 0., "L": L, "MP_NF": 0., "MP_NI": 0.}
    dF, dI = ces_marginals(LF, LI, omega, sigma_sub)
    mpl = (1 - alpha) * Y / L
    return {"Y": Y, "L": L, "MP_NF": mpl*dF*hF_eff,
            "MP_NI": mpl*dI*eta_I*hI_eff}


def evaluate_at_NF(NF, N_total, hF, hI, A, K, alpha, omega, sigma_sub, eta_I,
                   kappa, h_star, formal_wedge, pi_m, gamma_F, NF_prev, theta,
                   efficiency_mode="bilateral", hours_bins=None,
                   resource_costs=False):
    """Evaluate one feasible allocation, without reoptimizing its composition."""
    if N_total <= 0 or not 0 <= NF <= N_total:
        raise ValueError("Require N_total>0 and NF in [0,N_total]")
    hF_avg, eff_hF = formal_hours_hetero(hF, kappa, h_star, theta,
                                       efficiency_mode, hours_bins)
    eI = eff(hI, kappa, h_star, efficiency_mode)
    NI = N_total - NF
    L = ces_agg(NF * eff_hF, eta_I * NI * hI * eI, omega, sigma_sub)
    Y = float(production(A, K, alpha, L))
    adj = .5 * gamma_F * (NF - NF_prev)**2
    phi = informal_cost(NI, pi_m)
    tau_payment = formal_wedge * NF
    resource_cost = adj + (phi + tau_payment if resource_costs else 0.)
    hours = NF*hF_avg + NI*hI
    return {"NF": float(NF), "NI": float(NI), "Y": Y, "C": Y-resource_cost,
            "informality": NI/N_total, "hours_total": hours,
            "h_avg": hours/N_total, "Y_per_hour": Y/hours, "L": float(L),
            "eF": eff_hF/hF_avg, "eI": eI, "eff_hF": eff_hF,
            "hF_avg": hF_avg, "hI": hI, "adj": adj, "phi": phi,
            "formal_payment": tau_payment, "resource_cost": resource_cost,
            "objective": Y-tau_payment-phi-adj,
            "resource_accounting": "all_costs_resources" if resource_costs else "wedges_rebated_adjustment_resource"}


def solve_NF(N_total, hF, hI, A, K, alpha, omega, sigma_sub, eta_I,
             kappa, h_star, formal_wedge, pi_m, gamma_F, NF_prev, theta,
             grid=4001, efficiency_mode="bilateral", hours_bins=None,
             resource_costs=False):
    """Global solution by monotone FOC, with explicit endpoint comparisons.

    grid is retained solely for call compatibility; it no longer discretizes
    allocations. Positive CES elasticity, 0<alpha<1 and convex nonnegative
    costs imply a concave objective, hence the KKT conditions are sufficient.
    """
    if (N_total <= 0 or eta_I <= 0 or hI <= 0 or
            min(formal_wedge, pi_m, gamma_F) < 0 or not 0 <= NF_prev <= N_total):
        raise ValueError("Invalid labor/endowment/cost parameters")
    hF_avg, eff_hF = formal_hours_hetero(hF, kappa, h_star, theta,
                                       efficiency_mode, hours_bins)
    eff_hI = hI * eff(hI, kappa, h_star, efficiency_mode)

    def derivative(fraction):
        NF = N_total*fraction
        mp = production_marginals(NF, N_total-NF, eff_hF, eff_hI, eta_I,
                                  A, K, alpha, omega, sigma_sub)
        return (mp["MP_NF"]-mp["MP_NI"]-formal_wedge
                + pi_m*(N_total-NF)-gamma_F*(NF-NF_prev))

    # Exact one-sided derivative limits establish whether a boundary can be
    # optimal. Mixed CES with positive A and alpha has +infinity/-infinity
    # at the lower/upper endpoints; finite costs cannot create a true corner.
    cost_lower = -formal_wedge+pi_m*N_total+gamma_F*NF_prev
    cost_upper = -formal_wedge-gamma_F*(N_total-NF_prev)
    if A == 0:
        lower_limit,upper_limit = cost_lower,cost_upper
    elif omega == 1:
        y_full = float(production(A,K,alpha,N_total*eff_hF))
        lower_limit = float("inf")
        upper_limit = (1-alpha)*y_full/N_total+cost_upper
    elif omega == 0:
        y_full = float(production(A,K,alpha,N_total*eta_I*eff_hI))
        lower_limit = -(1-alpha)*y_full/N_total+cost_lower
        upper_limit = -float("inf")
    else:
        lower_limit,upper_limit = float("inf"),-float("inf")
    eps = 1e-13
    lower, upper = derivative(eps), derivative(1.-eps)
    if lower_limit <= 0:
        fraction, boundary = 0., "lower"
    elif upper_limit >= 0:
        fraction, boundary = 1., "upper"
    else:
        if lower <= 0 or upper >= 0:
            eps = 1e-15
            lower,upper = derivative(eps),derivative(1.-eps)
        if lower <= 0 or upper >= 0:
            raise RuntimeError("Interior optimum too close to a boundary to certify at floating-point precision")
        fraction = brentq(derivative, eps, 1.-eps, xtol=5e-15, rtol=1e-14)
        boundary = "interior"

    args = (N_total,hF,hI,A,K,alpha,omega,sigma_sub,eta_I,kappa,h_star,
            formal_wedge,pi_m,gamma_F,NF_prev,theta)
    opts = dict(efficiency_mode=efficiency_mode,hours_bins=hours_bins,
                resource_costs=resource_costs)
    sol = evaluate_at_NF(N_total*fraction, *args, **opts)
    left = evaluate_at_NF(0., *args, **opts)
    right = evaluate_at_NF(N_total, *args, **opts)
    scale = max(1., abs(sol["objective"]), abs(left["objective"]), abs(right["objective"]))
    if max(left["objective"], right["objective"]) > sol["objective"] + 1e-10*scale:
        raise RuntimeError("Continuous optimizer failed endpoint objective verification")
    derivative_at_solution = (derivative(fraction) if boundary == "interior"
                              else lower_limit if boundary == "lower" else upper_limit)
    violation = (abs(derivative_at_solution) if boundary == "interior" else
                 max(0., derivative_at_solution) if boundary == "lower"
                 else max(0., -derivative_at_solution))
    sol.update({"foc_residual": float(derivative_at_solution),
                "kkt_violation": float(violation), "boundary": boundary,
                "boundary_objectives": [left["objective"], right["objective"]],
                "optimizer": "continuous_brent_foc_with_endpoint_checks"})
    if violation > 1e-7 * max(1., abs(formal_wedge), abs(pi_m*N_total), abs(sol["Y"]/N_total)):
        raise RuntimeError(f"Unresolved first-order condition: {violation}")
    return sol


def solve_group(pars, h_cap, theta, A_mult=1., composition="reoptimized"):
    """Shared adapter: honors group-specific hours distributions and technology."""
    args = (pars["N_total"], h_cap, pars["hI"], pars["A"]*A_mult,
            pars["K"], pars["alpha"], pars["omega"], pars["sigma_sub"],
            pars["eta_I"], pars["kappa"], pars["h_star"],
            pars["formal_wedge"], pars["pi_m"], pars["gamma_F"],
            pars["NF_init"], pars.get("theta",theta))
    opts = dict(efficiency_mode=pars.get("efficiency_mode","bilateral"),
                hours_bins=pars.get("hours_bins"),
                resource_costs=pars.get("resource_costs",False))
    if composition == "reoptimized":
        return solve_NF(*args, **opts)
    if composition == "frozen":
        return evaluate_at_NF(pars.get("NF_frozen",pars["NF_init"]), *args, **opts)
    raise ValueError("composition must be reoptimized or frozen")

