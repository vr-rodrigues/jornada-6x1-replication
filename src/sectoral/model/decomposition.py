"""Additive output decomposition: physical hours, efficiency, reallocation.

All intermediate output changes divide by baseline output. Differences between
alternative heterogeneity assumptions are sensitivities, not this identity.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.sectoral.model.sector_model import main, _solve_Areq_multi


def _solve_Areq_single(pars, h1, Y_target, grid=3001):
    return _solve_Areq_multi({"sector": pars}, h1, Y_target, grid=grid)


def run_decomposition(argv=None):
    return main(argv)


if __name__ == "__main__":
    raise SystemExit(run_decomposition())
