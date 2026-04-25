# -*- coding: utf-8 -*-
"""
joint_envelope.py — Joint (sigma, omega, eta_I) disciplined-boundary envelope for A_req.

Addresses JMacro R&R item T1.2 (updated post-audit3 revision).

Computes A_req at all corners of the joint box under the revised anchors:
  sigma in {1.116, 1.469}   (from MNR R in [1.15, 1.55] at eta_I=0.40)
  omega in {0.58, 0.66}     (+/- 0.04 around 1 - narrow informality = 0.622)
  eta_I in {0.33, 0.50}     (LPS wage-ratio range 1/3 to 1/2)

plus the central point (1.326, 0.622, 0.40).
"""
import os, sys, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibrate_all import (
    solve_NF, calibrate_wedge, calibrate_pi_m, formal_hours_avg,
    eff, HOURS_BINS,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

THETA_DIEESE = np.array([0.085, 0.269, 0.646])

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


def solve_Areq(sigma_sub, omega, eta_I, theta=THETA_DIEESE):
    h_ref = float(np.dot(theta, HOURS_BINS))
    kappa = (1.0 - E_Q) / (2.0 * h_ref * (h_ref - H_STAR))

    N_S = NTOT * SHARE_S
    N_L = NTOT * SHARE_L
    K_S = KSHARE_S
    K_L = KSHARE_L

    groups = {}
    for name, Ng, Kg, inf_tgt, gF in [
        ("S", N_S, K_S, INF_S, GAMMA_F_S),
        ("L", N_L, K_L, INF_L, GAMMA_F_L),
    ]:
        sol0 = solve_NF(Ng, H0, HI, 1.0, Kg, ALPHA, omega, sigma_sub, eta_I,
                        kappa, H_STAR, 0.0, 0.0, 0.0, Ng*(1-inf_tgt), theta)
        pim = 0.0
        if sol0["informality"] > inf_tgt + 1e-10:
            pim = calibrate_pi_m(inf_tgt, Ng, H0, HI, 1.0, Kg, ALPHA, omega,
                                 sigma_sub, eta_I, kappa, H_STAR, theta)
        wedge = calibrate_wedge(inf_tgt, Ng, H0, HI, 1.0, Kg, ALPHA, omega,
                                sigma_sub, eta_I, kappa, H_STAR, pim, theta)
        groups[name] = dict(N=Ng, K=Kg, gamma_F=gF, wedge=wedge, pi_m=pim,
                             NF_init=Ng*(1-inf_tgt))

    def agg(A, hcap):
        Y = 0.0
        Iw = 0.0
        Ns = 0.0
        for g in groups.values():
            sol = solve_NF(g["N"], hcap, HI, A, g["K"], ALPHA, omega, sigma_sub,
                           eta_I, kappa, H_STAR, g["wedge"], g["pi_m"],
                           g["gamma_F"], g["NF_init"], theta)
            Y += sol["Y"]
            Iw += sol["informality"] * g["N"]
            Ns += g["N"]
        return Y, Iw/Ns

    Y0, _ = agg(1.0, H0)
    lo, hi = 1.0, 1.30
    for _ in range(70):
        mid = 0.5*(lo+hi)
        Ymid, _ = agg(mid, H1)
        if Ymid < Y0: lo = mid
        else: hi = mid
    return (0.5*(lo+hi) - 1.0) * 100


def main():
    sigmas = [1.116, 1.326, 1.469]
    omegas = [0.58, 0.622, 0.66]
    etas   = [0.33, 0.40, 0.50]

    results = []
    print(f"{'sigma':>6} {'omega':>6} {'eta_I':>6} {'A_req':>8}")
    print("-" * 30)
    central = None
    for s in sigmas:
        for w in omegas:
            for e in etas:
                Areq = solve_Areq(s, w, e)
                results.append({"sigma": s, "omega": w, "eta_I": e, "A_req": Areq})
                mark = "*" if (abs(s - 1.326) < 1e-6 and abs(w - 0.622) < 1e-6 and abs(e - 0.40) < 1e-6) else ""
                print(f"{s:>6.3f} {w:>6.3f} {e:>6.3f} {Areq:>7.3f}% {mark}")
                if mark: central = Areq

    Areqs = [r["A_req"] for r in results]
    print("\n=== Joint (sigma, omega, eta_I) envelope ===")
    print(f"  min  = {min(Areqs):.3f}%")
    print(f"  max  = {max(Areqs):.3f}%")
    print(f"  central = {central:.3f}%")

    # 8 corners only (no central)
    corners = [r for r in results if
               r["sigma"] in [1.116, 1.469] and
               r["omega"] in [0.58, 0.66] and
               r["eta_I"] in [0.33, 0.50]]
    print(f"\n  8-corner min = {min(c['A_req'] for c in corners):.3f}%")
    print(f"  8-corner max = {max(c['A_req'] for c in corners):.3f}%")

    out = {"grid": results, "central": central,
           "envelope_min": min(Areqs), "envelope_max": max(Areqs),
           "corner_min": min(c["A_req"] for c in corners),
           "corner_max": max(c["A_req"] for c in corners)}
    out_path = os.path.join(PROJECT_ROOT, "output", "validation", "joint_envelope.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
