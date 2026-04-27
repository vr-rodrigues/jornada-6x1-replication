# -*- coding: utf-8 -*-
"""
plot_sectoral_fig.py — Sectoral A_req figure (Fig 7) with ggplot aesthetic
matching Figs 1/2/3. Reads sectoral results CSV and produces a bar chart.
"""
import os, csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CSV_PATH = os.path.join(ROOT, "output", "sectoral", "tables", "SECTOR_AREQ_EMPIRICAL.csv")
OUT = os.path.join(ROOT, "output", "figures", "fig_sectoral_areq.png")
PAPER = os.path.join(ROOT, "paper", "overleaf", "figures", "fig_sectoral_areq.png")

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _style import apply_style, set_axis_style, save_pdf, COLOR_PREF, COLOR_CONS, TEXT_DARK
apply_style()

COLOR_40 = COLOR_PREF
COLOR_36 = COLOR_CONS

# Load CSV
rows = []
with open(CSV_PATH, "r") as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

sectors = ["agriculture", "industry", "services"]
labels = ["Agriculture", "Industry", "Services"]

areq_40 = [float(next(r["A_req_pct"] for r in rows
                       if r["sector"] == s and r["h1"] == "40")) for s in sectors]
areq_36 = [float(next(r["A_req_pct"] for r in rows
                       if r["sector"] == s and r["h1"] == "36")) for s in sectors]

x = np.arange(len(sectors))
w = 0.35

fig, ax = plt.subplots(figsize=(10, 5.5))
b1 = ax.bar(x - w/2, areq_40, width=w, color=COLOR_40, alpha=0.85,
             edgecolor="#2c3e50", linewidth=0.3, label=r"44$\to$40h" + "\ncap")
b2 = ax.bar(x + w/2, areq_36, width=w, color=COLOR_36, alpha=0.85,
             edgecolor="#2c3e50", linewidth=0.3, label=r"44$\to$36h" + "\ncap")

for bar, v in list(zip(b1, areq_40)) + list(zip(b2, areq_36)):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.15,
             f"{v:.2f}%", ha="center", va="bottom",
             fontsize=10, fontstyle="italic", color=TEXT_DARK)

ax.axhline(0, color="#666666", linewidth=0.5)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=11)
set_axis_style(
    ax,
    title="Required TFP Gain by Sector (conservative symmetric calibration)",
    xlabel=None,
    ylabel=r"Sector-specific $A_{req}$ (%)",
)
ax.xaxis.grid(False)
ax.legend(loc="upper right", frameon=False, labelspacing=0.8)
ax.set_ylim(0, max(areq_36) * 1.2)

plt.tight_layout()
pdf = save_pdf(fig, OUT)
plt.close()

import shutil
paper_pdf = PAPER.replace(".png", ".pdf")
if os.path.isdir(os.path.dirname(paper_pdf)):
    shutil.copy(pdf, paper_pdf)
    print(f"[OK] {paper_pdf}")
print(f"[OK] {pdf}")
