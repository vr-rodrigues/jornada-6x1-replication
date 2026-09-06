# -*- coding: utf-8 -*-
"""Welfare utilities and compensating variation diagnostics."""

import math


def ghh_composite(C, h, nu, psi):
    """GHH composite: C - psi * h^(1+nu) / (1+nu)"""
    return C - psi * h**(1.0 + nu) / (1.0 + nu)


def ghh_change(C0, h0, C1, h1, nu, psi):
    """Fractional change in the GHH composite, NOT consumption equivalent."""
    comp0 = ghh_composite(C0, h0, nu, psi)
    comp1 = ghh_composite(C1, h1, nu, psi)
    if comp0 <= 0:
        raise ValueError("GHH percent change requires a positive baseline composite")
    return float((comp1-comp0)/comp0)


def consumption_equivalent(C0, h0, C1, h1, nu, psi):
    """CE=[C1-C0-v(h1)+v(h0)]/C0, with unchanged baseline hours in CE."""
    if C0 <= 0:
        raise ValueError("Consumption equivalent requires positive baseline consumption")
    return float((ghh_composite(C1,h1,nu,psi)-ghh_composite(C0,h0,nu,psi))/C0)


def compensating_variation(C0, h0, C1, h1, nu, psi):
    """Compatibility name now returns the correctly normalized GHH CE."""
    return consumption_equivalent(C0,h0,C1,h1,nu,psi)


def crra_utility(C, gamma):
    """CRRA flow utility from consumption."""
    C = max(float(C), 1e-15)
    if abs(gamma - 1.0) < 1e-10:
        return math.log(C)
    return (C ** (1.0 - gamma) - 1.0) / (1.0 - gamma)


def separable_composite(C, h, gamma, nu, chi):
    """Separable CRRA utility: u(C) - chi*h^(1+nu)/(1+nu)."""
    return crra_utility(C, gamma) - chi * h ** (1.0 + nu) / (1.0 + nu)


def calibrate_separable_chi(w_hourly, C, h, gamma, nu):
    """Calibrate chi from MRS=w: chi*h^nu / C^(-gamma) = w."""
    C = max(float(C), 1e-15)
    return float(w_hourly * C ** (-gamma) / max(h ** nu, 1e-15))


def separable_consumption_equivalent(C0, h0, C1, h1, gamma, nu, chi):
    """Baseline consumption-equivalent welfare change.

    Returns lambda such that U((1+lambda)*C0, h0) = U(C1, h1).
    Positive values mean the reform allocation is preferred to baseline under
    the separable diagnostic utility.
    """
    target = separable_composite(C1, h1, gamma, nu, chi)
    utility_needed_from_consumption = target + chi * h0 ** (1.0 + nu) / (1.0 + nu)
    if abs(gamma - 1.0) < 1e-10:
        c_equiv = math.exp(utility_needed_from_consumption)
    else:
        c_power = 1.0 + (1.0 - gamma) * utility_needed_from_consumption
        if c_power <= 0.0:
            return float("nan")
        c_equiv = c_power ** (1.0 / (1.0 - gamma))
    return float(c_equiv / max(float(C0), 1e-15) - 1.0)
