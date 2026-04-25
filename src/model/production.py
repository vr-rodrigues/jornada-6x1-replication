# -*- coding: utf-8 -*-
"""Cobb-Douglas production technology."""

import numpy as np


def production(A, K, alpha, L):
    """Y = A * K^alpha * L^(1-alpha)"""
    return A * K**alpha * np.maximum(L, 1e-15)**(1 - alpha)


def mpl_L(A, K, alpha, L):
    """Marginal product of labor: (1-alpha) * Y / L"""
    Y = production(A, K, alpha, L)
    return (1 - alpha) * Y / np.maximum(L, 1e-15)
