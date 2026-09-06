"""Economic invariants for sector-specific distributions and aggregation."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from src.model.firm_problem import solve_group
from src.model.simulation import simulate_groups
from src.sectoral.model.inputs import load_empirical_facts, load_reprocessed_facts
from src.sectoral.model.workers_affected import compute_exposure
from src.sectoral.model.sector_model import (
    load_sectoral_facts, load_national_targets, build_sector_params,
    run_sectoral_simulation,
)

ROOT = Path(__file__).resolve().parents[1]


class SectoralCorrectedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.facts = load_sectoral_facts(ROOT / "data_final")
        cls.targets = load_national_targets(ROOT / "data_final")
        cls.params = {}
        cls.results = {}
        for mode in ("bilateral", "flat_below"):
            params, kappa = build_sector_params(copy.deepcopy(cls.facts), cls.targets,
                                                efficiency_mode=mode)
            cls.params[mode] = params
            cls.results[mode] = run_sectoral_simulation(params, kappa, 36.)

    def test_sector_informality_and_total_employment(self):
        for mode, result in self.results.items():
            pars = self.params[mode]
            N = sum(p["N_total"] for p in pars.values())
            self.assertAlmostEqual(N, self.targets["N_TOTAL"], places=12)
            expected = sum(p["N_total"] * p["inf_target"] for p in pars.values()) / N
            self.assertAlmostEqual(result["aggregate"]["inf_base"], expected, places=10)
            for name, p in pars.items():
                self.assertAlmostEqual(result["sectors"][name]["inf_base"], p["inf_target"], places=10)
                self.assertAlmostEqual(p["formal_wedge"] * p["pi_m"], 0., places=12)

    def test_different_sector_distributions_not_first_sector_for_all(self):
        result = self.results["bilateral"]["simulation"]
        parameters = self.params["bilateral"]
        for name, p in parameters.items():
            mean = float(np.dot(p["theta"], np.minimum(p["hours_bins"], p["h0"])))
            self.assertAlmostEqual(result["baseline"]["solutions"][name]["hF_avg"], mean, places=12)
        means = [s["hF_avg"] for s in result["baseline"]["solutions"].values()]
        self.assertGreater(max(means) - min(means), 0.1)

    def test_continuous_optima_and_endpoints(self):
        for result in self.results.values():
            for stage in ("baseline", "reform"):
                for solution in result["simulation"][stage]["solutions"].values():
                    self.assertLess(solution["kkt_violation"], 1e-8)
                    for boundary_objective in solution["boundary_objectives"]:
                        self.assertGreaterEqual(solution["objective"] + 1e-10, boundary_objective)

    def test_both_compensations_restore_output_and_reoptimize(self):
        for result in self.results.values():
            sim = result["simulation"]
            for key in ("A_req_details", "A_req_frozen_details"):
                restored = sim[key]
                self.assertAlmostEqual(restored["output"] / sim["baseline"]["Y"], 1., places=9)
            changed = []
            for name in sim["groups"]:
                nf0 = sim["baseline"]["solutions"][name]["NF"]
                nf_frozen = sim["A_req_frozen_details"]["allocations"][name]["NF"]
                self.assertAlmostEqual(nf_frozen, nf0, places=12)
                changed.append(abs(sim["A_req_details"]["allocations"][name]["NF"] -
                                   sim["reform"]["solutions"][name]["NF"]))
            self.assertGreater(max(changed), 1e-5)

    def test_same_denominator_decomposition_and_sector_addition(self):
        for result in self.results.values():
            aggregate = result["aggregate"]
            for row in [aggregate, *result["sectors"].values()]:
                d = row["decomposition"]
                self.assertAlmostEqual(d["hours_pct"] + d["efficiency_pct"] + d["reallocation_pct"],
                                       row["dY_pct"], places=10)
                level = d["levels"]
                self.assertAlmostEqual(d["efficiency_pct"],
                                       100*(level["efficiency"]-level["physical_hours"])/row["Y_base"], places=12)
            self.assertAlmostEqual(sum(r["contribution_to_dY"] for r in result["sectors"].values()),
                                   aggregate["dY_pct"], places=10)

    def test_consumption_equivalent_uses_consumption_denominator(self):
        for result in self.results.values():
            sim = result["simulation"]
            N = sum(p["N_total"] for p in sim["groups"].values())
            c0, c1 = sim["baseline"]["C"]/N, sim["reform"]["C"]/N
            h0, h1, psi, nu = sim["baseline"]["h_avg"], sim["reform"]["h_avg"], sim["psi"], sim["nu_ghh"]
            v0, v1 = psi*h0**(1+nu)/(1+nu), psi*h1**(1+nu)/(1+nu)
            numerator = c1-c0-v1+v0
            self.assertAlmostEqual(sim["results"]["CE_pct"], 100*numerator/c0, places=11)
            self.assertAlmostEqual(sim["results"]["dGHH_pct"], 100*numerator/(c0-v0), places=11)

    def test_resource_accounting_and_fixed_capital(self):
        pars = copy.deepcopy(self.params["bilateral"])
        for p in pars.values():
            solution = solve_group(p, 36., p["theta"])
            self.assertAlmostEqual(solution["C"] + solution["adj"], solution["Y"], places=12)
            p["resource_costs"] = True
            resource = solve_group(p, 36., p["theta"])
            self.assertAlmostEqual(resource["C"] + resource["adj"] + resource["phi"] +
                                   resource["formal_payment"], resource["Y"], places=12)
            self.assertEqual(solution["NF"], resource["NF"])

    def test_legacy_rounding_normalized_explicitly(self):
        facts = load_empirical_facts(ROOT / "data_final")
        self.assertAlmostEqual(sum(s["lambda_s"] for s in facts.values()), 1., places=12)
        self.assertAlmostEqual(facts["agriculture"]["raw_employment_share_sum"], 1.0001, places=12)
        self.assertTrue(all("unverified" in s["input_status"] for s in facts.values()))

    def test_exposure_is_mechanical_without_invented_counts(self):
        rows = compute_exposure(self.facts)
        self.assertTrue(all(row["mechanically_exposed_weighted"] is None for row in rows))
        for row in rows:
            facts = self.facts[row["sector"]]
            expected = (1-facts["inf_rate"]) * sum(
                weight for hour, weight in zip(facts["hours_bins"], facts["theta"])
                if hour > row["h1"])
            self.assertAlmostEqual(row["share_of_sector_employment"], expected, places=12)

    def test_actual_hours_support_and_informal_hours_remain_sector_specific(self):
        facts = copy.deepcopy(self.facts)
        facts["agriculture"].update(hours_bins=np.array([20., 42., 60.]), theta=np.array([0.1, 0.4, 0.5]), hI=35.)
        facts["industry"].update(hours_bins=np.array([30., 39., 41., 48.]), theta=np.array([0.1, 0.2, 0.4, 0.3]), hI=38.)
        pars, _ = build_sector_params(facts, self.targets)
        sim = simulate_groups(pars, 44., 40., facts["services"]["theta"])
        self.assertAlmostEqual(sim["baseline"]["solutions"]["agriculture"]["hF_avg"], 40.8, places=12)
        self.assertEqual(sim["reform"]["solutions"]["industry"]["hI"], 38.)
        self.assertAlmostEqual(sim["A_req_details"]["relative_error"], 0., places=10)

    def test_missing_new_microdata_cannot_fall_back(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(FileNotFoundError):
                load_reprocessed_facts(folder, ROOT / "data_final")
            (Path(folder) / "pnad_targets.json").write_text(
                json.dumps({"metadata": {"year": 2024, "quarter": 3}}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_reprocessed_facts(folder, ROOT / "data_final")

    def test_unrelated_population_denominator_rejected(self):
        with self.assertRaises(ValueError):
            run_sectoral_simulation(self.params["bilateral"], 0.002, 36., N_total=1.)


if __name__ == "__main__":
    unittest.main()
