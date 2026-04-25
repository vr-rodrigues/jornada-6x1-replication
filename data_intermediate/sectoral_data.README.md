# sectoral_data.json — provenance note

**Status**: auxiliary / legacy. Do NOT use for paper-level claims.

## Scope mismatch

`sectoral_data.json` is produced by `src/sectoral/data/collect_sectoral_data.py`,
which blends IBGE Contas Regionais (VAB by sector, 2021) with hardcoded
**narrow** PNAD informality rates (60.7% agri, 22.8% industry, 37.1% services)
and hardcoded DIEESE-style hours distributions.

The paper (and Table `tab:facts_informality`) uses the **broad** IBGE
informality definition (VD4009 + V4017 CNPJ) computed directly from PNAD
Continua Q4 2024 microdata, with rates 71.8% / 44.4% / 41.2% and the
empirically-estimated theta bins. Those numbers live in
`data_final/SECTORAL_PNAD_EMPIRICAL.csv`, produced by the R pipeline in
`src/sectoral/data/pnad_sectoral_microdata.R`.

## Canonical artifact

**`data_final/SECTORAL_PNAD_EMPIRICAL.csv` is the paper's sectoral source of
record.** All figures, tables, and calibration in the paper pull from it.

`sectoral_data.json` remains in the tree because
`audit3/checks/check_04_sectoral.py` and a handful of sectoral scripts
import it for VAB (value-added) shares, which are independent of
informality. VAB shares there (agri 0.077, industry 0.259, services 0.665)
come from SIDRA Table 5938 summed across UFs for 2021 and are unchanged.

## Action

Readers who need sectoral informality or theta: use
`data_final/SECTORAL_PNAD_EMPIRICAL.csv`. Readers who need sectoral VAB
shares: either file agrees.

Last verified: 2026-04-23 (post audit3 revision).
