"""Mechanical formal-hours exposure, never behavioral or distributive incidence.

Absolute counts require occupied survey totals in the freshly reprocessed file.
No hardcoded PNAD counts and no reads of prior A_req outputs are used.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.sectoral.model.inputs import load_inputs


def compute_exposure(facts, caps=(40., 36.)):
    rows = []
    for cap in caps:
        for name, s in facts.items():
            share_formal_above = float(np.asarray(s["theta"])[np.asarray(s["hours_bins"]) > cap].sum())
            share_sector = (1.0-s["inf_rate"]) * share_formal_above
            observed_population = s.get("observed", {}).get("occupied_weighted")
            rows.append({
                "h1": int(cap), "sector": name,
                "formal_hours_above_cap_share": share_formal_above,
                "share_of_sector_employment": share_sector,
                "share_of_classified_total_employment": s["lambda_s"]*share_sector,
                "occupied_weighted": observed_population,
                "mechanically_exposed_weighted": None if observed_population is None else observed_population*share_sector,
                "interpretation": "Mechanical exposure under model mapping of formal habitual hours to cap; not workers legally covered or welfare incidence",
                "input_status": s["input_status"],
            })
    return rows


def write_exposure(facts, output_path):
    rows = compute_exposure(facts)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=PROJECT_ROOT / "data_intermediate" / "reprocessed")
    parser.add_argument("--hypotheses-dir", type=Path, default=PROJECT_ROOT / "data_final")
    parser.add_argument("--input-kind", choices=("frozen", "frozen_pnad", "reprocessed"), default="reprocessed")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "output" / "corrected" / "sectoral_reprocessed")
    args = parser.parse_args(argv)
    facts, _ = load_inputs(args.data_dir, args.input_kind, args.hypotheses_dir)
    write_exposure(facts, args.output_dir / "SECTOR_HOURS_EXPOSURE.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
