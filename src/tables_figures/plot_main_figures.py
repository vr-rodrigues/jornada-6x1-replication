# -*- coding: utf-8 -*-
"""
plot_main_figures.py — Regenerate main paper figures under the preferred
flat-below e(h) specification, with ggplot aesthetic matching the fit table
and TFP figure style.

Outputs:
  - fig_areq_vs_hours.png     (Figure 1 replacement for curve_areq_vs_hours_total.png)
  - fig_decomposition.png     (Figure 2 replacement for slide07_decomp_fadiga_outros.png)
  - fig_welfare_schedule.png  (Figure 4 replacement for slide10d_welfare_by_hours.png)
"""
import json
import os, sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "calibration"))
from calibrate_flatbelow import (
    solve_NF_flat, eff_flat_below, kappa_from_eq,
    calib_wedge, calib_pim,
    THETA, ALPHA, ETA_I, E_Q, H_STAR, HI, H0, H1,
    SIGMA, OMEGA, NTOT, SHARE_S, SHARE_L,
    KSHARE_S, KSHARE_L, GAMMA_F_S, GAMMA_F_L,
    INF_S, INF_L,
)
from calibrate_all import HOURS_BINS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(ROOT, "output", "figures")
os.makedirs(OUT_DIR, exist_ok=True)
VALIDATION_DIR = os.path.join(ROOT, "output", "validation")
os.makedirs(VALIDATION_DIR, exist_ok=True)
PAPER_FIG_DIR = os.path.join(ROOT, "paper", "overleaf", "figures")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _style import apply_style, set_axis_style, save_pdf, COLOR_PREF, COLOR_CONS, TEXT_DARK
apply_style()


# ---------------------------------------------------------------
# Solve wedges under flat-below for reuse
# ---------------------------------------------------------------

def eff_sym(h, kappa, h_star=H_STAR):
    h = np.asarray(h, dtype=float)
    return np.exp(-kappa * (h - h_star) ** 2)


def calibrate_model(eff_fn, name):
    """Full calibration under any e(h) spec. Returns groups dict + kappa."""
    h_ref = float(np.dot(THETA, HOURS_BINS))
    kappa = (1.0 - E_Q) / (2.0 * h_ref * (h_ref - H_STAR))

    groups = {}
    for gname, N, K, inf_tgt, gF in [
        ("S", NTOT*SHARE_S, KSHARE_S, INF_S, GAMMA_F_S),
        ("L", NTOT*SHARE_L, KSHARE_L, INF_L, GAMMA_F_L),
    ]:
        NF_init = N * (1 - inf_tgt)
        # Reuse the flat-below solver by swapping eff_fn via monkeypatch.
        # calibrate_flatbelow.solve_NF_flat uses eff_flat_below internally.
        # For symmetric we'll compute wedges on a clean path below.
        # Here we use flat-below always (this function is only for flat-below)
        sol0 = solve_NF_flat(N, H0, HI, 1.0, K, 0.0, 0.0, 0.0, NF_init, kappa, THETA)
        pim = 0.0
        if sol0["informality"] > inf_tgt + 1e-10:
            pim = calib_pim(inf_tgt, N, K, kappa, NF_init)
        wedge = calib_wedge(inf_tgt, N, K, pim, kappa, gF, NF_init)
        groups[gname] = dict(N=N, K=K, gF=gF, wedge=wedge, pim=pim, NF_init=NF_init)
    return groups, kappa


def agg_out(groups, kappa, A, hcap, eff_fn):
    """Aggregate output at a given A and hours cap under custom eff_fn."""
    Y_total = 0.0
    Iw = 0.0
    # Monkeypatch-free: replicate solve_NF_flat body with chosen eff_fn
    for g in groups.values():
        NF_grid = np.linspace(0, g["N"], 4001)
        NI_grid = g["N"] - NF_grid
        h_capped = np.minimum(HOURS_BINS, float(hcap))
        e_bins = eff_fn(h_capped, kappa)
        eff_hF = float(np.sum(THETA * h_capped * e_bins))
        eI = float(eff_fn(np.array([HI]), kappa)[0])

        from calibrate_all import ces_agg, production
        LF = NF_grid * eff_hF
        LI = ETA_I * NI_grid * HI * eI
        L = ces_agg(LF, LI, OMEGA, SIGMA)
        Y = production(A, g["K"], ALPHA, L)
        adj = 0.5 * g["gF"] * (NF_grid - g["NF_init"])**2
        phi = 0.5 * g["pim"] * NI_grid**2
        obj = Y - g["wedge"] * NF_grid - phi - adj
        j = int(np.argmax(obj))
        Y_total += float(Y[j])
        Iw += float(NI_grid[j] / max(g["N"], 1e-15) * g["N"])
    return Y_total, Iw / NTOT


def areq_at_cap(groups, kappa, hcap, eff_fn, Y_target):
    lo, hi = 1.0, 1.60
    for _ in range(70):
        m = 0.5 * (lo + hi)
        Ym, _ = agg_out(groups, kappa, m, hcap, eff_fn)
        if Ym < Y_target:
            lo = m
        else:
            hi = m
    return (0.5*(lo+hi) - 1.0) * 100


def formal_hours(hcap):
    return float(np.sum(THETA * np.minimum(HOURS_BINS, float(hcap))))


def formal_effective_hours(hcap, kappa, eff_fn):
    capped = np.minimum(HOURS_BINS, float(hcap))
    return float(np.sum(THETA * capped * eff_fn(capped, kappa)))


def output_decomposition(groups, kappa, eff_fn, Y0):
    Y1, _ = agg_out(groups, kappa, 1.0, H1, eff_fn)
    total = (Y1 / Y0 - 1.0) * 100

    h_base = formal_hours(H0)
    h_reform = formal_hours(H1)
    mechanical = (h_reform / h_base - 1.0) * 100

    eff_base = formal_effective_hours(H0, kappa, eff_fn) / h_base
    eff_reform = formal_effective_hours(H1, kappa, eff_fn) / h_reform
    efficiency = (eff_reform / eff_base - 1.0) * 100

    residual = total - mechanical - efficiency
    return {
        "mechanical_hours": mechanical,
        "efficiency_channel": efficiency,
        "reallocation_residual": residual,
        "total_output": total,
    }


# ---------------------------------------------------------------
# Generate curves
# ---------------------------------------------------------------

def main():
    h_ref = float(np.dot(THETA, HOURS_BINS))
    kappa = (1.0 - E_Q) / (2.0 * h_ref * (h_ref - H_STAR))

    # Calibrate under flat-below
    print("[Calibrating flat-below wedges]")
    g_flat, kappa_flat = calibrate_model(eff_flat_below, "flat_below")
    Y0_flat, _ = agg_out(g_flat, kappa_flat, 1.0, H0, eff_flat_below)

    # Calibrate under symmetric (separately)
    print("[Calibrating symmetric wedges]")
    from calibrate_all import calibrate_wedge as cal_w_sym, calibrate_pi_m as cal_p_sym, solve_NF as solve_sym
    g_sym = {}
    for gname, N, K, inf_tgt, gF in [
        ("S", NTOT*SHARE_S, KSHARE_S, INF_S, GAMMA_F_S),
        ("L", NTOT*SHARE_L, KSHARE_L, INF_L, GAMMA_F_L),
    ]:
        NF_init = N * (1 - inf_tgt)
        sol0 = solve_sym(N, H0, HI, 1.0, K, ALPHA, OMEGA, SIGMA, ETA_I,
                          kappa, H_STAR, 0.0, 0.0, 0.0, NF_init, THETA)
        pim = 0.0
        if sol0["informality"] > inf_tgt + 1e-10:
            pim = cal_p_sym(inf_tgt, N, H0, HI, 1.0, K, ALPHA, OMEGA,
                             SIGMA, ETA_I, kappa, H_STAR, THETA)
        wedge = cal_w_sym(inf_tgt, N, H0, HI, 1.0, K, ALPHA, OMEGA,
                           SIGMA, ETA_I, kappa, H_STAR, pim, THETA)
        g_sym[gname] = dict(N=N, K=K, gF=gF, wedge=wedge, pim=pim, NF_init=NF_init)
    Y0_sym, _ = agg_out(g_sym, kappa, 1.0, H0, eff_sym)

    # Compute A_req curves over h_cap
    caps = np.arange(30, 45, 1, dtype=float)
    areq_flat, areq_sym = [], []
    for hc in caps:
        a_flat = areq_at_cap(g_flat, kappa_flat, hc, eff_flat_below, Y0_flat)
        a_sym  = areq_at_cap(g_sym,  kappa,       hc, eff_sym,        Y0_sym)
        areq_flat.append(a_flat)
        areq_sym.append(a_sym)
        print(f"  h={hc:.0f}: A_req flat={a_flat:+.2f}%, sym={a_sym:+.2f}%")

    # ---- FIGURE 1: A_req vs hours cap ----
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(caps, areq_flat, "-o", color=COLOR_PREF, linewidth=1.8,
            markersize=6, label="Preferred\n(flat-below)")
    ax.plot(caps, areq_sym, "--s", color=COLOR_CONS, linewidth=1.6,
            markersize=5.5, alpha=0.9, label="Conservative\n(symmetric)")
    ax.axhline(0, color="#666666", linewidth=0.5, alpha=0.6)
    ax.axvline(36, color="#888888", linewidth=0.6, linestyle=":", alpha=0.6)

    # Labels for 36h cap placed to empty space (top-left quadrant of chart).
    a_flat_36 = next(a for c, a in zip(caps, areq_flat) if c == 36)
    a_sym_36  = next(a for c, a in zip(caps, areq_sym)  if c == 36)
    ax.annotate(f"preferred:\n{a_flat_36:.2f}%",
                 xy=(36, a_flat_36), xytext=(40.5, 11),
                 fontsize=10, fontstyle="italic", color=COLOR_PREF,
                 ha="center", va="center",
                 arrowprops=dict(arrowstyle="->", color=COLOR_PREF, lw=1.0,
                                   connectionstyle="arc3,rad=-0.3"))
    ax.annotate(f"conservative:\n{a_sym_36:.2f}%",
                 xy=(36, a_sym_36), xytext=(41, 17),
                 fontsize=10, fontstyle="italic", color=COLOR_CONS,
                 ha="center", va="center",
                 arrowprops=dict(arrowstyle="->", color=COLOR_CONS, lw=1.0,
                                   connectionstyle="arc3,rad=-0.3"))

    set_axis_style(
        ax,
        title="Required TFP Gain by Hours Cap (preferred vs. conservative)",
        xlabel="Weekly hours cap",
        ylabel=r"Required TFP gain $A_{req}$ (%)",
    )
    ax.legend(loc="upper left", bbox_to_anchor=(0.01, 0.98),
              frameon=False, labelspacing=0.8)
    ax.invert_xaxis()

    out1 = os.path.join(OUT_DIR, "fig_areq_vs_hours.png")
    plt.tight_layout()
    save_pdf(fig, out1)
    plt.close()
    print(f"[OK] {out1.replace('.png','.pdf')}")

    # ---- FIGURE 2: Decomposition (preferred flat-below) ----
    dec_flat = output_decomposition(g_flat, kappa_flat, eff_flat_below, Y0_flat)
    dec_sym = output_decomposition(g_sym, kappa, eff_sym, Y0_sym)

    categories = ["Mechanical\n(hours cut)", "Efficiency\n$e(h)$",
                  "Reallocation\n(residual)", "Total"]
    vals_flat = [
        dec_flat["mechanical_hours"],
        dec_flat["efficiency_channel"],
        dec_flat["reallocation_residual"],
        dec_flat["total_output"],
    ]
    vals_sym = [
        dec_sym["mechanical_hours"],
        dec_sym["efficiency_channel"],
        dec_sym["reallocation_residual"],
        dec_sym["total_output"],
    ]

    dec_path = os.path.join(VALIDATION_DIR, "decomposition_results.json")
    with open(dec_path, "w", encoding="utf-8") as f:
        json.dump({"preferred_flat_below": dec_flat,
                   "conservative_symmetric": dec_sym}, f, indent=2)
    print(f"[OK] {dec_path}")

    x = np.arange(len(categories))
    w = 0.35

    fig, ax = plt.subplots(figsize=(10, 6.2))
    b1 = ax.bar(x - w/2, vals_flat, width=w, color=COLOR_PREF,
                 alpha=0.85, edgecolor="#2c3e50", linewidth=0.3,
                 label="Preferred\n(flat-below)")
    b2 = ax.bar(x + w/2, vals_sym, width=w, color=COLOR_CONS,
                 alpha=0.85, edgecolor="#2c3e50", linewidth=0.3,
                 label="Conservative\n(symmetric)")
    for bar in list(b1) + list(b2):
        h = bar.get_height()
        # For large-magnitude negative bars (mechanical), put label INSIDE bar
        # (white text), avoiding overlap with legend and chart bottom edge.
        if h <= -10:
            ax.text(bar.get_x() + bar.get_width()/2, h / 2,
                     f"{h:+.2f}%", ha="center", va="center",
                     fontsize=10, fontstyle="italic", color="white")
        else:
            y_text = h + 0.4 if h >= 0 else h - 0.4
            va = "bottom" if h >= 0 else "top"
            ax.text(bar.get_x() + bar.get_width()/2, y_text,
                     f"{h:+.2f}%", ha="center", va=va,
                     fontsize=10, fontstyle="italic", color=TEXT_DARK)
    ax.axhline(0, color="#666666", linewidth=0.5, alpha=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11)
    set_axis_style(
        ax,
        title=r"Output Decomposition at 44$\to$36h Cap",
        xlabel=None,
        ylabel=r"Contribution to $\Delta Y$ (%)",
    )
    # Legend to upper-left, clear of bars (positive ones are on right side)
    ax.legend(loc="upper left", bbox_to_anchor=(0.01, 0.99),
              frameon=False, labelspacing=0.8)
    # Set ylim with more headroom
    ax.set_ylim(-18, 12)
    ax.xaxis.grid(False)

    out2 = os.path.join(OUT_DIR, "fig_decomposition.png")
    plt.tight_layout()
    save_pdf(fig, out2)
    plt.close()
    print(f"[OK] {out2.replace('.png','.pdf')}")

    # ---- (Welfare figure is generated separately by plot_welfare_schedule.py) ----

    if os.path.isdir(PAPER_FIG_DIR):
        import shutil
        for f in ["fig_areq_vs_hours.pdf", "fig_decomposition.pdf"]:
            shutil.copy(os.path.join(OUT_DIR, f),
                        os.path.join(PAPER_FIG_DIR, f))
        print(f"\n[Copied PDFs to {PAPER_FIG_DIR}]")


if __name__ == "__main__":
    main()
