"""Independent tests of the conditional gross-pay bridge and firm aggregation."""
import copy
import os
import sys
import unittest
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,ROOT)
from src.model.simulation import load_targets,run_simulation
from src.model.firm_problem import production_marginals
from src.model.efficiency import formal_hours_hetero,eff
from src.model.ces_aggregator import wage_premium
from src.calibration.wage_bridge import aggregate_bridge,calibrate_omega

TARGETS = load_targets(os.path.join(ROOT,"data_final"))


class WageBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim = run_simulation(TARGETS,sigma_sub=1.326,omega=.622)
        cls.bridge = aggregate_bridge(cls.sim)

    def test_each_firm_payroll_obeys_euler_labor_share(self):
        for row in self.bridge["groups"]:
            p = self.sim["groups"][row["group"]]
            y = self.sim["baseline"]["solutions"][row["group"]]["Y"]
            self.assertAlmostEqual(row["payroll_formal"]+row["payroll_informal"],
                                   (1.-p["alpha"])*y,places=11)
        total = self.bridge["totals"]
        self.assertAlmostEqual(total["payroll_formal"]+total["payroll_informal"],
                               (1.-TARGETS["ALPHA"]["value"])*self.sim["baseline"]["Y"],
                               places=11)

    def test_bridge_marginals_match_independent_core_derivatives(self):
        for row in self.bridge["groups"]:
            p = self.sim["groups"][row["group"]]
            s = self.sim["baseline"]["solutions"][row["group"]]
            hbar,hf = formal_hours_hetero(p["h0"],p["kappa"],p["h_star"],p["theta"],
                                         p["efficiency_mode"],p["hours_bins"])
            hi = p["hI"]*eff(p["hI"],p["kappa"],p["h_star"],p["efficiency_mode"])
            mp = production_marginals(s["NF"],s["NI"],hf,hi,p["eta_I"],
                                      p["A"],p["K"],p["alpha"],p["omega"],p["sigma_sub"])
            self.assertAlmostEqual(row["weekly_formal"],mp["MP_NF"],places=11)
            self.assertAlmostEqual(row["weekly_informal"],mp["MP_NI"],places=11)
            self.assertAlmostEqual(row["hourly_formal"],mp["MP_NF"]/hbar,places=11)

    def test_payroll_weighting_differs_from_ces_of_aggregated_inputs(self):
        p = next(iter(self.sim["groups"].values()))
        total = self.bridge["totals"]
        _,hf = formal_hours_hetero(p["h0"],p["kappa"],p["h_star"],p["theta"])
        hi = p["hI"]*eff(p["hI"],p["kappa"],p["h_star"])
        incorrect_aggregate_ces = wage_premium(total["NF"],total["NI"],hf,hi,
                                               p["eta_I"],p["omega"],p["sigma_sub"])
        self.assertGreater(abs(incorrect_aggregate_ces-self.bridge["weekly_ratio"]),.01)
        formal_mean = sum(row["NF"]*row["weekly_formal"] for row in self.bridge["groups"])/total["NF"]
        informal_mean = sum(row["NI"]*row["weekly_informal"] for row in self.bridge["groups"])/total["NI"]
        self.assertAlmostEqual(self.bridge["weekly_ratio"],formal_mean/informal_mean,places=12)

    def test_hourly_conversion_uses_physical_not_effective_hours(self):
        total = self.bridge["totals"]
        hf = total["physical_hours_formal"]/total["NF"]
        hi = total["physical_hours_informal"]/total["NI"]
        self.assertAlmostEqual(self.bridge["hourly_ratio"],
                               self.bridge["weekly_ratio"]*hi/hf,places=12)
        self.assertNotAlmostEqual(self.bridge["hourly_ratio"],self.bridge["weekly_ratio"],places=5)

    def test_ratio_of_payroll_per_hours_is_not_mean_person_hourly_pay(self):
        # Survey estimands must be distinguished: mean(r/h) != sum(r)/sum(h).
        earnings,hours,weights = np.array([100.,500.]),np.array([20.,50.]),np.array([1.,3.])
        ratio_of_sums = np.dot(weights,earnings)/np.dot(weights,hours)
        mean_individual_hourly = np.dot(weights,earnings/hours)/sum(weights)
        self.assertNotAlmostEqual(ratio_of_sums,mean_individual_hourly,places=5)

    def test_conditional_omega_restores_hourly_target_at_fixed_sigma(self):
        for mode in ["bilateral","flat_below"]:
            fit = calibrate_omega(TARGETS,1.4,sigma_sub=1.326,measure="hourly",
                                  efficiency_mode=mode)
            self.assertEqual(fit["sigma_sub"],1.326)
            self.assertLess(abs(fit["residual"]),1e-8)
            sim = run_simulation(TARGETS,sigma_sub=1.326,omega=fit["omega"],
                                  efficiency_mode=mode)
            self.assertAlmostEqual(aggregate_bridge(sim)["hourly_ratio"],1.4,places=8)
            self.assertGreater(abs(fit["omega"]-(1.-sim["baseline"]["inf"])),1e-3)
            self.assertEqual(fit["status"],"conditional_calibration_not_joint_identification")

    def test_weekly_target_is_not_silently_treated_as_hourly(self):
        hourly = calibrate_omega(TARGETS,1.4,measure="hourly")
        weekly = calibrate_omega(TARGETS,1.4,measure="weekly")
        self.assertGreater(abs(hourly["omega"]-weekly["omega"]),1e-3)
        self.assertLess(abs(weekly["residual"]),1e-8)

    def test_incorrect_wage_measure_or_target_is_rejected(self):
        with self.assertRaises(ValueError):
            calibrate_omega(TARGETS,1.4,measure="unspecified")
        with self.assertRaises(ValueError):
            calibrate_omega(TARGETS,-1.,measure="hourly")

    def test_generic_hours_distribution_has_explicit_reference(self):
        target = copy.deepcopy(TARGETS)
        target["H_REF_EFFICIENCY"] = {"value":42.244}
        fit = calibrate_omega(target,1.4,measure="hourly",theta=[.2,.3,.5],
                              hours_bins=[25.,35.,45.],efficiency_mode="flat_below")
        self.assertLess(abs(fit["residual"]),1e-8)


if __name__ == "__main__":
    unittest.main()

