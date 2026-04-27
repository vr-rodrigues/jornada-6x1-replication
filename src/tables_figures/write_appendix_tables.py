"""Generate appendix LaTeX tables from validation outputs."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / "output" / "validation"
OUT_DIR = ROOT / "output" / "tables"

SIGMAS = (1.116, 1.469)
OMEGAS = (0.58, 0.66)
ETAS = (0.33, 0.50)


def load_json(name: str) -> dict:
    path = VALIDATION / name
    if not path.exists():
        raise FileNotFoundError(f"Required validation file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def params_key(row: dict) -> tuple[float, float, float]:
    return (
        round(float(row["sigma"]), 3),
        round(float(row["omega"]), 3),
        round(float(row["eta_I"]), 3),
    )


def corner_index(data: dict) -> dict[tuple[float, float, float], float]:
    grid = data.get("grid", [])
    rows = {}
    for row in grid:
        key = params_key(row)
        if key[0] in SIGMAS and key[1] in OMEGAS and key[2] in ETAS:
            rows[key] = float(row["A_req"])
    expected = {(s, w, e) for s in SIGMAS for w in OMEGAS for e in ETAS}
    missing = sorted(expected - set(rows))
    if missing:
        raise ValueError(f"Missing envelope corners in validation JSON: {missing}")
    return rows


def write_envelope_table() -> Path:
    flat = load_json("joint_envelope_flat.json")
    sym = load_json("joint_envelope.json")
    flat_rows = corner_index(flat)
    sym_rows = corner_index(sym)

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{$A_{\text{req}}$ (\%) at the eight corners of the disciplined $(\sigma,\omega,\eta_I)$ box.}\label{tab:envelope_corners}",
        r"\small",
        r"\begin{tabular}{cccrr}",
        r"\hline\hline",
        r"$\sigma$ & $\omega$ & $\eta_I$ & Preferred (flat-below) & Conservative (symmetric) \\",
        r"\hline",
    ]

    for s in SIGMAS:
        for w in OMEGAS:
            for e in ETAS:
                key = (s, w, e)
                lines.append(
                    f"{s:.3f} & {w:.2f} & {e:.2f} & "
                    f"{flat_rows[key]:.2f} & {sym_rows[key]:.2f} \\\\"
                )

    lines.extend([
        r"\hline",
        (
            r"\multicolumn{3}{l}{Envelope $[\min,\max]$} & "
            f"$[{float(flat['corner_min']):.2f},\\,{float(flat['corner_max']):.2f}]$ & "
            f"$[{float(sym['corner_min']):.2f},\\,{float(sym['corner_max']):.2f}]$ \\\\"
        ),
        r"\hline\hline",
        r"\end{tabular}",
        r"\\[2pt]",
        r"\begin{minipage}{0.95\textwidth}",
        (
            r"{\footnotesize \textit{Notes:} Each row reports $A_{\text{req}}$ at the "
            r"$44\to 36$h cap for one corner of the $(\sigma,\omega,\eta_I)$ box, "
            r"with all other primitives at baseline. The table is generated directly "
            r"from \texttt{output/validation/joint\_envelope\_flat.json} and "
            r"\texttt{output/validation/joint\_envelope.json}.}"
        ),
        r"\end{minipage}",
        r"\end{table}",
        "",
    ])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "tab_envelope_corners.tex"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> None:
    out = write_envelope_table()
    print(f"[OK] {out}")


if __name__ == "__main__":
    main()
