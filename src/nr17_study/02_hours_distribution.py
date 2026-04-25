# -*- coding: utf-8 -*-
"""
02_hours_distribution.py — Distribuição de horas contratadas dentro de CBO 4223
pré e pós-reforma, para avaliar se há variação suficiente para DiD.

Se a média de 36.2h em 2006 for resultado de (a) quase todo mundo já em 36h
ou (b) mistura de 36h + 44h, isso muda radicalmente o desenho.
"""
import os
import basedosdados as bd
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BILLING = os.environ.get("GCP_BILLING_PROJECT", "upa-research")
OUT = os.path.join(ROOT, "data_intermediate", "nr17", "hours_distribution.csv")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# Distribuição das horas contratadas por CBO 4223 e controles, pré/pós reforma
query = """
WITH sample AS (
  SELECT
    ano,
    SUBSTR(cbo_2002, 1, 4) AS cbo_familia,
    quantidade_horas_contratadas AS h
  FROM `basedosdados.br_me_rais.microdados_vinculos`
  WHERE ano IN (2005, 2006, 2007, 2008, 2009, 2012)
    AND SUBSTR(cbo_2002, 1, 4) IN ('4223', '4110', '4221', '4222', '4212')
    AND quantidade_horas_contratadas BETWEEN 1 AND 70
)
SELECT
  ano, cbo_familia,
  COUNT(*) AS n,
  MIN(h) AS min_h,
  APPROX_QUANTILES(h, 100)[OFFSET(10)] AS p10,
  APPROX_QUANTILES(h, 100)[OFFSET(25)] AS p25,
  APPROX_QUANTILES(h, 100)[OFFSET(50)] AS p50,
  APPROX_QUANTILES(h, 100)[OFFSET(75)] AS p75,
  APPROX_QUANTILES(h, 100)[OFFSET(90)] AS p90,
  MAX(h) AS max_h,
  AVG(h) AS mean_h,
  SUM(CASE WHEN h <= 30 THEN 1 ELSE 0 END) AS n_ate30,
  SUM(CASE WHEN h = 36 THEN 1 ELSE 0 END) AS n_eq36,
  SUM(CASE WHEN h BETWEEN 37 AND 43 THEN 1 ELSE 0 END) AS n_37a43,
  SUM(CASE WHEN h = 44 THEN 1 ELSE 0 END) AS n_eq44,
  SUM(CASE WHEN h > 44 THEN 1 ELSE 0 END) AS n_acima44
FROM sample
GROUP BY ano, cbo_familia
ORDER BY cbo_familia, ano
"""
print("Running hours distribution query...")
df = bd.read_sql(query, billing_project_id=BILLING)
df.to_csv(OUT, index=False)
print(f"[OK] Saved {OUT}")

# Focus on 4223
print("\n=== CBO 4223 (telemarketing) — hours distribution ===")
sub = df[df['cbo_familia'] == '4223'].copy()
sub['pct_36'] = sub['n_eq36'] / sub['n'] * 100
sub['pct_44'] = sub['n_eq44'] / sub['n'] * 100
sub['pct_37a43'] = sub['n_37a43'] / sub['n'] * 100
print(sub[['ano', 'n', 'mean_h', 'p10', 'p50', 'p90',
           'pct_36', 'pct_37a43', 'pct_44']].to_string(index=False,
    float_format=lambda x: f"{x:.1f}"))

print("\n=== CBO 4110 (escriturários, control) — hours distribution ===")
sub = df[df['cbo_familia'] == '4110'].copy()
sub['pct_36'] = sub['n_eq36'] / sub['n'] * 100
sub['pct_44'] = sub['n_eq44'] / sub['n'] * 100
sub['pct_37a43'] = sub['n_37a43'] / sub['n'] * 100
print(sub[['ano', 'n', 'mean_h', 'p10', 'p50', 'p90',
           'pct_36', 'pct_37a43', 'pct_44']].to_string(index=False,
    float_format=lambda x: f"{x:.1f}"))

print("\n=== CBO 4221 (telefonistas, control) — hours distribution ===")
sub = df[df['cbo_familia'] == '4221'].copy()
sub['pct_36'] = sub['n_eq36'] / sub['n'] * 100
sub['pct_44'] = sub['n_eq44'] / sub['n'] * 100
sub['pct_37a43'] = sub['n_37a43'] / sub['n'] * 100
print(sub[['ano', 'n', 'mean_h', 'p10', 'p50', 'p90',
           'pct_36', 'pct_37a43', 'pct_44']].to_string(index=False,
    float_format=lambda x: f"{x:.1f}"))
