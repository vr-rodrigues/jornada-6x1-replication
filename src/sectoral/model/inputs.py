"""Explicit input contracts for legacy and freshly reprocessed sectoral inputs."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np


SECTOR_NAMES = {
    "agriculture": "Agropecuária",
    "industry": "Indústria (incluindo construção)",
    "services": "Serviços",
}


def _read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _fingerprint(path):
    path = Path(path).resolve()
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def load_national_targets(data_final_path):
    """Read a target CSV without changing its values or claiming verification."""
    path = Path(data_final_path)
    if path.is_dir():
        path = path / "calibration_targets.csv"
    return {row["target_id"]: float(row["value"]) for row in _read_csv(path)}


def validate_sector_facts(sectors):
    """Validate economic domains; record and normalize legacy CSV rounding."""
    if set(sectors) != set(SECTOR_NAMES):
        raise ValueError("Expected agriculture, industry, services; missing sectors cannot be imputed")
    total_share = sum(float(s["lambda_s"]) for s in sectors.values())
    if not np.isfinite(total_share) or abs(total_share - 1.0) > 0.001:
        raise ValueError(f"Sector employment shares sum to {total_share}, outside rounding tolerance")
    for sector, facts in sectors.items():
        if not 0.0 < float(facts["inf_rate"]) < 1.0:
            raise ValueError(f"{sector}: informality must be strictly between zero and one")
        if facts["lambda_s"] <= 0 or facts["vab_share"] <= 0:
            raise ValueError(f"{sector}: employment and assumed capital shares must be positive")
        hours = np.asarray(facts.get("hours_bins", [36, 40, 44]), dtype=float)
        weights = np.asarray(facts["theta"], dtype=float)
        if (hours.shape != weights.shape or len(hours) == 0 or
                not np.isfinite(hours).all() or not np.isfinite(weights).all() or
                np.any(hours < 0) or np.any(weights < 0)):
            raise ValueError(f"{sector}: invalid hours support or weights")
        weights_sum = float(weights.sum())
        if abs(weights_sum - 1.0) > 0.001:
            raise ValueError(f"{sector}: hours weights sum to {weights_sum}")
        facts.setdefault("raw_employment_share_sum", total_share)
        facts["lambda_s"] = float(facts["lambda_s"]) / total_share
        facts["hours_bins"] = hours
        facts.setdefault("raw_hours_weight_sum", weights_sum)
        facts["theta"] = weights / weights_sum
    return sectors


def load_sectoral_facts(data_final_path):
    """Load legacy hypotheses, preserving employment shares and stated provenance."""
    path = Path(data_final_path) / "SECTORAL_BASELINE_FACTS.csv"
    sectors = {}
    for row in _read_csv(path):
        name = row["sector"]
        sectors[name] = {
            "name": row["sector_name"], "lambda_s": float(row["lambda_s"]),
            "inf_rate": float(row["inf_rate"]), "N_s": float(row["N_s"]),
            "NF_s": float(row["NF_s"]), "NI_s": float(row["NI_s"]),
            "theta": np.array([float(row[f"theta_{h}"]) for h in (36, 40, 44)]),
            "hours_bins": np.array([36., 40., 44.]),
            "vab_share": float(row["vab_share"]),
            "yph": float(row["yph_reais_per_hour"]),
            "input_status": "legacy_hypotheses_not_new_microdata",
            "source_hours": row.get("source_theta", "unverified legacy"),
        }
    return validate_sector_facts(sectors)


def load_empirical_facts(data_final_path):
    """Legacy API: an old 'EMPIRICAL' filename is explicitly unverified, not fresh."""
    sectors = load_sectoral_facts(data_final_path)
    rows = _read_csv(Path(data_final_path) / "SECTORAL_PNAD_EMPIRICAL.csv")
    for row in rows:
        if row["sector"] not in sectors:
            continue
        facts = sectors[row["sector"]]
        facts.pop("raw_employment_share_sum", None)
        facts.pop("raw_hours_weight_sum", None)
        facts.update({
            "lambda_s": float(row["lambda_s"]), "inf_rate": float(row["inf_rate"]),
            "theta": np.array([float(row[f"theta_{h}"]) for h in (36, 40, 44)]),
            "input_status": "legacy_PNAD_unverified_CNPJ_and_quarter",
            "source_hours": "legacy habitual hours compressed to 36/40/44; not contracted hours",
        })
    return validate_sector_facts(sectors)


def load_reprocessed_facts(data_dir, hypotheses_dir):
    """Require a new PNAD JSON. Missing data never falls back to legacy PNAD."""
    data_dir = Path(data_dir)
    source = data_dir if data_dir.is_file() else data_dir / "pnad_targets.json"
    if not source.exists() and data_dir.name == "reprocessed" and data_dir.parent.name == "data_final":
        source = data_dir.parent.parent / "data_intermediate" / "reprocessed" / "pnad_targets.json"
    if not source.exists():
        raise FileNotFoundError(f"Fresh PNAD 2024Q4 aggregate unavailable: {source}")
    payload = json.loads(source.read_text(encoding="utf-8-sig"))
    if payload.get("status") not in ("verified_reprocessed", "verified_official_fallback"):
        raise ValueError("PNAD payload is not marked as a verified reprocessing or explicit official fallback")
    metadata = payload.get("metadata", {})
    # Metadata fields are mandatory: an old summary cannot masquerade as a rebuild.
    year = metadata.get("year")
    quarter = metadata.get("quarter")
    if int(year or 0) != 2024 or int(quarter or 0) != 4:
        raise ValueError("Reprocessed sectoral inputs must explicitly identify year=2024, quarter=4")
    sectors = load_sectoral_facts(hypotheses_dir)
    for name in SECTOR_NAMES:
        observed = payload["sectors"][name]
        distribution = observed["formal_hours_distribution"]
        sectors[name].update({
            "lambda_s": float(observed["employment_share"]),
            "inf_rate": float(observed["informality_rate"]),
            "hours_bins": np.asarray(distribution["hours"], dtype=float),
            "theta": np.asarray(distribution["weights"], dtype=float),
            "observed": observed,
            "input_status": "reprocessed_PNAD_2024Q4_habitual_hours",
            "source_hours": "PNAD habitual hours at main job; statutory capping is a model assumption",
        })
        sectors[name].pop("raw_employment_share_sum", None)
        sectors[name].pop("raw_hours_weight_sum", None)
        means = observed.get("mean_hours_habitual", {})
        if isinstance(means, dict) and means.get("informal") is not None:
            sectors[name]["hI"] = float(means["informal"])
        elif observed.get("mean_hours_informal_habitual") is not None:
            sectors[name]["hI"] = float(observed["mean_hours_informal_habitual"])
        else:
            raise ValueError(f"{name}: missing newly computed informal habitual hours")
    coverage = sum(s["lambda_s"] for s in sectors.values())
    excluded = {name: facts for name, facts in payload["sectors"].items() if name not in SECTOR_NAMES}
    if not 0 < coverage <= 1.000001:
        raise ValueError("Invalid classified employment coverage")
    # Unclassified CNAE is a genuine exclusion, not rounding. Condition the
    # three-sector model explicitly on classified activity and report coverage.
    for facts in sectors.values():
        facts["raw_employment_share_sum"] = coverage
        facts["lambda_s"] /= coverage
        facts["employment_normalization"] = "conditional on the three classified sectors; unclassified CNAE excluded"
    return validate_sector_facts(sectors), {
        "source_file": _fingerprint(source), "pnad_metadata": metadata,
        "pnad_status": payload["status"], "pnad_quality": payload.get("quality", {}),
        "employment_coverage_share": coverage,
        "excluded_activity_groups": {name: {k: v for k, v in facts.items()
                                            if k in ("occupied_weighted", "employment_share", "sample_n")}
                                     for name, facts in excluded.items()},
        "employment_denominator": "occupied persons in agriculture, industry or services; national unclassified CNAE excluded",
        "national_wage_ratio_targets": payload["national"].get("wage_ratio_formal_informal", {}),
    }


def load_inputs(data_dir, input_kind="frozen", hypotheses_dir=None):
    """Return inputs and audit metadata for an explicitly selected vintage."""
    data_dir = Path(data_dir)
    hypotheses_dir = Path(hypotheses_dir or data_dir)
    if input_kind == "reprocessed":
        sectors, provenance = load_reprocessed_facts(data_dir, hypotheses_dir)
    elif input_kind == "frozen":
        sectors = load_sectoral_facts(data_dir)
        provenance = {"source_file": _fingerprint(data_dir / "SECTORAL_BASELINE_FACTS.csv")}
    elif input_kind == "frozen_pnad":
        sectors = load_empirical_facts(data_dir)
        provenance = {"source_file": _fingerprint(data_dir / "SECTORAL_PNAD_EMPIRICAL.csv")}
    else:
        raise ValueError(f"Unknown input_kind: {input_kind}")
    provenance.update({
        "input_kind": input_kind,
        "capital_hypothesis_source": _fingerprint(hypotheses_dir / "SECTORAL_BASELINE_FACTS.csv"),
        "capital_hypothesis": "K_sector proportional to legacy 2021 VAB shares; K fixed, not an observed capital stock",
        "sector_model_scope": "one representative group per sector; fixed sector employment and capital; no IO, no worker incidence",
        "hours_scope": "main job; PNAD habitual/actual hours are distinct from contracted hours",
    })
    return sectors, provenance
