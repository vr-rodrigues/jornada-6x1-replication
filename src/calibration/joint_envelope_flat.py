# -*- coding: utf-8 -*-
"""
joint_envelope_flat.py — Joint (sigma, omega, eta_I) envelope under the
preferred flat-below e(h) specification.
"""
import os, sys, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_all import HOURS_BINS, ces_agg, production

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

THETA = np.array([0.085, 0.269, 0.646])
ALPHA = 0.35
E_Q = 0.60
H_STAR = 40.0
HI = 44.0
H0 = 44.0
H1 = 36.0
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
    h = np.asarray(h, dtype=float)
    return np.where(h <= h_star, 1.0, np.exp(-kappa * (h - h_star) ** 2))


def solve_NF_flat(N, hF, A, K, alpha, omega, sigma, eta_I, kappa,
                   wedge, pim, gamma_F, NF_prev, theta, grid=3001):
    NF_grid = np.linspace(0, N, grid)
    NI_grid = N - NF_grid
    h_capped = np.minimum(HOURS_BINS, float(hF))
    e_bins = eff_flat_below(h_capped, kappa)
    eff_hF = float(np.sum(theta * h_capped * e_bins))
    eI = float(eff_flat_below(np.array([HI]), kappa)[0])
    LF = NF_grid * eff_hF
    LI = eta_I * NI_grid * HI * eI
    L = ces_agg(LF, LI, omega, sigma)
    Y = production(A, K, alpha, L)
    adj = 0.5 * gamma_F * (NF_grid - NF_prev) ** 2
    phi = 0.5 * pim * NI_grid ** 2
    obj = Y - wedge * NF_grid - phi - adj
    j = int(np.argmax(obj))
    return dict(NF=float(NF_grid[j]), NI=float(NI_grid[j]),
                Y=float(Y[j]),
                informality=float(NI_grid[j]/max(N, 1e-15)))


def calib_pim(target_inf, N, K, alpha, omega, sigma, eta_I, kappa, NF_init, theta):
    def inf_at(pm):
        return solve_NF_flat(N, H0, 1.0, K, alpha, omega, sigma, eta_I, kappa,
                              0.0, pm, 0.0, NF_init, theta)["informality"]
    if inf_at(0.0) <= target_inf + 1e-10:
        return 0.0
    hi = 1.0
    while inf_at(hi) > target_inf + 1e-10 and hi < 1e6:
        hi *= 2.0
    lo = 0.0
    for _ in range(70):
        m = 0.5 * (lo + hi)
        if inf_at(m) > target_inf: lo = m
        else: hi = m
    return hi


def calib_wedge(target_inf, N, K, pim, alpha, omega, sigma, eta_I, kappa, NF_init, theta):
    def inf_at(w):
        return solve_NF_flat(N, H0, 1.0, K, alpha, omega, sigma, eta_I, kappa,
                              w, pim, 0.0, NF_init, theta)["informality"]
    lo, hi = 0.0, 25.0
    for _ in range(60):
        m = 0.5 * (lo + hi)
        if inf_at(m) > target_inf: hi = m
        else: lo = m
    return 0.5 * (lo + hi)


def solve_Areq(sigma, omega, eta_I):
    h_ref = float(np.dot(THETA, HOURS_BINS))
    kappa = (1.0 - E_Q) / (2.0 * h_ref * (h_ref - H_STAR))
    N_S = NTOT*SHARE_S; N_L = NTOT*SHARE_L
    groups = {}
    for name, N, K, inf_t, gF in [
        ("S", N_S, KSHARE_S, INF_S, GAMMA_F_S),
        ("L", N_L, KSHARE_L, INF_L, GAMMA_F_L),
    ]:
        NF_init = N * (1 - inf_t)
        sol0 = solve_NF_flat(N, H0, 1.0, K, ALPHA, omega, sigma, eta_I,
                              kappa, 0.0, 0.0, 0.0, NF_init, THETA)
        pim = 0.0
        if sol0["informality"] > inf_t + 1e-10:
            pim = calib_pim(inf_t, N, K, ALPHA, omega, sigma, eta_I, kappa, NF_init, THETA)
        w = calib_wedge(inf_t, N, K, pim, ALPHA, omega, sigma, eta_I, kappa, NF_init, THETA)
        groups[name] = dict(N=N, K=K, gF=gF, w=w, pim=pim, NF_init=NF_init)

    def agg(A, hcap):
        Y = 0.0
        for g in groups.values():
            sol = solve_NF_flat(g["N"], hcap, A, g["K"], ALPHA, omega, sigma,
                                 eta_I, kappa, g["w"], g["pim"], g["gF"],
                                 g["NF_init"], THETA)
            Y += sol["Y"]
        return Y

    Y0 = agg(1.0, H0)
    lo, hi = 1.0, 1.60
    for _ in range(70):
        m = 0.5 * (lo + hi)
        if agg(m, H1) < Y0: lo = m
        else: hi = m
    return (0.5*(lo+hi) - 1.0) * 100


def main():
    sigmas = [1.116, 1.326, 1.469]
    omegas = [0.58, 0.622, 0.66]
    etas = [0.33, 0.40, 0.50]

    print(f"{'sigma':>6} {'omega':>6} {'eta_I':>6} {'A_req':>8}")
    print("-" * 30)
    results = []
    for s in sigmas:
        for w in omegas:
            for e in etas:
                a = solve_Areq(s, w, e)
                mark = " *" if (abs(s - 1.326) < 1e-6 and abs(w - 0.622) < 1e-6 and abs(e - 0.40) < 1e-6) else ""
                print(f"{s:>6.3f} {w:>6.3f} {e:>6.3f} {a:>7.3f}%{mark}")
                results.append(dict(sigma=s, omega=w, eta_I=e, A_req=a))

    vals = [r["A_req"] for r in results]
    corners = [r for r in results if
               r["sigma"] in [1.116, 1.469] and
               r["omega"] in [0.58, 0.66] and
               r["eta_I"] in [0.33, 0.50]]
    c_vals = [c["A_req"] for c in corners]
    print(f"\n=== Flat-below preferred envelope ===")
    print(f"  Full grid min/max   = [{min(vals):.3f}%, {max(vals):.3f}%]")
    print(f"  8-corner min/max    = [{min(c_vals):.3f}%, {max(c_vals):.3f}%]")

    out = dict(grid=results, corner_min=min(c_vals), corner_max=max(c_vals),
                full_min=min(vals), full_max=max(vals))
    op = os.path.join(PROJECT_ROOT, "output", "validation", "joint_envelope_flat.json")
    os.makedirs(os.path.dirname(op), exist_ok=True)
    with open(op, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved: {op}")


if __name__ == "__main__":
    main()
