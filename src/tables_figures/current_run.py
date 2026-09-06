"""Standalone asset regeneration requires an explicit audited run directory."""
from pathlib import Path
import argparse,json,sys,datetime,csv
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.tables_figures.build_corrected_assets import build_assets


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir',type=Path,required=True,
                   help='Successful output/runs/<id>; never implicit historical outputs')
    p.add_argument('--output-dir',type=Path)
    a=p.parse_args()
    manifest=json.loads((a.run_dir/'RUN_MANIFEST.json').read_text(encoding='utf-8'))
    if manifest.get('status')!='complete':raise ValueError('An audited successful run is required')
    with (a.run_dir/'COMPARATIVO_RESULTADOS.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    numeric={'hours_cap','sigma_sub','omega','Y0','Y1','dY_pct','A_req_pct','A_req_frozen_pct',
             'informality_pct','dGHH_pct','CE_pct','hours_pct','efficiency_pct','reallocation_pct'}
    for row in rows:
        for key in numeric:
            if key in row:row[key]=float(row[key]) if row[key] else None
    out=a.output_dir or a.run_dir/('assets_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    if out.exists():raise FileExistsError('Choose a new asset directory')
    build_assets(rows,out)
    print(out)


if __name__=='__main__':main()
