"""Original single-panel article drawings with recomputed, signed results.

Visual source: archived plot_figures_pt.py, plot_areq_vs_hours_pt and
plot_welfare_schedule_pt, and the PDFs in PAPER_original_20260905_020616.
The primary baseline caps formal hours at 44h with its own recalibrated bridge.
The complete observed-habitual-hours baseline remains an appendix sensitivity.
"""
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from paper_config import PRIMARY_MAPPING

PREF, CONS, NEUTRAL = '#f06f55', '#5e1a84', '#20132d'
RC = {
    'font.family': 'serif', 'font.size': 12, 'axes.titlesize': 15,
    'axes.titleweight': 'bold', 'axes.labelsize': 12,
    'xtick.labelsize': 11, 'ytick.labelsize': 11, 'legend.fontsize': 10,
    'axes.facecolor': 'white', 'figure.facecolor': 'white',
    'axes.edgecolor': '#333333', 'axes.linewidth': .7,
    'text.color': '#222222', 'axes.labelcolor': '#222222',
    'xtick.color': '#222222', 'ytick.color': '#222222',
    'axes.grid': False, 'xtick.direction': 'out', 'ytick.direction': 'out',
    'pdf.fonttype': 42, 'ps.fonttype': 42,
}


def number(value, digits=2, signed=False):
    return (f'{value:+.{digits}f}' if signed else f'{value:.{digits}f}').replace('.', ',')


def _curves(df, key, title, ylabel):
    fig, ax = plt.subplots(figsize=(9.5, 6.7))
    data = {}
    for mode, style, color, label in [
        ('flat_below', '-o', PREF, 'Fadiga só\nacima de 40h'),
        ('bilateral', '--s', CONS, 'Penalidade\nbilateral')]:
        d = df.loc[df.mapping.eq(PRIMARY_MAPPING) &
                   df.efficiency_mode.eq(mode)].sort_values('hours_cap', ascending=False)
        if d.hours_cap.duplicated().any() or d.hours_cap.min() != 30 or d.hours_cap.max() != 44:
            raise ValueError('Original hour-axis coverage must be 30 through 44, with unique caps')
        if not np.isfinite(d[key]).all():
            raise ValueError(f'Nonfinite {key} curve')
        at44 = d.loc[d.hours_cap.eq(44), key].iloc[0]
        if abs(at44) > 1.e-9:
            raise ValueError(f'The reference at 44h must be unchanged, got {key}={at44}')
        # Original markers and range; the finer computation grid is retained
        # in CSV and used for the maximum annotation, not extra dense markers.
        markers = np.flatnonzero(np.isclose(d.hours_cap, np.round(d.hours_cap))).tolist()
        ax.plot(d.hours_cap, d[key], style, color=color,
                linewidth=1.8 if mode == 'flat_below' else 1.6,
                markersize=6 if mode == 'flat_below' else 5.5,
                markevery=markers, alpha=1 if mode == 'flat_below' else .9, label=label)
        data[mode] = d
    ax.axhline(0, color=NEUTRAL, linewidth=.7, alpha=.45)
    ax.axvline(40, color=NEUTRAL, linewidth=.8, linestyle='--', alpha=.6,
               label='Alternativa 40h')
    ax.axvline(36, color=NEUTRAL, linewidth=.7, linestyle=':', alpha=.45,
               label='Endpoint 36h')
    ax.set_title(title, fontweight='bold', loc='left', pad=10)
    ax.set_xlabel('Teto semanal de horas')
    ax.set_ylabel(ylabel)
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(False)
    ax.set_xticks(np.arange(30, 45, 2))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:g}'.replace('.', ',')))
    ax.invert_xaxis()
    return fig, ax, data


def plot_areq(df):
    with mpl.rc_context(RC):
        fig, ax, data = _curves(df, 'A_req_pct',
            'Ganho requerido de PTF por teto de horas',
            r'Ganho requerido de PTF $A_{\mathrm{req}}$ (%)')
        annotations = [
            ('flat_below', 40, (43, 3.4), 'alternativa 40h:', PREF, .15),
            ('flat_below', 36, (40.5, 10), 'endpoint 36h:', PREF, .15),
            ('bilateral', 36, (41, 15.5), 'penalidade bilateral:', CONS, -.10),
        ]
        for mode, cap, position, label, color, curvature in annotations:
            value = float(data[mode].loc[data[mode].hours_cap.eq(cap), 'A_req_pct'].iloc[0])
            ax.annotate(f'{label}\n{number(value)}% PTF', xy=(cap, value), xytext=position,
                fontsize=10, fontstyle='italic', color=color, ha='left', va='center',
                arrowprops=dict(arrowstyle='->', color=color, lw=1,
                                connectionstyle=f'arc3,rad={curvature}'))
        ax.legend(loc='upper left', bbox_to_anchor=(.01, .98), frameon=False, labelspacing=.8)
        fig.tight_layout()
    return fig


def plot_welfare(df):
    with mpl.rc_context(RC):
        fig, ax, data = _curves(df, 'dGHH_pct',
            'Curva de bem-estar por teto de horas',
            r'$\Delta$GHH (%) - variação do composto GHH')
        for mode, color, position, curvature, label in [
            ('flat_below', PREF, (44, -1), .15, 'pico (fadiga longa)'),
            ('bilateral', CONS, (38, -4), -.2, 'pico (bilateral)')]:
            d = data[mode]
            maximum = d.loc[d.dGHH_pct.idxmax()]
            ax.annotate(f'{label}:\n{number(maximum.dGHH_pct, signed=True)}% em '
                        f'{number(maximum.hours_cap).rstrip("0").rstrip(",")}h',
                xy=(maximum.hours_cap, maximum.dGHH_pct), xytext=position,
                fontsize=10, fontstyle='italic', color=color,
                ha='left' if mode == 'flat_below' else 'center', va='center',
                arrowprops=dict(arrowstyle='->', color=color, lw=1,
                                connectionstyle=f'arc3,rad={curvature}'))
        ax.legend(loc='lower left', frameon=False, labelspacing=.8)
        fig.tight_layout()
    return fig
