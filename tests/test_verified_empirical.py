"""Accounting/definition tests for the independent empirical reconstruction."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("empirical_collector",ROOT/"src/data_raw/reprocess_verified_inputs.py")
collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)

class ClassificationTests(unittest.TestCase):
    def test_cnpj_and_not_partner(self):
        for position in (8,9):
            self.assertEqual(collector.classify_informality(position,1),0)
            self.assertEqual(collector.classify_informality(position,2),1)
            self.assertIsNone(collector.classify_informality(position,None))
            self.assertIsNone(collector.classify_informality(position,9))

    def test_employee_categories_and_missing(self):
        for position in (2,4,10):self.assertEqual(collector.classify_informality(position,None),1)
        for position in (1,3,5,6,7):self.assertEqual(collector.classify_informality(position,None),0)
        self.assertIsNone(collector.classify_informality(None,None))

    def test_empty_subsample_does_not_impute(self):
        summary=collector.summarize([])
        self.assertIsNone(summary['informality_rate'])
        self.assertEqual(summary['formal_hours_distribution']['weights'],[])
        self.assertIsNone(summary['formal_hours_bins_comparable']['theta_36'])

@unittest.skipUnless((ROOT/'data_intermediate/reprocessed/pnad_targets.json').exists(),'Run verified empirical collector first')
class RealDataAccounting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((ROOT/'data_intermediate/reprocessed/pnad_targets.json').read_text(encoding='utf-8'))
        cls.r=json.loads((ROOT/'data_intermediate/reprocessed/rais_targets.json').read_text(encoding='utf-8'))

    def test_exact_quarter_and_partition(self):
        self.assertEqual((self.p['metadata']['year'],self.p['metadata']['quarter']),(2024,4))
        self.assertAlmostEqual(sum(s['occupied_weighted'] for s in self.p['sectors'].values()),self.p['national']['occupied_weighted'],delta=.001)
        self.assertAlmostEqual(sum(s['employment_share'] for s in self.p['sectors'].values()),1.,places=12)

    def test_hours_distribution_and_mean(self):
        for d in [self.p['national'],*self.p['sectors'].values()]:
            h=d['formal_hours_distribution']
            self.assertAlmostEqual(sum(h['weights']),1.,places=12)
            self.assertTrue(all(1<=v<=120 for v in h['hours']))
            self.assertAlmostEqual(sum(a*b for a,b in zip(h['hours'],h['weights'])),d['mean_hours_habitual']['formal'],places=10)
            self.assertIsNone(d['contracted_hours'])

    def test_hourly_bridge_uses_same_sample_and_aggregates(self):
        n=self.p['national'];f=n['wages']['formal'];i=n['wages']['informal']
        expected=(f['income_monthly_sum']/f['hours_weekly_sum'])/(i['income_monthly_sum']/i['hours_weekly_sum'])
        self.assertAlmostEqual(expected,n['wage_ratio_formal_informal']['aggregate_hourly_payroll_over_hours'],places=12)
        self.assertNotAlmostEqual(expected,n['wage_ratio_formal_informal']['mean_weekly_per_worker'],places=2)
        self.assertLess(f['paid_workers_weighted'],n['wages']['formal']['hours_valid_weighted'])

    def test_rais_from_counts_not_legacy_claim(self):
        self.assertEqual(sum(r['n_active_links'] for r in self.r['breakdown']),self.r['n_active_links'])
        self.assertAlmostEqual(self.r['small_le49_share_formal']+self.r['large_ge50_share_formal'],1.,places=12)
        self.assertEqual(self.r['n_active_links'],52790864)
        self.assertAlmostEqual(self.r['small_le49_share_formal'],20793602/52790864,places=12)

if __name__=='__main__':unittest.main()
