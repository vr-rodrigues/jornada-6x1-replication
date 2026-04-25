# -*- coding: utf-8 -*-
"""
01_diagnose_sizes.py — Contagem de vínculos por CBO (família) × ano para
as ocupações treated (CBO 4223) e candidatas a controle (CBO 4110, 4221, 4212).

Objetivo: dimensionar volume do painel final antes de puxar dados completos.

Output:
  - data_intermediate/nr17/vinculo_counts_by_cbo_year.csv
  - impressão de resumo na tela
"""
import os
import sys
import basedosdados as bd
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BILLING = os.environ.get("GCP_BILLING_PROJECT", "upa-research")
OUT = os.path.join(ROOT, "data_intermediate", "nr17", "vinculo_counts_by_cbo_year.csv")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# Famílias CBO de interesse
# 4223 - Operadores de telemarketing (TREATED pela NR-17/2007)
# 4110 - Escriturários em geral (controle: admin geral, sem regulação específica)
# 4221 - Telefonistas (controle: atendimento telefônico mas não call center)
# 4212 - Caixas de agências bancárias (placebo: já 6h desde 1933)
# 4222 - Operadores de centrais de informação (alt. controle)
# 3547 - Técnicos em atendimento e informações ao usuário (alt. controle)
CBO_FAMILIES = ['4223', '4110', '4221', '4212', '4222', '3547']

query = f"""
SELECT
  ano,
  SUBSTR(cbo_2002, 1, 4) AS cbo_familia,
  COUNT(*) AS n_vinculos,
  COUNT(DISTINCT cnae_2_subclasse) AS n_cnae_subclasses,
  COUNT(DISTINCT sigla_uf) AS n_ufs,
  AVG(quantidade_horas_contratadas) AS mean_horas,
  APPROX_QUANTILES(quantidade_horas_contratadas, 2)[OFFSET(1)] AS median_horas,
  AVG(valor_salario_contratual) AS mean_salario,
  SUM(CASE WHEN vinculo_ativo_3112 = '1' THEN 1 ELSE 0 END) AS n_ativos_3112
FROM `basedosdados.br_me_rais.microdados_vinculos`
WHERE ano BETWEEN 2003 AND 2012
  AND SUBSTR(cbo_2002, 1, 4) IN ({",".join(f"'{c}'" for c in CBO_FAMILIES)})
GROUP BY ano, cbo_familia
ORDER BY cbo_familia, ano
"""

print("Running diagnostic counts query (years 2003-2012, 6 CBO families)...")
df = bd.read_sql(query, billing_project_id=BILLING)
df.to_csv(OUT, index=False)
print(f"\n[OK] Saved {OUT}")

# Pretty print
print("\n=== Total vínculos by CBO family, by year ===")
pivot = df.pivot(index='ano', columns='cbo_familia', values='n_vinculos')
print(pivot.to_string())

print("\n=== Mean contractual hours ===")
pivot_h = df.pivot(index='ano', columns='cbo_familia', values='mean_horas')
print(pivot_h.to_string(float_format=lambda x: f"{x:.1f}"))

print("\n=== Summary of potential panel volume ===")
totals = df.groupby('cbo_familia')['n_vinculos'].sum()
print(totals.to_string())
print(f"\nTotal vínculos across 6 CBOs, 2003-2012: {totals.sum():,}")
