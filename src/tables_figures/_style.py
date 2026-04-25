# -*- coding: utf-8 -*-
"""
_style.py — Unified figure style matching Figure 6 (heatmap) aesthetic.

Key features:
  - Serif font throughout
  - Italic title, NOT bold
  - Italic axis labels
  - White background, subtle or no grid
  - Minimal decoration
"""
import matplotlib as mpl
import matplotlib.pyplot as plt


# Palette (kept consistent across figures)
COLOR_PREF = "#2980b9"   # blue (preferred flat-below)
COLOR_CONS = "#c0392b"   # red (conservative symmetric)
COLOR_NEUTRAL = "#2c3e50"
COLOR_ACCENT = "#e67e22"


TEXT_DARK = "#1a1a1a"   # near-black for titles and labels, matching Fig 6


def apply_style():
    """Apply the unified paper style. Call at the top of each plot script."""
    mpl.rcParams.update({
        "font.family": "serif",
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.titleweight": "normal",
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "axes.edgecolor": "#333333",
        "axes.linewidth": 0.7,
        "axes.labelcolor": TEXT_DARK,
        "text.color": TEXT_DARK,
        "grid.color": "#d8d8d8",
        "grid.linestyle": "--",
        "grid.linewidth": 0.4,
        "grid.alpha": 0.7,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "xtick.color": TEXT_DARK,
        "ytick.color": TEXT_DARK,
        "pdf.fonttype": 42,    # embed fonts properly
        "ps.fonttype": 42,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.1,
    })


def set_axis_style(ax, title=None, xlabel=None, ylabel=None):
    """Apply unified axis styling: italic title, italic labels, subtle spines."""
    if title is not None:
        ax.set_title(title, fontstyle="italic", loc="left",
                      pad=10, color=TEXT_DARK)
    if xlabel is not None:
        ax.set_xlabel(xlabel, fontstyle="italic", color=TEXT_DARK)
    if ylabel is not None:
        ax.set_ylabel(ylabel, fontstyle="italic", color=TEXT_DARK)
    # Light grid
    ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.7, color="#d8d8d8")
    ax.set_axisbelow(True)
    # Hide top and right spines to match the heatmap look
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#333333")
        ax.spines[spine].set_linewidth(0.7)


def save_pdf(fig, base_path):
    """Save a figure as PDF. `base_path` ends in .png or no ext; replaces with .pdf."""
    import os
    root, _ = os.path.splitext(base_path)
    pdf_path = root + ".pdf"
    fig.savefig(pdf_path, format="pdf", bbox_inches="tight")
    return pdf_path
