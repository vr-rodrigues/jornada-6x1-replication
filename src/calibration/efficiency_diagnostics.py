"""Interior-inclusive conditional sensitivity using the unified continuous kernel.
No rectangular grid is called an identified parameter set.
"""
from pathlib import Path
import sys,argparse
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.calibration.corrected_pipeline import run_sensitivities,load_targets

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,default=ROOT/'output'/'corrected'/'sensitivity')
    a=p.parse_args();run_sensitivities(load_targets(str(ROOT/'data_final')),a.output_dir)
if __name__=='__main__':main()
