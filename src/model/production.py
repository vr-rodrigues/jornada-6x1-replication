# -*- coding: utf-8 -*-
"""Cobb-Douglas production technology."""

import numpy as np


def production(A, K, alpha, L):
    """Y = A * K^alpha * L^(1-alpha)"""
    if A < 0 or K <= 0 or not 0 < alpha < 1 or np.any(np.asarray(L) < 0):
        raise ValueError("Production requires A>=0, K>0, 0<alpha<1 and L>=0")
    return A * K**alpha * np.asarray(L)**(1 - alpha)


def mpl_L(A, K, alpha, L):
    """Marginal product of labor: (1-alpha) * Y / L"""
    Y = production(A, K, alpha, L)
    return (1 - alpha) * Y / np.maximum(L, 1e-15)
