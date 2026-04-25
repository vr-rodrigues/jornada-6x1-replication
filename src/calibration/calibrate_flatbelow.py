# -*- coding: utf-8 -*-
"""
calibrate_flatbelow.py — Full recalibration under asymmetric flat-below e(h).

The Pencavel evidence disciplines fatigue ABOVE h* (shorter hours reduce
efficiency only through coordination losses, which are small). This script
recalibrates the model with e(h) = 1 for h <= h* and exp(-kappa(h-h*)^2) for
h > h*, keeping h* = 40.

All wedges, pi_m, and kappa are recalibrated under the new e(h).
"""
import os, sys, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Reuse ces_agg, production, informal_cost, HOURS_BINS
from calibrate_all import HOURS_BINS, ces_agg, production

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

THETA = np.array([0.085, 0.269, 0.646])
ALPHA = 0.35
ETA_I = 0.40
E_Q = 0.60
H_STAR = 40.0
HI = 44.0
H0 = 44.0
H1 = 36.0
SIGMA = 1.326
OMEGA = 0.622
NTOT = 0.59
SHARE_S = 0.59
SHARE_L = 0.41
KSHARE_S = 0.35
KSHARE_L = 0.65
GAMMA_F_S = 0.12
GAMMA_F_L = 0.03
INF_S = 0.50
INF_L = 0.20


def eff_flat_below(h, kappa, h_star=H_STAR):
    """Asymmetric e(h): flat below h*, exponential fatigue above h*."""
    h = np.asarray(h, dtype=float)
    return np.where(h <= h_star, 1.0, np.exp(-kappa * (h - h_star) ** 2))


def kappa_from_eq(h_ref, h_star, e_q):
    """Same derivation as symmetric case at h_ref > h_star."""
    if abs(h_ref - h_star) < 1e-12:
        return 0.0
    if h_ref <= h_star:
        # Below h*: flat regime, elasticity = 1. Use a nominal kappa.
        return 1e-3
    return (1.0 - e_q) / (2.0 * h_ref * (h_ref - h_star))


def solve_NF_flat(N_total, hF, hI, A, K, formal_wedge, pi_m, gamma_F,
                  NF_prev, kappa, theta, grid=4001):
    """Solve firm problem under flat-below e(h)."""
    NF_grid = np.linspace(0, N_total, grid)
    NI_grid = N_total - NF_grid

    h_capped = np.minimum(HOURS_BINS, float(hF))
    e_bins = eff_flat_below(h_capped, kappa)
    eff_hF = float(np.sum(theta * h_capped * e_bins))
    eI = float(eff_flat_below(np.array([hI]), kappa)[0])

    LF = NF_grid * eff_hF
    LI = ETA_I * NI_grid * hI * eI
    L = ces_agg(LF, LI, OMEGA, SIGMA)
    Y = production(A, K, ALPHA, L)
    adj = 0.5 * gamma_F * (NF_grid - NF_prev) ** 2
    phi = 0.5 * pi_m * NI_grid ** 2
    obj = Y - formal_wedge * NF_grid - phi - adj
    j = int(np.argmax(obj))
    return dict(NF=float(NF_grid[j]), NI=float(NI_grid[j]), Y=float(Y[j]),
                informality=float(NI_grid[j] / max(N_total, 1e-15)),
                eff_hF=eff_hF)


def calib_wedge(target_inf, N, K, pim, kappa, gamma_F, NF_init):
    def inf_at(wedge):
        sol = solve_NF_flat(N, H0, HI, 1.0, K, wedge, pim, 0.0,
                             NF_init, kappa, THETA)
        return sol["informality"]
    lo, hi = 0.0, 25.0
    if inf_at(hi) < target_inf:
        return hi
    for _ in range(60):
        m = 0.5 * (lo + hi)
        if inf_at(m) > target_inf:
            hi = m
        else:
            lo = m
    return 0.5 * (lo + hi)


def calib_pim(target_inf, N, K, kappa, NF_init):
    def inf_at(pm):
        sol = solve_NF_flat(N, H0, HI, 1.0, K, 0.0, pm, 0.0,
                             NF_init, kappa, THETA)
        return sol["informality"]
    if inf_at(0.0) <= target_inf + 1e-10:
        return 0.0
    hi = 1.0
    while inf_at(hi) > target_inf + 1e-10 and hi < 1e6:
        hi *= 2.0
    lo = 0.0
    for _ in range(70):
        m = 0.5 * (lo + hi)
        if inf_at(m) > target_inf:
            lo = m
        else:
            hi = m
    return hi


def main():
    h_ref = float(np.dot(THETA, HOURS_BINS))
    kappa = kappa_from_eq(h_ref, H_STAR, E_Q)
    print(f"h_ref = {h_ref:.4f}, kappa = {kappa:.6e}")
    print(f"e(36)={eff_flat_below(np.array([36]), kappa)[0]:.4f}  "
          f"e(40)={eff_flat_below(np.array([40]), kappa)[0]:.4f}  "
          f"e(44)={eff_flat_below(np.array([44]), kappa)[0]:.4f}")

    specs = [
        ("S", NTOT*SHARE_S, KSHARE_S, INF_S, GAMMA_F_S),
        ("L", NTOT*SHARE_L, KSHARE_L, INF_L, GAMMA_F_L),
    ]
    groups = {}
    print("\n[Calibrating wedges under flat-below e(h)]")
    for name, N, K, inf_tgt, gF in specs:
        NF_init = N * (1 - inf_tgt)
        # Check if wedge=0 already overshoots target
        sol0 = solve_NF_flat(N, H0, HI, 1.0, K, 0.0, 0.0, 0.0,
                              NF_init, kappa, THETA)
        pim = 0.0
        if sol0["informality"] > inf_tgt + 1e-10:
            pim = calib_pim(inf_tgt, N, K, kappa, NF_init)
        wedge = calib_wedge(inf_tgt, N, K, pim, kappa, gF, NF_init)
        ver = solve_NF_flat(N, H0, HI, 1.0, K, wedge, pim, gF,
                             NF_init, kappa, THETA)
        print(f"  {name}: wedge={wedge:.4f}, pim={pim:.4f}, "
              f"inf={ver['informality']:.4f} (target {inf_tgt})")
        groups[name] = dict(N=N, K=K, gF=gF, wedge=wedge, pim=pim,
                             NF_init=NF_init)

    def agg(A, hcap):
        Y = 0.0
        Iw = 0.0
        for g in groups.values():
            sol = solve_NF_flat(g["N"], hcap, HI, A, g["K"],
                                g["wedge"], g["pim"], g["gF"],
                                g["NF_init"], kappa, THETA)
            Y += sol["Y"]
            Iw += sol["informality"] * g["N"]
        return Y, Iw / NTOT

    Y0, inf0 = agg(1.0, H0)
    Y1, inf1 = agg(1.0, H1)
    dY = (Y1 / Y0 - 1) * 100
    dInf = (inf1 - inf0) * 100
    print(f"\nBaseline Y={Y0:.6f}, inf={inf0*100:.2f}%")
    print(f"Reform   Y={Y1:.6f}, dY={dY:+.2f}%, dInf={dInf:+.2f} pp")

    # A_req
    lo, hi = 1.0, 1.30
    for _ in range(80):
        m = 0.5 * (lo + hi)
        Ym, _ = agg(m, H1)
        if Ym < Y0:
            lo = m
        else:
            hi = m
    A_req = (0.5 * (lo + hi) - 1.0) * 100
    print(f"\n*** A_req (flat-below e(h), h*={H_STAR}) = {A_req:.3f}% ***")
    print(f"*** Baseline symmetric                 = 7.26%          ***")

    out = dict(
        scenario="flat_below_h_star_40",
        h_ref=h_ref,
        kappa=kappa,
        wedge_S=groups["S"]["wedge"],
        wedge_L=groups["L"]["wedge"],
        pim_S=groups["S"]["pim"],
        pim_L=groups["L"]["pim"],
        dY_pct=dY,
        dInf_pp=dInf,
        A_req_pct=A_req,
    )
    op = os.path.join(PROJECT_ROOT, "output", "validation",
                       "calibrate_flatbelow.json")
    os.makedirs(os.path.dirname(op), exist_ok=True)
    with open(op, "w") as f:
        json.dump(out, f, indent=2)
    print(f"[Saved] {op}")


if __name__ == "__main__":
    main()
