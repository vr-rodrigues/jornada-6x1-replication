# -*- coding: utf-8 -*-
"""Calibration routines: wedge, pi_m, psi."""

from .firm_problem import solve_NF


def calibrate_wedge(target_inf, N_total, h0, hI, A, K, alpha, omega,
                    sigma_sub, eta_I, kappa, h_star, pi_m, theta,
                    lo=0.0, hi=25.0, n_iter=60, grid=3001):
    """Find formal_wedge such that equilibrium informality = target_inf."""

    def inf_at(wedge):
        sol = solve_NF(N_total, h0, hI, A, K, alpha, omega, sigma_sub, eta_I,
                       kappa, h_star, wedge, pi_m, 0.0,
                       N_total * (1 - target_inf), theta, grid)
        return sol["informality"]

    inf_lo = inf_at(lo)
    inf_hi = inf_at(hi)

    if target_inf <= inf_lo + 1e-10:
        return lo
    if target_inf >= inf_hi - 1e-10:
        return hi

    a, b = lo, hi
    for _ in range(n_iter):
        m = 0.5 * (a + b)
        if inf_at(m) > target_inf:
            b = m
        else:
            a = m
    return 0.5 * (a + b)


def calibrate_pi_m(target_inf, N_total, h0, hI, A, K, alpha, omega,
                   sigma_sub, eta_I, kappa, h_star, theta,
                   lo=0.0, hi=1.0, grid=2001):
    """Find pi_m such that informality at wedge=0 equals target_inf."""

    def inf_at(pm):
        sol = solve_NF(N_total, h0, hI, A, K, alpha, omega, sigma_sub, eta_I,
                       kappa, h_star, 0.0, pm, 0.0,
                       N_total * (1 - target_inf), theta, grid)
        return sol["informality"]

    if inf_at(lo) <= target_inf + 1e-10:
        return lo

    while inf_at(hi) > target_inf + 1e-10 and hi < 1e6:
        hi *= 2.0

    a, b = lo, hi
    for _ in range(70):
        m = 0.5 * (a + b)
        if inf_at(m) > target_inf:
            a = m
        else:
            b = m
    return b


def calibrate_psi(w_hourly, h, nu):
    """From GHH FOC: psi * h^nu = w => psi = w / h^nu"""
    return w_hourly / max(h**nu, 1e-15)
