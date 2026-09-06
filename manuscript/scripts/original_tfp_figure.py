"""Redraw the original Portuguese PWT figure from the verified annual series.

Design reference: archived ``plot_figures_pt.py::plot_tfp_history_pt`` and the
original PAPER PDF.  Its executed code draws ONE historical panel and returns;
the two-panel implementation below that return was never part of this figure.
This module preserves its purple line, gold decade band, serif typography,
axes, legend, dimensions and historical-level object.

The original figure contains no A_req series.  Updated PNAD compensation values
belong to the existing horizon table, not to this index-level axis.  No model
results are substituted into the PWT series and no additional panel is added.
The verified vintage still spans 1954--2023 (2021 = 1), so its historical curve
can correctly remain unchanged when only the policy results are updated.

Integration in generate_assets.make_tfp, replacing only its plotting block::

    from original_tfp_figure import draw_tfp_figure
    draw_tfp_figure(d, out, savefig)

All CSV/table/provenance calculations in make_tfp remain in that caller.
The callback has the existing signature ``savefig(fig, out, stem)``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Values copied from the original _style.py, scoped to this figure so the
# generator's other figures do not inherit a changed global style.
_ORIGINAL_STYLE = {
    "font.family": "serif",
    "font.serif": ["DejaVu Serif"],
    "font.size": 12,
    "axes.titlesize": 15,
    "axes.titleweight": "bold",
    "axes.labelsize": 12,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "legend.fontsize": 10,
    "axes.facecolor": "white",
    "figure.facecolor": "white",
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.7,
    "axes.labelcolor": "#222222",
    "text.color": "#222222",
    "axes.grid": False,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "xtick.color": "#222222",
    "ytick.color": "#222222",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.1,
}


def draw_tfp_figure(
    data: pd.DataFrame,
    out: Path,
    savefig: Callable,
) -> dict:
    """Save the original single-panel design using supplied verified PWT data.

    ``data`` must contain unique annual ``year`` and positive ``rtfpna`` values,
    with the verified 2021 normalization.  Missing observations are rejected
    rather than silently changing the historical reference window.  The return
    value describes the plotted observations and recomputed decade selection.
    Neither the input frame nor any empirical/model result is modified.
    """
    required = {"year", "rtfpna"}
    if not required.issubset(data.columns):
        raise ValueError("TFP figure requires year and rtfpna columns")
    bra = data.loc[:, ["year", "rtfpna"]].copy()
    for column in required:
        bra[column] = pd.to_numeric(bra[column], errors="raise")
    if not np.isfinite(bra.to_numpy(dtype=float)).all():
        raise ValueError("TFP figure refuses missing or nonfinite observations")
    if not np.equal(bra.year, np.floor(bra.year)).all():
        raise ValueError("TFP observations must be indexed by integer years")
    bra["year"] = bra.year.astype(int)
    if bra.year.duplicated().any() or (bra.rtfpna <= 0).any():
        raise ValueError("TFP figure requires unique years and positive levels")
    bra = bra.sort_values("year").reset_index(drop=True)
    values = bra.set_index("year").rtfpna
    if 2021 not in values.index or not np.isclose(values.loc[2021], 1.0, atol=1e-8, rtol=0):
        raise ValueError("TFP axis requires the verified PWT normalization 2021 = 1")
    if not set(range(1990, 2020)).issubset(values.index):
        raise ValueError("TFP figure requires all years in the 1990--2019 comparison window")

    # Same candidate windows as the archived figure: wholly within 1990--2019.
    decades = [
        (year, year + 10, float(100 * ((values.loc[year + 10] / values.loc[year]) ** 0.1 - 1)))
        for year in range(1990, 2010)
    ]
    best_start, best_end, best_growth = max(decades, key=lambda row: row[2])
    start, end = int(bra.year.min()), int(bra.year.max())

    with plt.rc_context(_ORIGINAL_STYLE):
        fig, ax = plt.subplots(figsize=(9.5, 5.8))
        ax.plot(bra.year, bra.rtfpna, color="#5e1a84", linewidth=2.0)
        ax.axhline(
            y=float(values.loc[1990]), color="#20132d", linestyle=":",
            alpha=0.6, linewidth=1.0, label="Nível de 1990",
        )
        ax.axvspan(
            best_start, best_end, alpha=0.18, color="#f6c36b",
            label=f"Melhor década pós-1990 ({best_start}-{best_end})",
        )
        ax.set_title(
            f"PTF brasileira, {start}-{end}", fontweight="bold", loc="left",
            pad=10, color="#222222",
        )
        ax.set_xlabel("Ano", color="#222222")
        ax.set_ylabel("PTF real (2021 = 1)", color="#222222")
        ax.grid(False)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color("#333333")
            ax.spines[side].set_linewidth(0.7)
        ax.legend(loc="lower left", frameon=False)
        fig.tight_layout()
        try:
            savefig(fig, Path(out), "fig_areq_vs_tfp_history_pt")
        finally:
            plt.close(fig)

    return {
        "layout": "original_single_historical_panel",
        "observations": len(bra),
        "start_year": start,
        "end_year": end,
        "unit": "PWT rtfpna; 2021 = 1",
        "level_1990": float(values.loc[1990]),
        "best_decade_search_start": 1990,
        "best_decade_search_end": 2019,
        "best_decade_start": best_start,
        "best_decade_end": best_end,
        "best_decade_growth_pct_year": best_growth,
    }
