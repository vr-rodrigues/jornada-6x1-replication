"""Independent audit of saved fresh outputs; never invokes old output as a solver."""
from pathlib import Path
import argparse,csv,datetime,hashlib,json,math
ROOT=Path(__file__).resolve().parents[1]

def read(path):
 return json.loads(Path(path).read_text(encoding="utf-8-sig"),
                   parse_constant=lambda token:(_ for _ in ()).throw(ValueError("Non-finite JSON: "+token)))

def audit(run):
 run=Path(run).resolve()
 manifest=read(run/"RUN_MANIFEST.json")
 assert manifest["status"] in ("complete","completed_independent_steps_with_blockers"),manifest["status"]
 assert manifest["raw_and_frozen_inputs_unchanged"] is True
 report=dict(run_directory=str(run),audited_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
             simulation_count=0,allocation_count=0,max_restore_error=0.,
             max_decomposition_error=0.,max_CE_error=0.,hashes_checked=0)
 for section,base in [("output_hashes",run),("input_hashes",ROOT),("code_hashes",ROOT)]:
  for relative,expected in manifest[section].items():
   path=base/relative
   assert path.exists(),str(path)
   actual=hashlib.sha256(path.read_bytes()).hexdigest()
   assert actual==expected,f"Stale or modified file in {section}: {relative}"
   report["hashes_checked"]+=1

 def check_sim(sim):
  report["simulation_count"]+=1
  b,r=sim["baseline"],sim["reform"];v=sim["results"];d=sim["decomposition"]
  error=abs(v["dY_pct"]-100*(r["Y"]/b["Y"]-1))
  assert error<1e-9,error
  de=abs(sum(d[k] for k in ["hours_pct","efficiency_pct","reallocation_pct"])-v["dY_pct"])
  report["max_decomposition_error"]=max(report["max_decomposition_error"],de)
  assert de<1e-8,de
  N=sum(p["N_total"] for p in sim["groups"].values())
  c0,c1=b["C"]/N,r["C"]/N;psi,nu=sim["psi"],sim["nu_ghh"]
  ce=100*((c1-c0)-psi*(r["h_avg"]**(1+nu)-b["h_avg"]**(1+nu))/(1+nu))/c0
  ce_error=abs(ce-v["CE_pct"]);report["max_CE_error"]=max(report["max_CE_error"],ce_error)
  assert ce_error<1e-8,ce_error
  for which in ["A_req_details","A_req_frozen_details"]:
   comp=sim[which];err=abs(comp["output"]/b["Y"]-1)
   report["max_restore_error"]=max(report["max_restore_error"],err)
   assert err<1e-9,err
   assert abs(comp["output"]-sum(p["Y"] for p in comp["allocations"].values()))<1e-9
   if which=="A_req_frozen_details":
    for g,p in comp["allocations"].items():assert abs(p["NF"]-b["solutions"][g]["NF"])<1e-10
  for allocation in [*b["solutions"].values(),*r["solutions"].values(),
                     *sim["A_req_details"]["allocations"].values()]:
   report["allocation_count"]+=1
   assert allocation["kkt_violation"]<1e-7,allocation["kkt_violation"]
   assert abs(allocation["C"]+allocation["resource_cost"]-allocation["Y"])<1e-9
  assert abs(b["inf"]-sum(s["NI"] for s in b["solutions"].values())/N)<1e-12

 for path in run.rglob("RESULTS_FULL.json"):
  for sim in read(path).values():check_sim(sim)
 for path in run.rglob("SECTOR_RESULTS_FULL.json"):
  for scenario in read(path)["scenarios"].values():check_sim(scenario["simulation"])
 with (run/"COMPARATIVO_RESULTADOS.csv").open(encoding="utf-8-sig") as stream:
  rows=list(csv.DictReader(stream))
 groups={}
 for row in rows:
  groups.setdefault(row["version"],[]).append(row)
  assert abs(float(row["sigma_sub"])-1.326)<1e-12
  assert abs(float(row["dY_pct"])-100*(float(row["Y1"])/float(row["Y0"])-1))<1e-7
 for version in ["original","code_corrected_frozen_inputs","reprocessed_data","reprocessed_topcoded44"]:
  expected={("bilateral",40),("bilateral",36),("flat_below",40),("flat_below",36)}
  assert {(r["efficiency_mode"],int(r["hours_cap"])) for r in groups[version]}==expected
  assert len(groups[version])==4
 full=read(run/"national_empirical"/"RESULTS_FULL.json")
 top=read(run/"national_empirical_topcode44"/"RESULTS_FULL.json")
 pnad=read(ROOT/"data_intermediate/reprocessed/pnad_targets.json")
 for sim in full.values():
  for p in sim["groups"].values():assert p["h0"]==max(p["hours_bins"])
  assert abs(sim["baseline"]["h_avg"]-pnad["national"]["mean_hours_habitual"]["total"])<1e-9
 for sim in top.values():
  for p in sim["groups"].values():assert p["h0"]==44.
 assert len({r["baseline_informality_pct"] for r in groups["original"]})>=1
 report.update(status="passed",national_rows=len(rows),versions=list(groups))
 return report

if __name__=="__main__":
 parser=argparse.ArgumentParser()
 parser.add_argument("--run",type=Path)
 parser.add_argument("--output",type=Path,default=ROOT/"docs/AUDITORIA_SAIDAS_EXECUTADAS.json")
 args=parser.parse_args()
 run=args.run or Path(read(ROOT/"output/LATEST_RUN.json")["run_directory"])
 result=audit(run);args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
 print(json.dumps(result,indent=2,ensure_ascii=False))

