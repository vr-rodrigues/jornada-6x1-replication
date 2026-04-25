# -*- coding: utf-8 -*-
"""
04_scan_all_cbos.py — Data-driven search for clean hours-reduction events
across all major CBOs. Scans RAIS 2003-2019 and ranks CBO-year pairs by
magnitude of year-over-year change in hours distribution.

Heuristic: a genuine reform leaves a sharp shift in the share of workers
at key hours-levels (30, 36, 40, 44). Composition-change artifacts tend
to affect many levels at once and are not concentrated at these "round"
numbers.

Output: ranked list of candidate events.
"""
import os
import basedosdados as bd
import pandas as pd
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BILLING = os.environ.get("GCP_BILLING_PROJECT", "upa-research")
OUT = os.path.join(ROOT, "data_intermediate", "nr17", "all_cbos_scan.csv")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# Aggregate per CBO x ano
query = """
WITH base AS (
  SELECT
    ano,
    SUBSTR(cbo_2002, 1, 4) AS cbo,
    quantidade_horas_contratadas AS h
  FROM `basedosdados.br_me_rais.microdados_vinculos`
  WHERE ano BETWEEN 2003 AND 2019
    AND quantidade_horas_contratadas BETWEEN 1 AND 60
    AND cbo_2002 IS NOT NULL
    AND LENGTH(cbo_2002) >= 4
)
SELECT
  ano, cbo,
  COUNT(*) AS n,
  AVG(h) AS mean_h,
  APPROX_QUANTILES(h, 100)[OFFSET(50)] AS p50,
  SUM(CASE WHEN h = 30 THEN 1 ELSE 0 END) / COUNT(*) AS pct_30,
  SUM(CASE WHEN h = 36 THEN 1 ELSE 0 END) / COUNT(*) AS pct_36,
  SUM(CASE WHEN h = 40 THEN 1 ELSE 0 END) / COUNT(*) AS pct_40,
  SUM(CASE WHEN h = 44 THEN 1 ELSE 0 END) / COUNT(*) AS pct_44
FROM base
GROUP BY ano, cbo
HAVING n >= 5000
"""

print("Scanning all CBOs across 2003-2019 (this may take a minute)...")
df = bd.read_sql(query, billing_project_id=BILLING)
df = df.sort_values(['cbo', 'ano']).reset_index(drop=True)
print(f"Rows returned: {len(df):,}")
print(f"Distinct CBOs: {df['cbo'].nunique()}")

# Compute year-over-year changes per CBO
def yoy(series):
    return series.diff()

for col in ['mean_h', 'pct_30', 'pct_36', 'pct_40', 'pct_44']:
    df[f'd_{col}'] = df.groupby('cbo')[col].transform(yoy)

# Score: biggest single-year drop in pct_44 (candidate for hours-reduction reform)
# OR biggest single-year rise in pct_36
df['score_drop44'] = df['d_pct_44']
df['score_rise36'] = df['d_pct_36']
df['score_drop_mean'] = df['d_mean_h']

# Save full table
df.to_csv(OUT, index=False)
print(f"[OK] Saved {OUT}")

# Top candidates: ordered by year-over-year drop in pct_44
print("\n=== TOP 30 candidates by DROP in %-at-44h (downward shift to shorter hours) ===")
top_drop44 = df.nsmallest(30, 'score_drop44')[
    ['ano', 'cbo', 'n', 'mean_h', 'pct_36', 'pct_44', 'd_pct_44', 'd_pct_36', 'd_mean_h']
]
print(top_drop44.to_string(index=False, float_format=lambda x: f"{x:.3f}"))

print("\n=== TOP 30 candidates by RISE in %-at-36h (shift into 36h bucket) ===")
top_rise36 = df.nlargest(30, 'score_rise36')[
    ['ano', 'cbo', 'n', 'mean_h', 'pct_36', 'pct_44', 'd_pct_36', 'd_pct_44', 'd_mean_h']
]
print(top_rise36.to_string(index=False, float_format=lambda x: f"{x:.3f}"))

print("\n=== TOP 20 candidates by DROP in mean hours (any magnitude) ===")
top_drop_mean = df.nsmallest(20, 'score_drop_mean')[
    ['ano', 'cbo', 'n', 'mean_h', 'pct_36', 'pct_44', 'd_mean_h', 'd_pct_36', 'd_pct_44']
]
print(top_drop_mean.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
