# -*- coding: utf-8 -*-
"""Efficiency function e(h) and hours heterogeneity."""

import numpy as np

HOURS_BINS = np.array([36.0, 40.0, 44.0])


def eff(h, kappa, h_star):
    """Efficiency: e(h) = exp{-kappa * (h - h_star)^2}"""
    return float(np.exp(-kappa * (h - h_star)**2))


def calibrate_kappa(h_ref, h_star, e_q):
    """
    Calibrate kappa from hours-output elasticity.
    d ln(h*e(h)) / d ln(h) = 1 - 2*kappa*h*(h - h_star) = e_q
    => kappa = (1 - e_q) / (2 * h_ref * (h_ref - h_star))
    """
    if abs(h_ref - h_star) < 1e-12:
        return 0.0
    return (1.0 - e_q) / (2.0 * h_ref * (h_ref - h_star))


def formal_hours_avg(h_cap, theta):
    """Average formal hours under cap, weighted by theta."""
    h_capped = np.minimum(HOURS_BINS, float(h_cap))
    return float(np.sum(theta * h_capped))


def formal_hours_hetero(h_cap, kappa, h_star, theta):
    """
    Returns (avg_hours, effective_hours_per_worker) under cap.
    effective = sum(theta_b * h_b * e(h_b)) for each hours bin b.
    """
    h_capped = np.minimum(HOURS_BINS, float(h_cap))
    avg_h = float(np.sum(theta * h_capped))
    e_bins = np.exp(-kappa * (h_capped - h_star)**2)
    eff_h = float(np.sum(theta * h_capped * e_bins))
    return avg_h, eff_h
