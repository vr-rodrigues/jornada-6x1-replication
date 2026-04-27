"""Master orchestrator -- regenerates the replication package.

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
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
OUTPUT = ROOT / "output"
TEX_DIR = ROOT / "paper" / "tex"
PAPER_DIR = ROOT / "paper"


PIPELINE = [
    ("Calibration",            SRC / "calibration" / "calibrate_all.py"),
    ("Flat-below calibration", SRC / "calibration" / "calibrate_flatbelow.py"),
    ("Conservative envelope",  SRC / "calibration" / "joint_envelope.py"),
    ("Preferred envelope",     SRC / "calibration" / "joint_envelope_flat.py"),
    ("TFP anchor table",       SRC / "tables_figures" / "compute_tfp_anchor.py"),
    ("Stress test table",      SRC / "tables_figures" / "compute_stress_test.py"),
    ("Main figures",           SRC / "tables_figures" / "plot_main_figures.py"),
    ("Welfare schedule",       SRC / "tables_figures" / "plot_welfare_schedule.py"),
    ("Portugal validation",    SRC / "tables_figures" / "compute_portugal_validation.py"),
    ("Appendix tables",        SRC / "tables_figures" / "write_appendix_tables.py"),
    ("Sectoral figure",        SRC / "tables_figures" / "plot_sectoral_fig.py"),
]

TABLE_COPIES = {
    OUTPUT / "tables" / "tab_stress_test.tex": TEX_DIR / "tab_stress_test_autogen.tex",
    OUTPUT / "tables" / "tab_areq_tfp_horizons.tex": TEX_DIR / "tab_areq_tfp_horizons_autogen.tex",
    OUTPUT / "tables" / "tab_portugal_validation.tex": TEX_DIR / "tab_portugal_validation_autogen.tex",
    OUTPUT / "tables" / "tab_envelope_corners.tex": TEX_DIR / "tab_envelope_corners_autogen.tex",
}

PDF_TARGETS = ("main", "main_pt", "online_appendix", "online_appendix_pt")


def run_step(label: str, script: Path) -> bool:
    if not script.exists():
        print(f"[SKIP] {label}: {script.relative_to(ROOT)} not found")
        return True
    print(f"\n=== {label} ===", flush=True)
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT)
    if result.returncode != 0:
        print(f"[FAIL] {label} exited with code {result.returncode}")
        return False
    return True


def run_tests() -> bool:
    print("\n=== Unit tests ===", flush=True)
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT,
    )
    return result.returncode == 0


def latex_sources() -> list[Path]:
    if not TEX_DIR.exists():
        return []
    return sorted(TEX_DIR.glob("*.tex"))


def find_graphics_references() -> set[str]:
    pattern = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
    refs: set[str] = set()
    for tex in latex_sources():
        for match in pattern.finditer(tex.read_text(encoding="utf-8")):
            refs.add(match.group(1))
    return refs


def find_input_references() -> set[str]:
    pattern = re.compile(r"\\input\{([^}]+)\}")
    refs: set[str] = set()
    for tex in latex_sources():
        for match in pattern.finditer(tex.read_text(encoding="utf-8")):
            refs.add(match.group(1))
    return refs


def verify_latex_inputs() -> bool:
    """Fail early if a LaTeX input is missing from paper/tex."""
    ok = True
    for ref in sorted(find_input_references()):
        path = TEX_DIR / ref
        if path.suffix == "":
            path = path.with_suffix(".tex")
        if not path.exists():
            print(f"[MISS] LaTeX input not found: {path.relative_to(ROOT)}")
            ok = False
    return ok


def sync_paper_assets() -> bool:
    """Copy generated figures and autogen tables into paper/tex."""
    if not TEX_DIR.exists():
        print("[SKIP] paper/tex not found")
        return True

    print("\n=== Sync paper assets ===", flush=True)
    ok = True
    fig_dir = TEX_DIR / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    for ref in sorted(find_graphics_references()):
        source = OUTPUT / "figures" / ref
        dest = fig_dir / Path(ref).name
        if source.exists():
            shutil.copy2(source, dest)
            print(f"[OK] {source.relative_to(ROOT)} -> {dest.relative_to(ROOT)}")
        elif dest.exists():
            print(f"[OK] {dest.relative_to(ROOT)} already present")
        else:
            print(f"[MISS] figure referenced by LaTeX not found: {ref}")
            ok = False

    for source, dest in TABLE_COPIES.items():
        if source.exists():
            shutil.copy2(source, dest)
            print(f"[OK] {source.relative_to(ROOT)} -> {dest.relative_to(ROOT)}")
        else:
            print(f"[MISS] generated table not found: {source.relative_to(ROOT)}")
            ok = False

    return ok and verify_latex_inputs()


def run_tex_command(cmd: list[str], target: str) -> bool:
    result = subprocess.run(cmd, cwd=TEX_DIR)
    if result.returncode != 0:
        print(f"[FAIL] {target}: {' '.join(cmd)} exited with code {result.returncode}")
        return False
    return True


def compile_paper() -> bool:
    if not TEX_DIR.exists():
        print("[SKIP] paper/tex not found")
        return True
    print("\n=== Compile paper ===", flush=True)
    if not sync_paper_assets():
        return False

    targets = [(stem, f"{stem}.tex") for stem in PDF_TARGETS
               if (TEX_DIR / f"{stem}.tex").exists()]

    for _, target in targets:
        if not run_tex_command(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", target],
            target,
        ):
            return False

    for stem, target in targets:
        if not run_tex_command(["bibtex", stem], target):
            return False

    for _ in range(2):
        for _, target in targets:
            if not run_tex_command(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", target],
                target,
            ):
                return False

    for stem, _ in targets:
        pdf = TEX_DIR / f"{stem}.pdf"
        if pdf.exists():
            target_pdf = PAPER_DIR / pdf.name
            shutil.copy2(pdf, target_pdf)
            print(f"[OK] {pdf.relative_to(ROOT)} -> {target_pdf.relative_to(ROOT)}")
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

    if not sync_paper_assets():
        print("\nPipeline generated outputs, but paper asset sync failed.")
        return 1

    if args.tests and not run_tests():
        print("\nUnit tests failed.")
        return 1

    if args.paper and not compile_paper():
        print("\nPaper compilation failed.")
        return 1

    print("\nReplication pipeline complete. Outputs in ./output/ and ./paper/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
