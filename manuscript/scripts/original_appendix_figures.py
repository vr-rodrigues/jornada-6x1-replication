"""Restore the appendix's original grouped-bar figures with corrected results.

Visual references are the actual PDFs archived in
``replication_package/paper/tex/figures/`` (also preserved in the original
audit snapshot), rather than their stale PNG counterparts.  The original
``plot_sectoral_fig.py`` and ``plot_main_figures.py`` establish the panel,
category and series order.  Their old model calculations are never imported.

Both public functions accept a DataFrame, records, or a CSV path and return a
Matplotlib Figure.  They do not write artifacts; the manuscript generator
owns saving, source hashes, and integration.  These figures retain the
original single panel, vertical grouped bars, blue/red series, serif type,
italic title and labels, numeric bar labels, and restrained horizontal grid.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from copy import deepcopy
import sys

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
from paper_config import PRIMARY_VERSION, SECTORAL_VERSION


COLOR_FIRST = "#2980b9"
COLOR_SECOND = "#c0392b"
TEXT_DARK = "#222222"
SECTORS = ("agriculture", "industry", "services")
MODES = ("flat_below", "bilateral")

ORIGINAL_REFERENCES = {
    "sectoral": {
        "pdf": "replication_package/paper/tex/figures/fig_sectoral_areq.pdf",
        "sha256": "4c0d9c83857502333ee956ad0aedeee4cbda966f60c0bda38dd548dbaf7018f",
        "script": "auditoria_original_20260905_002456/snapshot/src/tables_figures/plot_sectoral_fig.py",
        "layout": "single grouped vertical bar chart, three sectors, 40h/36h, bilateral",
    },
    "decomposition": {
        "pdf": "replication_package/paper/tex/figures/fig_decomposition.pdf",
        "sha256": "c02ebd76c2a5ea8a7e77aef97f212eee82939b0ec98f18e38eb00c02a8595fb3",
        "script": "auditoria_original_20260905_002456/snapshot/src/tables_figures/plot_main_figures.py",
        "layout": "single grouped vertical bar chart, three ordered channels plus total, 36h",
        "accounting": "corrected intermediate-output differences, all divided by Y0; no mixed-denominator residual",
    },
    "welfare_threshold": {
        "png": "replication_package/paper/tex/figures/slide10c_welfare_threshold.png",
        "script": "auditoria_original_20260905_002456/snapshot/src/tables_figures/plot_welfare_schedule.py",
        "layout": "single line chart at 36h, exogenous TFP 0-8%, two efficiency modes and zero-crossing annotations",
        "metric_correction": "old delta-CV label actually measures percent change in the GHH composite; not individual incidence",
    },
}

_RC = {
    "font.family": "DejaVu Serif", "font.size": 12,
    "mathtext.fontset": "dejavuserif",
    "axes.titlesize": 14, "axes.titleweight": "normal",
    "axes.labelsize": 12, "xtick.labelsize": 11, "ytick.labelsize": 11,
    "legend.fontsize": 10, "axes.facecolor": "white",
    "figure.facecolor": "white", "axes.edgecolor": "#333333",
    "axes.linewidth": .7, "text.color": TEXT_DARK,
    "axes.labelcolor": TEXT_DARK, "xtick.color": TEXT_DARK,
    "ytick.color": TEXT_DARK, "axes.grid": False,
    "xtick.direction": "out", "ytick.direction": "out",
    "pdf.fonttype": 42, "ps.fonttype": 42,
}


def _frame(rows: Any) -> pd.DataFrame:
    if isinstance(rows, (str, Path)):
        return pd.read_csv(rows)
    if isinstance(rows, pd.DataFrame):
        return rows.copy()
    return pd.DataFrame(rows)


def _number(value: float, digits: int = 2, signed: bool = False,
            language: str = "pt") -> str:
    result = f"{value:+.{digits}f}" if signed else f"{value:.{digits}f}"
    return result.replace(".", ",") if language == "pt" else result


def _axis(ax, title: str, ylabel: str, language: str) -> None:
    ax.set_title(title, fontstyle="italic", fontweight="normal", loc="left", pad=10)
    ax.set_ylabel(ylabel, fontstyle="italic")
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", color="#b8b8b8", linewidth=.35, alpha=.55)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=6))
    ax.yaxis.set_major_formatter(FuncFormatter(
        lambda value, _: _number(value, 0 if float(value).is_integer() else 1,
                                  language=language)))
    ax.axhline(0, color="#666666", linewidth=.5, alpha=.8)


def _single(df: pd.DataFrame, mask: pd.Series, description: str) -> pd.Series:
    selected = df.loc[mask]
    if len(selected) != 1:
        raise ValueError(f"Expected exactly one {description}; found {len(selected)}")
    return selected.iloc[0]


def plot_sectoral_areq(rows: Any, *, language: str = "pt"):
    """Original sector figure: bilateral A_req, agriculture/industry/services,
    blue 40h and red 36h bars. Negative A_req values remain visible.

    Input: the primary ``sectoral_empirical_bridge/SECTOR_RESULTS.csv`` or
    ``RESULTADOS_SETORIAIS.csv`` (explicitly filtered to empirical_bridge).
    """
    df = _frame(rows)
    if "scenario_variant" in df:
        df = df.loc[df["scenario_variant"].eq(SECTORAL_VERSION)]
    df = df.loc[df["efficiency_mode"].eq("bilateral")]
    values = {
        cap: np.array([float(_single(
            df, df["sector"].eq(sector) & df["h1"].eq(cap),
            f"bilateral {sector} at {cap}h")["A_req_pct"])
            for sector in SECTORS]) for cap in (40, 36)
    }
    if not np.isfinite(np.concatenate(list(values.values()))).all():
        raise ValueError("Nonfinite sector productivity requirement")

    with mpl.rc_context(_RC):
        fig, ax = plt.subplots(figsize=(10, 5.5))
        x, width = np.arange(3), .35
        for cap, offset, color in ((40, -width / 2, COLOR_FIRST),
                                   (36, width / 2, COLOR_SECOND)):
            label = f"Teto de {cap}h" if language == "pt" else f"{cap}h cap"
            bars = ax.bar(x + offset, values[cap], width=width, color=color,
                          alpha=.85, edgecolor="#2c3e50", linewidth=.3, label=label)
            for bar, value in zip(bars, values[cap]):
                ax.text(bar.get_x() + width / 2, value + (.15 if value >= 0 else -.15),
                        _number(value, language=language) + "%", ha="center",
                        va="bottom" if value >= 0 else "top", fontsize=10,
                        fontstyle="italic", color=TEXT_DARK)
        labels = (["Agricultura", "Indústria", "Serviços"] if language == "pt"
                  else ["Agriculture", "Industry", "Services"])
        title = ("Ganho requerido de PTF por setor (penalidade bilateral)"
                 if language == "pt" else
                 "Required TFP Gain by Sector (two-sided penalty calibration)")
        ylabel = (r"$A_{\mathrm{req}}$ setorial (%)" if language == "pt"
                  else r"Sector-specific $A_{\mathrm{req}}$ (%)")
        ax.set_xticks(x, labels)
        _axis(ax, title, ylabel, language)
        ymin = min(0., min(float(v.min()) for v in values.values()))
        ymax = max(float(v.max()) for v in values.values())
        ax.set_ylim(ymin - (.55 if ymin < 0 else 0), ymax * 1.2)
        ax.legend(loc="upper right", frameon=False, labelspacing=.8)
        fig.tight_layout()
    return fig


def plot_decomposition(rows: Any, *, hours_cap: int = 36,
                       language: str = "pt"):
    """Original four-category grouped chart, using corrected common-denominator
    accounting. Input is the primary rows of COMPARATIVO_RESULTADOS.csv.

    Channels: physical hours -> efficiency -> formal/informal reallocation;
    fourth category is their sum (the total change in output). Unlike the old
    figure, the third term is not a residual combining incompatible units.
    """
    df = _frame(rows)
    if "version" in df:
        df = df.loc[df["version"].eq(PRIMARY_VERSION)]
    if "mode" in df and "efficiency_mode" not in df:
        df = df.rename(columns={"mode": "efficiency_mode", "cap": "hours_cap",
                                "total_pct": "dY_pct"})
    columns = ["hours_pct", "efficiency_pct", "reallocation_pct", "dY_pct"]
    values = {}
    for mode in MODES:
        row = _single(df, df["efficiency_mode"].eq(mode) &
                      df["hours_cap"].eq(hours_cap), f"{mode} at {hours_cap}h")
        values[mode] = row[columns].to_numpy(dtype=float)
        if not np.isfinite(values[mode]).all():
            raise ValueError("Nonfinite output decomposition")
        if abs(values[mode][:3].sum() - values[mode][3]) > 1.e-9:
            raise ValueError("The three product contributions do not sum to total")

    with mpl.rc_context(_RC):
        fig, ax = plt.subplots(figsize=(10, 6.2))
        x, width = np.arange(4), .35
        for mode, offset, color in (("flat_below", -width / 2, COLOR_FIRST),
                                    ("bilateral", width / 2, COLOR_SECOND)):
            if language == "pt":
                label = "Fadiga só acima\ndo pico" if mode == "flat_below" else "Penalidade\nbilateral"
            else:
                label = "One-sided\nfatigue" if mode == "flat_below" else "Two-sided\npenalty"
            bars = ax.bar(x + offset, values[mode], width=width, color=color,
                          alpha=.85, edgecolor="#2c3e50", linewidth=.3, label=label)
            for bar, value in zip(bars, values[mode]):
                # Preserve the original long-bar label treatment while allowing
                # the corrected (smaller) mechanical contributions to be read.
                inside = value <= -6.
                text_y = value / 2 if inside else value + (.18 if value >= 0 else -.18)
                ax.text(bar.get_x() + width / 2, text_y,
                        _number(value, signed=True, language=language) + "%",
                        ha="center", va="center" if inside else
                        ("bottom" if value >= 0 else "top"), fontsize=10,
                        fontstyle="italic", color="white" if inside else TEXT_DARK)
        labels = (["Horas físicas", "Eficiência\n" + r"$e(h)$",
                   "Realocação\nformal-informal", "Total"] if language == "pt"
                  else ["Physical hours", "Efficiency\n" + r"$e(h)$",
                        "Formal-informal\nreallocation", "Total"])
        title = (f"Decomposição do produto no teto de {hours_cap}h" if language == "pt"
                 else f"Output Decomposition at the {hours_cap}h Cap")
        ylabel = (r"Contribuição a $\Delta Y$ (% de $Y_0$)" if language == "pt"
                  else r"Contribution to $\Delta Y$ (% of $Y_0$)")
        ax.set_xticks(x, labels)
        _axis(ax, title, ylabel, language)
        all_values = np.concatenate(list(values.values()))
        ax.set_ylim(float(all_values.min()) - 1.3, float(all_values.max()) + 2.8)
        ax.legend(loc="upper left", bbox_to_anchor=(.01, .99),
                  frameon=False, labelspacing=.8)
        fig.tight_layout()
    return fig


def compute_welfare_threshold(inputs: dict, bridges: list[dict], *,
                              replication_root: str | Path,
                              anchor_rows: Any = None,
                              gains_pct: Any = None):
    """Recompute the original aggregate welfare-versus-TFP experiment at 36h.

    ``inputs`` and ``bridges`` are the pinned national_empirical INPUTS.json
    and BRIDGE.json. The shared current kernel builds each baseline once;
    every TFP evaluation then solves composition anew with the same baseline
    wedges, capital and preferences. The function returns (DataFrame, checks)
    and writes no files. Optional canonical national rows validate A=1.
    """
    replication_root = str(Path(replication_root).resolve())
    if replication_root not in sys.path:
        sys.path.insert(0, replication_root)
    from scipy.optimize import brentq
    from src.model.simulation import run_simulation
    from src.model.firm_problem import solve_group
    from src.model.welfare import ghh_change, consumption_equivalent

    gains = (np.linspace(0., 8., 81) if gains_pct is None
             else np.asarray(gains_pct, dtype=float))
    if (gains.ndim != 1 or len(gains) < 2 or gains[0] != 0.
            or not np.isfinite(gains).all() or not np.all(np.diff(gains) > 0)):
        raise ValueError("TFP gains must form an increasing finite grid starting at zero")
    anchors = None if anchor_rows is None else _frame(anchor_rows)
    if anchors is not None and "version" in anchors:
        anchors = anchors.loc[anchors["version"].eq(PRIMARY_VERSION)]
    records, mode_checks = [], {}
    for mode in MODES:
        matched = [row for row in bridges if row["efficiency_mode"] == mode]
        if len(matched) != 1:
            raise ValueError(f"Expected one canonical hourly bridge for {mode}")
        bridge = matched[0]
        targets = deepcopy(inputs["targets"])
        targets["H1"]["value"] = 36.
        sim = run_simulation(
            targets, sigma_sub=bridge["sigma_sub"], omega=bridge["omega"],
            theta=inputs["theta"], group_specs=inputs["group_specs"],
            efficiency_mode=mode, hours_bins=inputs["hours_bins"],
            share_basis=inputs["share_basis"],
            resource_costs=inputs["resource_costs"])
        groups, base = sim["groups"], sim["baseline"]
        population = sum(pars["N_total"] for pars in groups.values())
        c0, h0 = base["C"] / population, base["h_avg"]
        diagnostics = {"max_kkt_violation": 0., "max_resource_residual": 0.,
                       "model_evaluations": 0}

        def evaluate(gain):
            allocations = {key: solve_group(pars, 36., sim["theta"],
                           A_mult=1. + float(gain) / 100., composition="reoptimized")
                           for key, pars in groups.items()}
            total = {key: sum(sol[key] for sol in allocations.values())
                     for key in ("Y", "C", "hours_total", "NI", "resource_cost")}
            h1, c1 = total["hours_total"] / population, total["C"] / population
            kkt = max(float(sol["kkt_violation"]) for sol in allocations.values())
            resource_error = abs(total["C"] + total["resource_cost"] - total["Y"])
            diagnostics["max_kkt_violation"] = max(diagnostics["max_kkt_violation"], kkt)
            diagnostics["max_resource_residual"] = max(
                diagnostics["max_resource_residual"], resource_error)
            diagnostics["model_evaluations"] += 1
            return {"efficiency_mode": mode, "hours_cap": 36,
                    "gain_pct": float(gain), "A_mult": 1. + float(gain) / 100.,
                    "dGHH_pct": 100. * ghh_change(c0, h0, c1, h1, sim["nu_ghh"], sim["psi"]),
                    "CE_pct": 100. * consumption_equivalent(c0, h0, c1, h1, sim["nu_ghh"], sim["psi"]),
                    "dY_pct": 100. * (total["Y"] / base["Y"] - 1.),
                    "Y0": base["Y"], "Y1": total["Y"],
                    "C0_per_worker": c0, "C1_per_worker": c1,
                    "hours0_per_worker": h0, "hours1_per_worker": h1,
                    "informality_pct": 100. * total["NI"] / population,
                    "max_kkt_violation": kkt, "resource_residual": resource_error}

        mode_records = [evaluate(gain) for gain in gains]
        records.extend(mode_records)
        zero = mode_records[0]
        anchor_error = max(abs(zero[key] - sim["results"][key])
                           for key in ("dGHH_pct", "CE_pct", "dY_pct"))
        if anchors is not None:
            expected = _single(anchors, anchors["efficiency_mode"].eq(mode) &
                               anchors["hours_cap"].eq(36), f"{mode} canonical 36h anchor")
            anchor_error = max(anchor_error, *(abs(zero[key] - float(expected[key]))
                               for key in ("dGHH_pct", "CE_pct", "dY_pct")))
        if anchor_error > 1.e-9:
            raise ValueError(f"The zero-gain welfare point differs from the audited {mode} run")

        welfare = np.array([row["dGHH_pct"] for row in mode_records])
        if (np.diff(welfare) < -1.e-9).any():
            raise ValueError("Welfare is not increasing on the requested gain grid")
        root, root_residual = None, None
        if welfare[0] < 0. <= welfare[-1]:
            root = float(brentq(lambda gain: evaluate(gain)["dGHH_pct"],
                                float(gains[0]), float(gains[-1]), xtol=1.e-11))
            root_residual = abs(evaluate(root)["dGHH_pct"])
        elif abs(welfare[0]) <= 1.e-12:
            root, root_residual = 0., abs(float(welfare[0]))
        if diagnostics["max_kkt_violation"] > 1.e-7:
            raise ValueError("TFP experiment failed the composition optimality check")
        if diagnostics["max_resource_residual"] > 1.e-9:
            raise ValueError("TFP experiment failed the resource accounting check")
        mode_checks[mode] = {**diagnostics, "canonical_anchor_max_error": anchor_error,
            "zero_crossing_gain_pct": root, "zero_crossing_residual_dGHH_pct": root_residual,
            "nonnegative_gain_required_pct": 0. if welfare[0] >= 0. else root,
            "status": "positive_at_zero_gain" if welfare[0] > 0. else
                      ("neutrality_root_found" if root is not None else "no_root_in_range"),
            "dGHH_pct_at_zero_gain": zero["dGHH_pct"],
            "CE_pct_at_zero_gain": zero["CE_pct"]}
    checks = {"hours_cap": 36, "gain_range_pct": [float(gains[0]), float(gains[-1])],
              "points_per_mode": len(gains), "modes": mode_checks,
              "composition": "reoptimized at every TFP evaluation, including root search",
              "calibration": "baseline bridge, wedges and preferences held fixed along each curve",
              "metric_plotted": "100*(G1-G0)/G0; G=C-v(h), per-worker representative mean hours",
              "CE_in_csv": "100*(G1-G0)/C0; same zero as GHH, different denominator",
              "resource_constraint": "C + resource_cost = Y; input-selected transfer treatment"}
    return pd.DataFrame(records), checks


def plot_welfare_threshold(rows: Any, checks: dict, *, language: str = "pt"):
    """Original single-panel threshold plot, correctly labelled as GHH change.
    A mode already above zero at zero TFP gain is marked as such; no fictitious
    positive neutrality root is drawn for that mode.
    """
    df = _frame(rows)
    with mpl.rc_context(_RC):
        fig, ax = plt.subplots(figsize=(10, 6))
        for mode, style, color in (("flat_below", "-", COLOR_FIRST),
                                    ("bilateral", "--", COLOR_SECOND)):
            selected = df.loc[df["efficiency_mode"].eq(mode)].sort_values("gain_pct")
            if language == "pt":
                label = "Fadiga só acima\ndo pico" if mode == "flat_below" else "Penalidade\nbilateral"
            else:
                label = "One-sided\nfatigue" if mode == "flat_below" else "Two-sided\npenalty"
            ax.plot(selected["gain_pct"], selected["dGHH_pct"], style,
                    color=color, linewidth=1.8, label=label)
            diagnostics = checks["modes"][mode]
            root = diagnostics["zero_crossing_gain_pct"]
            if root is not None:
                ax.axvline(root, color=color, linewidth=.8, linestyle=":", alpha=.8)
                name = "Bilateral" if mode == "bilateral" else (
                    "Acima do pico" if language == "pt" else "One-sided")
                ax.annotate(f"{name}:\n{_number(root, language=language)}%",
                    xy=(root, 0), xytext=(root + .5, 1.4 if mode == "flat_below" else -1.35), fontsize=10,
                    fontstyle="italic", color=color, ha="left", va="center",
                    arrowprops={"arrowstyle": "->", "color": color, "lw": .9})
            elif diagnostics["status"] == "positive_at_zero_gain":
                y0 = diagnostics["dGHH_pct_at_zero_gain"]
                text = ("Positivo já em\n0% de PTF" if language == "pt" else
                        "Positive already\nat 0% TFP")
                ax.annotate(text, xy=(0., y0), xytext=(.5, y0 + 2.4),
                    fontsize=10, fontstyle="italic", color=color,
                    arrowprops={"arrowstyle": "->", "color": color, "lw": .9})
        title = ("Limiar de bem-estar no teto de 36h" if language == "pt" else
                 "Welfare Threshold at the 36h Cap")
        ylabel = (r"Variação do composto GHH (%)" if language == "pt" else
                  "Change in the GHH composite (%)")
        _axis(ax, title, ylabel, language)
        ax.set_xlabel("Ganho exógeno de PTF (%)" if language == "pt" else
                      "Exogenous TFP gain (%)", fontstyle="italic")
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.xaxis.set_major_formatter(FuncFormatter(
            lambda value, _: _number(value, 0, language=language)))
        ax.xaxis.grid(True, linestyle="--", color="#b8b8b8", linewidth=.35, alpha=.55)
        ax.set_ylim(min(-2., float(df["dGHH_pct"].min()) - .5),
                    float(df["dGHH_pct"].max()) + .7)
        # A borderless white backing keeps the zero line from crossing the
        # two-line legend, whose original lower-right position is preserved.
        ax.legend(loc="lower right", frameon=True, facecolor="white",
                  edgecolor="none", framealpha=1., labelspacing=.8)
        fig.tight_layout()
    return fig
