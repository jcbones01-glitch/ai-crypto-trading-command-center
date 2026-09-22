from __future__ import annotations
import argparse,gzip,hashlib,json
from pathlib import Path
from research_core.ams_dep_v2_aggregation import summarize,task_index
from research_core.release_gate import assert_ams_dep_v2_calibration_execution_allowed

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/"research/experiments/ams_dep_synthetic_core_v2.json"
MANIFEST=ROOT/"research/governance/ams_dep_v2_freeze_manifest.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    gate=assert_ams_dep_v2_calibration_execution_allowed()
    cfg=json.loads(CONFIG.read_text())
    ledgers=sorted(a.input_dir.rglob("shard_*.jsonl.gz"))
    sums=sorted(a.input_dir.rglob("shard_*_summary.json"))
    if len(ledgers)!=128 or len(sums)!=128:
        raise RuntimeError("expected 128 shard ledgers and summaries")
    manifest_sha=sha(MANIFEST.read_bytes())
    spec_sha=sha(CONFIG.read_bytes())
    shard_ids=set()
    commits=set()
    for path in sums:
        s=json.loads(path.read_text())
        shard_ids.add(int(s["shard_id"]))
        commits.add(s["executing_commit"])
        if s["freeze_manifest_sha256"]!=manifest_sha or s["frozen_spec_sha256"]!=spec_sha:
            raise RuntimeError("mixed frozen provenance")
        if s["holdout_run"] or s["market_data_accessed"] or s["validation_or_oos_accessed"]:
            raise RuntimeError("forbidden access flag")
    if shard_ids!=set(range(128)) or len(commits)!=1:
        raise RuntimeError("incomplete/mixed shard summaries")
    n_outer=int(cfg["calibration_replications_per_dgp"])
    expected=len(cfg["cases"])*n_outer*6
    rows={}
    shard_hashes={}
    for path in ledgers:
        shard=int(path.name[6:9])
        raw=path.read_bytes()
        shard_hashes[path.name]=sha(raw)
        for line in gzip.decompress(raw).splitlines():
            row=json.loads(line)
            idx=int(row["task_index"])
            if idx in rows:
                raise RuntimeError("duplicate task index")
            d=int(row["dgp_index"]); o=int(row["outer_index"])
            asset=int(row["asset_index"]); hyp=int(row["hypothesis_index"])
            if idx!=task_index(d,o,asset,hyp,n_outer) or idx%128!=shard:
                raise RuntimeError("task coordinate mismatch")
            if cfg["cases"][d]!=row["case"]:
                raise RuntimeError("DGP mismatch")
            rows[idx]=row
    if set(rows)!=set(range(expected)):
        raise RuntimeError("incomplete task coverage")
    cases,outer=summarize(cfg,rows)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    payload=b"".join((json.dumps(x,sort_keys=True,allow_nan=False)+"\n").encode() for x in outer)
    comp=gzip.compress(payload,mtime=0)
    (a.output_dir/"outer_results.jsonl.gz").write_bytes(comp)
    report={"classification":"FROZEN_AMS_DEP_V2_SYNTHETIC_CALIBRATION",
            "suite":"calibration","executing_commit":next(iter(commits)),
            "freeze_manifest_sha256":manifest_sha,"frozen_spec_sha256":spec_sha,
            "task_count":len(rows),"outer_result_count":len(outer),"shard_count":128,
            "shard_ledger_sha256":shard_hashes,"outer_ledger_sha256":sha(comp),
            "market_data_accessed":False,"validation_or_oos_accessed":False,
            "holdout_accessed":False,"empirical_release_authorized":False,
            "calibration_execution_authorized":gate["v2_calibration_execution_authorized"],
            "cases":cases,"calibration_screen_pass":all(v["calibration_screen_pass"] for v in cases.values())}
    (a.output_dir/"summary.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("AMS_DEP_V2_CALIBRATION_SCREEN="+("PASS" if report["calibration_screen_pass"] else "FAIL"))


if __name__=="__main__":
    main()
