from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DEFAULT_QUEUE=ROOT/'generated_v2_foundry'/'CORE_V2_FOUNDRY_COMPOSITION_QUEUE.json'
REQUIRED={
    'decision_identity': ('decision_id',),
    'uncertainty_state': ('uncertainty_axes',),
    'test_catalog': ('test_channels',),
}
TEST_REQUIRED=('test_signature','expected_resolution_by_axis','compute_seconds','reliability','calibration_id','evidence_role','selection_generation','measurement_backreaction','backreaction_adjusted')


def audit(rows):
    result=[]; ready=0; missing_counter=Counter()
    for i,row in enumerate(rows):
        missing=[]
        for _,fields in REQUIRED.items():
            for f in fields:
                if f not in row:
                    missing.append(f)
        if 'test_channels' in row and isinstance(row.get('test_channels'),list):
            for j,t in enumerate(row['test_channels']):
                if not isinstance(t,dict):
                    missing.append(f'test_channels[{j}]')
                    continue
                for f in TEST_REQUIRED:
                    if f not in t:
                        missing.append(f'test_channels[{j}].{f}')
        else:
            # If no test catalog exists, list the internal telemetry as missing too so
            # the patch is operationally explicit rather than just saying "tests missing".
            missing += [f'test_channels[*].{f}' for f in TEST_REQUIRED]
        for f in missing: missing_counter[f]+=1
        is_ready=not missing
        ready+=int(is_ready)
        result.append({
            'queue_index':i,
            'supplier_id':row.get('supplier_id'),
            'consumer_id':row.get('consumer_id'),
            'ready_for_experiment_routing':is_ready,
            'missing_fields':sorted(set(missing)),
        })
    return {
        'engine':'LAB_EXPERIMENT_READINESS_AUDIT_R5',
        'queue_rows':len(rows),
        'ready_rows':ready,
        'not_ready_rows':len(rows)-ready,
        'readiness_fraction':ready/len(rows) if rows else 0.0,
        'missing_field_counts':dict(sorted(missing_counter.items())),
        'required_candidate_contract':{
            'decision_id':'stable research decision identifier',
            'uncertainty_axes':'axis_id + current uncertainty + decision leverage + importance',
            'test_channels':'predeclared candidate tests; protected validation may be present but is never adaptively ranked',
            'test_channel_fields':list(TEST_REQUIRED),
            'unknown_policy':'UNKNOWN stays unquantified; no guessed information gain, reliability, or compute cost',
        },
        'rows':result,
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--queue',type=Path,default=DEFAULT_QUEUE); ap.add_argument('--output',type=Path,required=True); args=ap.parse_args()
    rows=json.loads(args.queue.read_text(encoding='utf-8'))
    out=audit(rows); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({k:out[k] for k in ('queue_rows','ready_rows','not_ready_rows','readiness_fraction')},indent=2))
if __name__=='__main__': main()
