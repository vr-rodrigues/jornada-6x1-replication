"""CES technology, including exact zero-input and Cobb-Douglas limits."""
import numpy as np


def ces_agg(LF, LI, omega, sigma_sub):
    if not 0 <= omega <= 1 or sigma_sub <= 0:
        raise ValueError("CES requires omega in [0,1], sigma_sub > 0")
    LF, LI = np.broadcast_arrays(np.asarray(LF, dtype=float), np.asarray(LI, dtype=float))
    if np.any(LF < 0) or np.any(LI < 0):
        raise ValueError("Labor inputs cannot be negative")
    if omega == 1:
        result = LF
    elif omega == 0:
        result = LI
    else:
        rho = (sigma_sub - 1.0) / sigma_sub
        positive = (LF > 0) & (LI > 0)
        with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
            logF, logI = np.log(LF), np.log(LI)
            if abs(rho) < 1e-8:
                # Cumulant expansion prevents cancellation near rho=0.
                logL = omega * logF + (1 - omega) * logI
                if rho != 0:
                    logL += .5 * rho * omega * (1 - omega) * (logF - logI)**2
                result = np.where(positive, np.exp(logL), 0.)
            else:
                logL = np.logaddexp(np.log(omega) + rho * logF,
                                   np.log1p(-omega) + rho * logI) / rho
                result = np.exp(logL)
                if rho < 0:
                    result = np.where(positive, result, 0.)
                result = np.where((LF == 0) & (LI == 0), 0., result)
    return float(result) if result.ndim == 0 else result


def ces_marginals(LF, LI, omega, sigma_sub):
    """Interior partial derivatives dL/dLF,dL/dLI; pure-weight endpoints."""
    L = ces_agg(LF, LI, omega, sigma_sub)
    if omega == 1:
        return 1., 0.
    if omega == 0:
        return 0., 1.
    if LF <= 0 or LI <= 0 or L <= 0:
        raise ValueError("Mixed CES marginal products require positive inputs")
    return (float(omega * (L / LF)**(1. / sigma_sub)),
            float((1 - omega) * (L / LI)**(1. / sigma_sub)))


def wage_premium(NF, NI, hF_eff, hI_eff, eta_I, omega, sigma_sub,
                 basis="weekly", hF_avg=None, hI_avg=None):
    """Within-firm productive marginal-revenue ratio, not net wage incidence.

    The legacy expression was per worker/week. Hourly divides worker marginal
    products by physical hours; effective-labor ratio omits hours scaling.
    Heterogeneous firms must be aggregated using their separate wage bills.
    """
    LF, LI = NF * hF_eff, eta_I * NI * hI_eff
    dF, dI = ces_marginals(LF, LI, omega, sigma_sub)
    ratio = dF / dI
    if basis == "effective":
        return ratio
    ratio *= hF_eff / (eta_I * hI_eff)
    if basis == "weekly":
        return ratio
    if basis == "hourly":
        if hF_avg is None or hI_avg is None:
            raise ValueError("Hourly premium requires physical hours")
        return ratio * hI_avg / hF_avg
    raise ValueError("basis must be hourly, weekly, or effective")

