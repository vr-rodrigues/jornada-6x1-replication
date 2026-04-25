# -*- coding: utf-8 -*-
"""
collect_pnad.py — Coleta de dados da PNAD Continua via API SIDRA (IBGE)

Dados coletados:
  1. Taxa de informalidade agregada (Tabela 4093)
  2. Posicao na ocupacao — breakdown formal/informal (Tabela 4097)
  3. Distribuicao por tamanho de empreendimento (Tabela 6413, anual)
  4. Horas medias por posicao na ocupacao (Tabela 6374)

SIDRA API response format:
  - Record 0: header (column names as values)
  - Record 1+: data
  - D2C = variable code, D2N = variable name
  - D3C = period code, D3N = period name
  - V = value

Saida: data_intermediate/pnad_targets.json
"""

import json
import os
import sys
import hashlib
import requests
import datetime

# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Configuracao
# ============================================================
BASE_URL = "https://apisidra.ibge.gov.br/values"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "data_intermediate")
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {"Accept": "application/json"}


def fetch_sidra(table, variables, period, geo_level="n1", geo_value="all",
                classifications=None):
    """Fetch data from SIDRA API. Returns list of dicts (record 0 = header)."""
    url = f"{BASE_URL}/t/{table}/{geo_level}/{geo_value}/v/{variables}/p/{period}"
    if classifications:
        for cls_id, cls_values in classifications.items():
            url += f"/c{cls_id}/{cls_values}"
    print(f"  Fetching: {url}")
    resp = requests.get(url, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    return resp.json()


def parse_sidra(data):
    """Parse SIDRA response: skip header (record 0), extract D2C as var_code."""
    records = data[1:] if len(data) > 1 else data
    parsed = []
    for rec in records:
        val_str = rec.get("V", "")
        val = None
        if val_str not in (None, "", "...", "-", "X"):
            try:
                val = float(str(val_str).replace(",", "."))
            except (ValueError, TypeError):
                pass
        parsed.append({
            "var_code": rec.get("D2C", ""),
            "var_name": rec.get("D2N", ""),
            "period_code": rec.get("D3C", ""),
            "period_name": rec.get("D3N", ""),
            "value": val,
            # Extra dimensions (classifications)
            "d4_code": rec.get("D4C", ""),
            "d4_name": rec.get("D4N", ""),
            "d5_code": rec.get("D5C", ""),
            "d5_name": rec.get("D5N", ""),
        })
    return parsed


# ============================================================
# 1. Taxa de Informalidade Agregada (Tabela 4093)
# ============================================================
def collect_informality_rate():
    """
    Tabela 4093: Pessoas de 14+ anos, por condicao de ocupacao.
    D2C=12466: taxa de informalidade (%).
    D2C=4090: total ocupados (mil).
    D2C=4723: informais (mil).
    c2=6794: sexo=total.
    """
    print("\n[1/4] Coletando taxa de informalidade (Tabela 4093)...")
    data = fetch_sidra(4093, "4090,4723,12466", "last 4", classifications={"2": "6794"})
    records = parse_sidra(data)

    # Extract informality rates
    inf_rates = [(r["period_name"], r["value"]) for r in records
                 if r["var_code"] == "12466" and r["value"] is not None]

    # Extract totals for context
    total_occupied = [(r["period_name"], r["value"]) for r in records
                      if r["var_code"] == "4090" and r["value"] is not None]
    informal_count = [(r["period_name"], r["value"]) for r in records
                      if r["var_code"] == "4723" and r["value"] is not None]

    latest_rate = inf_rates[-1][1] if inf_rates else None
    avg_rate = sum(r[1] for r in inf_rates) / len(inf_rates) if inf_rates else None

    return {
        "source": "PNAD Continua Trimestral, Tabela 4093, SIDRA/IBGE",
        "variable": "Taxa de informalidade (%)",
        "latest_quarter_name": inf_rates[-1][0] if inf_rates else None,
        "latest_quarter_value": latest_rate,
        "avg_last_4_quarters": round(avg_rate, 2) if avg_rate else None,
        "n_quarters": len(inf_rates),
        "quarterly_rates": [{"period": p, "rate_pct": v} for p, v in inf_rates],
        "quarterly_total_occupied_thousands": [{"period": p, "value": v} for p, v in total_occupied],
        "quarterly_informal_thousands": [{"period": p, "value": v} for p, v in informal_count],
        "api_table": 4093,
        "collection_date": datetime.datetime.now().isoformat()
    }


# ============================================================
# 2. Posicao na Ocupacao (Tabela 4097)
# ============================================================
def collect_position_occupation():
    """
    Tabela 4097: Pessoas de 14+ ocupadas, por posicao na ocupacao.
    D2C=4090 (mil pessoas), D2C=4108 (distribuicao %).
    c11913: categorias detalhadas de posicao.
    """
    print("\n[2/4] Coletando posicao na ocupacao (Tabela 4097)...")
    data = fetch_sidra(4097, "4090,4108", "last 1", classifications={"11913": "all"})
    records = parse_sidra(data)

    # Group by category (d4 = classification c11913)
    categories = {}
    for rec in records:
        cat_code = rec["d4_code"]
        cat_name = rec["d4_name"]
        if cat_code not in categories:
            categories[cat_code] = {"name": cat_name, "code": cat_code}
        if rec["var_code"] == "4090":
            categories[cat_code]["thousands"] = rec["value"]
        elif rec["var_code"] == "4108":
            categories[cat_code]["pct"] = rec["value"]

    # Formal vs informal aggregation
    # Formal: com carteira privado (31722) + domestico com carteira (31725)
    #         + publico com carteira (31728) + militar/estatutario (31730)
    #         + empregador com CNPJ (45934) + conta propria com CNPJ (45936)
    # Informal: sem carteira privado (31723) + domestico sem carteira (31726)
    #           + publico sem carteira (31729) + empregador sem CNPJ (45935)
    #           + conta propria sem CNPJ (45937) + auxiliar familiar (31731)
    formal_codes = ["31722", "31725", "31728", "31730", "45934", "45936"]
    informal_codes = ["31723", "31726", "31729", "45935", "45937", "31731"]

    get_val = lambda codes: sum(categories.get(c, {}).get("thousands", 0) or 0 for c in codes)
    formal_total = get_val(formal_codes)
    informal_total = get_val(informal_codes)
    total = formal_total + informal_total
    inf_rate = (informal_total / total * 100) if total > 0 else None

    return {
        "source": "PNAD Continua Trimestral, Tabela 4097, SIDRA/IBGE",
        "formal_thousands": round(formal_total, 1),
        "informal_thousands": round(informal_total, 1),
        "total_thousands": round(total, 1),
        "informality_rate_computed_pct": round(inf_rate, 2) if inf_rate else None,
        "categories": {k: v for k, v in categories.items()},
        "formal_codes_used": formal_codes,
        "informal_codes_used": informal_codes,
        "api_table": 4097,
        "collection_date": datetime.datetime.now().isoformat()
    }


# ============================================================
# 3. Tamanho do Empreendimento (Tabela 6413, Anual)
# ============================================================
def collect_firm_size():
    """
    Tabela 6413: Ocupados por tamanho do empreendimento.
    Exclui setor publico e domesticos.
    c790: tamanho; c2=6794: sexo=total.
    """
    print("\n[3/4] Coletando distribuicao por porte (Tabela 6413)...")
    data = fetch_sidra(6413, "10441,10443", "last 1",
                       classifications={"2": "6794", "790": "all"})
    records = parse_sidra(data)

    # d4 or d5 has the firm size classification
    sizes = {}
    period_name = ""
    for rec in records:
        # Firm size is in d5 (c790 is 5th dimension after n1, v, p, c2)
        size_code = rec["d5_code"] or rec["d4_code"]
        size_name = rec["d5_name"] or rec["d4_name"]
        period_name = rec["period_name"] or period_name
        if size_code not in sizes:
            sizes[size_code] = {"name": size_name, "code": size_code}
        if rec["var_code"] == "10441":
            sizes[size_code]["thousands"] = rec["value"]
        elif rec["var_code"] == "10443":
            sizes[size_code]["pct"] = rec["value"]

    # Small (<=49) vs Large (50+)
    # 40304=1-5, 40305=6-10, 40306=11-50, 40307=51+
    small_codes = ["40304", "40305", "40306"]
    large_codes = ["40307"]
    small_total = sum(sizes.get(c, {}).get("thousands", 0) or 0 for c in small_codes)
    large_total = sum(sizes.get(c, {}).get("thousands", 0) or 0 for c in large_codes)
    total = small_total + large_total
    small_share = (small_total / total * 100) if total > 0 else None

    return {
        "source": "PNAD Continua Anual, Tabela 6413, SIDRA/IBGE",
        "note": "Exclui setor publico e domesticos",
        "period": period_name,
        "small_le49_thousands": round(small_total, 1),
        "large_ge50_thousands": round(large_total, 1),
        "total_thousands": round(total, 1),
        "small_share_pct": round(small_share, 2) if small_share else None,
        "large_share_pct": round(100 - small_share, 2) if small_share else None,
        "sizes_detail": {k: v for k, v in sizes.items()},
        "api_table": 6413,
        "collection_date": datetime.datetime.now().isoformat()
    }


# ============================================================
# 4. Horas Medias por Posicao (Tabela 6374)
# ============================================================
def collect_average_hours():
    """
    Tabela 6374: Horas habitualmente trabalhadas.
    D2C=8186: media de horas semanais.
    c2399: posicao na ocupacao.
    """
    print("\n[4/4] Coletando horas medias (Tabela 6374)...")
    data = fetch_sidra(6374, "8186", "last 4", classifications={"2399": "all"})
    records = parse_sidra(data)

    results = []
    for rec in records:
        results.append({
            "period": rec["period_name"],
            "position": rec["d4_name"],
            "position_code": rec["d4_code"],
            "avg_hours": rec["value"]
        })

    return {
        "source": "PNAD Continua Trimestral, Tabela 6374, SIDRA/IBGE",
        "variable": "Media de horas semanais habitualmente trabalhadas",
        "records": results,
        "api_table": 6374,
        "collection_date": datetime.datetime.now().isoformat()
    }


# ============================================================
# Main
# ============================================================
def main():
    print("=" * 60)
    print("COLETA PNAD CONTINUA -- SIDRA/IBGE")
    print("=" * 60)

    results = {}

    try:
        results["informality_rate"] = collect_informality_rate()
    except Exception as e:
        print(f"  ERRO coleta informalidade: {e}")
        results["informality_rate"] = {"error": str(e)}

    try:
        results["position_occupation"] = collect_position_occupation()
    except Exception as e:
        print(f"  ERRO coleta posicao: {e}")
        results["position_occupation"] = {"error": str(e)}

    try:
        results["firm_size"] = collect_firm_size()
    except Exception as e:
        print(f"  ERRO coleta porte: {e}")
        results["firm_size"] = {"error": str(e)}

    try:
        results["average_hours"] = collect_average_hours()
    except Exception as e:
        print(f"  ERRO coleta horas: {e}")
        results["average_hours"] = {"error": str(e)}

    # Save
    outpath = os.path.join(OUTPUT_DIR, "pnad_targets.json")
    content = json.dumps(results, ensure_ascii=False, indent=2)
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(content)

    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
    print(f"\n[OK] Dados salvos em: {outpath}")
    print(f"     SHA-256: {sha}")

    # Summary
    inf = results.get("informality_rate", {})
    print(f"\n--- RESUMO ---")
    print(f"  Informalidade (ultimo trim.): {inf.get('latest_quarter_value', '?')}%")
    print(f"  Informalidade (media 4 trim.): {inf.get('avg_last_4_quarters', '?')}%")

    pos = results.get("position_occupation", {})
    print(f"  Informais (mil): {pos.get('informal_thousands', '?')}")
    print(f"  Formais (mil): {pos.get('formal_thousands', '?')}")
    print(f"  Inf. rate (computada): {pos.get('informality_rate_computed_pct', '?')}%")

    fs = results.get("firm_size", {})
    print(f"  Share pequenas (<=49): {fs.get('small_share_pct', '?')}%")
    print(f"  Share grandes (50+): {fs.get('large_share_pct', '?')}%")

    return results


if __name__ == "__main__":
    main()
