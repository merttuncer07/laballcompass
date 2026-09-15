from __future__ import annotations
import json
from pathlib import Path
from experiment_selector import *

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'generated_search'/'EXPERIMENT_SELECTOR_SYNTHETIC_REPLAY_R4.json'

def make_contract():
    axes=tuple(UncertaintyAxis(x,x.upper(),1.0,1.0,1.0) for x in 'abcde')
    tests=(
        TestChannel('T_C','cheap C discriminator',{'c':1.0},1.0,1.0,selection_generation=4,calibration_id='SYNTH_CAL'),
        TestChannel('T_AB','joint A/B discriminator',{'a':.9,'b':.9},2.0,1.0,selection_generation=4,calibration_id='SYNTH_CAL'),
        TestChannel('T_DE','joint D/E discriminator',{'d':.9,'e':.9},3.0,1.0,selection_generation=4,calibration_id='SYNTH_CAL'),
        TestChannel('T_FULL','expensive exhaustive discriminator',{x:1.0 for x in 'abcde'},20.0,1.0,selection_generation=4,calibration_id='SYNTH_CAL'),
        TestChannel('T_UNKNOWN','uncalibrated attractive-looking test',{'a':1.0},None,None,selection_generation=4,calibration_id='SYNTH_CAL'),
        TestChannel('T_PROTECTED','untouched final surface',{x:1.0 for x in 'abcde'},.1,1.0,EvidenceRole.PROTECTED_VALIDATION,4,calibration_id='SYNTH_CAL'),
    )
    return ExperimentContract('SYNTHETIC_DECISION',4,0,axes,tests,stop_unresolved_mass=.5,problem_shell='SYNTHETIC_MECHANICS_ONLY')

def run():
    c=make_contract(); rows=[]; total_compute=0.0; protected_selected=False; unknown_selected=False
    while True:
        plan=choose_next_experiment(c)
        rows.append({'round':c.selection_round,'unresolved_mass':c.unresolved_mass,'plan':plan.to_dict()})
        if plan.stop: break
        tid=plan.selected_test_id
        t=next(t for t in c.tests if t.test_id==tid)
        protected_selected |= t.evidence_role==EvidenceRole.PROTECTED_VALIDATION
        unknown_selected |= t.compute_seconds is None or t.reliability is None
        total_compute += float(t.compute_seconds)
        next_unc={}
        by={a.axis_id:a for a in c.axes}
        for axis,reduction in t.expected_resolution_by_axis.items():
            if axis in by and reduction is not None:
                next_unc[axis]=by[axis].uncertainty*(1-float(reduction))
        out=ExperimentOutcome(f'E{c.selection_round}',c.decision_id,tid,c.search_generation,c.selection_round,c.selection_round+1,next_unc)
        c=apply_outcome(c,plan,out)
    out={
        'engine':'LAB_EXPERIMENT_SELECTOR_R4',
        'claim_scope':'SYNTHETIC MECHANICS REPLAY ONLY; declared resolution/cost values are constructed test data, not Lab empirical estimates',
        'initial_unresolved_mass':5.0,
        'final_unresolved_mass':c.unresolved_mass,
        'selected_tests':[r['plan']['selected_test_id'] for r in rows if r['plan']['selected_test_id']],
        'selected_compute_seconds':total_compute,
        'exhaustive_single_test_compute_seconds':20.0,
        'protected_validation_selected':protected_selected,
        'unquantified_test_selected':unknown_selected,
        'rounds':rows,
    }
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return out
if __name__=='__main__':
    r=run(); print(json.dumps({k:r[k] for k in ('selected_tests','initial_unresolved_mass','final_unresolved_mass','selected_compute_seconds','protected_validation_selected','unquantified_test_selected')},indent=2))
