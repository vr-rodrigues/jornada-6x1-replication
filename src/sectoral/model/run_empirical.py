"""Strict empirical entry point: only freshly reprocessed PNAD 2024Q4 is accepted."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.sectoral.model.inputs import load_empirical_facts  # explicit legacy API
from src.sectoral.model.sector_model import main as sectoral_main


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    defaults = ["--input-kind", "reprocessed"]
    if "--data-dir" not in args:
        defaults += ["--data-dir", str(PROJECT_ROOT / "data_intermediate" / "reprocessed")]
    if "--output-dir" not in args:
        defaults += ["--output-dir", str(PROJECT_ROOT / "output" / "corrected" / "sectoral_reprocessed")]
    return sectoral_main(defaults + args)


if __name__ == "__main__":
    raise SystemExit(main())
