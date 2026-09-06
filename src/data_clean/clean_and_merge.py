"""Merge verified inputs with evidence labels, preserving all legacy inputs."""
from __future__ import annotations
import csv
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]

def main():
    intermediate = ROOT / 'data_intermediate/reprocessed'
    pnad = json.loads((intermediate / 'pnad_targets.json').read_text(encoding='utf-8'))
    rais = json.loads((intermediate / 'rais_targets.json').read_text(encoding='utf-8'))
    if not pnad.get('status', '').startswith('verified'):
        raise ValueError('Reprocessed PNAD data have not been verified')
    if (pnad['metadata']['year'], pnad['metadata']['quarter']) != (2024, 4):
        raise ValueError('Expected PNAD 2024Q4; quarter substitution is forbidden')
    n = pnad['national']; rows = []
    def add(key, value, unit, source, definition, status='verified_observation'):
        if value is None: raise ValueError(f'Missing empirical target: {key}')
        rows.append(dict(target_id=key, value=value, unit=unit, source=source,
                         definition=definition, evidence_status=status))
    pn = 'PNAD 2024Q4 official microdata; see reprocessed/provenance and manifest.json'
    add('INF_AGG', n['informality_rate'], 'proportion', pn, 'VD4009 and V4019; occupied persons age14+; V1028 weights')
    add('N_TOTAL', n['employment_to_population_14plus'], 'proportion', pn, 'Occupied persons / population aged14+')
    add('HI', n['mean_hours_habitual']['informal'], 'hours/week', pn, 'Habitual main-job hours, informal workers')
    add('H_FORMAL_HABITUAL', n['mean_hours_habitual']['formal'], 'hours/week', pn, 'Habitual main-job hours; not contracted')
    add('H_FORMAL_ACTUAL', n['mean_hours_actual']['formal'], 'hours/week', pn, 'Actual main-job hours; not contracted')
    add('R_HOURLY_AGGREGATE', n['wage_ratio_formal_informal']['aggregate_hourly_payroll_over_hours'], 'ratio', pn, '(sum weighted formal income / sum weighted formal hours)/(informal analogue); same paid sample')
    add('R_WEEKLY_PER_WORKER', n['wage_ratio_formal_informal']['mean_weekly_per_worker'], 'ratio', pn, 'Ratio of means; monthly income multiplied by12/52; includes employer/self-employment earnings')
    for key in ['theta_36','theta_40','theta_44']:
        add(key.upper(), n['formal_hours_bins_comparable'][key], 'proportion', pn, 'Habitual hours <=36/37-40/>40; representative36/40/44 is a model approximation')
    add('RAIS_SHARE_SMALL', rais['small_le49_share_formal'], 'proportion', 'MTE RAIS2022 Table6 / workbook TABELA2', 'Active links at establishments1-49; not PNAD person or total-employment share')
    add('RAIS_SHARE_LARGE', rais['large_ge50_share_formal'], 'proportion', 'MTE RAIS2022 Table6 / workbook TABELA2', 'Active links at establishments50+; not consolidated firms')
    original = {r['target_id']:r for r in csv.DictReader((ROOT/'data_final/calibration_targets.csv').open(encoding='utf-8'))}
    for key in ['ALPHA','ETA_I','E_Q','H0','H1','H_STAR','GAMMA_F_SMALL','GAMMA_F_LARGE','INF_SMALL','INF_LARGE']:
        r=original[key]
        add(key,float(r['value']),r['unit'],'Frozen structural choice; not re-estimated',r['name']+'; legacy provenance is not verified evidence','assumption')
    destination=ROOT/'data_final/reprocessed/calibration_targets.csv'
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(f'Wrote {destination}; {len(rows)} targets with evidence labels')

if __name__=='__main__':main()
