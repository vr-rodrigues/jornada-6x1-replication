# -*- coding: utf-8 -*-
"""
Compute number of workers affected by the reform in each sector.

For 44->40h: affected = formal workers at >=41h (theta_44)
For 44->36h: affected = formal workers at 37-40h + >=41h (theta_40 + theta_44)

Uses empirical PNAD data.
"""

import csv
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))


def main():
    data_final = os.path.join(PROJECT_ROOT, "data_final")
    output_dir = os.path.join(PROJECT_ROOT, "output", "sectoral", "tables")

    # Load empirical PNAD data
    emp_path = os.path.join(data_final, "SECTORAL_PNAD_EMPIRICAL.csv")
    sectors = {}
    with open(emp_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sectors[row["sector"]] = {
                "lambda_s": float(row["lambda_s"]),
                "inf_rate": float(row["inf_rate"]),
                "theta_36": float(row["theta_36"]),
                "theta_40": float(row["theta_40"]),
                "theta_44": float(row["theta_44"]),
            }

    # Load estimated data
    est_path = os.path.join(data_final, "SECTORAL_BASELINE_FACTS.csv")
    estimated = {}
    with open(est_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            estimated[row["sector"]] = {
                "lambda_s": float(row["lambda_s"]),
                "inf_rate": float(row["inf_rate"]),
                "theta_36": float(row["theta_36"]),
                "theta_40": float(row["theta_40"]),
                "theta_44": float(row["theta_44"]),
            }

    # Load A_req results
    areq_emp_path = os.path.join(output_dir, "SECTOR_AREQ_EMPIRICAL.csv")
    areq_est_path = os.path.join(output_dir, "SECTOR_AREQ_RESULTS.csv")

    areq_emp = {}
    with open(areq_emp_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            areq_emp[(int(row["h1"]), row["sector"])] = float(row["A_req_pct"])

    areq_est = {}
    with open(areq_est_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            areq_est[(int(row["h1"]), row["sector"])] = float(row["A_req_pct"])

    # Total occupied (PNAD weighted, thousands)
    # From PNAD run output
    N_total_thousands = {
        "agriculture": 7712,
        "industry": 20849,
        "services": 73252,
    }
    total_occ = sum(N_total_thousands.values())

    print("=" * 90)
    print("WORKERS AFFECTED BY REFORM — BY SECTOR (PNAD Q4 2024 empirical)")
    print("=" * 90)

    # ── Table 1: Sector composition ──
    print("\n--- SECTOR COMPOSITION ---")
    print(f"{'Sector':>12s}  {'Total':>8s}  {'Formal':>8s}  {'Informal':>8s}  "
          f"{'Inf.Rate':>8s}  {'<=36h':>8s}  {'37-40h':>8s}  {'>=41h':>8s}")
    print(f"{'':>12s}  {'(mil)':>8s}  {'(mil)':>8s}  {'(mil)':>8s}  "
          f"{'':>8s}  {'(mil)':>8s}  {'(mil)':>8s}  {'(mil)':>8s}")
    print("-" * 90)

    formal_total = {}
    for sname in ["agriculture", "industry", "services"]:
        s = sectors[sname]
        N = N_total_thousands[sname]
        NF = N * (1 - s["inf_rate"])
        NI = N * s["inf_rate"]
        formal_total[sname] = NF

        f_le36 = NF * s["theta_36"]
        f_3740 = NF * s["theta_40"]
        f_ge41 = NF * s["theta_44"]

        print(f"{sname:>12s}  {N:>8,.0f}  {NF:>8,.0f}  {NI:>8,.0f}  "
              f"{s['inf_rate']:>7.1%}  {f_le36:>8,.0f}  {f_3740:>8,.0f}  "
              f"{f_ge41:>8,.0f}")

    # Totals
    NF_all = sum(formal_total.values())
    NI_all = total_occ - NF_all
    nat = sectors["NATIONAL"]
    f_le36_all = NF_all * nat["theta_36"]
    f_3740_all = NF_all * nat["theta_40"]
    f_ge41_all = NF_all * nat["theta_44"]

    print("-" * 90)
    print(f"{'TOTAL':>12s}  {total_occ:>8,.0f}  {NF_all:>8,.0f}  {NI_all:>8,.0f}  "
          f"{nat['inf_rate']:>7.1%}  {f_le36_all:>8,.0f}  {f_3740_all:>8,.0f}  "
          f"{f_ge41_all:>8,.0f}")

    # ── Table 2: Workers affected by 44->40h ──
    print(f"\n{'='*90}")
    print("REFORM 44 -> 40h: Workers affected = formal at >=41h")
    print("=" * 90)
    print(f"{'Sector':>12s}  {'Formal':>8s}  {'theta_44':>8s}  {'Affected':>10s}  "
          f"{'% of Sector':>11s}  {'% of Total':>10s}  {'A_req':>7s}")
    print("-" * 90)

    total_affected_40 = 0
    for sname in ["agriculture", "industry", "services"]:
        s = sectors[sname]
        N = N_total_thousands[sname]
        NF = formal_total[sname]
        affected = NF * s["theta_44"]
        total_affected_40 += affected
        pct_sector = affected / N * 100
        pct_total = affected / total_occ * 100
        areq = areq_emp.get((40, sname), 0)

        print(f"{sname:>12s}  {NF:>8,.0f}  {s['theta_44']:>8.3f}  "
              f"{affected:>10,.0f}  {pct_sector:>10.1f}%  {pct_total:>9.1f}%  "
              f"{areq:>6.2f}%")

    pct_total_40 = total_affected_40 / total_occ * 100
    areq_agg_40 = areq_emp.get((40, "AGGREGATE"), 0)
    print("-" * 90)
    print(f"{'TOTAL':>12s}  {NF_all:>8,.0f}  {nat['theta_44']:>8.3f}  "
          f"{total_affected_40:>10,.0f}  {total_affected_40/total_occ*100:>10.1f}%  "
          f"{pct_total_40:>9.1f}%  {areq_agg_40:>6.2f}%")

    # ── Table 3: Workers affected by 44->36h ──
    print(f"\n{'='*90}")
    print("REFORM 44 -> 36h: Workers affected = formal at 37-40h + >=41h")
    print("=" * 90)
    print(f"{'Sector':>12s}  {'Formal':>8s}  {'th40+th44':>9s}  {'Affected':>10s}  "
          f"{'% of Sector':>11s}  {'% of Total':>10s}  {'A_req':>7s}")
    print("-" * 90)

    total_affected_36 = 0
    for sname in ["agriculture", "industry", "services"]:
        s = sectors[sname]
        N = N_total_thousands[sname]
        NF = formal_total[sname]
        share_affected = s["theta_40"] + s["theta_44"]
        affected = NF * share_affected
        total_affected_36 += affected
        pct_sector = affected / N * 100
        pct_total = affected / total_occ * 100
        areq = areq_emp.get((36, sname), 0)

        print(f"{sname:>12s}  {NF:>8,.0f}  {share_affected:>9.3f}  "
              f"{affected:>10,.0f}  {pct_sector:>10.1f}%  {pct_total:>9.1f}%  "
              f"{areq:>6.2f}%")

    share_aff_nat = nat["theta_40"] + nat["theta_44"]
    areq_agg_36 = areq_emp.get((36, "AGGREGATE"), 0)
    print("-" * 90)
    print(f"{'TOTAL':>12s}  {NF_all:>8,.0f}  {share_aff_nat:>9.3f}  "
          f"{total_affected_36:>10,.0f}  {total_affected_36/total_occ*100:>10.1f}%  "
          f"{total_affected_36/total_occ*100:>9.1f}%  {areq_agg_36:>6.2f}%")

    # ── Table 4: Comparison estimated vs empirical affected workers ──
    print(f"\n{'='*90}")
    print("COMPARISON: Estimated vs Empirical — Workers affected (44->36h)")
    print("=" * 90)
    print(f"{'Sector':>12s}  {'Est.Formal':>10s}  {'Emp.Formal':>10s}  "
          f"{'Est.Aff%':>8s}  {'Emp.Aff%':>8s}  "
          f"{'Est.Areq':>8s}  {'Emp.Areq':>8s}")
    print("-" * 90)

    for sname in ["agriculture", "industry", "services"]:
        se = estimated[sname]
        sp = sectors[sname]
        N = N_total_thousands[sname]

        NF_est = N * (1 - se["inf_rate"])
        NF_emp = N * (1 - sp["inf_rate"])

        aff_est = se["theta_40"] + se["theta_44"]
        aff_emp = sp["theta_40"] + sp["theta_44"]

        # % of SECTOR total that is affected
        pct_est = NF_est * aff_est / N * 100
        pct_emp = NF_emp * aff_emp / N * 100

        areq_e = areq_est.get((36, sname), 0)
        areq_p = areq_emp.get((36, sname), 0)

        print(f"{sname:>12s}  {NF_est:>10,.0f}  {NF_emp:>10,.0f}  "
              f"{pct_est:>7.1f}%  {pct_emp:>7.1f}%  "
              f"{areq_e:>7.2f}%  {areq_p:>7.2f}%")

    # ── Key insight ──
    print(f"\n{'='*90}")
    print("KEY INSIGHT: A_req per affected worker")
    print("=" * 90)
    print(f"\n{'Scenario':>10s}  {'Sector':>12s}  {'Affected':>10s}  "
          f"{'A_req':>7s}  {'Areq/Aff':>10s}")
    print("-" * 60)

    for h1 in [40, 36]:
        for sname in ["agriculture", "industry", "services"]:
            s = sectors[sname]
            N = N_total_thousands[sname]
            NF = formal_total[sname]

            if h1 == 40:
                affected = NF * s["theta_44"]
            else:
                affected = NF * (s["theta_40"] + s["theta_44"])

            areq = areq_emp.get((h1, sname), 0)
            pct_aff = affected / N * 100

            # A_req "intensity" = A_req / (affected share of sector)
            areq_per_pct = areq / (pct_aff / 100) if pct_aff > 0 else 0

            print(f"  44->{h1:2d}h  {sname:>12s}  {pct_aff:>9.1f}%  "
                  f"{areq:>6.2f}%  {areq_per_pct:>9.2f}%")
        print()

    # Save summary table
    out_path = os.path.join(output_dir, "SECTOR_WORKERS_AFFECTED.csv")
    rows = []
    for h1 in [40, 36]:
        for sname in ["agriculture", "industry", "services"]:
            s = sectors[sname]
            N = N_total_thousands[sname]
            NF = N * (1 - s["inf_rate"])
            NI = N * s["inf_rate"]

            if h1 == 40:
                share_aff = s["theta_44"]
            else:
                share_aff = s["theta_40"] + s["theta_44"]

            affected = NF * share_aff
            unaffected_formal = NF * (1 - share_aff)

            rows.append({
                "h1": h1,
                "sector": sname,
                "total_workers_k": N,
                "formal_workers_k": round(NF),
                "informal_workers_k": round(NI),
                "inf_rate": round(s["inf_rate"], 4),
                "theta_below_cap": round(1 - share_aff, 4),
                "theta_above_cap": round(share_aff, 4),
                "affected_workers_k": round(affected),
                "pct_of_sector": round(affected / N * 100, 2),
                "pct_of_total_occ": round(affected / total_occ * 100, 2),
                "A_req_pct": areq_emp.get((h1, sname), 0),
            })

    fieldnames = ["h1", "sector", "total_workers_k", "formal_workers_k",
                   "informal_workers_k", "inf_rate", "theta_below_cap",
                   "theta_above_cap", "affected_workers_k",
                   "pct_of_sector", "pct_of_total_occ", "A_req_pct"]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved: {out_path}")
    print("\nDONE")


if __name__ == "__main__":
    main()
