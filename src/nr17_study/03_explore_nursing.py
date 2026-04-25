# -*- coding: utf-8 -*-
"""
03_explore_nursing.py — Exploratory scan of hours trajectories for nursing CBOs.
If a sharp break appears, we investigate what law/reform caused it.
If not, nursing is not a viable case.

CBOs of interest:
  2235 — Enfermeiros de nível superior (enfermeiro, enfermeiro obstetra, etc.)
  3222 — Técnicos de enfermagem
  3221 — Auxiliares de enfermagem (CBO older — may have declining counts)
  2236 — Obstetras (parteiras) — small group
Also compare:
  2232 — Médicos (control / reference)
  3252 — Farmacêuticos técnicos (alt reference)
"""
import os
import basedosdados as bd
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BILLING = os.environ.get("GCP_BILLING_PROJECT", "upa-research")
OUT = os.path.join(ROOT, "data_intermediate", "nr17", "nursing_hours_trends.csv")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

CBOs = ['2235', '3222', '3221', '2232']  # enfermeiros, téc enf, aux enf, médicos

query = f"""
WITH sample AS (
  SELECT
    ano,
    SUBSTR(cbo_2002, 1, 4) AS cbo_familia,
    sigla_uf,
    tipo_vinculo,
    quantidade_horas_contratadas AS h
  FROM `basedosdados.br_me_rais.microdados_vinculos`
  WHERE ano BETWEEN 2003 AND 2019
    AND SUBSTR(cbo_2002, 1, 4) IN ({",".join(f"'{c}'" for c in CBOs)})
    AND quantidade_horas_contratadas BETWEEN 1 AND 60
)
SELECT
  ano, cbo_familia,
  COUNT(*) AS n,
  AVG(h) AS mean_h,
  APPROX_QUANTILES(h, 100)[OFFSET(10)] AS p10,
  APPROX_QUANTILES(h, 100)[OFFSET(50)] AS p50,
  APPROX_QUANTILES(h, 100)[OFFSET(90)] AS p90,
  SUM(CASE WHEN h <= 30 THEN 1 ELSE 0 END) AS n_ate30,
  SUM(CASE WHEN h = 36 THEN 1 ELSE 0 END) AS n_eq36,
  SUM(CASE WHEN h = 40 THEN 1 ELSE 0 END) AS n_eq40,
  SUM(CASE WHEN h = 44 THEN 1 ELSE 0 END) AS n_eq44
FROM sample
GROUP BY ano, cbo_familia
ORDER BY cbo_familia, ano
"""
print("Querying nursing CBOs 2003-2019...")
df = bd.read_sql(query, billing_project_id=BILLING)
df.to_csv(OUT, index=False)

# Pretty
for cbo in CBOs:
    sub = df[df['cbo_familia'] == cbo].copy()
    if len(sub) == 0:
        continue
    label = {'2235': 'Enfermeiros', '3222': 'Tec. Enf.',
             '3221': 'Aux. Enf.', '2232': 'Medicos'}[cbo]
    sub['pct_30'] = sub['n_ate30'] / sub['n'] * 100
    sub['pct_36'] = sub['n_eq36'] / sub['n'] * 100
    sub['pct_40'] = sub['n_eq40'] / sub['n'] * 100
    sub['pct_44'] = sub['n_eq44'] / sub['n'] * 100
    print(f"\n=== CBO {cbo} ({label}) ===")
    print(sub[['ano', 'n', 'mean_h', 'p50',
               'pct_30', 'pct_36', 'pct_40', 'pct_44']].to_string(
                   index=False, float_format=lambda x: f"{x:.1f}"))
