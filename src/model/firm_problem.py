# -*- coding: utf-8 -*-
"""Firm optimization: choose NF to maximize profits."""

import numpy as np
from .production import production
from .ces_aggregator import ces_agg
from .efficiency import eff, formal_hours_hetero


def informal_cost(NI, pi_m):
    """Convex cost of informality: 0.5 * pi_m * NI^2"""
    return 0.5 * pi_m * NI**2


def solve_NF(N_total, hF, hI, A, K, alpha, omega, sigma_sub, eta_I,
             kappa, h_star, formal_wedge, pi_m, gamma_F, NF_prev, theta,
             grid=4001):
    """
    Firm chooses NF to maximize Y - wedge*NF - informal_cost - adjustment_cost.
    Grid search over NF in [0, N_total].
    Returns dict with equilibrium allocation.
    """
    NF_grid = np.linspace(0, N_total, grid)
    NI_grid = N_total - NF_grid

    hF_avg, eff_hF = formal_hours_hetero(hF, kappa, h_star, theta)
    eI = eff(hI, kappa, h_star)

    LF = NF_grid * eff_hF
    LI = eta_I * NI_grid * hI * eI
    L = ces_agg(LF, LI, omega, sigma_sub)
    Y = production(A, K, alpha, L)

    adj = 0.5 * gamma_F * (NF_grid - NF_prev)**2
    phi = informal_cost(NI_grid, pi_m)

    obj = Y - formal_wedge * NF_grid - phi - adj
    j = int(np.argmax(obj))

    NF = float(NF_grid[j])
    NI = float(NI_grid[j])
    Ys = float(Y[j])
    C = Ys - float(adj[j])

    hours_total = NF * hF_avg + NI * hI
    h_avg = hours_total / max(N_total, 1e-15)
    eF_avg = eff_hF / max(hF_avg, 1e-15)

    return {
        "NF": NF, "NI": NI, "Y": Ys, "C": C,
        "informality": NI / max(N_total, 1e-15),
        "hours_total": hours_total,
        "h_avg": h_avg,
        "Y_per_hour": Ys / max(hours_total, 1e-15),
        "eF": eF_avg, "eI": eI,
        "hF_avg": hF_avg,
        "adj": float(adj[j]),
        "phi": float(phi[j]),
    }
