"""Pipeline contracts: measured hours, explicit variants and fresh serialization."""
import copy,csv,json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run_all import empirical_configuration
from src.model.simulation import load_targets,run_simulation
from src.calibration.corrected_pipeline import run_version

TARGETS=load_targets(str(ROOT/"data_final"))
PNAD=ROOT/"data_intermediate/reprocessed/pnad_targets.json"

@unittest.skipUnless(PNAD.exists(),"Verified PNAD data must be collected first")
class EmpiricalPipelineContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pnad=json.loads(PNAD.read_text(encoding="utf-8"))
  cls.config=empirical_configuration(TARGETS,cls.pnad)

 def test_principal_baseline_preserves_all_observed_habitual_hours(self):
  t,specs,theta,bins,ratio=self.config
  self.assertEqual(t["H0"]["value"],max(bins))
  self.assertGreater(max(bins),44.)
  sim=run_simulation(t,sigma_sub=1.326,theta=theta,hours_bins=bins,group_specs=specs)
  mean=sum(s["NF"]*s["hF_avg"] for s in sim["baseline"]["solutions"].values())/sum(s["NF"] for s in sim["baseline"]["solutions"].values())
  self.assertAlmostEqual(mean,self.pnad["national"]["mean_hours_habitual"]["formal"],places=10)
  self.assertAlmostEqual(sim["baseline"]["h_avg"],self.pnad["national"]["mean_hours_habitual"]["total"],places=10)

 def test_efficiency_anchor_is_separate_from_empirical_mean(self):
  t,_,_,_,_=self.config
  self.assertEqual(t["H_REF_EFFICIENCY"]["value"],42.244)
  self.assertEqual(t["N_TOTAL"]["value"],TARGETS["N_TOTAL"]["value"])
  self.assertEqual(t["HI"]["value"],self.pnad["national"]["mean_hours_habitual"]["informal"])

 def test_single_national_group_does_not_silently_mix_rais_universe(self):
  t,specs,_,_,_=self.config
  self.assertEqual(set(specs),{"Brasil"})
  self.assertEqual(specs["Brasil"]["inf_target"],self.pnad["national"]["informality_rate"])
  self.assertEqual(specs["Brasil"]["share"],1.)

 def test_unsupported_quarter_and_status_fail(self):
  for key,value in [("year",2025),("quarter",3)]:
   p=copy.deepcopy(self.pnad);p["metadata"][key]=value
   with self.assertRaises(ValueError):empirical_configuration(TARGETS,p)
  p=copy.deepcopy(self.pnad);p["status"]="unverified"
  with self.assertRaises(ValueError):empirical_configuration(TARGETS,p)

 def test_topcode_bridge_keeps_informal_denominator_uncapped(self):
  n=self.pnad["national"];f=n["wages"]["formal"];i=n["wages"]["informal"]
  expected=(f["income_monthly_sum"]/f["hours_weekly_sum_capped44"])/(i["income_monthly_sum"]/i["hours_weekly_sum"])
  self.assertAlmostEqual(n["wage_ratio_formal_informal"]["aggregate_hourly_formal_capped44"],expected,places=12)
  self.assertNotAlmostEqual(expected,n["wage_ratio_formal_informal"]["aggregate_hourly_payroll_over_hours"],places=4)

 def test_fresh_exports_retain_metrics_and_declared_inputs(self):
  t,specs,theta,bins,ratio=self.config
  with tempfile.TemporaryDirectory(prefix="jornada_pipeline_test_") as folder:
   rows,details,bridges=run_version(t,"test_fresh",Path(folder),theta=theta,hours_bins=bins,group_specs=specs,bridge_target=ratio)
   with (Path(folder)/"RESULTS.csv").open(encoding="utf-8-sig") as stream:
    saved=list(csv.DictReader(stream))
   self.assertEqual(len(saved),4)
   self.assertEqual({(r["efficiency_mode"],int(r["hours_cap"])) for r in saved},
                    {("bilateral",40),("bilateral",36),("flat_below",40),("flat_below",36)})
   js=json.loads((Path(folder)/"RESULTS_FULL.json").read_text(encoding="utf-8"),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
   self.assertEqual(set(js),set(details))
   for row in saved:
    self.assertAlmostEqual(float(row["implied_hourly_ratio"]),ratio,places=8)
    self.assertAlmostEqual(sum(float(row[k]) for k in ["hours_pct","efficiency_pct","reallocation_pct"]),float(row["dY_pct"]),places=9)
    for key in ["A_req_frozen_pct","dGHH_pct","CE_pct"]:self.assertNotEqual(row[key],"")
   inputs=json.loads((Path(folder)/"INPUTS.json").read_text(encoding="utf-8"))
   self.assertEqual(inputs["targets"]["H0"]["value"],max(bins))

if __name__=="__main__":unittest.main()

