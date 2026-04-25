# -*- coding: utf-8 -*-
"""
Sectoral data pipeline for the 3-sector extension.

Collects and assembles baseline facts for Agriculture, Industry, Services:
  - VAB by sector from SIDRA Table 5938 (API)
  - Employment and informality by sector from IBGE published PNAD Contínua
  - Hours distribution theta_s from DIEESE / national default

Outputs: data_final/SECTORAL_BASELINE_FACTS.csv
"""

import json
import csv
import os
import urllib.request
import datetime

# ── Paths ──────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_FINAL = os.path.join(BASE, "data_final")
DATA_INTERMEDIATE = os.path.join(BASE, "data_intermediate")
os.makedirs(DATA_FINAL, exist_ok=True)
os.makedirs(DATA_INTERMEDIATE, exist_ok=True)

SIDRA_BASE = "https://apisidra.ibge.gov.br/values"


def fetch_sidra(url):
    """Fetch JSON from SIDRA API."""
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


# ═══════════════════════════════════════════════════════════════════════════
# 1. VAB BY SECTOR — SIDRA Table 5938 (Contas Regionais)
# ═══════════════════════════════════════════════════════════════════════════
# Variables:
#   v/37  = PIB a preços correntes (R$ mil)
#   v/513 = VAB Agropecuária (R$ mil)
#   v/517 = VAB Indústria (R$ mil)
#   v/6575 = VAB Serviços excl. admin pública (R$ mil)
#   v/525  = VAB Admin, defesa, educ e saúde públicas, seguridade social (R$ mil)
#   Total services = v/6575 + v/525

def fetch_vab_by_sector():
    """Fetch VAB by sector from SIDRA Table 5938, summing across all states.

    National-level queries (n1/1) return '...' for sector VAB variables.
    State-level queries (n3/all) return actual values. We sum across all 27 UFs.
    Uses 2021 data (latest with full sector breakdown available).
    """
    url = (
        f"{SIDRA_BASE}/t/5938/n3/all"
        f"/v/37,498,513,517,6575,525"
        f"/p/2021"
        f"/f/a"
    )
    print(f"  Fetching VAB from: {url}")
    data = fetch_sidra(url)

    # Sum across all states. Keys: D1C=UF code, D2C=variable code, V=value
    totals = {}  # var_code -> sum
    period = "2021"
    for row in data[1:]:
        var_code = row.get("D2C", "")
        val_str = row.get("V", "")
        if val_str and val_str not in ("...", "-", "X", ""):
            try:
                val = float(val_str)
                totals[var_code] = totals.get(var_code, 0) + val
            except ValueError:
                pass

    pib = totals.get("37", 0)
    vab_total_direct = totals.get("498", 0)
    vab_agro = totals.get("513", 0)
    vab_ind = totals.get("517", 0)
    vab_serv_ex = totals.get("6575", 0)
    vab_admin = totals.get("525", 0)
    vab_serv_total = vab_serv_ex + vab_admin
    vab_total = vab_agro + vab_ind + vab_serv_total

    result = {
        "source": "IBGE, Contas Regionais do Brasil 2021, SIDRA Table 5938 (sum of 27 UFs)",
        "period": period,
        "pib_mil_reais": pib,
        "vab_total_direct_mil_reais": vab_total_direct,
        "vab_agro_mil_reais": vab_agro,
        "vab_industry_mil_reais": vab_ind,
        "vab_services_mil_reais": vab_serv_total,
        "vab_services_ex_admin_mil_reais": vab_serv_ex,
        "vab_admin_mil_reais": vab_admin,
        "vab_total_mil_reais": vab_total,
        "share_agro": round(vab_agro / vab_total, 4) if vab_total > 0 else None,
        "share_industry": round(vab_ind / vab_total, 4) if vab_total > 0 else None,
        "share_services": round(vab_serv_total / vab_total, 4) if vab_total > 0 else None,
    }

    print(f"  Period: {period}")
    print(f"  VAB Agro:     {vab_agro:>18,.0f} ({result['share_agro']:.1%})")
    print(f"  VAB Industry: {vab_ind:>18,.0f} ({result['share_industry']:.1%})")
    print(f"  VAB Services: {vab_serv_total:>18,.0f} ({result['share_services']:.1%})")
    print(f"  VAB Total:    {vab_total:>18,.0f}")

    return result


# ═══════════════════════════════════════════════════════════════════════════
# 2. EMPLOYMENT AND INFORMALITY BY SECTOR — Published IBGE Data
# ═══════════════════════════════════════════════════════════════════════════
# Source: IBGE, PNAD Contínua 2024, Síntese de Indicadores Sociais.
# Cross-referenced with: DIEESE Nota Técnica 2024, IBGE Informality Bulletin.
#
# The SIDRA API (Table 4093) does not provide informality by economic
# activity grouping. These values are from IBGE's published tabulations
# of PNAD Contínua microdata by "grupamento de atividade no trabalho
# principal" (CNAE broad groups).

SECTOR_EMPLOYMENT = {
    "agriculture": {
        "name": "Agropecuária",
        "cnae_sections": "A",
        "employment_share": 0.085,
        "informality_rate": 0.607,
        "avg_hours_formal": 43.5,
        "avg_hours_total": 39.0,
        "source": "IBGE, PNAD Contínua Trimestral 2024 (T4), Grupamento de atividade",
        "notes": (
            "Agriculture has highest informality due to family farming, "
            "seasonal work, and self-employment without CNPJ. "
            "Hours: formal workers cluster at 44h; many informal work <40h."
        ),
    },
    "industry": {
        "name": "Indústria (incl. construção)",
        "cnae_sections": "B-F",
        "employment_share": 0.203,
        "informality_rate": 0.228,
        "avg_hours_formal": 42.5,
        "avg_hours_total": 41.0,
        "source": "IBGE, PNAD Contínua Trimestral 2024 (T4), Grupamento de atividade",
        "notes": (
            "Industry (extractive + manufacturing + utilities + construction) "
            "has low informality in manufacturing (CLT-dominated) but higher "
            "in construction (~45%). Blended rate ~22.8%."
        ),
    },
    "services": {
        "name": "Serviços",
        "cnae_sections": "G-U",
        "employment_share": 0.712,
        "informality_rate": 0.371,
        "avg_hours_formal": 41.0,
        "avg_hours_total": 39.5,
        "source": "IBGE, PNAD Contínua Trimestral 2024 (T4), Grupamento de atividade",
        "notes": (
            "Services encompass commerce, transport, accommodation, IT, finance, "
            "public admin, education, health, domestic work. Informality driven "
            "by self-employed (conta-própria) and domestic workers without carteira."
        ),
    },
}


def build_employment_data(N_total=0.59):
    """Build sector-level employment allocation from published shares."""
    rows = {}
    total_N_check = 0.0

    for sector, info in SECTOR_EMPLOYMENT.items():
        lam_s = info["employment_share"]
        inf_s = info["informality_rate"]
        N_s = N_total * lam_s
        NF_s = N_s * (1 - inf_s)
        NI_s = N_s * inf_s
        total_N_check += N_s

        rows[sector] = {
            "lambda_s": lam_s,
            "N_s": round(N_s, 6),
            "NF_s": round(NF_s, 6),
            "NI_s": round(NI_s, 6),
            "inf_rate": inf_s,
        }

    # Verify shares sum to 1
    total_share = sum(v["lambda_s"] for v in rows.values())
    print(f"\n  Employment shares sum: {total_share:.3f} (should be 1.000)")
    print(f"  Total N check: {total_N_check:.4f} (should be {N_total})")

    for sector, r in rows.items():
        print(f"  {sector:12s}: lam={r['lambda_s']:.3f}, N={r['N_s']:.4f}, "
              f"NF={r['NF_s']:.4f}, NI={r['NI_s']:.4f}, inf={r['inf_rate']:.1%}")

    return rows


# ═══════════════════════════════════════════════════════════════════════════
# 3. HOURS DISTRIBUTION BY SECTOR (theta_s)
# ═══════════════════════════════════════════════════════════════════════════
# Source: DIEESE Nota Técnica 2024, Tabela 7.
# Ideally theta_s should be sector-specific from RAIS microdata.
# As baseline, we use sector-differentiated estimates consistent with
# the DIEESE aggregate theta = [0.085, 0.269, 0.646].
#
# Agriculture: more workers at 44h (long hours in rural work)
# Industry: most workers at 40-44h (CLT-regulated shifts)
# Services: more dispersion (part-time, flexible schedules)

THETA_BY_SECTOR = {
    "agriculture": {
        "theta_36": 0.040,  # Few part-time formal workers in rural areas
        "theta_40": 0.180,  # Some at 40h
        "theta_44": 0.780,  # Bulk at 44h (rural schedules)
        "source": "Estimated from DIEESE 2024 + RAIS sector composition",
        "notes": "Agriculture formal workers predominantly work 44h/week",
    },
    "industry": {
        "theta_36": 0.050,  # Few part-time
        "theta_40": 0.300,  # Significant share at 40h (3-shift manufacturing)
        "theta_44": 0.650,  # Majority at 44h
        "source": "Estimated from DIEESE 2024 + RAIS sector composition",
        "notes": "Industry: mix of 40h (continuous shifts) and 44h (standard CLT)",
    },
    "services": {
        "theta_36": 0.100,  # More part-time (retail, domestic, education)
        "theta_40": 0.260,  # Public sector + banks at 40h or less
        "theta_44": 0.640,  # Commerce typically at 44h
        "source": "Estimated from DIEESE 2024 + RAIS sector composition",
        "notes": "Services: highest part-time share due to commerce/domestic/education",
    },
}


def build_theta_data():
    """Build theta_s arrays and verify consistency with national aggregate."""
    national_theta = [0.085, 0.269, 0.646]
    lambda_s = {s: SECTOR_EMPLOYMENT[s]["employment_share"]
                for s in SECTOR_EMPLOYMENT}
    inf_s = {s: SECTOR_EMPLOYMENT[s]["informality_rate"]
             for s in SECTOR_EMPLOYMENT}

    # theta applies to FORMAL workers only. Weight by formal employment share.
    formal_share = {}
    total_formal = 0.0
    for s in SECTOR_EMPLOYMENT:
        fs = lambda_s[s] * (1 - inf_s[s])
        formal_share[s] = fs
        total_formal += fs

    for s in formal_share:
        formal_share[s] /= total_formal

    print(f"\n  Formal employment weights:")
    for s, w in formal_share.items():
        print(f"    {s:12s}: {w:.3f}")

    # Verify that weighted theta_s ~ national theta
    for i, bin_name in enumerate(["theta_36", "theta_40", "theta_44"]):
        weighted = sum(
            formal_share[s] * THETA_BY_SECTOR[s][bin_name]
            for s in THETA_BY_SECTOR
        )
        print(f"  Weighted {bin_name}: {weighted:.3f} (national: {national_theta[i]:.3f})")

    return THETA_BY_SECTOR, formal_share


# ═══════════════════════════════════════════════════════════════════════════
# 4. HOURLY PRODUCTIVITY BY SECTOR
# ═══════════════════════════════════════════════════════════════════════════

def compute_hourly_productivity(vab_data, employment_data):
    """Compute yph_s = VAB_s / (N_s_thousands × avg_hours_s × 52)."""
    # Map sector keys to VAB fields
    vab_map = {
        "agriculture": vab_data["vab_agro_mil_reais"],
        "industry": vab_data["vab_industry_mil_reais"],
        "services": vab_data["vab_services_mil_reais"],
    }

    # Total employed from PNAD (thousands) — use approximate 2024 total
    N_total_thousands = 103000  # ~103 million occupied (PNAD Q4 2024)

    print(f"\n  Hourly productivity (yph_s = VAB_s / N_s / h_avg_s / 52):")
    yph = {}
    for sector, info in SECTOR_EMPLOYMENT.items():
        N_s_thousands = N_total_thousands * info["employment_share"]
        h_avg = info["avg_hours_total"]
        annual_hours = N_s_thousands * 1000 * h_avg * 52
        vab_reais = vab_map[sector] * 1000  # mil reais → reais
        yph_s = vab_reais / annual_hours if annual_hours > 0 else 0
        yph[sector] = round(yph_s, 2)
        print(f"  {sector:12s}: VAB={vab_map[sector]:>15,.0f} mil R$, "
              f"N={N_s_thousands:>10,.0f} mil, h_avg={h_avg}, "
              f"yph={yph_s:.2f} R$/hour")

    return yph


# ═══════════════════════════════════════════════════════════════════════════
# 5. ASSEMBLE AND SAVE
# ═══════════════════════════════════════════════════════════════════════════

def assemble_baseline_facts():
    """Main pipeline: collect all data and save SECTORAL_BASELINE_FACTS.csv."""
    print("=" * 70)
    print("SECTORAL DATA PIPELINE")
    print("=" * 70)

    # 1. VAB by sector
    print("\n[1/4] Fetching VAB by sector from SIDRA Table 5938...")
    try:
        vab = fetch_vab_by_sector()
    except Exception as e:
        print(f"  WARNING: SIDRA API failed: {e}")
        print("  Using fallback VAB shares from IBGE published data (2022).")
        vab = {
            "source": "IBGE, Contas Regionais 2022 (fallback)",
            "period": "2022",
            "vab_agro_mil_reais": 604_888_000,
            "vab_industry_mil_reais": 1_293_649_000,
            "vab_services_mil_reais": 3_846_897_000,
            "vab_total_mil_reais": 5_745_434_000,
            "share_agro": 0.1053,
            "share_industry": 0.2252,
            "share_services": 0.6695,
        }

    # 2. Employment and informality
    print("\n[2/4] Building employment data from IBGE published sources...")
    emp = build_employment_data(N_total=0.59)

    # 3. Hours distribution
    print("\n[3/4] Building hours distribution by sector...")
    theta, formal_weights = build_theta_data()

    # 4. Hourly productivity
    print("\n[4/4] Computing hourly productivity by sector...")
    yph = compute_hourly_productivity(vab, emp)

    # ── Save CSV ──
    out_path = os.path.join(DATA_FINAL, "SECTORAL_BASELINE_FACTS.csv")
    fieldnames = [
        "sector", "sector_name", "cnae_sections",
        "lambda_s", "inf_rate", "N_s", "NF_s", "NI_s",
        "theta_36", "theta_40", "theta_44",
        "vab_share", "yph_reais_per_hour",
        "source_employment", "source_vab", "source_theta"
    ]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for sector in ["agriculture", "industry", "services"]:
            row = {
                "sector": sector,
                "sector_name": SECTOR_EMPLOYMENT[sector]["name"],
                "cnae_sections": SECTOR_EMPLOYMENT[sector]["cnae_sections"],
                "lambda_s": SECTOR_EMPLOYMENT[sector]["employment_share"],
                "inf_rate": SECTOR_EMPLOYMENT[sector]["informality_rate"],
                "N_s": emp[sector]["N_s"],
                "NF_s": emp[sector]["NF_s"],
                "NI_s": emp[sector]["NI_s"],
                "theta_36": theta[sector]["theta_36"],
                "theta_40": theta[sector]["theta_40"],
                "theta_44": theta[sector]["theta_44"],
                "vab_share": vab.get(f"share_{sector[:4] if sector != 'services' else 'services'}", ""),
                "yph_reais_per_hour": yph.get(sector, ""),
                "source_employment": SECTOR_EMPLOYMENT[sector]["source"],
                "source_vab": vab.get("source", ""),
                "source_theta": theta[sector]["source"],
            }
            # Fix vab_share key for agriculture
            if sector == "agriculture":
                row["vab_share"] = vab.get("share_agro", "")
            elif sector == "industry":
                row["vab_share"] = vab.get("share_industry", "")
            else:
                row["vab_share"] = vab.get("share_services", "")

            writer.writerow(row)

    print(f"\n  Saved: {out_path}")

    # ── Save intermediate JSON ──
    intermediate = {
        "collection_date": datetime.datetime.now().isoformat(),
        "vab": vab,
        "employment": {s: {**v, **SECTOR_EMPLOYMENT[s]} for s, v in emp.items()},
        "theta": theta,
        "yph": yph,
        "formal_weights": formal_weights,
    }
    json_path = os.path.join(DATA_INTERMEDIATE, "sectoral_data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(intermediate, f, indent=2, ensure_ascii=False, default=str)
    print(f"  Saved: {json_path}")

    # ── Consistency checks ──
    print("\n" + "=" * 70)
    print("CONSISTENCY CHECKS")
    print("=" * 70)

    # Check 1: employment shares sum to 1
    total_lam = sum(SECTOR_EMPLOYMENT[s]["employment_share"] for s in SECTOR_EMPLOYMENT)
    status1 = "PASS" if abs(total_lam - 1.0) < 0.01 else "FAIL"
    print(f"  [1] Employment shares sum to 1: {total_lam:.3f} [{status1}]")

    # Check 2: VAB shares sum to ~1
    total_vab_share = (vab.get("share_agro", 0) + vab.get("share_industry", 0)
                       + vab.get("share_services", 0))
    status2 = "PASS" if abs(total_vab_share - 1.0) < 0.02 else "FAIL"
    print(f"  [2] VAB shares sum to 1: {total_vab_share:.3f} [{status2}]")

    # Check 3: weighted informality ~ national (37.8%)
    wt_inf = sum(SECTOR_EMPLOYMENT[s]["employment_share"] *
                 SECTOR_EMPLOYMENT[s]["informality_rate"]
                 for s in SECTOR_EMPLOYMENT)
    status3 = "PASS" if abs(wt_inf - 0.378) < 0.03 else "FAIL"
    print(f"  [3] Weighted informality ~ 37.8%: {wt_inf:.1%} [{status3}]")

    # Check 4: theta_s bins sum to 1 within each sector
    for s in THETA_BY_SECTOR:
        t = THETA_BY_SECTOR[s]
        s_sum = t["theta_36"] + t["theta_40"] + t["theta_44"]
        status4 = "PASS" if abs(s_sum - 1.0) < 0.001 else "FAIL"
        print(f"  [4] theta_{s} sums to 1: {s_sum:.3f} [{status4}]")

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)

    return intermediate


if __name__ == "__main__":
    assemble_baseline_facts()
