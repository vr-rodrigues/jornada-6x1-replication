"""Publication plots from newly computed sector result rows only."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def build_sectoral_figure(rows, out):
    """Plot empirical fixed-omega and bridge scenarios in 40/36h, both e(h).

    Expected columns: input_kind, scenario_variant (empirical_fixed_omega or empirical_bridge;
    aliases fixed_omega and bridge are also accepted),
    efficiency_mode, h1, sector, A_req_pct. No legacy output fallback.
    Returns explicit paths of all newly generated figure formats.
    """
    if isinstance(rows, (str, Path)):
        with Path(rows).open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
    sectors = ("agriculture", "industry", "services")
    names = ("Agropecuária", "Indústria e construção", "Serviços")
    variants = ("fixed_omega", "bridge")
    selected = {}
    variant_aliases = {"empirical_fixed_omega": "fixed_omega", "empirical_bridge": "bridge",
                       "fixed_omega": "fixed_omega", "bridge": "bridge"}
    for row in rows:
        if (row.get("input_kind") == "reprocessed" and row.get("sector") in sectors
                and row.get("scenario_variant") in variant_aliases):
            key = (row["efficiency_mode"], int(float(row["h1"])), row["sector"], variant_aliases[row["scenario_variant"]])
            if key in selected:
                raise ValueError(f"Ambiguous sector figure input, duplicate scenario: {key}")
            selected[key] = float(row["A_req_pct"])
    expected = {(mode, cap, sector, variant) for mode in ("bilateral", "flat_below")
                for cap in (40, 36) for sector in sectors for variant in variants}
    if set(selected) != expected:
        raise ValueError(f"Missing fresh sector figure scenarios: {sorted(expected-set(selected))}")
    out = Path(out)
    base = out.with_suffix("") if out.suffix else out / "figures" / "sectoral_areq"
    base.parent.mkdir(parents=True, exist_ok=True)
    colors = {"fixed_omega": "#217090", "bridge": "#a43d64"}
    labels = {"fixed_omega": "Peso tecnológico fixo (ω = 0,622)",
              "bridge": "Peso tecnológico recalibrado pela remuneração horária"}
    modes = (("bilateral", "Eficiência bilateral"), ("flat_below", "Fadiga apenas acima do pico"))
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.spines.left": False, "axes.edgecolor": "#c8cdd3",
                         "text.color": "#182631", "axes.labelcolor": "#182631"}):
        fig, axes = plt.subplots(2, 2, figsize=(12.8, 8), sharey=True)
        y = np.arange(3)
        for row_index, (mode, mode_title) in enumerate(modes):
            for col_index, cap in enumerate((40, 36)):
                ax = axes[row_index, col_index]
                values_all = [value for (m, h, s, v), value in selected.items() if h == cap]
                minimum, maximum = min(values_all), max(values_all)
                margin = max(0.4, (maximum-minimum)*0.2)
                lo, hi = min(0., minimum-margin), maximum + 1.5*margin
                for variant, offset in (("fixed_omega", -0.12), ("bridge", 0.12)):
                    values = [selected[(mode, cap, sector, variant)] for sector in sectors]
                    ax.scatter(values, y+offset, s=66, color=colors[variant], zorder=3,
                               label=labels[variant], edgecolors="white", linewidths=0.7)
                    for value, level in zip(values, y+offset):
                        ax.annotate(f"{value:.2f}".replace(".", ",") + "%", (value, level),
                                    xytext=(7, 0), textcoords="offset points", va="center",
                                    fontsize=9, color=colors[variant])
                ax.set_yticks(y, names)
                ax.set_ylim(2.6, -0.6)
                ax.set_xlim(lo, hi)
                ax.set_title(f"{cap} horas · {mode_title}", fontsize=11, loc="left", pad=14)
                ax.xaxis.grid(True, alpha=0.18)
                ax.tick_params(axis="y", length=0, pad=12)
                ax.set_xlabel("Produtividade necessária para restaurar o produto (%)", fontsize=9)
        handles, legend_labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, legend_labels, loc="upper left", bbox_to_anchor=(0.065, 0.902),
                   frameon=False, ncol=1, fontsize=10, labelspacing=0.8)
        fig.suptitle("Compensação de produtividade por setor", x=0.065, y=0.985,
                     ha="left", fontsize=20, fontweight="bold")
        fig.text(0.065, 0.935, "PNAD 2024T4 · σ = 1,326 · composição formal–informal reotimizada em cada busca",
                 ha="left", fontsize=11, color="#53646f")
        fig.text(0.065, 0.025,
                 "Três setores independentes; capital fixo com participações mantidas como hipótese. "
                 "Sem incidência individual ou ajuste endógeno de capital.", fontsize=9, color="#53646f")
        fig.subplots_adjust(left=0.18, right=0.96, bottom=0.13, top=0.75, hspace=0.58, wspace=0.22)
        paths = {}
        for suffix in ("png", "pdf", "svg"):
            path = base.with_suffix("."+suffix)
            fig.savefig(path, dpi=180, facecolor="white")
            paths[suffix] = str(path.resolve())
        plt.close(fig)
    return paths


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    for kind, path in build_sectoral_figure(args.results, args.output_dir).items():
        print(f"{kind}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
