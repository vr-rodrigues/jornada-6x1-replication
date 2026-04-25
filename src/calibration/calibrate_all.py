# -*- coding: utf-8 -*-
"""
calibrate_all.py — Reimplemented calibration from zero

Reads: data_final/calibration_targets.csv
Produces:
  - data_final/PARAMETER_MASTER_TABLE.csv
  - Console output with all calibrated parameters

Calibration flow:
  1. Load external targets (alpha, eta_I, e_q, theta, gamma_F, informality targets)
  2. Derive kappa from e_q and h_ref
  3. Build groups (Pequenas, Grandes) with N, K allocated by shares
  4. For each group, calibrate wedge (tau) via bisection to match informality target
  5. Solve baseline to get per-capita values
  6. Calibrate psi (GHH) from baseline FOC
  7. Compute A_req via bisection
  8. Compute welfare (DeltaCV)
  9. Output PARAMETER_MASTER_TABLE.csv
"""

import os
import sys
import csv
import json
import hashlib
import datetime
import numpy as np

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Paths
# ============================================================
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FINAL = os.path.join(PROJECT_ROOT, "data_final")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "validation")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# Model primitives (reimplemented from zero)
# ============================================================

# --- Production ---
def production(A, K, alpha, L):
    """Cobb-Douglas: Y = A * K^alpha * L^(1-alpha)"""
    return A * K**alpha * np.maximum(L, 1e-15)**(1 - alpha)

def mpl_L(A, K, alpha, L):
    """Marginal product of labor: (1-alpha) * Y / L"""
    Y = production(A, K, alpha, L)
    return (1 - alpha) * Y / np.maximum(L, 1e-15)

# --- CES Aggregator ---
def ces_agg(LF, LI, omega, sigma_sub):
    """
    CES aggregator: L = [omega*LF^rho + (1-omega)*LI^rho]^(1/rho)
    where rho = (sigma_sub - 1) / sigma_sub
    """
    rho = (sigma_sub - 1.0) / sigma_sub
    if abs(rho) < 1e-12:
        # Cobb-Douglas limit (sigma -> 1)
        return np.maximum(LF, 1e-15)**omega * np.maximum(LI, 1e-15)**(1 - omega)
    LF_safe = np.maximum(LF, 1e-15)
    LI_safe = np.maximum(LI, 1e-15)
    inside = omega * LF_safe**rho + (1 - omega) * LI_safe**rho
    return np.maximum(inside, 1e-15)**(1.0 / rho)

# --- Efficiency function ---
def eff(h, kappa, h_star):
    """Efficiency: e(h) = exp{-kappa * (h - h_star)^2}"""
    return float(np.exp(-kappa * (h - h_star)**2))

# --- Hours heterogeneity ---
HOURS_BINS = np.array([36.0, 40.0, 44.0])

def formal_hours_avg(h_cap, theta):
    """Average formal hours under cap, weighted by theta."""
    h_capped = np.minimum(HOURS_BINS, float(h_cap))
    return float(np.sum(theta * h_capped))

def formal_hours_hetero(h_cap, kappa, h_star, theta):
    """Return (avg_hours, effective_hours_per_worker) under cap."""
    h_capped = np.minimum(HOURS_BINS, float(h_cap))
    avg_h = float(np.sum(theta * h_capped))
    e_bins = np.exp(-kappa * (h_capped - h_star)**2)
    eff_h = float(np.sum(theta * h_capped * e_bins))
    return avg_h, eff_h

# --- Kappa calibration ---
def calibrate_kappa(h_ref, h_star, e_q):
    """
    Calibrate kappa from hours-output elasticity.

    The elasticity of output w.r.t. hours at h_ref is:
      d ln(h * e(h)) / d ln(h) = 1 - 2*kappa*h*(h - h_star)
    Setting this equal to e_q:
      kappa = (1 - e_q) / (2 * h_ref * (h_ref - h_star))
    """
    if abs(h_ref - h_star) < 1e-12:
        return 0.0
    return (1.0 - e_q) / (2.0 * h_ref * (h_ref - h_star))

# --- Informal cost ---
def informal_cost(NI, pi_m):
    """Convex cost of informality: 0.5 * pi_m * NI^2"""
    return 0.5 * pi_m * NI**2

# --- GHH utility ---
def ghh_composite(C, h, nu, psi):
    """GHH composite: C - psi * h^(1+nu) / (1+nu)"""
    return C - psi * h**(1.0 + nu) / (1.0 + nu)

def calibrate_psi(w_hourly, h, nu):
    """From GHH FOC: psi * h^nu = w  =>  psi = w / h^nu"""
    return w_hourly / max(h**nu, 1e-15)

def compensating_variation(C0, h0, C1, h1, nu, psi):
    """DeltaCV = composite_1 / composite_0 - 1"""
    comp0 = ghh_composite(C0, h0, nu, psi)
    comp1 = ghh_composite(C1, h1, nu, psi)
    return float(comp1 / max(comp0, 1e-15) - 1.0)

# ============================================================
# Firm optimization (grid search)
# ============================================================
def solve_NF(N_total, hF, hI, A, K, alpha, omega, sigma_sub, eta_I,
             kappa, h_star, formal_wedge, pi_m, gamma_F, NF_prev, theta,
             grid=4001):
    """
    Firm chooses NF to maximize Y - wedge*NF - informal_cost - adjustment_cost.
    Returns dict with equilibrium allocation.
    """
    NF_grid = np.linspace(0, N_total, grid)
    NI_grid = N_total - NF_grid

    hF_avg, eff_hF = formal_hours_hetero(hF, kappa, h_star, theta)
    eI = eff(hI, kappa, h_star)

    LF = NF_grid * eff_hF
    LI = eta_I * NI_grid * hI * eI
    L = ces_agg(LF, LI, omega, sigma_sub)
    Y = production(A, K, alpha, L)

    adj = 0.5 * gamma_F * (NF_grid - NF_prev)**2
    phi = informal_cost(NI_grid, pi_m)

    obj = Y - formal_wedge * NF_grid - phi - adj
    j = int(np.argmax(obj))

    NF = float(NF_grid[j])
    NI = float(NI_grid[j])
    Ys = float(Y[j])
    C = Ys - float(adj[j])

    hours_total = NF * hF_avg + NI * hI
    h_avg = hours_total / max(N_total, 1e-15)

    eF_avg = eff_hF / max(hF_avg, 1e-15)

    return {
        "NF": NF, "NI": NI, "Y": Ys, "C": C,
        "informality": NI / max(N_total, 1e-15),
        "hours_total": hours_total,
        "h_avg": h_avg,
        "Y_per_hour": Ys / max(hours_total, 1e-15),
        "eF": eF_avg, "eI": eI,
        "hF_avg": hF_avg,
        "adj": float(adj[j]),
        "phi": float(phi[j]),
    }

# ============================================================
# Wedge calibration via bisection
# ============================================================
def calibrate_wedge(target_inf, N_total, h0, hI, A, K, alpha, omega,
                    sigma_sub, eta_I, kappa, h_star, pi_m, theta,
                    lo=0.0, hi=25.0, n_iter=60, grid=3001):
    """Find formal_wedge such that equilibrium informality = target_inf."""

    def inf_at(wedge):
        sol = solve_NF(N_total, h0, hI, A, K, alpha, omega, sigma_sub, eta_I,
                       kappa, h_star, wedge, pi_m, 0.0,
                       N_total * (1 - target_inf), theta, grid)
        return sol["informality"]

    inf_lo = inf_at(lo)
    inf_hi = inf_at(hi)

    if target_inf <= inf_lo + 1e-10:
        return lo
    if target_inf >= inf_hi - 1e-10:
        return hi

    a, b = lo, hi
    for _ in range(n_iter):
        m = 0.5 * (a + b)
        if inf_at(m) > target_inf:
            b = m
        else:
            a = m
    return 0.5 * (a + b)

# ============================================================
# pi_m calibration
# ============================================================
def calibrate_pi_m(target_inf, N_total, h0, hI, A, K, alpha, omega,
                   sigma_sub, eta_I, kappa, h_star, theta,
                   lo=0.0, hi=1.0, grid=2001):
    """Find pi_m such that informality at wedge=0 equals target_inf."""

    def inf_at(pm):
        sol = solve_NF(N_total, h0, hI, A, K, alpha, omega, sigma_sub, eta_I,
                       kappa, h_star, 0.0, pm, 0.0,
                       N_total * (1 - target_inf), theta, grid)
        return sol["informality"]

    if inf_at(lo) <= target_inf + 1e-10:
        return lo

    while inf_at(hi) > target_inf + 1e-10 and hi < 1e6:
        hi *= 2.0

    a, b = lo, hi
    for _ in range(70):
        m = 0.5 * (a + b)
        if inf_at(m) > target_inf:
            a = m
        else:
            b = m
    return b

# ============================================================
# A_req solver (bisection with re-optimized allocation)
# ============================================================
def solve_Areq(groups, hF_cap, Y_target, theta, grid=3001):
    """Find A_mult such that sum Y_g(A*A_mult) = Y_target. Returns %."""

    def Y_at(A_mult):
        total = 0.0
        for pars in groups.values():
            sol = solve_NF(
                pars["N_total"], hF_cap, pars["hI"],
                pars["A"] * A_mult, pars["K"], pars["alpha"],
                pars["omega"], pars["sigma_sub"], pars["eta_I"],
                pars["kappa"], pars["h_star"],
                pars["formal_wedge"], pars["pi_m"],
                pars["gamma_F"], pars["NF_init"], theta, grid)
            total += sol["Y"]
        return total

    Y1 = Y_at(1.0)
    if Y1 >= Y_target:
        return 0.0

    A_lo, A_hi = 1.0, (Y_target / max(Y1, 1e-15)) * 1.3
    for _ in range(35):
        A_mid = 0.5 * (A_lo + A_hi)
        if Y_at(A_mid) < Y_target:
            A_lo = A_mid
        else:
            A_hi = A_mid
        if (A_hi - A_lo) < 1e-5 * A_lo:
            break
    return 100.0 * (0.5 * (A_lo + A_hi) - 1.0)

# ============================================================
# Main calibration
# ============================================================
def load_targets():
    """Load calibration_targets.csv into dict."""
    path = os.path.join(DATA_FINAL, "calibration_targets.csv")
    targets = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            targets[row["target_id"]] = {
                "value": float(row["value"]),
                "source": row["source"],
                "notes": row.get("notes", "")
            }
    return targets


def main():
    print("=" * 60)
    print("CALIBRATION FROM ZERO")
    print("=" * 60)

    # Load targets
    targets = load_targets()
    print(f"  Loaded {len(targets)} calibration targets")

    # Extract values
    alpha = targets["ALPHA"]["value"]
    eta_I = targets["ETA_I"]["value"]
    e_q = targets["E_Q"]["value"]
    h0 = targets["H0"]["value"]
    h1 = targets["H1"]["value"]
    h_star = targets["H_STAR"]["value"]
    hI = targets["HI"]["value"]
    N_total = targets["N_TOTAL"]["value"]
    omega = 0.622  # 1 - narrow informality (PNAD Continua 2025, avg 4q = 0.378)
    sigma_sub = 1.326  # Disciplined by MNR wage premium R=1.40 (midpoint of [1.15,1.55]); at eta_I=0.40, R in [1.15,1.55] -> sigma in [1.116,1.469]

    theta = np.array([
        targets["THETA_36"]["value"],
        targets["THETA_40"]["value"],
        targets["THETA_44"]["value"],
    ])

    share_small = targets["SHARE_SMALL"]["value"]
    share_large = targets["SHARE_LARGE"]["value"]
    inf_small = targets["INF_SMALL"]["value"]
    inf_large = targets["INF_LARGE"]["value"]
    gamma_F_small = targets["GAMMA_F_SMALL"]["value"]
    gamma_F_large = targets["GAMMA_F_LARGE"]["value"]

    # GHH preferences
    sigma_ghh = 1.0  # log utility
    nu_ghh = 2.0     # inverse Frisch (Frisch = 0.5)

    # ================================================================
    # Step 1: Calibrate kappa
    # ================================================================
    h_ref = formal_hours_avg(h0, theta)
    kappa = calibrate_kappa(h_ref, h_star, e_q)
    print(f"\n[1] Kappa calibration:")
    print(f"    h_ref (avg formal hours at h0=44): {h_ref:.3f}")
    print(f"    e_q (hours-output elasticity): {e_q}")
    print(f"    kappa = {kappa:.6e}")
    print(f"    e(36) = {eff(36, kappa, h_star):.4f}")
    print(f"    e(40) = {eff(40, kappa, h_star):.4f}")
    print(f"    e(44) = {eff(44, kappa, h_star):.4f}")

    # ================================================================
    # Step 2: Build groups and calibrate wedges
    # ================================================================
    print(f"\n[2] Group construction and wedge calibration:")

    groups = {}
    group_specs = {
        "Pequenas": {"share": share_small, "inf_target": inf_small,
                     "gamma_F": gamma_F_small, "K_share": 0.35},
        "Grandes":  {"share": share_large, "inf_target": inf_large,
                     "gamma_F": gamma_F_large, "K_share": 0.65},
    }

    common = {
        "A": 1.0, "alpha": alpha, "h0": h0, "h1": h1, "hI": hI,
        "h_star": h_star, "omega": omega, "sigma_sub": sigma_sub,
        "eta_I": eta_I, "kappa": kappa,
    }

    for gname, spec in group_specs.items():
        N_g = N_total * spec["share"]
        K_g = 1.0 * spec["K_share"]

        # First check if wedge=0 gives informality above target
        # If so, need to calibrate pi_m first
        pi_m_g = 0.0
        sol_w0 = solve_NF(N_g, h0, hI, 1.0, K_g, alpha, omega, sigma_sub,
                          eta_I, kappa, h_star, 0.0, pi_m_g, 0.0,
                          N_g * (1 - spec["inf_target"]), theta)
        if sol_w0["informality"] > spec["inf_target"] + 1e-10:
            pi_m_g = calibrate_pi_m(spec["inf_target"], N_g, h0, hI,
                                    1.0, K_g, alpha, omega, sigma_sub,
                                    eta_I, kappa, h_star, theta)
            print(f"    {gname}: pi_m = {pi_m_g:.6f} (needed to reach inf target at wedge=0)")

        # Calibrate wedge
        wedge = calibrate_wedge(spec["inf_target"], N_g, h0, hI,
                                1.0, K_g, alpha, omega, sigma_sub,
                                eta_I, kappa, h_star, pi_m_g, theta)

        # Verify
        sol_verify = solve_NF(N_g, h0, hI, 1.0, K_g, alpha, omega, sigma_sub,
                              eta_I, kappa, h_star, wedge, pi_m_g,
                              spec["gamma_F"], N_g * (1 - spec["inf_target"]), theta)

        groups[gname] = {
            **common,
            "N_total": N_g, "K": K_g,
            "gamma_F": spec["gamma_F"],
            "pi_m": pi_m_g,
            "formal_wedge": wedge,
            "NF_init": N_g * (1 - spec["inf_target"]),
        }

        print(f"    {gname}: N={N_g:.4f}, K={K_g:.2f}, "
              f"wedge={wedge:.4f}, pi_m={pi_m_g:.4f}, "
              f"inf_actual={sol_verify['informality']:.4f} "
              f"(target={spec['inf_target']:.2f})")

    # ================================================================
    # Step 3: Solve baseline
    # ================================================================
    print(f"\n[3] Baseline solution:")
    Y_base_total = 0.0
    C_base_total = 0.0
    hours_base_total = 0.0
    N_base_total = 0.0
    NI_base_total = 0.0

    baseline_solutions = {}
    for gname, pars in groups.items():
        sol = solve_NF(pars["N_total"], h0, hI, pars["A"], pars["K"],
                       pars["alpha"], pars["omega"], pars["sigma_sub"],
                       pars["eta_I"], pars["kappa"], pars["h_star"],
                       pars["formal_wedge"], pars["pi_m"],
                       pars["gamma_F"], pars["NF_init"], theta)
        baseline_solutions[gname] = sol
        Y_base_total += sol["Y"]
        C_base_total += sol["C"]
        hours_base_total += sol["hours_total"]
        N_base_total += pars["N_total"]
        NI_base_total += sol["NI"]

        print(f"    {gname}: Y={sol['Y']:.4f}, NF={sol['NF']:.4f}, "
              f"NI={sol['NI']:.4f}, inf={sol['informality']:.4f}")

    inf_agg = NI_base_total / N_base_total
    h_avg_base = hours_base_total / N_base_total
    print(f"    AGGREGATE: Y={Y_base_total:.4f}, inf={inf_agg:.4f}, "
          f"h_avg={h_avg_base:.2f}")

    # ================================================================
    # Step 4: Calibrate psi (GHH)
    # ================================================================
    w_hourly = (1.0 - alpha) * Y_base_total / (N_base_total * h_avg_base)
    psi = calibrate_psi(w_hourly, h_avg_base, nu_ghh)
    print(f"\n[4] GHH calibration:")
    print(f"    w_hourly = {w_hourly:.6f}")
    print(f"    h_avg = {h_avg_base:.2f}")
    print(f"    psi = {psi:.6e}")

    # ================================================================
    # Step 5: Solve reform (h0 -> h1) and compute A_req
    # ================================================================
    print(f"\n[5] Reform simulation (h={h0} -> h={h1}):")

    # Cap solution (without TFP gain)
    Y_cap_total = 0.0
    C_cap_total = 0.0
    hours_cap_total = 0.0
    NI_cap_total = 0.0
    cap_solutions = {}

    for gname, pars in groups.items():
        sol = solve_NF(pars["N_total"], h1, hI, pars["A"], pars["K"],
                       pars["alpha"], pars["omega"], pars["sigma_sub"],
                       pars["eta_I"], pars["kappa"], pars["h_star"],
                       pars["formal_wedge"], pars["pi_m"],
                       pars["gamma_F"], pars["NF_init"], theta)
        cap_solutions[gname] = sol
        Y_cap_total += sol["Y"]
        C_cap_total += sol["C"]
        hours_cap_total += sol["hours_total"]
        NI_cap_total += sol["NI"]

        print(f"    {gname}: Y={sol['Y']:.4f}, inf={sol['informality']:.4f}")

    inf_cap = NI_cap_total / N_base_total
    dY = (Y_cap_total / Y_base_total - 1) * 100
    dInf = (inf_cap - inf_agg) * 100
    h_avg_cap = hours_cap_total / N_base_total
    Yph_base = Y_base_total / hours_base_total
    Yph_cap = Y_cap_total / hours_cap_total
    dYph = (Yph_cap / Yph_base - 1) * 100

    print(f"    AGGREGATE: Y_cap={Y_cap_total:.4f}, dY={dY:.2f}%, "
          f"dInf={dInf:+.2f}pp, dY/h={dYph:+.2f}%")

    # A_req
    Areq = solve_Areq(groups, h1, Y_base_total, theta)
    print(f"    A_req = {Areq:.2f}%")

    # Per-group A_req
    for gname, pars in groups.items():
        Areq_g = solve_Areq({gname: pars}, h1,
                            baseline_solutions[gname]["Y"], theta)
        print(f"    A_req_{gname} = {Areq_g:.2f}%")

    # ================================================================
    # Step 6: Welfare
    # ================================================================
    print(f"\n[6] Welfare (GHH compensating variation):")
    c_base_pc = C_base_total / N_base_total
    c_cap_pc = C_cap_total / N_base_total

    dcv = compensating_variation(c_base_pc, h_avg_base, c_cap_pc, h_avg_cap, nu_ghh, psi)
    print(f"    C_base/N = {c_base_pc:.4f}, h_base = {h_avg_base:.2f}")
    print(f"    C_cap/N  = {c_cap_pc:.4f}, h_cap  = {h_avg_cap:.2f}")
    print(f"    DeltaCV  = {dcv*100:+.2f}%")

    # Welfare schedule
    print(f"\n    Welfare schedule:")
    print(f"    {'h1':>4}  {'A_req':>8}  {'dY':>8}  {'dCV':>8}  {'dInf':>8}")
    welfare_rows = []
    for h_target in range(44, 29, -1):
        # Cap at h_target
        Y_t = 0.0; C_t = 0.0; hrs_t = 0.0; NI_t = 0.0
        for pars in groups.values():
            sol = solve_NF(pars["N_total"], h_target, hI, pars["A"], pars["K"],
                           pars["alpha"], pars["omega"], pars["sigma_sub"],
                           pars["eta_I"], pars["kappa"], pars["h_star"],
                           pars["formal_wedge"], pars["pi_m"],
                           pars["gamma_F"], pars["NF_init"], theta)
            Y_t += sol["Y"]; C_t += sol["C"]
            hrs_t += sol["hours_total"]; NI_t += sol["NI"]

        Areq_t = solve_Areq(groups, h_target, Y_base_total, theta)
        dY_t = (Y_t / Y_base_total - 1) * 100
        h_avg_t = hrs_t / N_base_total
        c_pc_t = C_t / N_base_total
        dcv_t = compensating_variation(c_base_pc, h_avg_base, c_pc_t, h_avg_t, nu_ghh, psi)
        dInf_t = (NI_t / N_base_total - inf_agg) * 100

        print(f"    {h_target:>4}  {Areq_t:>7.2f}%  {dY_t:>7.2f}%  "
              f"{dcv_t*100:>+7.2f}%  {dInf_t:>+7.2f}pp")

        welfare_rows.append({
            "h1": h_target, "A_req_pct": round(Areq_t, 4),
            "dY_pct": round(dY_t, 4), "dCV_pct": round(dcv_t * 100, 4),
            "dInf_pp": round(dInf_t, 4)
        })

    # ================================================================
    # Step 7: Generate PARAMETER_MASTER_TABLE.csv
    # ================================================================
    print(f"\n[7] Generating PARAMETER_MASTER_TABLE.csv...")

    params = [
        ("alpha", "Capital share", alpha, "proportion", "External",
         "labsh from PWT", targets["ALPHA"]["source"]),
        ("kappa", "Efficiency curvature", kappa, "1/h^2", "Derived from e_q",
         f"e_q={e_q}, h_ref={h_ref:.3f}", "Pencavel (2015)"),
        ("omega", "CES formal weight", omega, "proportion", "External (PNAD-anchored)",
         "1 - narrow informality (avg 4q 2025)", "PNAD Continua 2025"),
        ("sigma_sub", "CES substitution elasticity", sigma_sub, "elasticity",
         "Moment-matched (wage premium)", "MNR wage premium R in [1.15,1.55]",
         "Meghir, Narita, Robin (2015)"),
        ("eta_I", "Informal relative efficiency", eta_I, "proportion", "External",
         "Wage-ratio midpoint (informal/formal) approx 1/3 to 1/2",
         "La Porta & Shleifer (2014) informal/formal wage ratio midpoint"),
        ("e_q", "Hours-output elasticity", e_q, "elasticity", "External",
         "At h_ref=42.24", "Pencavel (2015, Economic Journal)"),
        ("psi", "GHH disutility weight", psi, "model units", "GHH FOC",
         f"w_hourly={w_hourly:.4f}, h_avg={h_avg_base:.2f}", "Calibrated from baseline"),
        ("nu", "Inverse Frisch elasticity", nu_ghh, "dimensionless", "External",
         "Frisch = 0.5", "Standard macro calibration"),
        ("sigma_ghh", "Risk aversion (GHH)", sigma_ghh, "dimensionless", "External",
         "Log utility", "Standard"),
        ("tau_S", "Formal wedge (small firms)", groups["Pequenas"]["formal_wedge"],
         "model units", "Bisection", f"Target inf={inf_small}", "Calibrated"),
        ("tau_L", "Formal wedge (large firms)", groups["Grandes"]["formal_wedge"],
         "model units", "Bisection", f"Target inf={inf_large}", "Calibrated"),
        ("pi_m_S", "Informal cost (small)", groups["Pequenas"]["pi_m"],
         "model units", "Bisection", "Ensures wedge >= 0", "Calibrated"),
        ("pi_m_L", "Informal cost (large)", groups["Grandes"]["pi_m"],
         "model units", "Bisection", "Ensures wedge >= 0", "Calibrated"),
        ("gamma_F_S", "Adjustment cost (small)", gamma_F_small,
         "proportion", "External", "CLT/FGTS effective marginal cost", "RAIS + CLT"),
        ("gamma_F_L", "Adjustment cost (large)", gamma_F_large,
         "proportion", "External", "CLT/FGTS effective marginal cost", "RAIS + CLT"),
        ("N_total", "Total employment (normalized)", N_total,
         "normalized", "External", "Employment-to-population", "PNAD Continua"),
        ("h0", "Baseline hours cap", h0, "hours/week", "Institutional",
         "CLT Art. 58", "Statutory"),
        ("h1", "Reform hours cap", h1, "hours/week", "Policy",
         "PEC 6x1", "Main counterfactual"),
        ("h_star", "Peak-efficiency hours", h_star, "hours/week", "External",
         "International evidence", "Pencavel (2015)"),
        ("hI", "Informal hours", hI, "hours/week", "Assumption",
         "Not subject to cap", "Model assumption"),
    ]

    outpath = os.path.join(DATA_FINAL, "PARAMETER_MASTER_TABLE.csv")
    with open(outpath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["symbol", "name", "value", "unit",
                         "calibration_method", "target_moment", "source"])
        for p in params:
            writer.writerow(p)

    sha = hashlib.sha256(
        open(outpath, "r", encoding="utf-8").read().encode("utf-8")
    ).hexdigest()

    print(f"    Saved: {outpath}")
    print(f"    {len(params)} parameters")
    print(f"    SHA-256: {sha}")

    # ================================================================
    # Step 8: Save results summary
    # ================================================================
    summary = {
        "calibration_date": datetime.datetime.now().isoformat(),
        "targets_file": "data_final/calibration_targets.csv",
        "parameters_file": "data_final/PARAMETER_MASTER_TABLE.csv",
        "key_results": {
            "kappa": kappa,
            "A_req_aggregate_pct": round(Areq, 4),
            "dY_pct": round(dY, 4),
            "dInf_pp": round(dInf, 4),
            "dCV_pct": round(dcv * 100, 4),
            "dYph_pct": round(dYph, 4),
            "psi": psi,
            "wedge_small": groups["Pequenas"]["formal_wedge"],
            "wedge_large": groups["Grandes"]["formal_wedge"],
            "pi_m_small": groups["Pequenas"]["pi_m"],
            "pi_m_large": groups["Grandes"]["pi_m"],
            "inf_aggregate_baseline": round(inf_agg, 4),
            "inf_aggregate_cap": round(inf_cap, 4),
        },
        "welfare_schedule": welfare_rows,
    }

    summary_path = os.path.join(OUTPUT_DIR, "calibration_results.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Results saved to: {summary_path}")

    # ================================================================
    # Comparison with legacy
    # ================================================================
    print(f"\n{'='*60}")
    print(f"COMPARISON WITH LEGACY")
    print(f"{'='*60}")
    print(f"  {'Parameter':<20} {'New':>12} {'Legacy':>12} {'Match':>8}")
    print(f"  {'-'*52}")
    legacy = {
        "kappa": 2.111389e-03,
        "A_req": 8.42,
        "dY": -8.66,
        "e(36)": 0.9668,
        "e(40)": 1.0000,
        "e(44)": 0.9668,
    }
    new_vals = {
        "kappa": kappa,
        "A_req": Areq,
        "dY": dY,
        "e(36)": eff(36, kappa, h_star),
        "e(40)": eff(40, kappa, h_star),
        "e(44)": eff(44, kappa, h_star),
    }
    for key in legacy:
        leg = legacy[key]
        new = new_vals[key]
        match = "OK" if abs(new - leg) / max(abs(leg), 1e-10) < 0.02 else "DIFF"
        print(f"  {key:<20} {new:>12.6f} {leg:>12.6f} {match:>8}")

    return summary


if __name__ == "__main__":
    main()
