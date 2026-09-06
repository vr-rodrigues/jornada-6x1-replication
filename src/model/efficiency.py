"""One efficiency technology and explicit, validated hours distributions."""
import numpy as np

HOURS_BINS = np.array([36.0, 40.0, 44.0])


def eff(h, kappa, h_star, efficiency_mode="bilateral"):
    """Bilateral quadratic efficiency or fatigue only above the peak."""
    if kappa < 0 or h_star <= 0:
        raise ValueError("kappa must be nonnegative and h_star positive")
    distance = np.asarray(h, dtype=float) - h_star
    if efficiency_mode in ("flat_below", "flatbelow", "fatigue_above"):
        distance = np.maximum(distance, 0.0)
    elif efficiency_mode != "bilateral":
        raise ValueError(f"Unknown efficiency mode: {efficiency_mode}")
    result = np.exp(-kappa * distance ** 2)
    return float(result) if result.ndim == 0 else result


def calibrate_kappa(h_ref, h_star, e_q, efficiency_mode="bilateral"):
    """Local elasticity of h*e(h), not behavioral validation of hours bins.

    No arbitrary curvature is substituted if the equation cannot identify
    nonnegative curvature, for instance below the fatigue peak.
    """
    if not np.isfinite([h_ref, h_star, e_q]).all() or h_ref <= 0:
        raise ValueError("Invalid elasticity calibration inputs")
    denominator = 2.0 * h_ref * (h_ref - h_star)
    if abs(1.0 - e_q) < 1e-14:
        return 0.0
    if abs(denominator) < 1e-14 or (efficiency_mode != "bilateral" and h_ref <= h_star):
        raise ValueError("This local elasticity cannot identify kappa at/below the fatigue peak; supply explicit kappa")
    kappa = (1.0 - e_q) / denominator
    if kappa < 0:
        raise ValueError("Elasticity and reference hours imply negative kappa")
    return float(kappa)


def hours_distribution(theta, hours_bins=None):
    bins = HOURS_BINS if hours_bins is None else np.asarray(hours_bins, dtype=float)
    weights = np.asarray(theta, dtype=float)
    if bins.ndim != 1 or weights.shape != bins.shape or not len(bins):
        raise ValueError("Hours bins and weights must be nonempty vectors of equal length")
    if not np.isfinite(bins).all() or not np.isfinite(weights).all():
        raise ValueError("Hours distribution must be finite")
    if np.any(bins <= 0) or np.any(weights < 0) or not np.isclose(weights.sum(), 1., atol=1e-10, rtol=0):
        raise ValueError("Hours must be positive and nonnegative weights must sum to one")
    return weights, bins


def formal_hours_avg(h_cap, theta, hours_bins=None):
    weights, bins = hours_distribution(theta, hours_bins)
    if h_cap <= 0:
        raise ValueError("Hours cap must be positive")
    return float(np.dot(weights, np.minimum(bins, float(h_cap))))


def formal_hours_hetero(h_cap, kappa, h_star, theta,
                        efficiency_mode="bilateral", hours_bins=None):
    weights, bins = hours_distribution(theta, hours_bins)
    if h_cap <= 0:
        raise ValueError("Hours cap must be positive")
    capped = np.minimum(bins, float(h_cap))
    return (float(np.dot(weights, capped)),
            float(np.dot(weights, capped * eff(capped, kappa, h_star, efficiency_mode))))

