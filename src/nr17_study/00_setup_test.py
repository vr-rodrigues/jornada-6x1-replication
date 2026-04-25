# -*- coding: utf-8 -*-
"""
00_setup_test.py — Confirm basedosdados / BigQuery access and do a small
sanity-check query against RAIS pseudonymized microdata.

Prerequisites:
- basedosdados installed (`pip install basedosdados`)
- GCP application-default credentials OR a service account key
  (set GOOGLE_APPLICATION_CREDENTIALS env var to the key file path)

This script:
1. Attempts a minimal query that counts CBO 4223 vínculos in 2006.
2. Reports row count and small sample.
3. If successful, proves access is fine for Sprint 2.
"""

import os
import sys
import json

try:
    import basedosdados as bd
except ImportError:
    sys.exit("ERROR: basedosdados not installed. Run: pip install basedosdados")

BILLING_PROJECT = os.environ.get("GCP_BILLING_PROJECT")
if not BILLING_PROJECT:
    sys.exit("ERROR: set env var GCP_BILLING_PROJECT to your Google Cloud project id.")

print(f"Billing project: {BILLING_PROJECT}")
print("Running sanity-check query against br_me_rais.microdados_vinculos ...")

# Very small query: count rows for CBO 4223 in 2006
query = """
SELECT
  ano,
  COUNT(*) AS n_vinculos,
  COUNT(DISTINCT id_estabelecimento) AS n_estabelecimentos
FROM `basedosdados.br_me_rais.microdados_vinculos`
WHERE ano = 2006
  AND SUBSTR(cbo_2002, 1, 4) = '4223'
GROUP BY ano
"""

try:
    df = bd.read_sql(query, billing_project_id=BILLING_PROJECT)
    print("\n[OK] Query succeeded.")
    print(df.to_string(index=False))
except Exception as e:
    print(f"\n[ERROR] Query failed: {type(e).__name__}: {e}")
    print("\nPossible causes:")
    print("  - Auth not configured: run `gcloud auth application-default login`")
    print("  - Billing not enabled on project.")
    print("  - Table name changed: check https://basedosdados.org/dataset/br-me-rais")
    sys.exit(1)

print("\nNext step: run 01_build_panel.py to construct the firm-year panel.")
