# -*- coding: utf-8 -*-
"""
Compute historical Brazilian TFP growth rates and generate the A_req
anchoring figure/table for the paper.

Preferred source:
  - data_raw/fred/RTFPNABRA632NRUG_pwt110.csv
  - FRED mirror of Penn World Table 11.0, variable rtfpna

Fallback source:
  - data_raw/pwt1001.xlsx
  - bundled Penn World Table 10.01 Excel file
"""

from __future__ import annotations

import json
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PWT_PATH = os.path.join(ROOT, "data_raw", "pwt1001.xlsx")
FRED_PWT11_PATH = os.path.join(ROOT, "data_raw", "fred", "RTFPNABRA632NRUG_pwt110.csv")
OUT_DATA = os.path.join(ROOT, "data_final", "tfp_brazil_anchor.json")
OUT_FIG = os.path.join(ROOT, "output", "figures", "fig_areq_vs_tfp_history.png")
OUT_TAB = os.path.join(ROOT, "output", "tables", "tab_areq_tfp_horizons.tex")
OUT_PHASEIN = os.path.join(ROOT, "output", "validation", "areq_phasein_benchmarks.json")
FLAT_BELOW_PATH = os.path.join(ROOT, "output", "validation", "calibrate_flatbelow.json")
SYMMETRIC_PATH = os.path.join(ROOT, "output", "validation", "calibration_results.json")

os.makedirs(os.path.dirname(OUT_DATA), exist_ok=True)
os.makedirs(os.path.dirname(OUT_FIG), exist_ok=True)
os.makedirs(os.path.dirname(OUT_TAB), exist_ok=True)
os.makedirs(os.path.dirname(OUT_PHASEIN), exist_ok=True)

A_REQ = 6.63  # percent, one-sided fatigue baseline
PHASE_IN_YEARS = (3, 5, 10)


def annualized_growth(series: pd.Series, years_span: int) -> float:
    """Compute the annualized growth rate between first and last point."""
    first = series.iloc[0]
    last = series.iloc[-1]
    return (last / first) ** (1 / years_span) - 1


def years_to_compensate(a_req_pct: float, annual_growth_pct: float) -> float:
    """Years needed to accumulate a_req_pct at annual_growth_pct."""
    if annual_growth_pct <= 0:
        return float("inf")
    return np.log(1 + a_req_pct / 100) / np.log(1 + annual_growth_pct / 100)


def required_annualized_gain(a_req_pct: float, years: int) -> float:
    """Annualized gain needed to accumulate a_req_pct over a fixed horizon."""
    return ((1 + a_req_pct / 100) ** (1 / years) - 1) * 100


def read_json_if_exists(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def json_sanitize(obj):
    """Convert numpy scalars and non-finite floats before writing strict JSON."""
    if isinstance(obj, dict):
        return {key: json_sanitize(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [json_sanitize(value) for value in obj]
    if isinstance(obj, tuple):
        return [json_sanitize(value) for value in obj]
    if isinstance(obj, np.generic):
        return json_sanitize(obj.item())
    if isinstance(obj, float) and not np.isfinite(obj):
        return None
    return obj


def load_areq_scenarios() -> list[dict]:
    """Load central A_req scenarios from existing calibration outputs."""
    flat = read_json_if_exists(FLAT_BELOW_PATH)
    sym = read_json_if_exists(SYMMETRIC_PATH)

    sym_schedule = sym.get("welfare_schedule", [])
    cap40 = next((row for row in sym_schedule if int(row.get("h1", -1)) == 40), {})
    sym_key = sym.get("key_results", {})

    return [
        {
            "scenario": r"40h alternative, central",
            "hours_cap": 40,
            "specification": "central schedule",
            "a_req_pct": float(cap40.get("A_req_pct", 1.925)),
        },
        {
            "scenario": r"36h endpoint, one-sided fatigue",
            "hours_cap": 36,
            "specification": "one-sided fatigue e(h)",
            "a_req_pct": float(flat.get("A_req_pct", A_REQ)),
        },
        {
            "scenario": r"36h endpoint, two-sided penalty",
            "hours_cap": 36,
            "specification": "two-sided penalty e(h)",
            "a_req_pct": float(sym_key.get("A_req_aggregate_pct", 8.182)),
        },
    ]


def phasein_rows(scenarios: list[dict]) -> list[dict]:
    rows = []
    for scenario in scenarios:
        row = dict(scenario)
        for years in PHASE_IN_YEARS:
            row[f"required_gain_{years}yr_pct"] = required_annualized_gain(
                row["a_req_pct"], years
            )
        rows.append(row)
    return rows


def load_brazil_tfp() -> tuple[pd.DataFrame, str, str, str]:
    """Load Brazil rtfpna from PWT 11.0/FRED when available, else PWT 10.01."""
    if os.path.exists(FRED_PWT11_PATH):
        df = pd.read_csv(FRED_PWT11_PATH)
        df["year"] = pd.to_datetime(df["observation_date"]).dt.year
        bra = (
            df.rename(columns={"RTFPNABRA632NRUG": "rtfpna"})[["year", "rtfpna"]]
            .dropna(subset=["rtfpna"])
            .sort_values("year")
            .reset_index(drop=True)
        )
        source_label = "Penn World Table 11.0 via FRED (RTFPNABRA632NRUG)"
        source_note = (
            "PWT 11.0 via FRED, series RTFPNABRA632NRUG, "
            "downloaded to data_raw/fred/RTFPNABRA632NRUG_pwt110.csv"
        )
        tfp_units = "Real TFP (2021 = 1)"
        return bra, source_label, source_note, tfp_units

    df = pd.read_excel(PWT_PATH, sheet_name="Data")
    bra = (
        df[df["countrycode"] == "BRA"][["year", "rtfpna"]]
        .dropna(subset=["rtfpna"])
        .sort_values("year")
        .reset_index(drop=True)
    )
    source_label = "Penn World Table 10.01 (bundled fallback)"
    source_note = "Penn World Table 10.01, variable rtfpna"
    tfp_units = "Real TFP (2017 = 1)"
    return bra, source_label, source_note, tfp_units


def horizon_rows(bra: pd.DataFrame) -> list[dict]:
    """Compute growth statistics over the horizons used in the paper."""
    tfp_start_year = int(bra["year"].min())
    tfp_end_year = int(bra["year"].max())
    latest_modern_end = min(2023, tfp_end_year)

    horizons = [
        (f"{tfp_start_year}-{tfp_end_year}", tfp_start_year, tfp_end_year),
        (f"{tfp_start_year}-1980", tfp_start_year, 1980),
        ("1980-2000", 1980, 2000),
        (f"1990-{latest_modern_end}", 1990, latest_modern_end),
        ("1990-2019", 1990, 2019),
        (f"1995-{latest_modern_end}", 1995, latest_modern_end),
        ("1995-2019", 1995, 2019),
        (f"2000-{latest_modern_end}", 2000, latest_modern_end),
        ("2003-2013", 2003, 2013),
        ("2010-2019", 2010, 2019),
        (f"2019-{latest_modern_end}", 2019, latest_modern_end),
    ]

    results = []
    for _, y0, y1 in horizons:
        sub = bra[(bra["year"] >= y0) & (bra["year"] <= y1)].dropna(subset=["rtfpna"])
        if len(sub) < 2:
            continue
        tfp_series = sub["rtfpna"]
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
            "years_to_compensate_areq": (
                round(years_to_compensate(A_REQ, g * 100), 1) if g > 0 else float("inf")
            ),
        })
    return results


def result_for(results: list[dict], horizon: str) -> dict:
    return next(row for row in results if row["horizon"] == horizon)


def best_rolling_decade(bra: pd.DataFrame, start_year: int = 1990, end_year: int = 2019) -> dict:
    """Return the highest annualized 10-year TFP growth window."""
    rows = []
    for y0 in range(start_year, end_year - 9):
        y1 = y0 + 10
        sub = bra[bra["year"].isin([y0, y1])].dropna(subset=["rtfpna"])
        if len(sub) != 2:
            continue
        tfp0 = float(sub[sub["year"] == y0]["rtfpna"].iloc[0])
        tfp1 = float(sub[sub["year"] == y1]["rtfpna"].iloc[0])
        growth = (tfp1 / tfp0) ** (1 / 10) - 1
        rows.append({
            "horizon": f"{y0}-{y1}",
            "start_year": y0,
            "end_year": y1,
            "span_years": 10,
            "tfp_start": round(tfp0, 4),
            "tfp_end": round(tfp1, 4),
            "annual_growth_pct": round(growth * 100, 3),
            "years_to_compensate_areq": (
                round(years_to_compensate(A_REQ, growth * 100), 1)
                if growth > 0 else float("inf")
            ),
        })
    if not rows:
        raise ValueError("No rolling 10-year windows available")
    return max(rows, key=lambda row: row["annual_growth_pct"])


def main() -> None:
    print("Loading PWT data...")
    bra, source_label, source_note, tfp_units = load_brazil_tfp()
    tfp_start_year = int(bra["year"].min())
    tfp_end_year = int(bra["year"].max())
    latest_modern_end = min(2023, tfp_end_year)
    print(f"Brazil series: {tfp_start_year}-{tfp_end_year}, {len(bra)} years")

    results = horizon_rows(bra)

    print("\n" + "=" * 80)
    print(f"Brazilian TFP growth ({source_label}) and years to accumulate A_req = {A_REQ}%")
    print("=" * 80)
    print(f"{'Horizon':<15} {'Years':>6} {'TFP_0':>8} {'TFP_1':>8} {'g (%/yr)':>10} {'Years->A_req':>14}")
    print("-" * 80)
    for row in results:
        yts = row["years_to_compensate_areq"]
        yts_str = f"{yts:.1f}" if yts != float("inf") else "inf"
        print(
            f"{row['horizon']:<15} {row['span_years']:>6} "
            f"{row['tfp_start']:>8.4f} {row['tfp_end']:>8.4f} "
            f"{row['annual_growth_pct']:>9.3f}  {yts_str:>14}"
        )

    long_run = result_for(results, f"1990-{latest_modern_end}")
    modern = result_for(results, f"1995-{latest_modern_end}")
    pre_covid = result_for(results, "1990-2019")
    best = best_rolling_decade(bra, 1990, min(2019, tfp_end_year))
    recent = result_for(results, "2010-2019")
    if all(row["horizon"] != best["horizon"] for row in results):
        results.append(best)
    phase_rows = phasein_rows(load_areq_scenarios())

    summary = {
        "source": source_note,
        "country": "Brazil",
        "a_req_pct": A_REQ,
        "modern_era_1995_latest": modern,
        "long_run_1990_latest": long_run,
        "pre_covid_1990_2019": pre_covid,
        "best_post1990_rolling_decade": best,
        "growth_decade_2003_2013": result_for(results, "2003-2013"),
        "recent_decade_2010_2019": recent,
        "required_annualized_gains": phase_rows,
        "all_horizons": results,
        "key_finding": (
            "PWT is used as an external scale benchmark, not as validation evidence. "
            f"For the one-sided fatigue 36h endpoint, accumulating A_req={phase_rows[1]['a_req_pct']:.2f}% "
            f"requires annual TFP gains of {phase_rows[1]['required_gain_3yr_pct']:.2f}% "
            f"over 3 years, {phase_rows[1]['required_gain_5yr_pct']:.2f}% over 5 years, "
            f"or {phase_rows[1]['required_gain_10yr_pct']:.2f}% over 10 years. "
            f"For scale, Brazil's PWT rtfpna growth was {long_run['annual_growth_pct']:+.2f}%/yr "
            f"over {long_run['horizon']} and {best['annual_growth_pct']:+.2f}%/yr in "
            f"the best post-1990 rolling decade ({best['horizon']})."
        ),
    }

    with open(OUT_DATA, "w", encoding="utf-8") as f:
        json.dump(json_sanitize(summary), f, ensure_ascii=False, indent=2, allow_nan=False)
    print(f"\n[OK] Saved numerical results to {OUT_DATA}")

    phasein_summary = {
        "source": source_note,
        "role": "external scale benchmark, not counterfactual validation",
        "phase_in_years": list(PHASE_IN_YEARS),
        "pwt_scale_benchmarks": {
            "long_run_1990_latest": long_run,
            "pre_covid_1990_2019": pre_covid,
            "best_post1990_rolling_decade": best,
        },
        "required_annualized_gains": phase_rows,
    }
    with open(OUT_PHASEIN, "w", encoding="utf-8") as f:
        json.dump(json_sanitize(phasein_summary), f, ensure_ascii=False, indent=2, allow_nan=False)
    print(f"[OK] Saved phase-in benchmark data to {OUT_PHASEIN}")

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _style import apply_style, set_axis_style, save_pdf, TEXT_DARK

    apply_style()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 10.5), gridspec_kw={"hspace": 0.45})

    ax1.plot(bra["year"], bra["rtfpna"], color="#2c3e50", linewidth=1.6)
    ax1.axhline(
        y=bra[bra["year"] == 1990]["rtfpna"].iloc[0],
        color="#888888",
        linestyle=":",
        alpha=0.6,
        linewidth=1.0,
        label="1990 level",
    )
    ax1.axvspan(
        best["start_year"],
        best["end_year"],
        alpha=0.12,
        color="#27ae60",
        label=f"Best post-1990 decade ({best['horizon']})",
    )
    set_axis_style(
        ax1,
        title=f"A. Brazilian TFP, {tfp_start_year}-{tfp_end_year}",
        xlabel="Year",
        ylabel=tfp_units,
    )
    ax1.legend(loc="lower left", frameon=False)

    plot_rows = [long_run, pre_covid, modern, best, recent]
    horizons_plot = [row["horizon"] for row in plot_rows]
    growth_rates = [row["annual_growth_pct"] for row in plot_rows]

    colors = ["#c0392b" if g <= 0 else "#2980b9" for g in growth_rates]
    x = np.arange(len(horizons_plot))
    bars = ax2.bar(
        x,
        growth_rates,
        width=0.65,
        color=colors,
        edgecolor="#2c3e50",
        linewidth=0.4,
        alpha=0.85,
    )
    ax2.axhline(y=0, color="#666666", linewidth=0.5)

    ax2.set_xticks(x)
    ax2.set_xticklabels(horizons_plot, rotation=0, fontsize=10)
    set_axis_style(
        ax2,
        title="B. PWT scale benchmarks for annual TFP growth",
        xlabel=None,
        ylabel="Annual TFP growth (%/year)",
    )
    ax2.xaxis.grid(False)
    ax2.set_ylim(min(growth_rates) - 0.45, max(growth_rates) + 0.50)

    for bar, growth in zip(bars, growth_rates):
        if growth >= 0:
            y_text = growth + 0.10
            va = "bottom"
        else:
            y_text = growth - 0.12
            va = "top"
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            y_text,
            f"{growth:+.2f}%",
            ha="center",
            va=va,
            fontsize=11,
            fontstyle="italic",
            color=TEXT_DARK,
        )

    pdf_path = save_pdf(fig, OUT_FIG)
    print(f"[OK] Saved figure to {pdf_path}")
    plt.close()

    tex_lines = [
        r"% Auto-generated by src/tables_figures/compute_tfp_anchor.py",
        rf"% Source: {source_note}",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Annual TFP gains required to accumulate $A_{\text{req}}$ over phase-in horizons.}\label{tab:tfp_history}",
        r"\small",
        r"\begin{tabular}{lrrrr}",
        r"\hline\hline",
        r"Scenario & $A_{\text{req}}$ (\%) & 3 yrs & 5 yrs & 10 yrs \\",
        r" & & \multicolumn{3}{c}{Required annual gain (\%/yr)} \\",
        r"\hline",
    ]
    for row in phase_rows:
        tex_lines.append(
            f"{row['scenario']} & {row['a_req_pct']:.2f} & "
            f"{row['required_gain_3yr_pct']:.2f} & "
            f"{row['required_gain_5yr_pct']:.2f} & "
            f"{row['required_gain_10yr_pct']:.2f} \\\\"
        )

    tex_lines += [
        r"\hline\hline",
        r"\end{tabular}",
        r"\\[2pt]",
        r"\begin{minipage}{0.95\textwidth}",
        r"\justifying",
        (
            rf"{{\footnotesize \textit{{Source:}} {source_label}, variable \texttt{{rtfpna}}. "
            r"Required annual gains are $g_T=(1+A_{\text{req}}/100)^{1/T}-1$ for "
            r"$T\in\{3,5,10\}$. PWT is used here only as an external scale benchmark: "
            rf"Brazil's annualized PWT growth was {long_run['annual_growth_pct']:+.2f}\%/yr "
            rf"over {long_run['horizon']} and {best['annual_growth_pct']:+.2f}\%/yr in "
            rf"the best post-1990 rolling decade ({best['horizon']}). These historical "
            r"series do not validate or reject the policy counterfactual.}"
        ),
        r"\end{minipage}",
        r"\end{table}",
    ]

    with open(OUT_TAB, "w", encoding="utf-8") as f:
        f.write("\n".join(tex_lines))
    print(f"[OK] Saved LaTeX table to {OUT_TAB}")

    print("\n" + "=" * 80)
    print("PWT SCALE BENCHMARK FOR THE PAPER")
    print("=" * 80)
    print(summary["key_finding"])


if __name__ == "__main__":
    main()
