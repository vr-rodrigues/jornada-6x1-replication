"""Master orchestrator — regenerates every numbered table and figure in the paper.

Usage:
    python run_all.py            # full pipeline
    python run_all.py --tests    # also run unit tests
    python run_all.py --paper    # also recompile the LaTeX paper

Expected runtime: under five minutes on a modern laptop (excluding the
optional PNAD microdata download in the sectoral pipeline).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"


PIPELINE = [
    ("Calibration",            SRC / "calibration" / "calibrate_all.py"),
    ("TFP anchor table",       SRC / "tables_figures" / "compute_tfp_anchor.py"),
    ("Stress test table",      SRC / "tables_figures" / "compute_stress_test.py"),
    ("Main figures",           SRC / "tables_figures" / "plot_main_figures.py"),
    ("Welfare schedule",       SRC / "tables_figures" / "plot_welfare_schedule.py"),
    ("Portugal validation",    SRC / "tables_figures" / "compute_portugal_validation.py"),
]


def run_step(label: str, script: Path) -> bool:
    if not script.exists():
        print(f"[SKIP] {label}: {script.relative_to(ROOT)} not found")
        return True
    print(f"\n=== {label} ===")
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT)
    if result.returncode != 0:
        print(f"[FAIL] {label} exited with code {result.returncode}")
        return False
    return True


def run_tests() -> bool:
    print("\n=== Unit tests ===")
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT,
    )
    return result.returncode == 0


def compile_paper() -> bool:
    tex_dir = ROOT / "paper" / "tex"
    if not tex_dir.exists():
        print("[SKIP] paper/tex not found")
        return True
    print("\n=== Compile paper ===")
    for target in ("online_appendix.tex", "online_appendix_pt.tex", "main.tex", "main_pt.tex"):
        if not (tex_dir / target).exists():
            continue
        stem = Path(target).stem
        for cmd in (
            ["pdflatex", "-interaction=nonstopmode", target],
            ["bibtex", stem],
            ["pdflatex", "-interaction=nonstopmode", target],
            ["pdflatex", "-interaction=nonstopmode", target],
        ):
            subprocess.run(cmd, cwd=tex_dir, check=False)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tests", action="store_true", help="run unit tests after the pipeline")
    parser.add_argument("--paper", action="store_true", help="recompile the LaTeX paper")
    args = parser.parse_args()

    os.environ.setdefault("JORNADA_BASE_DIR", str(ROOT))

    failed = [label for label, script in PIPELINE if not run_step(label, script)]
    if failed:
        print(f"\nPipeline finished with {len(failed)} failure(s): {', '.join(failed)}")
        return 1

    if args.tests and not run_tests():
        print("\nUnit tests failed.")
        return 1

    if args.paper:
        compile_paper()

    print("\nReplication pipeline complete. Outputs in ./output/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
