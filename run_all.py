"""Audited replication. Original inputs and paper files are never overwritten.

python run_all.py --tests --refresh-data
Each run creates a new output/runs/<timestamp> directory with logs and hashes.
"""
from __future__ import annotations
import argparse,datetime,hashlib,json,os,subprocess,sys,traceback,shutil
from pathlib import Path
from copy import deepcopy
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from src.calibration.corrected_pipeline import load_targets,run_version,run_sensitivities,save_json,save_csv
from src.calibration.audit_fit_moments import audit
from src.sectoral.model.sector_model import run_sectoral_pipeline
from src.tables_figures.build_corrected_assets import build_assets


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(cmd,log,cwd=ROOT):
    print('RUN: '+' '.join(map(str,cmd)),flush=True)
    with Path(log).open('w',encoding='utf-8') as stream:
        p=subprocess.run(list(map(str,cmd)),cwd=cwd,stdout=stream,stderr=subprocess.STDOUT,
                         env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8',MPLBACKEND='Agg'))
    return p.returncode


def empirical_configuration(targets,pnad):
    if pnad.get('status') not in ('verified_reprocessed','verified_official_fallback'):
        raise ValueError('PNAD inputs are not verified/reprocessed')
    meta=pnad['metadata']
    if meta['year']!=2024 or meta['quarter']!=4:raise ValueError('Refusing a quarter substitution')
    d=pnad['national'];t=deepcopy(targets)
    t['INF_AGG']['value']=d['informality_rate']
    t['HI']['value']=d['mean_hours_habitual']['informal']
    # Keep normalized population fixed so quadratic cost units do not change.
    # Observed E/P is reported as an empirical moment, not silently inserted.
    t['H_REF_EFFICIENCY']={'value':42.244,'source':'Frozen external efficiency anchor hypothesis','notes':'Independent of PNAD mean hours'}
    specs={'Brasil':{'share':1.,'K_share':1.,'inf_target':d['informality_rate'],'gamma_F':.06}}
    dist=d['formal_hours_distribution']
    # This is the identity operator on observed baseline hours, not a legal cap.
    t['H0']['value']=max(dist['hours'])
    target=d['wage_ratio_formal_informal']['aggregate_hourly_payroll_over_hours']
    if target is None:raise ValueError('No comparable hourly earnings moment')
    return t,specs,dist['weights'],dist['hours'],target


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tests',action='store_true',help='Run the full model/empirical test suite')
    p.add_argument('--refresh-data',action='store_true',help='Collect BQ inputs; explicit official fallback when blocked')
    p.add_argument('--project',default='upa-research')
    p.add_argument('--original-archive',type=Path)
    p.add_argument('--output-dir',type=Path)
    p.add_argument('--paper',action='store_true',help='Generate a new numerical appendix, preserving the old manuscript')
    args=p.parse_args()
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    out=args.output_dir or ROOT/'output'/'runs'/stamp
    if out.exists():raise FileExistsError('Use a new output directory: '+str(out))
    out.mkdir(parents=True);(out/'logs').mkdir()
    status={'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'command':sys.argv,'python':sys.version,'executable':sys.executable,
            'run_directory':str(out.resolve()),'steps':{},'blockers':[]}
    frozen_paths=[p for folder in ('data_raw','data_intermediate','data_final') for p in (ROOT/folder).rglob('*')
                  if p.is_file() and 'reprocessed' not in p.relative_to(ROOT).parts]
    before={str(p.relative_to(ROOT)):digest(p) for p in frozen_paths}
    try:
        command([sys.executable,'-m','pip','freeze'],out/'logs'/'python_packages.txt')
        archive=args.original_archive
        if archive is None:
            pointer=ROOT.parent/'AUDITORIA_ATUAL.txt'
            if pointer.exists():archive=Path(pointer.read_text(encoding='utf-8').strip())
        if archive is not None:
            rc=command([sys.executable,ROOT/'src/calibration/probe_original.py','--archive',archive,
                        '--output',out/'original_fresh.json'],out/'logs'/'original_probe.log')
            if rc:raise RuntimeError('Original-code probe failed; see original_probe.log')
            rows=json.loads((out/'original_fresh.json').read_text(encoding='utf-8'))
            status['original_archive']=str(archive.resolve())
            status['original_baseline']=json.loads((archive/'baseline_status.json').read_text(encoding='utf-8'))
        else:
            rows=[];status['blockers'].append('Original archive unavailable; no old output substituted')
        if args.refresh_data:
            rc=command([sys.executable,ROOT/'src/data_raw/reprocess_verified_inputs.py','--project',args.project,
                        '--allow-official-fallback'],out/'logs'/'data_reprocessing.log')
            status['steps']['data_collection_returncode']=rc
            if rc:status['blockers'].append('Requested data collection failed; see data_reprocessing.log')
        if (ROOT/'data_intermediate/reprocessed/pnad_targets.json').exists():
            rc=command([sys.executable,ROOT/'src/data_clean/clean_and_merge.py'],out/'logs'/'merge_inputs.log')
            if rc:raise RuntimeError('Verified input merger failed')
            provenance=json.loads((ROOT/'data_intermediate/reprocessed/manifest.json').read_text(encoding='utf-8'))
            for relative,expected in provenance['digests'].items():
                path=ROOT/relative
                if not path.is_file() or digest(path)!=expected:
                    raise ValueError('Reprocessed provenance hash mismatch: '+relative)
        targets=load_targets(str(ROOT/'data_final'))
        versions={};all_sectors=[]
        print('National: accounting and continuous optimization, frozen inputs',flush=True)
        rr,dd,bb=run_version(targets,'code_corrected_frozen_inputs',out/'national_frozen',
            note='Original numerical inputs frozen; 59/41 and group informality treated as hypotheses; formal-to-total accounting corrected')
        rows+=rr;versions['national_frozen']=dd
        rr,dd,bb=run_version(targets,'bridge_recalibrated_assumed_hourly',out/'national_bridge_assumed',bridge_target=1.4,
            note='Sigma fixed at 1.326; R=1.4 hourly is an explicit hypothesis, not a verified Brazilian observation')
        rows+=rr;versions['national_bridge_assumed']=dd
        # Separate changing RAIS from changing PNAD or the group structure.
        rais_path=ROOT/'data_intermediate/reprocessed/rais_targets.json'
        if rais_path.exists():
            rais=json.loads(rais_path.read_text(encoding='utf-8'))
            if rais.get('status') in ('verified_reprocessed','verified_official_fallback'):
                t=deepcopy(targets)
                t['SHARE_SMALL']['value']=rais['small_le49_share_formal']
                t['SHARE_LARGE']['value']=rais['large_ge50_share_formal']
                rr,dd,_=run_version(t,'rais_verified_only',out/'national_rais_only',
                    note='RAIS 2022 establishment links verified; 50%/20% group informality and all other parameters still hypotheses, not matched PNAD universes')
                rows+=rr;versions['national_rais_only']=dd
        print('Sectoral: frozen inputs, recomputing every output',flush=True)
        sector=run_sectoral_pipeline(ROOT/'data_final',out/'sectoral_frozen',input_kind='frozen')
        all_sectors+=sector['rows']
        pnad_path=ROOT/'data_intermediate/reprocessed/pnad_targets.json'
        if pnad_path.exists():
            pnad=json.loads(pnad_path.read_text(encoding='utf-8'))
            t,specs,theta,bins,ratio=empirical_configuration(targets,pnad)
            # A one-group control exposes the model aggregation change separately.
            ctrl={'Brasil':{'share':1.,'K_share':1.,'inf_target':versions['national_frozen']['bilateral_36']['baseline']['inf'],'gamma_F':.06}}
            rr,dd,_=run_version(targets,'single_group_frozen_control',out/'national_single_group_control',group_specs=ctrl,
                note='Aggregation control: same frozen hours/technology, aggregate informality from corrected two-group baseline; blended gamma=.06 hypothesis')
            rows+=rr;versions['single_group_control']=dd
            rr,dd,_=run_version(t,'reprocessed_data_fixed_omega',out/'national_empirical_fixed_omega',group_specs=specs,theta=theta,hours_bins=bins,
                note='PNAD 2024Q4 national one-group; observed baseline habitual hours preserved; omega=.622 frozen technology hypothesis')
            rows+=rr;versions['empirical_fixed_omega']=dd
            rr,dd,bb=run_version(t,'reprocessed_data',out/'national_empirical',group_specs=specs,theta=theta,hours_bins=bins,bridge_target=ratio,
                note='PNAD 2024Q4 national one-group; observed baseline habitual hours preserved; hourly remuneration bridge (includes mixed self-employment income); reform is habitual-hours proxy, not contracted hours')
            rows+=rr;versions['national_empirical']=dd
            fits=[]
            for row in rr:
                if row['hours_cap']!=40:continue
                for metric,key in [('hourly','aggregate_hourly_payroll_over_hours'),('weekly','mean_weekly_per_worker')]:
                    observed=pnad['national']['wage_ratio_formal_informal'][key]
                    fits.append({'efficiency_mode':row['efficiency_mode'],'moment':metric,
                        'observed_paid_sample':observed,'model_all_occupied':row['implied_'+metric+'_ratio'],
                        'gap':row['implied_'+metric+'_ratio']-observed,'targeted':metric=='hourly',
                        'interpretation':'Paid earnings ratio extended to all occupied including unpaid workers under an explicit selection/marginal-product hypothesis'})
            save_csv(out/'MOMENT_FIT.csv',fits)
            tc=deepcopy(t);tc['H0']['value']=44.
            topcode_ratio=pnad['national']['wage_ratio_formal_informal'].get('aggregate_hourly_formal_capped44')
            if topcode_ratio is None:
                raise ValueError('Topcode sensitivity requires the matching capped-hours remuneration target')
            rr,dt,_=run_version(tc,'reprocessed_topcoded44',out/'national_empirical_topcode44',group_specs=specs,theta=theta,hours_bins=bins,bridge_target=topcode_ratio,
                note='Additional compliance/measurement hypothesis: formal baseline hours topcoded44, informal hours unchanged; hourly bridge denominator also topcoded44')
            rows+=rr;versions['empirical_topcode44']=dt
            from src.calibration.corrected_pipeline import run_empirical_sensitivity
            run_empirical_sensitivity(t,specs,theta,bins,ratio,out/'sensitivity')
            private_ratio=pnad['national']['private_employee_wage_bridge']['wage_ratio_formal_informal']['aggregate_hourly_payroll_over_hours']
            rr,_,_=run_version(t,'bridge_private_employee_proxy',out/'sensitivity'/'private_employee_bridge',group_specs=specs,theta=theta,hours_bins=bins,bridge_target=private_ratio,
                note='Sensitivity only: private-employee wage ratio applied to broad employment model; universe mismatch explicitly maintained')
            save_csv(out/'sensitivity'/'PRIVATE_EMPLOYEE_BRIDGE.csv',rr)
            for key,tt in [('empirical',t),('empirical_topcode44',tc)]:
                save_csv(out/'inputs'/f'{key}_targets.csv',[{'target_id':k,**v} for k,v in tt.items()])
            save_json(out/'EMPIRICAL_MODEL_MAPPING.json',{'source':pnad['metadata'],
                'normalization':'N=.59,K=1 held fixed to preserve quadratic cost units; observed employment/population reported separately',
                'grouping':'One national PNAD group avoids combining RAIS links/establishments with PNAD persons; separate one-group frozen control reported',
                'hours':'Observed habitual main-job distribution preserved at baseline; min(h,40/36) reform is an intervention proxy, not contracted hours. Separate formal topcode44 variant.',
                'baseline_identity_cap':max(bins),
                'hours_above44_weight':sum(w for h,w in zip(bins,theta) if h>44),
                'wage_bridge':'Gross marginal products mapped to remuneration under an explicit competitive-pay assumption; sigma fixed=1.326',
                'empirical_moments':pnad['national'],'efficiency_anchor_hours':42.244})
            # The common omega must be calibrated on the actual sector payrolls.
            # Frozen .622 run remains separate; no national share is substituted.
            empirical_targets=out/'inputs'/'empirical_targets.csv'
            sector=run_sectoral_pipeline(ROOT/'data_intermediate/reprocessed',out/'sectoral_empirical',input_kind='reprocessed',targets_path=empirical_targets,
                omega=.622,omega_source='Frozen technology hypothesis; not the formal employment share')
            all_sectors+=[dict(r,scenario_variant='empirical_fixed_omega') for r in sector['rows']]
            from src.sectoral.model.sector_model import calibrate_sector_omega
            bridges={mode:calibrate_sector_omega(ROOT/'data_intermediate/reprocessed',empirical_targets,efficiency_mode=mode)
                     for mode in ('bilateral','flat_below')}
            save_json(out/'sectoral_empirical_bridge'/'BRIDGE.json',bridges)
            sector=run_sectoral_pipeline(ROOT/'data_intermediate/reprocessed',out/'sectoral_empirical_bridge',input_kind='reprocessed',targets_path=empirical_targets,
                omega_by_mode={mode:b['omega'] for mode,b in bridges.items()},
                omega_source='Sigma=1.326; common technology weight calibrated to observed hourly remuneration ratio using summed sector payrolls')
            all_sectors+=[dict(r,scenario_variant='empirical_bridge') for r in sector['rows']]
            from src.sectoral.model.sensitivity import run_sensitivity
            run_sensitivity(ROOT/'data_intermediate/reprocessed',out/'sensitivity'/'sectoral_empirical',input_kind='reprocessed',targets_path=empirical_targets)
            status['steps']['pnad_reprocessed']='complete'
        else:
            status['blockers'].append('PNAD 2024Q4 reprocessed microdata unavailable; empirical results not fabricated')
            status['steps']['pnad_reprocessed']='blocked'
        print('Sensitivity grids with interior points',flush=True)
        run_sensitivities(targets,out/'sensitivity')
        resource_rows,_,_=run_version(targets,'all_private_costs_as_resources',out/'sensitivity'/'resource_treatment',
            resource_costs=True,note='Alternative resource accounting: C+adjustment+tau*NF+pi*NI^2/2=Y')
        save_csv(out/'sensitivity'/'RESOURCE_TREATMENT.csv',resource_rows)
        save_json(out/'audit_fit_moments.json',audit(targets))
        save_csv(out/'COMPARATIVO_RESULTADOS.csv',rows)
        parameter_rows=[]
        for variant,scenarios in versions.items():
            for scenario,sim in scenarios.items():
                for group,pars in sim['groups'].items():
                    parameter_rows.append({'version':variant,'scenario':scenario,'group':group,
                        **{k:v for k,v in pars.items() if isinstance(v,(int,float,str,bool))}})
        save_csv(out/'CALIBRATED_PARAMETERS.csv',parameter_rows)
        save_csv(out/'RESULTADOS_SETORIAIS.csv',all_sectors)
        build_assets(rows,out,all_sectors)
        from src.sectoral.model.sector_assets import build_sectoral_figure
        build_sectoral_figure(all_sectors,out)
        status['steps']['computed_national_rows']=len(rows)
        status['steps']['computed_sectoral_rows']=len(all_sectors)
        checks={'max_foc_violation':0.,'max_output_restoration_error':0.,'max_decomposition_error_pct':0.,
                'max_ce_identity_error':0.}
        for scenarios in versions.values():
            for sim in scenarios.values():
                for stage in ('baseline','reform'):
                    checks['max_foc_violation']=max(checks['max_foc_violation'],
                        *(s['kkt_violation'] for s in sim[stage]['solutions'].values()))
                checks['max_output_restoration_error']=max(checks['max_output_restoration_error'],
                    abs(sim['A_req_details']['relative_error']),abs(sim['A_req_frozen_details']['relative_error']))
                checks['max_decomposition_error_pct']=max(checks['max_decomposition_error_pct'],abs(sim['decomposition']['sum_error_pct']))
                n=sum(g['N_total'] for g in sim['groups'].values())
                c0,c1=sim['baseline']['C']/n,sim['reform']['C']/n
                h0,h1=sim['baseline']['h_avg'],sim['reform']['h_avg']
                ce=((c1-c0)-sim['psi']*(h1**3-h0**3)/3)/c0
                checks['max_ce_identity_error']=max(checks['max_ce_identity_error'],abs(ce*100-sim['results']['CE_pct']))
        if checks['max_foc_violation']>1e-6 or checks['max_output_restoration_error']>1e-9 or checks['max_decomposition_error_pct']>1e-9 or checks['max_ce_identity_error']>1e-9:
            raise ArithmeticError('Current-run mathematical validation failed: '+str(checks))
        status['numerical_checks']=checks
        if args.tests:
            rc=command([sys.executable,'-m','unittest','discover','-s','tests','-v'],out/'logs'/'tests.log')
            status['steps']['tests_returncode']=rc
            if rc:raise RuntimeError('Tests failed; see tests.log')
        if args.paper:
            from src.tables_figures.write_corrected_appendix import write_appendix
            pdf=write_appendix(out,rows)
            status['steps']['numerical_appendix']=str(pdf.relative_to(out))
        from src.calibration.write_corrections_report import write_report
        write_report(out,rows,status,archive)
        after={str(p.relative_to(ROOT)):digest(p) for p in frozen_paths}
        if before!=after:raise RuntimeError('Original data changed unexpectedly')
        status['raw_and_frozen_inputs_unchanged']=True
        status['input_hashes']={str(p.relative_to(ROOT)):digest(p) for folder in ('data_final','data_intermediate')
            for p in (ROOT/folder).rglob('*') if p.is_file()}
        code_files=[p for folder in ('src','tests') for p in (ROOT/folder).rglob('*')
                    if p.suffix.lower() in ('.py','.r','.sql')]
        code_files += [ROOT/f for f in ('run_all.py','requirements.txt','requirements-replication.lock.txt')]
        status['code_hashes']={str(p.relative_to(ROOT)):digest(p) for p in code_files}
        status['output_hashes']={str(p.relative_to(out)):digest(p) for p in out.rglob('*') if p.is_file()}
        status['status']='complete' if not status['blockers'] else 'completed_independent_steps_with_blockers'
        data_manifest=ROOT/'data_intermediate/reprocessed/manifest.json'
        if data_manifest.exists():status['data_route']=json.loads(data_manifest.read_text(encoding='utf-8'))
        shutil.copy2(out/'COMPARATIVO_RESULTADOS.csv',ROOT/'COMPARATIVO_RESULTADOS.csv')
        shutil.copy2(out/'RESULTADOS_SETORIAIS.csv',ROOT/'RESULTADOS_SETORIAIS.csv')
        save_json(ROOT/'output'/'LATEST_RUN.json',{'run_directory':str(out.resolve()),'status':status['status']})
    except Exception as exc:
        status['status']='failed';status['error']=str(exc)
        (out/'logs'/'failure.log').write_text(traceback.format_exc(),encoding='utf-8')
        raise
    finally:
        status['end_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        save_json(out/'RUN_MANIFEST.json',status)
    print('Replication finished: '+str(out),flush=True)
    return 0 if status['status']=='complete' else 2


if __name__=='__main__':raise SystemExit(main())
