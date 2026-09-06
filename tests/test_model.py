"""Accounting, optimization and welfare tests; no fitted legacy output targets.

Legacy assertions that forced A_req back to manuscript values are archived
with the original package. These tests independently check the mathematics.
"""
import copy
import os
import sys
import unittest
import numpy as np
from scipy.optimize import minimize_scalar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,ROOT)
from src.model.efficiency import eff,calibrate_kappa,formal_hours_avg,formal_hours_hetero
from src.model.ces_aggregator import ces_agg,wage_premium
from src.model.firm_problem import solve_NF,evaluate_at_NF,production_marginals,solve_group
from src.model.groups import build_groups,formal_to_total_shares
from src.model.calibration import calibrate_wedges
from src.model.areq_solver import solve_Areq
from src.model.simulation import load_targets,run_simulation
from src.model.welfare import ghh_composite,ghh_change,consumption_equivalent,compensating_variation

TARGETS = load_targets(os.path.join(ROOT,"data_final"))


class EmploymentAccounting(unittest.TestCase):
    def test_formal_shares_recover_aggregate_409158_percent(self):
        shares = formal_to_total_shares({"S":.59,"L":.41},{"S":.50,"L":.20})
        agg = .5*shares["S"]+.2*shares["L"]
        self.assertAlmostEqual(100*agg,40.91580502215657,places=11)
        self.assertNotAlmostEqual(agg,.377,places=4)
        formal = {g:shares[g]*(1.-i) for g,i in {"S":.5,"L":.2}.items()}
        self.assertAlmostEqual(formal["S"]/sum(formal.values()),.59,places=13)

    def test_baseline_hits_each_target_and_preserves_formal_shares(self):
        result = run_simulation(TARGETS,sigma_sub=1.326)
        groups = result["groups"]
        for g,p in groups.items():
            self.assertAlmostEqual(result["baseline"]["solutions"][g]["informality"],
                                   p["inf_target"],places=10)
            self.assertAlmostEqual(p["share_formal_implied"],p["input_share"],places=12)
        self.assertAlmostEqual(sum(p["N_total"] for p in groups.values()),
                               TARGETS["N_TOTAL"]["value"],places=13)

    def test_default_group_specs_read_changed_targets(self):
        target = copy.deepcopy(TARGETS)
        target["SHARE_SMALL"]["value"] = .32
        target["SHARE_LARGE"]["value"] = .68
        groups,_,_ = build_groups(target,sigma_sub=1.326)
        self.assertAlmostEqual(groups["Pequenas"]["share_formal_implied"],.32,places=12)

    def test_invalid_share_inputs_fail(self):
        with self.assertRaises(ValueError):
            formal_to_total_shares({"S":.7,"L":.4},{"S":.5,"L":.2})


class EfficiencyAndCES(unittest.TestCase):
    def test_two_modes_share_peak_and_above_peak_technology(self):
        for h in [40.,41.7,44.,52.]:
            self.assertAlmostEqual(eff(h,.002,40.,"bilateral"),
                                   eff(h,.002,40.,"flat_below"),places=14)
        self.assertEqual(eff(36.,.002,40.,"flat_below"),1.)
        self.assertLess(eff(36.,.002,40.,"bilateral"),1.)

    def test_local_elasticity_calibration_by_numerical_derivative(self):
        href = 42.244
        kappa = calibrate_kappa(href,40.,.6)
        eps = 1e-5
        derivative = (np.log((href+eps)*eff(href+eps,kappa,40.))-
                      np.log((href-eps)*eff(href-eps,kappa,40.)))/(2*eps)*href
        self.assertAlmostEqual(derivative,.6,places=7)

    def test_no_invented_curvature_below_fatigue_peak(self):
        with self.assertRaises(ValueError):
            calibrate_kappa(38.,40.,.6,"flat_below")
        with self.assertRaises(ValueError):
            calibrate_kappa(40.,40.,.6)

    def test_generic_hours_distribution_and_external_anchor(self):
        target = copy.deepcopy(TARGETS)
        target["H_REF_EFFICIENCY"] = {"value":42.244}
        result = run_simulation(target,theta=[.25,.25,.5],hours_bins=[20.,35.,48.],
                                efficiency_mode="flat_below",sigma_sub=1.326)
        self.assertAlmostEqual(result["baseline"]["solutions"]["Pequenas"]["hF_avg"],
                               .25*20+.25*35+.5*44,places=12)
        self.assertTrue(np.isfinite(result["results"]["A_req_pct"]))

    def test_hours_weights_validate_accounting_only(self):
        with self.assertRaises(ValueError):
            formal_hours_avg(44.,[.2,.3,.3])
        with self.assertRaises(ValueError):
            formal_hours_avg(44.,[-.2,.3,.9])
        self.assertEqual(formal_hours_avg(36.,[.085,.269,.646]),36.)

    def test_ces_zero_input_limits_and_homogeneity(self):
        self.assertEqual(ces_agg(0.,2.,.6,.8),0.)
        self.assertEqual(ces_agg(0.,2.,.6,1.),0.)
        self.assertGreater(ces_agg(0.,2.,.6,1.3),0.)
        self.assertEqual(ces_agg(0.,0.,.6,1.3),0.)
        for sigma in [.4,.9,1.,1.326,2.]:
            self.assertAlmostEqual(ces_agg(3.*2.,3.*7.,.6,sigma),
                                   3.*ces_agg(2.,7.,.6,sigma),places=11)

    def test_ces_cobb_douglas_continuity(self):
        expected = 2.**.6*7.**.4
        for sigma in [1.-1e-9,1.,1.+1e-9]:
            self.assertAlmostEqual(ces_agg(2.,7.,.6,sigma),expected,places=7)

    def test_hourly_and_weekly_premiums_are_distinct(self):
        weekly = wage_premium(.2,.1,39.,42.,.4,.622,1.326)
        hourly = wage_premium(.2,.1,39.,42.,.4,.622,1.326,
                              basis="hourly",hF_avg=40.,hI_avg=44.)
        self.assertAlmostEqual(hourly,weekly*44./40.,places=12)


class ContinuousOptimization(unittest.TestCase):
    def make_args(self,sigma=1.326,mode="bilateral"):
        return dict(N_total=.59,hF=36.,hI=44.,A=1.,K=1.,alpha=.35,
                    omega=.622,sigma_sub=sigma,eta_I=.4,kappa=.0021,h_star=40.,
                    formal_wedge=2.,pi_m=.1,gamma_F=.12,NF_prev=.3,
                    theta=[.085,.269,.646],efficiency_mode=mode)

    def test_continuous_optimum_beats_independent_scalar_and_dense_grid(self):
        for sigma in [.55,1.,1.326,1.8]:
            for mode in ["bilateral","flat_below"]:
                args = self.make_args(sigma,mode)
                sol = solve_NF(**args)
                objective = lambda n:evaluate_at_NF(n,**args)["objective"]
                opt = minimize_scalar(lambda n:-objective(n),bounds=(0.,.59),
                                       method="bounded",options={"xatol":1e-12})
                self.assertAlmostEqual(sol["objective"],-opt.fun,places=9)
                for n in np.linspace(0.,.59,51):
                    self.assertGreaterEqual(sol["objective"]+1e-10,objective(n))
                self.assertLess(sol["kkt_violation"],1e-8)
                self.assertGreaterEqual(sol["NF"],0.)
                self.assertLessEqual(sol["NF"],.59)

    def test_grid_argument_does_not_change_continuous_solution(self):
        args = self.make_args()
        self.assertAlmostEqual(solve_NF(**args,grid=7)["NF"],
                               solve_NF(**args,grid=100001)["NF"],places=14)

    def test_analytic_production_marginals_match_finite_difference(self):
        args = self.make_args()
        hf,hi = 35.,42.
        params = dict(hF_eff=hf,hI_eff=hi,eta_I=.4,A=1.,K=1.,alpha=.35,
                      omega=.622,sigma_sub=1.326)
        mp = production_marginals(.3,.29,**params)
        eps = 1e-6
        yplus = production_marginals(.3+eps,.29,**params)["Y"]
        yminus = production_marginals(.3-eps,.29,**params)["Y"]
        self.assertAlmostEqual(mp["MP_NF"],(yplus-yminus)/(2*eps),places=6)

    def test_explicit_lower_and_upper_boundaries(self):
        lower_args = self.make_args()
        lower_args.update(A=0.,formal_wedge=5.,pi_m=0.,gamma_F=0.)
        lower = solve_NF(**lower_args)
        self.assertEqual(lower["NF"],0.)
        self.assertEqual(lower["boundary"],"lower")
        self.assertEqual(lower["kkt_violation"],0.)
        upper_args = self.make_args()
        upper_args.update(A=0.,formal_wedge=0.,pi_m=5.,gamma_F=0.)
        upper = solve_NF(**upper_args)
        self.assertEqual(upper["NI"],0.)
        self.assertEqual(upper["boundary"],"upper")
        self.assertEqual(upper["kkt_violation"],0.)

    def test_wedge_normalization_and_exact_foc(self):
        for sigma in [.5,1.,1.326,1.8]:
            for mode in ["bilateral","flat_below"]:
                groups,_,theta = build_groups(TARGETS,sigma_sub=sigma,
                                              efficiency_mode=mode)
                for p in groups.values():
                    self.assertGreaterEqual(p["formal_wedge"],0.)
                    self.assertGreaterEqual(p["pi_m"],0.)
                    self.assertEqual(p["formal_wedge"]*p["pi_m"],0.)
                    sol = solve_group(p,TARGETS["H0"]["value"],theta)
                    self.assertAlmostEqual(sol["NF"],p["NF_init"],places=10)

    def test_resource_constraint_and_transfer_accounting(self):
        args = self.make_args()
        transfer = solve_NF(**args)
        resource = solve_NF(**args,resource_costs=True)
        self.assertAlmostEqual(transfer["C"]+transfer["adj"],transfer["Y"],places=12)
        self.assertAlmostEqual(resource["C"]+resource["adj"]+resource["phi"]+
                               resource["formal_payment"],resource["Y"],places=12)
        self.assertAlmostEqual(transfer["NF"],resource["NF"],places=14)


class RestorationAndDecomposition(unittest.TestCase):
    def test_exact_restoration_and_reoptimization_at_each_productivity(self):
        for cap in [40.,36.]:
            for mode in ["bilateral","flat_below"]:
                t = copy.deepcopy(TARGETS)
                t["H1"]["value"] = cap
                r = run_simulation(t,sigma_sub=1.326,efficiency_mode=mode)
                d = r["A_req_details"]
                self.assertLess(abs(d["relative_error"]),1e-10)
                self.assertAlmostEqual(d["output"],r["baseline"]["Y"],places=9)
                self.assertTrue(any(abs(d["allocations"][g]["NF"]-
                                        r["reform"]["solutions"][g]["NF"])>1e-7
                                    for g in r["groups"]))
                for sol in d["allocations"].values():
                    self.assertLess(sol["kkt_violation"],1e-8)

    def test_frozen_compensation_preserves_baseline_composition(self):
        r = run_simulation(TARGETS,sigma_sub=1.326)
        d = r["A_req_frozen_details"]
        for g,sol in d["allocations"].items():
            self.assertAlmostEqual(sol["NF"],r["baseline"]["solutions"][g]["NF"],places=12)
        self.assertAlmostEqual(d["output"],r["baseline"]["Y"],places=10)

    def test_decomposition_same_denominator_and_telescoping_levels(self):
        for mode in ["bilateral","flat_below"]:
            r = run_simulation(TARGETS,sigma_sub=1.326,efficiency_mode=mode)
            d = r["decomposition"]
            self.assertAlmostEqual(d["hours_pct"]+d["efficiency_pct"]+
                                   d["reallocation_pct"],r["results"]["dY_pct"],places=11)
            self.assertAlmostEqual(d["total_pct"],r["results"]["dY_pct"],places=11)
            self.assertEqual(d["levels"]["baseline"],r["baseline"]["Y"])
            self.assertEqual(d["levels"]["reallocation"],r["reform"]["Y"])
            self.assertEqual(d["order"],["physical_hours","efficiency",
                                        "formal_informal_reallocation"])

    def test_unchanged_hours_zero_output_decomposition_and_welfare(self):
        t = copy.deepcopy(TARGETS)
        t["H1"]["value"] = t["H0"]["value"]
        r = run_simulation(t,sigma_sub=1.326)
        for key in ["dY_pct","dGHH_pct","CE_pct","A_req_pct","A_req_frozen_pct"]:
            self.assertAlmostEqual(r["results"][key],0.,places=10)
        for key in ["hours_pct","efficiency_pct","reallocation_pct"]:
            self.assertAlmostEqual(r["decomposition"][key],0.,places=10)

    def test_signed_compensation_when_output_rises(self):
        r = run_simulation(TARGETS,sigma_sub=1.326)
        d = solve_Areq(r["groups"],36.,r["reform"]["Y"]*.95,r["theta"],
                       composition="frozen",return_details=True)
        self.assertLess(d["A_req_pct"],0.)
        self.assertLess(abs(d["relative_error"]),1e-10)


class WelfareDefinitions(unittest.TestCase):
    def test_consumption_equivalent_restores_exact_ghh_level(self):
        c0,c1,h0,h1,nu,psi = 2.,1.85,44.,36.,2.,1e-5
        ce = consumption_equivalent(c0,h0,c1,h1,nu,psi)
        self.assertAlmostEqual(ghh_composite(c0*(1.+ce),h0,nu,psi),
                               ghh_composite(c1,h1,nu,psi),places=13)
        expected = (c1-c0-psi*h1**3/3+psi*h0**3/3)/c0
        self.assertAlmostEqual(ce,expected,places=13)

    def test_ghh_percentage_is_not_ce(self):
        ce = consumption_equivalent(2.,44.,1.85,36.,2.,1e-5)
        ghh = ghh_change(2.,44.,1.85,36.,2.,1e-5)
        self.assertNotAlmostEqual(ce,ghh,places=5)
        self.assertAlmostEqual(ce,compensating_variation(2.,44.,1.85,36.,2.,1e-5),places=14)

    def test_equal_hours_ce_equals_consumption_percent(self):
        self.assertAlmostEqual(consumption_equivalent(2.,40.,1.8,40.,2.,1e-5),-.1,places=14)

    def test_invalid_denominators_not_silently_clipped(self):
        with self.assertRaises(ValueError):
            consumption_equivalent(0.,40.,1.,36.,2.,1e-5)
        with self.assertRaises(ValueError):
            ghh_change(.01,44.,.02,36.,2.,1.)


if __name__ == "__main__":
    unittest.main()

