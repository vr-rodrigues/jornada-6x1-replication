# -*- coding: utf-8 -*-
"""
plot_calibration_fit.py — Calibration fit figure.
Stacked vertically (A on top, B1 middle, B2 bottom).
ggplot-style visuals, larger fonts.
"""
import os
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from matplotlib.lines import Line2D

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_FIG = os.path.join(ROOT, "output", "figures", "fig_calibration_fit.png")
os.makedirs(os.path.dirname(OUT_FIG), exist_ok=True)

# ggplot-inspired theme
plt.style.use("ggplot")
mpl.rcParams.update({
    "font.family": "serif",
    "font.size": 12,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "legend.fontsize": 11,
    "axes.facecolor": "white",
    "figure.facecolor": "white",
    "axes.edgecolor": "#333333",
    "grid.color": "#d0d0d0",
    "grid.linestyle": "-",
    "grid.linewidth": 0.6,
})

# ---------------- Panel A: targeted moments ----------------
targeted = [
    ("Informality rate, small firms ($\\leq 49$ empl.)",  0.500, 0.500),
    ("Informality rate, large firms",                     0.200, 0.200),
    ("Formal employment share, small firms",              0.590, 0.590),
    ("Formal employment share, large firms",              0.410, 0.410),
    ("Aggregate informality (narrow, PNAD)",              0.378, 0.377),
    ("Wage premium $R$ (MNR 2015 central)",               1.260, 1.260),
]

# ---------------- Panel B1: domestic alternative-measurement check ----------
domestic = [
    {"label": "Average weekly formal hours",
     "data": 41.23, "model": 42.24, "unit": "h/week"},
    {"label": "Share of formal workers above 36h (%)",
     "data": 85.7,  "model": 91.5,  "unit": "pp"},
]

# ---------------- Panel B2: external directional benchmark ----------
external = [
    {"label": r"$\Delta Y$ at common 44$\to$40h cap (\%)",
     "data": -3.20, "model": -1.81, "unit": "pp"},
]

DATA_COLOR = "#2c3e50"
MODEL_COLOR = "#e67e22"


def draw_dumbbell(ax, items):
    n = len(items)
    yvals = np.arange(n)
    labels = [it["label"] for it in items]
    d_arr  = np.array([it["data"]  for it in items], dtype=float)
    m_arr  = np.array([it["model"] for it in items], dtype=float)
    scale  = np.maximum(np.abs(d_arr), 1e-6)
    rel    = (m_arr - d_arr) / scale

    for i, (d, m, r, it) in enumerate(zip(d_arr, m_arr, rel, items)):
        ax.plot([0, r], [i, i], color="#95a5a6", linewidth=2.5,
                alpha=0.85, zorder=1, solid_capstyle="round")
        ax.scatter([0], [i], s=210, c=DATA_COLOR, marker="o",
                   edgecolor="black", linewidth=1.0, zorder=3)
        ax.scatter([r], [i], s=210, c=MODEL_COLOR, marker="o",
                   edgecolor="black", linewidth=1.0, zorder=3)

        ax.text(-0.015, i, f"{d}", va="center", ha="right",
                fontsize=12, color=DATA_COLOR, fontweight="bold")
        ax.text(r + 0.015 if r >= 0 else r - 0.015, i, f"{m}",
                va="center", ha="left" if r >= 0 else "right",
                fontsize=12, color=MODEL_COLOR, fontweight="bold")

        gap = abs(m - d)
        unit = it.get("unit", "")
        gap_text = f"gap = {gap:.2f} {unit}".strip().replace("  ", " ")
        ax.text((0 + r) / 2.0, i + 0.38, gap_text,
                va="top", ha="center", fontsize=11,
                color="#7b241c", style="italic")

    ax.set_yticks(yvals)
    ax.set_yticklabels(labels, fontsize=12)
    ax.invert_yaxis()
    ax.axvline(x=0, color="#2c3e50", linewidth=0.6, alpha=0.4)
    rmax = max(0.25, max(abs(rel.min()), abs(rel.max())) * 1.9)
    ax.set_xlim(-rmax, rmax)
    ax.set_ylim(n - 0.45, -0.45)
    ax.tick_params(axis="y", length=0)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


# ---------------- Figure (stacked vertically) ----------------
fig = plt.figure(figsize=(11.5, 12.5))
gs = fig.add_gridspec(
    nrows=3, ncols=1,
    height_ratios=[1.5, 0.9, 0.55],
    hspace=0.55,
)
axA  = fig.add_subplot(gs[0, 0])
axB1 = fig.add_subplot(gs[1, 0])
axB2 = fig.add_subplot(gs[2, 0])

# ---- Panel A: targets ----
labels_A = [m[0] for m in targeted]
data_A   = [m[1] for m in targeted]
model_A  = [m[2] for m in targeted]
yA = np.arange(len(labels_A))
h = 0.35

axA.barh(yA - h/2, data_A,  height=h, color=DATA_COLOR, label="Data target",
         alpha=0.88, edgecolor="black", linewidth=0.4)
axA.barh(yA + h/2, model_A, height=h, color="#3498db", label="Model",
         alpha=0.88, edgecolor="black", linewidth=0.4)
axA.set_yticks(yA)
axA.set_yticklabels(labels_A, fontsize=12)
axA.invert_yaxis()
axA.set_xlabel("Moment value", fontsize=12)
axA.set_title("A. Calibration targets (matched by construction)",
              fontsize=13, loc="left", fontweight="bold", pad=12)
axA.legend(loc="lower right", fontsize=11, frameon=True,
           facecolor="white", edgecolor="#bdc3c7")
axA.grid(True, axis="x", alpha=0.4, linestyle="-", linewidth=0.6)

for i, (d, m) in enumerate(zip(data_A, model_A)):
    axA.text(d + 0.02, i - h/2, f"{d:.3f}", va="center",
             fontsize=10, color=DATA_COLOR)
    axA.text(m + 0.02, i + h/2, f"{m:.3f}", va="center",
             fontsize=10, color="#2980b9")

axA.set_xlim(0, 1.55)

# ---- Panel B1: Domestic alternative-measurement check ----
draw_dumbbell(axB1, domestic)
axB1.set_title("B1. Domestic alternative-measurement check (DIEESE contracted vs PNAD habitual)",
               fontsize=13, loc="left", fontweight="bold", pad=12)
axB1.set_xlabel("Relative position: (model $-$ data) / |data|", fontsize=12)

# ---- Panel B2: External directional benchmark ----
draw_dumbbell(axB2, external)
axB2.set_title("B2. External directional benchmark (Portugal 1996, firm-level)",
               fontsize=13, loc="left", fontweight="bold", pad=12)
axB2.set_xlabel("Relative position: (model $-$ data) / |data|", fontsize=12)

legend_handles = [
    Line2D([], [], marker="o", linestyle="", markersize=12,
           markerfacecolor=DATA_COLOR, markeredgecolor="black", label="Data"),
    Line2D([], [], marker="o", linestyle="", markersize=12,
           markerfacecolor=MODEL_COLOR, markeredgecolor="black", label="Model"),
]
axB2.legend(handles=legend_handles, loc="lower right", fontsize=11,
            frameon=True, facecolor="white", edgecolor="#bdc3c7")

plt.savefig(OUT_FIG, dpi=150, bbox_inches="tight")
plt.close()
print(f"[OK] Saved: {OUT_FIG}")
