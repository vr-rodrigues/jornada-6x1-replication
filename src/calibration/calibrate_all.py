"""Compatibility exports and national calibration using the single model kernel."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.model.production import production, mpl_L
from src.model.ces_aggregator import ces_agg
from src.model.efficiency import eff, HOURS_BINS, formal_hours_avg, formal_hours_hetero, calibrate_kappa
from src.model.firm_problem import solve_NF, informal_cost
from src.model.calibration import calibrate_wedge, calibrate_pi_m, calibrate_psi
from src.model.areq_solver import solve_Areq
from src.model.welfare import ghh_composite, compensating_variation
from src.model.simulation import load_targets, run_simulation


def main():
    from src.calibration.corrected_pipeline import run_national_cli
    return run_national_cli('bilateral')

if __name__ == '__main__':
    main()
