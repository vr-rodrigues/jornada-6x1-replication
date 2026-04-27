# Referee Replication Checklist

This checklist records the package-level fixes made for the referee round.

## One-Command Replication

Run from the package root:

```bash
python run_all.py --tests --paper
```

On Windows, use `py` if `python` is mapped to the Microsoft Store alias:

```powershell
py run_all.py --tests --paper
```

The command regenerates numerical results, validation JSONs, tables, figures, synced LaTeX assets, tests, and final PDFs.

## Build-Failure Guard

`run_all.py --paper` now checks every `pdflatex` and `bibtex` return code. A missing figure, missing table, or fatal TeX error causes a nonzero exit.

## Paper Asset Sync

Generated artifacts are written first to `output/`. The orchestrator then copies them into the LaTeX tree:

- figures: `output/figures/*` -> `paper/tex/figures/`
- generated tables: `output/tables/*.tex` -> `paper/tex/*_autogen.tex`

The sync step scans LaTeX `\includegraphics{...}` and `\input{...}` references and fails early if an asset is missing.

## Eliminated Manual/Stale Numbers

- The appendix eight-corner envelope table is generated from `output/validation/joint_envelope.json` and `output/validation/joint_envelope_flat.json`.
- The output-decomposition figure is computed by `src/tables_figures/plot_main_figures.py` and audited in `output/validation/decomposition_results.json`.
- The welfare-threshold figure is computed by `src/tables_figures/plot_welfare_schedule.py` and audited in `output/validation/welfare_thresholds.json`.

## Expected Validation Values

Current generated envelope row:

| Specification | 8-corner envelope |
|---|---:|
| Preferred flat-below | `[5.62, 7.48]` |
| Conservative symmetric | `[6.93, 9.23]` |

Current generated decomposition at the 44-to-36h cap:

| Channel | Preferred | Conservative |
|---|---:|---:|
| Mechanical hours | `-14.78` | `-14.78` |
| Efficiency channel | `+2.28` | `-0.87` |
| Reallocation residual | `+5.90` | `+7.63` |
| Total output | `-6.60` | `-8.02` |
