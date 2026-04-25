# -*- coding: utf-8 -*-
"""
Unit tests for the 6x1 model modules.

6 tests required by TASKS.md:
  1. test_baseline_reproduces_targets
  2. test_areq_monotonicity
  3. test_sigma_sub_sensitivity
  4. test_hours_distribution_mapping
  5. test_welfare_object
  6. test_small_vs_large_firms_heterogeneity
"""

import sys
import os
import unittest
import numpy as np

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.model.production import production, mpl_L
from src.model.ces_aggregator import ces_agg, wage_premium
from src.model.efficiency import eff, calibrate_kappa, formal_hours_avg, formal_hours_hetero
from src.model.firm_problem import solve_NF
from src.model.calibration import calibrate_wedge, calibrate_pi_m, calibrate_psi
from src.model.areq_solver import solve_Areq
from src.model.welfare import ghh_composite, compensating_variation
from src.model.simulation import load_targets, run_simulation


DATA_FINAL = os.path.join(PROJECT_ROOT, "data_final")


class TestBaselineReproducesTargets(unittest.TestCase):
    """Test 1: Full pipeline reproduces legacy results with sigma=0.80."""

    def setUp(self):
        self.targets = load_targets(DATA_FINAL)

    def test_kappa_value(self):
        theta = np.array([0.085, 0.269, 0.646])
        h_ref = formal_hours_avg(44.0, theta)
        kappa = calibrate_kappa(h_ref, 40.0, 0.60)
        self.assertAlmostEqual(kappa, 2.110e-03, places=5,
                               msg="kappa must match legacy 2.110e-03")

    def test_efficiency_symmetry(self):
        kappa = calibrate_kappa(42.244, 40.0, 0.60)
        e36 = eff(36, kappa, 40.0)
        e44 = eff(44, kappa, 40.0)
        self.assertAlmostEqual(e36, e44, places=6,
                               msg="e(36) must equal e(44) by symmetry around h*=40")
        self.assertAlmostEqual(eff(40, kappa, 40.0), 1.0, places=10,
                               msg="e(h*) must equal 1.0")

    def test_full_pipeline_central(self):
        """Run full simulation at the current central calibration
        (sigma_sub=1.326, disciplined by the MNR wage premium R=1.40)."""
        result = run_simulation(self.targets, sigma_sub=1.326)
        r = result["results"]
        self.assertAlmostEqual(r["A_req_pct"], 8.18, delta=0.10,
                               msg="A_req must be ~8.18% at the central sigma_sub=1.326")
        self.assertAlmostEqual(r["dY_pct"], -8.02, delta=0.10,
                               msg="dY must be ~-8.02% at the central sigma_sub=1.326")
        self.assertAlmostEqual(r["dCV_pct"], -3.63, delta=0.15,
                               msg="dCV must be ~-3.63% at the central sigma_sub=1.326")

    def test_full_pipeline_high_sigma(self):
        """Stress check at sigma_sub=1.469 (top of MNR-disciplined interval)."""
        result = run_simulation(self.targets, sigma_sub=1.469)
        r = result["results"]
        self.assertAlmostEqual(r["A_req_pct"], 8.58, delta=0.15,
                               msg="A_req must be ~8.58% at sigma_sub=1.469")
        self.assertGreater(r["dInf_pp"], 0.0,
                           msg="dInf must be positive in the high-sigma regime")


class TestAreqMonotonicity(unittest.TestCase):
    """Test 2: A_req increases as hours cap decreases."""

    def setUp(self):
        self.targets = load_targets(DATA_FINAL)

    def test_areq_decreasing_with_hours(self):
        """A_req(h=30) > A_req(h=36) > A_req(h=40) > A_req(h=44)=0"""
        from src.model.groups import build_groups
        groups, kappa, theta = build_groups(self.targets, sigma_sub=0.60)

        # Baseline Y
        Y_base = 0.0
        for pars in groups.values():
            sol = solve_NF(pars["N_total"], 44, pars["hI"], pars["A"],
                           pars["K"], pars["alpha"], pars["omega"],
                           pars["sigma_sub"], pars["eta_I"], pars["kappa"],
                           pars["h_star"], pars["formal_wedge"], pars["pi_m"],
                           pars["gamma_F"], pars["NF_init"], theta)
            Y_base += sol["Y"]

        areqs = []
        for h in [44, 40, 36, 30]:
            areqs.append(solve_Areq(groups, h, Y_base, theta))

        # Should be strictly increasing (more TFP needed for lower hours)
        for i in range(len(areqs) - 1):
            self.assertLess(areqs[i], areqs[i + 1],
                            msg=f"A_req must increase as hours decrease: "
                                f"h={[44,40,36,30][i]} A_req={areqs[i]:.2f} vs "
                                f"h={[44,40,36,30][i+1]} A_req={areqs[i+1]:.2f}")


class TestSigmaSubSensitivity(unittest.TestCase):
    """Test 3: A_req varies with sigma_sub in expected direction."""

    def setUp(self):
        self.targets = load_targets(DATA_FINAL)

    def test_areq_increases_with_sigma(self):
        """Higher sigma -> easier substitution -> larger informal response -> higher A_req."""
        areqs = {}
        for sigma in [0.50, 0.60, 0.80, 1.50]:
            result = run_simulation(self.targets, sigma_sub=sigma)
            areqs[sigma] = result["results"]["A_req_pct"]

        for s_lo, s_hi in [(0.50, 0.60), (0.60, 0.80), (0.80, 1.50)]:
            self.assertLess(areqs[s_lo], areqs[s_hi],
                            msg=f"A_req(sigma={s_lo}) < A_req(sigma={s_hi}): "
                                f"{areqs[s_lo]:.2f} vs {areqs[s_hi]:.2f}")

    def test_disciplined_range(self):
        """A_req in roughly [7.5, 8.6] for sigma in the MNR-disciplined
        interval [1.116, 1.469] (R in [1.15, 1.55] at eta_I=0.40)."""
        for sigma, expected_lo, expected_hi in [(1.116, 7.0, 8.0), (1.469, 8.0, 9.0)]:
            result = run_simulation(self.targets, sigma_sub=sigma)
            areq = result["results"]["A_req_pct"]
            self.assertGreater(areq, expected_lo,
                               msg=f"A_req too low at sigma={sigma}")
            self.assertLess(areq, expected_hi,
                            msg=f"A_req too high at sigma={sigma}")


class TestHoursDistributionMapping(unittest.TestCase):
    """Test 4: Hours distribution theta maps correctly."""

    def test_theta_sums_to_one(self):
        theta = np.array([0.085, 0.269, 0.646])
        self.assertAlmostEqual(sum(theta), 1.0, places=10)

    def test_formal_hours_avg_at_44(self):
        """With cap=44, all bins are uncapped: avg = sum(theta*bins)."""
        theta = np.array([0.085, 0.269, 0.646])
        avg = formal_hours_avg(44.0, theta)
        expected = 0.085 * 36 + 0.269 * 40 + 0.646 * 44
        self.assertAlmostEqual(avg, expected, places=6)
        self.assertAlmostEqual(avg, 42.244, places=2)

    def test_formal_hours_avg_at_36(self):
        """With cap=36, all bins capped to 36: avg = 36."""
        theta = np.array([0.085, 0.269, 0.646])
        avg = formal_hours_avg(36.0, theta)
        self.assertAlmostEqual(avg, 36.0, places=6)

    def test_formal_hours_avg_at_40(self):
        """With cap=40, 44-bin capped to 40."""
        theta = np.array([0.085, 0.269, 0.646])
        avg = formal_hours_avg(40.0, theta)
        expected = 0.085 * 36 + 0.269 * 40 + 0.646 * 40
        self.assertAlmostEqual(avg, expected, places=6)

    def test_effective_hours_at_hstar(self):
        """At h*=40 with cap=40, efficiency=1 for 40h bins."""
        kappa = 2.11e-03
        theta = np.array([0.085, 0.269, 0.646])
        avg_h, eff_h = formal_hours_hetero(40.0, kappa, 40.0, theta)
        # 36h bin has e(36) < 1, so eff_h < avg_h
        self.assertLess(eff_h, avg_h,
                        msg="Effective hours should be less than average "
                            "when some bins deviate from h*")


class TestWelfareObject(unittest.TestCase):
    """Test 5: GHH welfare computations."""

    def test_ghh_composite_positive(self):
        """Composite must be positive for reasonable parameters."""
        comp = ghh_composite(C=1.0, h=40.0, nu=2.0, psi=1e-5)
        self.assertGreater(comp, 0.0)

    def test_cv_zero_same_allocation(self):
        """CV = 0 when baseline = reform."""
        cv = compensating_variation(1.0, 40.0, 1.0, 40.0, 2.0, 1e-5)
        self.assertAlmostEqual(cv, 0.0, places=10)

    def test_cv_negative_when_consumption_drops(self):
        """CV < 0 when consumption drops and hours unchanged."""
        cv = compensating_variation(1.0, 40.0, 0.9, 40.0, 2.0, 1e-5)
        self.assertLess(cv, 0.0)

    def test_cv_positive_when_hours_drop_enough(self):
        """CV > 0 when hours drop substantially and consumption unchanged."""
        cv = compensating_variation(1.0, 44.0, 1.0, 36.0, 2.0, 1e-5)
        self.assertGreater(cv, 0.0)

    def test_psi_calibration_roundtrip(self):
        """psi from FOC should reproduce the hourly wage."""
        w = 0.05
        h = 42.0
        nu = 2.0
        psi = calibrate_psi(w, h, nu)
        w_implied = psi * h**nu
        self.assertAlmostEqual(w, w_implied, places=10)


class TestSmallVsLargeFirmsHeterogeneity(unittest.TestCase):
    """Test 6: Small firms have higher informality than large firms."""

    def setUp(self):
        self.targets = load_targets(DATA_FINAL)

    def test_informality_heterogeneity(self):
        """Small firms: ~50% informal. Large firms: ~20% informal."""
        result = run_simulation(self.targets, sigma_sub=1.326)
        sol_P = result["baseline"]["solutions"]["Pequenas"]
        sol_G = result["baseline"]["solutions"]["Grandes"]

        self.assertAlmostEqual(sol_P["informality"], 0.50, delta=0.02,
                               msg="Small firms informality should be ~50%")
        self.assertAlmostEqual(sol_G["informality"], 0.20, delta=0.02,
                               msg="Large firms informality should be ~20%")

    def test_wedge_heterogeneity(self):
        """Small firms should have higher wedge (more costly to formalize).

        At the central sigma_sub=1.326 the calibration loads heterogeneity
        onto the formal wedge (tau_S >> tau_L); at very low sigma it instead
        loads heterogeneity onto the informal cost pi_m, so the wedge
        ordering can flip — the test pins the central case.
        """
        result = run_simulation(self.targets, sigma_sub=1.326)
        wedge_P = result["groups"]["Pequenas"]["formal_wedge"]
        wedge_G = result["groups"]["Grandes"]["formal_wedge"]
        self.assertGreater(wedge_P, wedge_G,
                           msg="Small firms must have higher formal wedge")

    def test_aggregate_informality(self):
        """Aggregate informality should be between small and large."""
        result = run_simulation(self.targets, sigma_sub=1.326)
        inf_agg = result["baseline"]["inf"]
        inf_P = result["baseline"]["solutions"]["Pequenas"]["informality"]
        inf_G = result["baseline"]["solutions"]["Grandes"]["informality"]
        self.assertGreater(inf_agg, inf_G)
        self.assertLess(inf_agg, inf_P)


if __name__ == "__main__":
    unittest.main()
