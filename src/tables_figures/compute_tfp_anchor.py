# -*- coding: utf-8 -*-
"""
compute_tfp_anchor.py — Computes historical Brazilian TFP growth rates from PWT 10.0
and generates the A_req vs historical TFP anchoring figure/table for the paper.

Output:
  - data_final/tfp_brazil_anchor.json (numerical results)
  - output/figures/fig_areq_vs_tfp_history.png
  - output/tables/tab_areq_tfp_horizons.tex

Source: Penn World Table 10.0 (rtfpna = real TFP at constant national prices)
"""

import json
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PWT_PATH = os.path.join(ROOT, "data_raw", "pwt1001.xlsx")
OUT_DATA = os.path.join(ROOT, "data_final", "tfp_brazil_anchor.json")
OUT_FIG = os.path.join(ROOT, "output", "figures", "fig_areq_vs_tfp_history.png")
OUT_TAB = os.path.join(ROOT, "output", "tables", "tab_areq_tfp_horizons.tex")

os.makedirs(os.path.dirname(OUT_FIG), exist_ok=True)
os.makedirs(os.path.dirname(OUT_TAB), exist_ok=True)

A_REQ = 6.63  # percent, preferred flat-below baseline (post-audit3 revision, eta_I=0.40, sigma=1.326)


def annualized_growth(series, years_span):
    """Compute the annualized growth rate between first and last point of a series."""
    first = series.iloc[0]
    last = series.iloc[-1]
    return (last / first) ** (1 / years_span) - 1


def years_to_compensate(a_req_pct, annual_growth_pct):
    """How many years at `annual_growth_pct` per year to accumulate `a_req_pct`?"""
    if annual_growth_pct <= 0:
        return float("inf")
    return np.log(1 + a_req_pct / 100) / np.log(1 + annual_growth_pct / 100)


# ============================================================
# Load data
# ============================================================
print("Loading PWT data...")
df = pd.read_excel(PWT_PATH, sheet_name="Data")
bra = df[df["countrycode"] == "BRA"].copy().sort_values("year").reset_index(drop=True)
bra = bra[["year", "rtfpna", "rgdpna", "emp", "avh", "labsh"]]

print(f"Brazil series: {bra['year'].min()}-{bra['year'].max()}, {len(bra)} years")

# ============================================================
# Compute growth rates over various horizons
# ============================================================
horizons = [
    ("1950-2019", 1950, 2019),  # full post-war
    ("1950-1980", 1950, 1980),  # Brazilian miracle
    ("1980-2000", 1980, 2000),  # lost decades
    ("1990-2019", 1990, 2019),  # post-Constitution/Real Plan era
    ("1995-2019", 1995, 2019),  # post-Real Plan stabilization
    ("2000-2019", 2000, 2019),  # 21st century
    ("2003-2013", 2003, 2013),  # growth decade
    ("2010-2019", 2010, 2019),  # last decade available
]

results = []
for label, y0, y1 in horizons:
    sub = bra[(bra["year"] >= y0) & (bra["year"] <= y1)]
    sub = sub.dropna(subset=["rtfpna"])
    if len(sub) < 2:
        continue
    tfp_series = sub["rtfpna"]
    # Use actual first/last valid years for robust computation
    actual_y0 = int(sub["year"].iloc[0])
    actual_y1 = int(sub["year"].iloc[-1])
    span = actual_y1 - actual_y0
    if span == 0:
        continue
    g = annualized_growth(tfp_series, span)
    if np.isnan(g):
        continue
    results.append({
        "horizon": f"{actual_y0}-{actual_y1}",
        "start_year": actual_y0,
        "end_year": actual_y1,
        "span_years": span,
        "tfp_start": round(float(tfp_series.iloc[0]), 4),
        "tfp_end": round(float(tfp_series.iloc[-1]), 4),
        "annual_growth_pct": round(g * 100, 3),
        "years_to_compensate_areq": round(years_to_compensate(A_REQ, g * 100), 1)
            if g > 0 else float("inf"),
    })

# Print summary
print("\n" + "=" * 80)
print(f"Brazilian TFP growth (PWT 10.0, rtfpna) and years to accumulate A_req = {A_REQ}%")
print("=" * 80)
print(f"{'Horizon':<15} {'Years':>6} {'TFP_0':>8} {'TFP_1':>8} {'g (%/yr)':>10} {'Years->A_req':>14}")
print("-" * 80)
for r in results:
    yts = r["years_to_compensate_areq"]
    yts_str = f"{yts:.1f}" if yts != float("inf") else "inf"
    print(f"{r['horizon']:<15} {r['span_years']:>6} {r['tfp_start']:>8.4f} {r['tfp_end']:>8.4f} "
          f"{r['annual_growth_pct']:>9.3f}  {yts_str:>14}")

# ============================================================
# Key summary numbers for the paper
# ============================================================
# "Modern era": 1995-2019 (post-Real Plan)
modern = [r for r in results if r["horizon"] == "1995-2019"][0]
# "Long run": 1990-2019
long_run = [r for r in results if r["horizon"] == "1990-2019"][0]
# "Growth decade" (best recent performance): 2003-2013
best = [r for r in results if r["horizon"] == "2003-2013"][0]
# "Last decade": 2010-2019
recent = [r for r in results if r["horizon"] == "2010-2019"][0]

summary = {
    "source": "Penn World Table 10.0 (downloaded 2026-04-20), variable rtfpna",
    "country": "Brazil",
    "a_req_pct": A_REQ,
    "modern_era_1995_2019": modern,
    "long_run_1990_2019": long_run,
    "growth_decade_2003_2013": best,
    "recent_decade_2010_2019": recent,
    "all_horizons": results,
    "key_finding": (
        "Brazilian TFP has declined over the long run (1990-2019: "
        f"{long_run['annual_growth_pct']:+.2f}%/yr) and over recent decades. "
        "Even the best growth decade (2003-2013) had TFP growth of only "
        f"{best['annual_growth_pct']:+.2f}%/yr, requiring "
        f"{best['years_to_compensate_areq']:.0f} years to accumulate A_req = {A_REQ}%. "
        "A one-off TFP gain of this magnitude has no historical precedent in the "
        "modern Brazilian series."
    ),
}

with open(OUT_DATA, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(f"\n[OK] Saved numerical results to {OUT_DATA}")

# ============================================================
# Generate figure
# ============================================================
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _style import apply_style, set_axis_style, save_pdf, TEXT_DARK
apply_style()
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 10.5), gridspec_kw={"hspace": 0.45})

# Panel A: TFP series
ax1.plot(bra["year"], bra["rtfpna"], color="#2c3e50", linewidth=1.6)
ax1.axhline(y=bra[bra["year"] == 1990]["rtfpna"].iloc[0], color="#888888",
            linestyle=":", alpha=0.6, linewidth=1.0, label="1990 level")
ax1.axvspan(2003, 2013, alpha=0.12, color="#27ae60",
             label="Growth decade (2003-2013)")
set_axis_style(ax1,
                title="A. Brazilian TFP, 1950-2019",
                xlabel="Year",
                ylabel="Real TFP (2017 = 1)")
ax1.legend(loc="lower left", frameon=False)

# Panel B: Growth rates by horizon with numerical values + years-to-A_req
horizons_plot = ["1990-2019", "1995-2019", "2000-2019", "2003-2013", "2010-2019"]
growth_rates = [next(r["annual_growth_pct"] for r in results if r["horizon"] == h)
                for h in horizons_plot]
years_req = [next(r["years_to_compensate_areq"] for r in results if r["horizon"] == h)
             for h in horizons_plot]

colors = ["#c0392b" if g <= 0 else "#2980b9" for g in growth_rates]
x = np.arange(len(horizons_plot))
bar_width = 0.65
bars = ax2.bar(x, growth_rates, width=bar_width, color=colors,
                edgecolor="#2c3e50", linewidth=0.4, alpha=0.85)
ax2.axhline(y=0, color="#666666", linewidth=0.5)

two_line_labels = []
for h, g, y in zip(horizons_plot, growth_rates, years_req):
    if g > 0 and y != float("inf"):
        yrs = f"{y:.0f} yrs to A$_{{req}}$"
    else:
        yrs = "never"
    two_line_labels.append(f"{h}\n({yrs})")
ax2.set_xticks(x)
ax2.set_xticklabels(two_line_labels, rotation=0, fontsize=10)
set_axis_style(
    ax2,
    title=f"B. Historical TFP growth by horizon (A$_{{req}}$ = {A_REQ}%)",
    xlabel=None,
    ylabel="Annual TFP growth (%/year)",
)
ax2.xaxis.grid(False)

ymin = min(growth_rates) - 0.45
ymax = max(growth_rates) + 0.50
ax2.set_ylim(ymin, ymax)

for bar, g in zip(bars, growth_rates):
    if g >= 0:
        y_text = g + 0.10
        va = "bottom"
    else:
        y_text = g - 0.12
        va = "top"
    ax2.text(bar.get_x() + bar.get_width()/2, y_text,
              f"{g:+.2f}%", ha="center", va=va,
              fontsize=11, fontstyle="italic", color=TEXT_DARK)

# Tighten layout
pdf_path = save_pdf(fig, OUT_FIG)
print(f"[OK] Saved figure to {pdf_path}")
plt.close()

# ============================================================
# Generate LaTeX table
# ============================================================
tex_lines = [
    r"% Auto-generated by src/tables_figures/compute_tfp_anchor.py",
    r"% Source: PWT 10.0, rtfpna (real TFP at constant national prices), Brazil",
    r"\begin{table}[htbp]",
    r"\centering",
    r"\caption{Historical Brazilian TFP growth and years required to accumulate $A_{\text{req}}$.}\label{tab:tfp_history}",
    r"\small",
    r"\begin{tabular}{lrrrr}",
    r"\hline\hline",
    r"Horizon & Span (yrs) & TFP growth (\%/yr) & Years to $A_{\text{req}}$ & Feasibility \\",
    r"\hline",
]
for r in results:
    horizon = r["horizon"]
    span = r["span_years"]
    g = r["annual_growth_pct"]
    y2a = r["years_to_compensate_areq"]
    if g <= 0:
        feas = r"\textit{never}"
        y2a_str = r"$\infty$"
    else:
        feas = "feasible"
        y2a_str = f"{y2a:.1f}"
    tex_lines.append(f"{horizon} & {span} & {g:+.2f} & {y2a_str} & {feas} \\\\")

tex_lines += [
    r"\hline\hline",
    r"\multicolumn{5}{l}{\footnotesize \textit{Source:} Penn World Table 10.0, variable \texttt{rtfpna} (real TFP at}\\",
    r"\multicolumn{5}{l}{\footnotesize constant national prices). Growth rate is annualized $(\text{TFP}_1/\text{TFP}_0)^{1/T}-1$. }\\",
    r"\multicolumn{5}{l}{\footnotesize Years to $A_{\text{req}} = " + f"{A_REQ}" + r"\%$ computed as $\ln(1+A_{\text{req}})/\ln(1+g)$.}",
    r"\end{tabular}",
    r"\end{table}",
]

with open(OUT_TAB, "w", encoding="utf-8") as f:
    f.write("\n".join(tex_lines))
print(f"[OK] Saved LaTeX table to {OUT_TAB}")

# ============================================================
# Print the key finding
# ============================================================
print("\n" + "=" * 80)
print("KEY FINDING FOR THE PAPER")
print("=" * 80)
print(summary["key_finding"])
