# -*- coding: utf-8 -*-
"""A_req solver: find TFP gain to maintain GDP under reduced hours."""

from .firm_problem import solve_NF


def solve_Areq(groups, hF_cap, Y_target, theta, grid=3001):
    """
    Find A_mult such that sum Y_g(A*A_mult, hF_cap) = Y_target.
    Returns A_req in percent: 100*(A_mult - 1).
    """

    def Y_at(A_mult):
        total = 0.0
        for pars in groups.values():
            sol = solve_NF(
                pars["N_total"], hF_cap, pars["hI"],
                pars["A"] * A_mult, pars["K"], pars["alpha"],
                pars["omega"], pars["sigma_sub"], pars["eta_I"],
                pars["kappa"], pars["h_star"],
                pars["formal_wedge"], pars["pi_m"],
                pars["gamma_F"], pars["NF_init"], theta, grid)
            total += sol["Y"]
        return total

    Y1 = Y_at(1.0)
    if Y1 >= Y_target:
        return 0.0

    A_lo, A_hi = 1.0, (Y_target / max(Y1, 1e-15)) * 1.3
    for _ in range(35):
        A_mid = 0.5 * (A_lo + A_hi)
        if Y_at(A_mid) < Y_target:
            A_lo = A_mid
        else:
            A_hi = A_mid
        if (A_hi - A_lo) < 1e-5 * A_lo:
            break
    return 100.0 * (0.5 * (A_lo + A_hi) - 1.0)
