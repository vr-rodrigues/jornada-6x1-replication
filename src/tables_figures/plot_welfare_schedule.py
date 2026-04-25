# -*- coding: utf-8 -*-
"""
plot_welfare_schedule.py — Proper welfare schedule under both calibrations,
using the exact same psi-calibration and compensating-variation formula
as calibrate_all.py.
"""
import os, sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

CAL_DIR = os.path.join(os.path.dirname(__file__), "..", "calibration")
sys.path.insert(0, CAL_DIR)
from calibrate_all import (
    solve_NF, calibrate_wedge, calibrate_pi_m, HOURS_BINS,
    ces_agg, production, compensating_variation, calibrate_psi,
)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "output", "figures", "fig_welfare_schedule.png")
PAPER_COPY = os.path.join(ROOT, "paper", "overleaf", "figures",
                           "fig_welfare_schedule.png")

# -- Common parameters --
THETA = np.array([0.085, 0.269, 0.646])
ALPHA = 0.35
ETA_I = 0.40
E_Q = 0.60
H_STAR = 40.0
HI = 44.0
H0 = 44.0
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
NU_GHH = 2.0

# -- Styling (Fig 6 aesthetic) --
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _style import apply_style, set_axis_style, save_pdf, COLOR_PREF, COLOR_CONS, TEXT_DARK
apply_style()


def solve_NF_custom(eff_fn, kappa, N_total, hF, hI, A, K, alpha, omega,
                     sigma_sub, eta_I, h_star, formal_wedge, pi_m,
                     gamma_F, NF_prev, theta, grid=3001):
    """Custom solver that uses a user-supplied eff_fn(h, kappa, h_star)."""
    NF_grid = np.linspace(0, N_total, grid)
    NI_grid = N_total - NF_grid
    h_capped = np.minimum(HOURS_BINS, float(hF))
    e_bins = eff_fn(h_capped, kappa, h_star)
    eff_hF = float(np.sum(theta * h_capped * e_bins))
    eI = float(eff_fn(np.array([hI]), kappa, h_star)[0])

    LF = NF_grid * eff_hF
    LI = eta_I * NI_grid * hI * eI
    L = ces_agg(LF, LI, omega, sigma_sub)
    Y = production(A, K, alpha, L)
    adj = 0.5 * gamma_F * (NF_grid - NF_prev) ** 2
    phi = 0.5 * pi_m * NI_grid ** 2
    obj = Y - formal_wedge * NF_grid - phi - adj
    j = int(np.argmax(obj))
    NF = float(NF_grid[j])
    NI = float(NI_grid[j])
    Ys = float(Y[j])
    C = Ys - float(adj[j])
    hF_avg = float(np.sum(theta * h_capped))
    hours_total = NF * hF_avg + NI * hI
    return dict(NF=NF, NI=NI, Y=Ys, C=C,
                informality=NI / max(N_total, 1e-15),
                hours_total=hours_total)


def eff_sym(h, kappa, h_star):
    h = np.asarray(h, dtype=float)
    return np.exp(-kappa * (h - h_star) ** 2)


def eff_flat_below(h, kappa, h_star):
    h = np.asarray(h, dtype=float)
    return np.where(h <= h_star, 1.0, np.exp(-kappa * (h - h_star) ** 2))


def build_spec(eff_fn):
    """Full baseline calibration + return groups dict, kappa, psi, base stats."""
    h_ref = float(np.dot(THETA, HOURS_BINS))
    kappa = (1.0 - E_Q) / (2.0 * h_ref * (h_ref - H_STAR))

    groups = {}
    N_base_total = 0.0
    Y_base_total = 0.0
    C_base_total = 0.0
    hours_base_total = 0.0
    NI_base_total = 0.0

    for gname, N, K, inf_tgt, gF in [
        ("S", NTOT*SHARE_S, KSHARE_S, INF_S, GAMMA_F_S),
        ("L", NTOT*SHARE_L, KSHARE_L, INF_L, GAMMA_F_L),
    ]:
        NF_init = N * (1 - inf_tgt)

        # Calibrate pim, wedge using the native symmetric path (wedges
        # depend on e(h) shape; use custom solver for flat-below too)
        def inf_at_wedge(wedge, pim):
            sol = solve_NF_custom(eff_fn, kappa, N, H0, HI, 1.0, K, ALPHA,
                                    OMEGA, SIGMA, ETA_I, H_STAR,
                                    wedge, pim, 0.0, NF_init, THETA)
            return sol["informality"]

        # Check if wedge=0 overshoots
        if inf_at_wedge(0.0, 0.0) > inf_tgt + 1e-10:
            # Calibrate pim first
            lo, hi = 0.0, 1.0
            while inf_at_wedge(0.0, hi) > inf_tgt + 1e-10 and hi < 1e6:
                hi *= 2.0
            for _ in range(70):
                m = 0.5 * (lo + hi)
                if inf_at_wedge(0.0, m) > inf_tgt:
                    lo = m
                else:
                    hi = m
            pim = hi
        else:
            pim = 0.0

        # Calibrate wedge
        lo, hi = 0.0, 25.0
        for _ in range(60):
            m = 0.5 * (lo + hi)
            if inf_at_wedge(m, pim) > inf_tgt:
                hi = m
            else:
                lo = m
        wedge = 0.5 * (lo + hi)

        # Verify with gamma_F applied
        sol = solve_NF_custom(eff_fn, kappa, N, H0, HI, 1.0, K, ALPHA,
                               OMEGA, SIGMA, ETA_I, H_STAR,
                               wedge, pim, gF, NF_init, THETA)
        groups[gname] = dict(N=N, K=K, gF=gF, wedge=wedge, pim=pim,
                              NF_init=NF_init)
        N_base_total += N
        Y_base_total += sol["Y"]
        C_base_total += sol["C"]
        hours_base_total += sol["hours_total"]
        NI_base_total += sol["NI"]

    h_avg_base = hours_base_total / N_base_total
    w_hourly = (1.0 - ALPHA) * Y_base_total / (N_base_total * h_avg_base)
    psi = calibrate_psi(w_hourly, h_avg_base, NU_GHH)

    return dict(groups=groups, kappa=kappa, psi=psi,
                c_base_pc=C_base_total / N_base_total,
                h_base=h_avg_base,
                Y_base=Y_base_total, N_base=N_base_total,
                eff_fn=eff_fn)


def welfare_at(spec, hcap):
    """Return (dY_pct, dCV_pct, h_avg_cap) at a given cap for a spec."""
    Y_t, C_t, hrs_t = 0.0, 0.0, 0.0
    for g in spec["groups"].values():
        sol = solve_NF_custom(spec["eff_fn"], spec["kappa"],
                               g["N"], hcap, HI, 1.0, g["K"], ALPHA,
                               OMEGA, SIGMA, ETA_I, H_STAR,
                               g["wedge"], g["pim"], g["gF"],
                               g["NF_init"], THETA)
        Y_t += sol["Y"]; C_t += sol["C"]; hrs_t += sol["hours_total"]
    dY = (Y_t / spec["Y_base"] - 1) * 100
    h_cap = hrs_t / spec["N_base"]
    c_pc = C_t / spec["N_base"]
    dcv = compensating_variation(spec["c_base_pc"], spec["h_base"],
                                   c_pc, h_cap, NU_GHH, spec["psi"]) * 100
    return dY, dcv, h_cap


def main():
    print("[Calibrating flat-below]")
    spec_flat = build_spec(eff_flat_below)
    print(f"  psi={spec_flat['psi']:.4e}, c_pc={spec_flat['c_base_pc']:.4f}, "
          f"h_base={spec_flat['h_base']:.2f}")

    print("[Calibrating symmetric]")
    spec_sym = build_spec(eff_sym)
    print(f"  psi={spec_sym['psi']:.4e}, c_pc={spec_sym['c_base_pc']:.4f}, "
          f"h_base={spec_sym['h_base']:.2f}")

    caps = np.arange(30, 45, dtype=float)[::-1]  # 44 -> 30 descending

    flat_dy, flat_dcv = [], []
    sym_dy, sym_dcv = [], []
    for hc in caps:
        dyF, dcvF, _ = welfare_at(spec_flat, hc)
        dyS, dcvS, _ = welfare_at(spec_sym, hc)
        flat_dy.append(dyF); flat_dcv.append(dcvF)
        sym_dy.append(dyS);  sym_dcv.append(dcvS)
        print(f"  h={hc:.0f}: flat dY={dyF:+.2f}%, dCV={dcvF:+.2f}% |  "
              f"sym dY={dyS:+.2f}%, dCV={dcvS:+.2f}%")

    # --- Figure (Fig 6 aesthetic) ---
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(caps, flat_dcv, "-o", color=COLOR_PREF, linewidth=1.8,
            markersize=6, label="Preferred\n(flat-below)")
    ax.plot(caps, sym_dcv,  "--s", color=COLOR_CONS, linewidth=1.6,
            markersize=5.5, alpha=0.9, label="Conservative\n(symmetric)")
    ax.axhline(0, color="#666666", linewidth=0.5, alpha=0.6)
    ax.axvline(36, color="#888888", linewidth=0.6, linestyle=":",
                alpha=0.6, label="Proposed cap\n(36h)")

    # Annotate peaks on two lines each, at user-requested positions:
    #   blue (preferred): text at (x=44, y=-2.5)
    #   red (conservative): text at (x=38, y=-5)
    i_pf = int(np.argmax(flat_dcv))
    i_ps = int(np.argmax(sym_dcv))
    ax.annotate(
        f"peak (preferred):\n$+{flat_dcv[i_pf]:.2f}\\%$ at {caps[i_pf]:.0f}h",
        xy=(caps[i_pf], flat_dcv[i_pf]),
        xytext=(44, -2.5),
        fontsize=10, fontstyle="italic", color=COLOR_PREF,
        ha="left", va="center",
        arrowprops=dict(arrowstyle="->", color=COLOR_PREF, lw=1.0,
                         connectionstyle="arc3,rad=0.15"))
    ax.annotate(
        f"peak (conservative):\n$+{sym_dcv[i_ps]:.2f}\\%$ at {caps[i_ps]:.0f}h",
        xy=(caps[i_ps], sym_dcv[i_ps]),
        xytext=(38, -5),
        fontsize=10, fontstyle="italic", color=COLOR_CONS,
        ha="center", va="center",
        arrowprops=dict(arrowstyle="->", color=COLOR_CONS, lw=1.0,
                         connectionstyle="arc3,rad=-0.2"))

    set_axis_style(
        ax,
        title="Welfare Schedule by Hours Cap (preferred vs. conservative)",
        xlabel="Weekly hours cap",
        ylabel=r"$\Delta$CV (%) $-$ GHH compensating variation",
    )
    ax.legend(loc="lower left", frameon=False, labelspacing=0.8)
    ax.invert_xaxis()

    plt.tight_layout()
    pdf = save_pdf(fig, OUT)
    plt.close()
    print(f"[OK] {pdf}")

    paper_pdf = PAPER_COPY.replace(".png", ".pdf")
    if os.path.isdir(os.path.dirname(paper_pdf)):
        import shutil
        shutil.copy(pdf, paper_pdf)
        print(f"[OK] {paper_pdf}")


if __name__ == "__main__":
    main()
