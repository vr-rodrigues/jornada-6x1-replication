# -*- coding: utf-8 -*-
"""Group construction for heterogeneous firm-size analysis."""

import numpy as np
from .efficiency import calibrate_kappa, formal_hours_avg
from .firm_problem import solve_NF
from .calibration import calibrate_wedge, calibrate_pi_m


# Default group specifications
DEFAULT_GROUP_SPECS = {
    "Pequenas": {"share": 0.59, "inf_target": 0.50, "gamma_F": 0.12, "K_share": 0.35},
    "Grandes":  {"share": 0.41, "inf_target": 0.20, "gamma_F": 0.03, "K_share": 0.65},
}


def build_groups(targets, sigma_sub=1.15, omega=0.622,
                 group_specs=None, theta=None):
    """
    Build calibrated group parameters from targets dict.

    Args:
        targets: dict from calibration_targets.csv
        sigma_sub: CES substitution elasticity (default: 1.15, central of MNR-disciplined interval)
        omega: CES formal weight (default: 0.622 = 1 - narrow PNAD informality 2025)
        group_specs: dict of group specifications (default: DEFAULT_GROUP_SPECS)
        theta: hours distribution array (default: from targets)

    Returns:
        groups: dict of group parameter dicts
        kappa: calibrated kappa
        theta: theta array used
    """
    if group_specs is None:
        group_specs = DEFAULT_GROUP_SPECS

    alpha = targets["ALPHA"]["value"]
    eta_I = targets["ETA_I"]["value"]
    e_q = targets["E_Q"]["value"]
    h0 = targets["H0"]["value"]
    h1 = targets["H1"]["value"]
    h_star = targets["H_STAR"]["value"]
    hI = targets["HI"]["value"]
    N_total = targets["N_TOTAL"]["value"]

    if theta is None:
        theta = np.array([
            targets["THETA_36"]["value"],
            targets["THETA_40"]["value"],
            targets["THETA_44"]["value"],
        ])

    h_ref = formal_hours_avg(h0, theta)
    kappa = calibrate_kappa(h_ref, h_star, e_q)

    common = {
        "A": 1.0, "alpha": alpha, "h0": h0, "h1": h1, "hI": hI,
        "h_star": h_star, "omega": omega, "sigma_sub": sigma_sub,
        "eta_I": eta_I, "kappa": kappa,
    }

    groups = {}
    for gname, spec in group_specs.items():
        N_g = N_total * spec["share"]
        K_g = 1.0 * spec["K_share"]

        # Check if pi_m is needed (wedge=0 gives too much informality)
        pi_m_g = 0.0
        sol_w0 = solve_NF(N_g, h0, hI, 1.0, K_g, alpha, omega, sigma_sub,
                          eta_I, kappa, h_star, 0.0, pi_m_g, 0.0,
                          N_g * (1 - spec["inf_target"]), theta)
        if sol_w0["informality"] > spec["inf_target"] + 1e-10:
            pi_m_g = calibrate_pi_m(spec["inf_target"], N_g, h0, hI,
                                    1.0, K_g, alpha, omega, sigma_sub,
                                    eta_I, kappa, h_star, theta)

        wedge = calibrate_wedge(spec["inf_target"], N_g, h0, hI,
                                1.0, K_g, alpha, omega, sigma_sub,
                                eta_I, kappa, h_star, pi_m_g, theta)

        groups[gname] = {
            **common,
            "N_total": N_g, "K": K_g,
            "gamma_F": spec["gamma_F"],
            "pi_m": pi_m_g,
            "formal_wedge": wedge,
            "NF_init": N_g * (1 - spec["inf_target"]),
        }

    return groups, kappa, theta
