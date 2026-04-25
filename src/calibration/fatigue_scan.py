# -*- coding: utf-8 -*-
"""
fatigue_scan.py — Find calibration combinations where the fatigue effect
(efficiency change from baseline to 36h cap) is POSITIVE rather than negative.

Background: the user expects that cutting hours lets workers rest, so the
fatigue channel should improve per-hour productivity. Under symmetric
e(h) = exp(-kappa(h-h*)^2) with h* = 40, e(36) = e(44), so cutting from
h_ref ~ 42.2 to 36 crosses h* and ends up at the same efficiency as h=44.
The net fatigue effect is slightly negative.

We scan combinations of:
  (i)  h* in {36, 38, 40}
  (ii) e(h) shape: symmetric OR flat-below-h* asymmetric OR half-curvature-below
and report for each the change in average e at formal hours from baseline
to the post-36h-cap state.
"""
import os, sys, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_all import HOURS_BINS

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

THETA = np.array([0.085, 0.269, 0.646])
H_REF = float(np.dot(THETA, HOURS_BINS))   # 42.244
H_REFORM_BINS = np.minimum(HOURS_BINS, 36.0)  # bins under 36h cap: [36, 36, 36]
E_Q = 0.60


def kappa_from_eq(h_ref, h_star, e_q):
    if abs(h_ref - h_star) < 1e-12:
        return 0.0
    return (1.0 - e_q) / (2.0 * h_ref * (h_ref - h_star))


def eff_sym(h, kappa, h_star):
    return np.exp(-kappa * (np.asarray(h) - h_star) ** 2)


def eff_flat_below(h, kappa, h_star):
    h = np.asarray(h)
    return np.where(h <= h_star, 1.0, np.exp(-kappa * (h - h_star) ** 2))


def eff_half_below(h, kappa, h_star):
    h = np.asarray(h)
    return np.where(h <= h_star,
                    np.exp(-0.5 * kappa * (h - h_star) ** 2),
                    np.exp(-kappa * (h - h_star) ** 2))


def fatigue_effect(h_star, eff_fn, name):
    """Return dict with e(36), e(40), e(44), baseline and reform avg e,
    change in percentage points.
    Notes: baseline hours = theta-weighted mix of (36, 40, 44). Post-36 cap,
    every bin becomes 36h.
    """
    kappa = kappa_from_eq(H_REF, h_star, E_Q)
    # If h_star == H_REF the derivation breaks; use a small perturbation.
    if abs(H_REF - h_star) < 1e-9:
        kappa = 1e-3

    e_bins_base = eff_fn(HOURS_BINS, kappa, h_star)
    e_bins_reform = eff_fn(H_REFORM_BINS, kappa, h_star)

    # Average formal efficiency, weighted by theta AND by hours
    # (because effective labor = theta * h * e)
    L_eff_base = float(np.sum(THETA * HOURS_BINS * e_bins_base))
    L_eff_reform = float(np.sum(THETA * H_REFORM_BINS * e_bins_reform))

    # Mechanical hours decline
    h_base = float(np.sum(THETA * HOURS_BINS))
    h_reform = float(np.sum(THETA * H_REFORM_BINS))  # = 36

    # dY_mechanical = d(h_eff)/dh * dh + d(h_eff)/de * de
    # But here everyone moves to 36, so e changes too.
    # Fatigue effect (in pp): change in avg e from base to reform
    e_avg_base = float(np.sum(THETA * e_bins_base))
    e_avg_reform = float(np.sum(THETA * e_bins_reform))
    de_pct = (e_avg_reform / e_avg_base - 1.0) * 100

    # Output effect decomposition: dY = dh + de (both in logs)
    dh_pct = (h_reform / h_base - 1.0) * 100
    dY_approx = dh_pct + de_pct

    return dict(
        spec=name, h_star=h_star, kappa=kappa,
        e36=float(eff_fn(36.0, kappa, h_star)),
        e40=float(eff_fn(40.0, kappa, h_star)),
        e44=float(eff_fn(44.0, kappa, h_star)),
        e_avg_base=e_avg_base, e_avg_reform=e_avg_reform,
        fatigue_pp=de_pct,
        mechanical_pp=dh_pct,
        dY_approx_pp=dY_approx,
    )


def main():
    # h_ref is around 42.2 so valid peaks are 36, 38, 40
    h_stars = [36.0, 38.0, 40.0, 42.0]
    specs = [
        ("symmetric",       eff_sym),
        ("flat-below",      eff_flat_below),
        ("half-curv-below", eff_half_below),
    ]

    print(f"{'Spec':<18} {'h*':>4} {'e(36)':>7} {'e(40)':>7} {'e(44)':>7} "
          f"{'e_base':>8} {'e_ref':>8} {'fatigue':>9} {'mech':>8} {'dY':>8}")
    print("-" * 90)
    results = []
    for h_star in h_stars:
        for name, fn in specs:
            try:
                r = fatigue_effect(h_star, fn, name)
            except Exception as e:
                print(f"  {name} h*={h_star}: ERROR {e}")
                continue
            flag = "POS" if r["fatigue_pp"] > 0 else "neg"
            print(f"{r['spec']:<18} {h_star:>4.0f} "
                  f"{r['e36']:>7.4f} {r['e40']:>7.4f} {r['e44']:>7.4f} "
                  f"{r['e_avg_base']:>8.4f} {r['e_avg_reform']:>8.4f} "
                  f"{r['fatigue_pp']:>+8.3f}% "
                  f"{r['mechanical_pp']:>+7.3f}% "
                  f"{r['dY_approx_pp']:>+7.3f}% {flag}")
            results.append(r)

    # Identify combinations with positive fatigue effect
    print()
    print("COMBINATIONS WITH POSITIVE FATIGUE EFFECT AT h* = 40:")
    print("-" * 70)
    for r in results:
        if r["h_star"] == 40.0 and r["fatigue_pp"] > 0:
            print(f"  {r['spec']:<18}: fatigue = {r['fatigue_pp']:+.3f}% "
                  f"(e_base={r['e_avg_base']:.4f}, e_reform={r['e_avg_reform']:.4f})")

    out_path = os.path.join(PROJECT_ROOT, "output", "validation",
                             "fatigue_scan.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[Saved] {out_path}")


if __name__ == "__main__":
    main()
