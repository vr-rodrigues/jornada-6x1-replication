# -*- coding: utf-8 -*-
"""CES aggregator for formal/informal labor."""

import numpy as np


def ces_agg(LF, LI, omega, sigma_sub):
    """
    CES aggregator: L = [omega*LF^rho + (1-omega)*LI^rho]^(1/rho)
    where rho = (sigma_sub - 1) / sigma_sub.
    Cobb-Douglas limit when sigma -> 1.
    """
    rho = (sigma_sub - 1.0) / sigma_sub
    if abs(rho) < 1e-12:
        return np.maximum(LF, 1e-15)**omega * np.maximum(LI, 1e-15)**(1 - omega)
    LF_safe = np.maximum(LF, 1e-15)
    LI_safe = np.maximum(LI, 1e-15)
    inside = omega * LF_safe**rho + (1 - omega) * LI_safe**rho
    return np.maximum(inside, 1e-15)**(1.0 / rho)


def wage_premium(NF, NI, hF_eff, hI_eff, eta_I, omega, sigma_sub):
    """
    Formal/informal wage premium from CES FOC:
    R = (omega/(1-omega)) * (LF/LI)^(rho-1) * z
    where z = hF_eff / (eta_I * hI_eff).
    """
    rho = (sigma_sub - 1.0) / sigma_sub
    LF = NF * hF_eff
    LI = eta_I * NI * hI_eff
    z = hF_eff / max(eta_I * hI_eff, 1e-15)
    ratio = max(LF, 1e-15) / max(LI, 1e-15)
    return (omega / (1 - omega)) * ratio**(rho - 1) * z
