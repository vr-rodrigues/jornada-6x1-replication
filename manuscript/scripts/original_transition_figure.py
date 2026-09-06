"""Figure 4: comparable transition maps for 44 -> 40h and 44 -> 36h.

Retains the original magma heatmap and CES horizontal axis. Both panels share
axes, color normalization and contour levels. The computation lives in
transition_experiments.py and preserves the same baseline at every cost relief.
"""
from __future__ import annotations
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.ticker import FuncFormatter
from paper_config import PRIMARY_FOLDER
from transition_experiments import compute_transition_map


def _decimal(value, digits=1):
    return f"{value:.{digits}f}".replace(".", ",")


def plot_transition_map(df, checks):
    """Two vertically stacked maps, with common scales and explicit cost units."""
    if checks.get("status") != "passed":
        raise ValueError("Only validated transition maps can be plotted")
    if set(df.hours_cap.astype(float).unique()) != {40., 36.}:
        raise ValueError("Figure 4 requires both 44 -> 40h and 44 -> 36h panels")
    if not np.allclose(df.baseline_operator_h0, 44.):
        raise ValueError("Both panels must have the same explicit 44h reference")
    low, high = float(df.A_req_pct.min()), float(df.A_req_pct.max())
    norm = Normalize(vmin=np.floor(low), vmax=np.ceil(high))
    levels = [v for v in (-6., -4., -2., 0., 1., 2., 4., 6., 8., 10.)
              if low < v < high]
    style = {"font.family":"serif", "font.size":12, "axes.titlesize":15,
        "axes.titleweight":"bold", "axes.labelsize":12, "xtick.labelsize":11,
        "ytick.labelsize":11, "axes.facecolor":"white", "figure.facecolor":"white",
        "axes.edgecolor":"#333333", "axes.linewidth":.7,
        "axes.labelcolor":"#222222", "text.color":"#222222", "axes.grid":False,
        "xtick.direction":"out", "ytick.direction":"out", "pdf.fonttype":42,
        "ps.fonttype":42}
    with plt.rc_context(style):
        fig, axes = plt.subplots(2, 1, figsize=(9.5, 10.5), sharex=True, sharey=True)
        fig.subplots_adjust(left=.12, right=.84, top=.95, bottom=.08, hspace=.22)
        for ax, cap, label in zip(axes, (40., 36.), ("A", "B")):
            rows = df.loc[np.isclose(df.hours_cap, cap)]
            grid = rows.pivot(index="wedge_relief_national", columns="sigma_sub",
                              values="A_req_pct")
            x, y = np.meshgrid(grid.columns.to_numpy(float), 100.*grid.index.to_numpy(float))
            z = grid.to_numpy(float)
            filled = ax.pcolormesh(x, y, z, shading="gouraud", cmap="magma",
                                   norm=norm, rasterized=True)
            local_levels = [v for v in levels if z.min() < v < z.max()]
            if local_levels:
                level_colors = ["#20132d" if norm(v) > .73 else "white" for v in local_levels]
                cs = ax.contour(x, y, z, levels=local_levels, colors=level_colors,
                                linewidths=1.15, linestyles="solid")
                labs = ax.clabel(cs, inline=True, fmt=lambda v: f"{v:g}%".replace(".", ","),
                                 fontsize=10, colors="white")
                for lab in labs:
                    val = float(lab.get_text().rstrip("%").replace(",", "."))
                    if norm(val) > .73:
                        lab.set_color("#20132d")
            ax.axvline(1.326, color="white", linestyle=(0, (3, 4)), linewidth=.9, alpha=.65)
            ax.set_title(f"{label}. Redução de 44 para {int(cap)} horas", loc="left", pad=11)
            ax.set_ylabel("Redução do custo de formalização (%)")
            ax.set_xlim(.4, 2.5)
            ax.set_ylim(0., 100.)
            ax.set_yticks(np.arange(0., 101., 20.))
            ax.set_xticks([.4, .8, 1.326, 1.8, 2.2, 2.5])
            ax.xaxis.set_major_formatter(FuncFormatter(
                lambda v, _: "1,326" if np.isclose(v, 1.326) else _decimal(v)))
            ax.grid(False)
        axes[1].set_xlabel(r"Elasticidade de substituição formal–informal ($\sigma_{sub}$)")
        cax = fig.add_axes([.87, .08, .025, .87])
        bar = fig.colorbar(filled, cax=cax)
        bar.set_label(r"PTF necessária para preservar o produto: $A_{req}$ (%)", labelpad=12)
        bar.set_ticks(np.arange(np.ceil(norm.vmin/2)*2, norm.vmax+.01, 2))
        bar.ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
    return fig


def main():
    paper = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replication-root", type=Path, default=(paper.parent/"replication_package" if (paper.parent/"replication_package"/"run_all.py").is_file() else paper.parent))
    parser.add_argument("--run-id", default="20260905_005724_846373")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    folder = args.replication_root/"output/runs"/args.run_id/PRIMARY_FOLDER
    inputs = json.loads((folder/"INPUTS.json").read_text(encoding="utf-8-sig"))
    inputs["bridges"] = json.loads((folder/"BRIDGE.json").read_text(encoding="utf-8-sig"))
    df, checks = compute_transition_map(inputs, args.replication_root,
                                      pd.read_csv(folder/"RESULTS.csv"))
    fig = plot_transition_map(df, checks)
    if args.output_dir is not None:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(args.output_dir/"transition_map.csv", index=False, encoding="utf-8-sig")
        (args.output_dir/"transition_map_checks.json").write_text(
            json.dumps(checks, indent=2, ensure_ascii=False), encoding="utf-8")
        for ext in ("pdf", "png"):
            fig.savefig(args.output_dir/f"fig_transition_map_pt.{ext}", dpi=190, bbox_inches="tight")
    plt.close(fig)
    print(json.dumps(checks, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
