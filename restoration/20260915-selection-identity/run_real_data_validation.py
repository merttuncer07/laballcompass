"""Replay the existing fixed-seed real digits pilot and record selection identity.

No manufactured audit dataset is used. Error matrices come from fitted models on
the original published handwritten-digit observations. This is not a banking test.
"""
from pathlib import Path
import hashlib, importlib.metadata, importlib.util, json, sys
import numpy as np

HERE=Path(__file__).resolve().parent
LAB=HERE.parents[1]
CORE=LAB/'LAC_REPRO_R210/BASE_R401/18_R387_R393_CURRENT_POINT/06_EXACT_WORKTREE/02_FOUNDRY_ALL_PRODUCTS'
sys.path.insert(0,str(CORE/'products/P001_DREW'))
import real_data_pilot_digits as pilot
from parents.acsa import audit_adaptive_selection
from sklearn.datasets import load_digits

captured={}
original=pilot.audit_decision_model_selection
def observed(*args,**kwargs):
    audit=original(*args,**kwargs)
    names,search_losses=pilot.decision_regret_matrix(args[0],args[1],args[4],
        initial_action_exposure=kwargs['initial_action_exposure'])
    _,holdout_losses=pilot.decision_regret_matrix(args[2],args[3],args[4],
        initial_action_exposure=kwargs['initial_action_exposure'])
    assert audit.decision_loss.selected_by_training_decision_loss==audit.adaptive_selection.selected_candidate
    assert audit.protected_best_candidate==names[int(np.argmin(holdout_losses.mean(axis=0)))]
    captured.update(selected=audit.decision_loss.selected_by_training_decision_loss,
        audited=audit.adaptive_selection.selected_candidate,
        selection_rule=audit.adaptive_selection.selection_rule,
        plain_holdout_argmin=names[int(np.argmin(holdout_losses.mean(axis=0)))],
        drew_status=audit.status)
    spec=importlib.util.spec_from_file_location('before_threshold_acsa',HERE/'acsa-before-finite-threshold.py')
    before=importlib.util.module_from_spec(spec);sys.modules[spec.name]=before;spec.loader.exec_module(before)
    threshold_checks=[]
    for value,label in [(float('nan'),'NaN'),(float('inf'),'+Infinity')]:
        old=before.audit_adaptive_selection(search_losses,holdout_losses,
            candidate_names=names,material_regret=value,bootstrap_samples=100)
        try:
            audit_adaptive_selection(search_losses,holdout_losses,
                candidate_names=names,material_regret=value,bootstrap_samples=100)
        except ValueError as exc:
            threshold_checks.append({'threshold':label,'before_status':old.status,
                'actual_selected_holdout_regret':old.selected_holdout_regret,'after':str(exc)})
        else:raise AssertionError('Invalid threshold was accepted')
    captured['threshold_checks_on_actual_model_losses']=threshold_checks
    for name,losses in [('search',search_losses),('holdout',holdout_losses)]:
        np.savetxt(HERE/f'digits-{name}-model-errors.csv',losses,delimiter=',',header=','.join(names),comments='',fmt='%.0f')
    return audit
pilot.audit_decision_model_selection=observed
result=pilot.run()
x,y=load_digits(return_X_y=True)
record={'pilot':result,'identity_check':captured,
    'environment':{name:importlib.metadata.version(name) for name in ('numpy','scipy','scikit-learn','joblib','threadpoolctl')},
    'source':'https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_digits.html',
    'dataset_shape':list(x.shape),'dataset_sha256':hashlib.sha256(x.tobytes()+y.tobytes()).hexdigest(),
    'scope':'One unchanged fixed-seed, real-data classification pilot. Row splits do not establish writer-group independence. Protected argmin is the ordinary validation baseline; no unique DREW accuracy gain or banking-field benefit is demonstrated.'}
(HERE/'real-data-validation.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))
