# -*- coding: utf-8 -*-
"""GHH utility and compensating variation."""


def ghh_composite(C, h, nu, psi):
    """GHH composite: C - psi * h^(1+nu) / (1+nu)"""
    return C - psi * h**(1.0 + nu) / (1.0 + nu)


def compensating_variation(C0, h0, C1, h1, nu, psi):
    """DeltaCV = composite_1 / composite_0 - 1"""
    comp0 = ghh_composite(C0, h0, nu, psi)
    comp1 = ghh_composite(C1, h1, nu, psi)
    return float(comp1 / max(comp0, 1e-15) - 1.0)
