import json,numpy as np
from pathlib import Path
from pcfdlw import closure_fidelity_decision_selection as f
y=np.array([[1.,0.],[0.,1.],[1.,0.],[0.,1.]])
unsafe_train=y.copy(); safe_train=y.copy(); safe_train[0]=[.4,.6]
unsafe_val=1-y; safe_val=y.copy()
r=f({'unsafe':unsafe_train,'safe':safe_train},y,{'unsafe':unsafe_val,'safe':safe_val},y,[[1,0],[0,1]],initial_action_exposure=[.5,.5],closure_violation={'unsafe':.3,'safe':.01},predictive_improvement={'unsafe':.2,'safe':.1},allowed_closure_rate=.1,min_predictive_improvement=.05)
out={'model_version':'V2P030_PCFDLW_V1','result':r.to_dict(),'mechanism_removing_comparator':{'blind_selected':r.blind_selected,'blind_validation_regret':r.blind_validation_regret},'evidence_boundary':'synthetic recursive-state certification plus decision-loss shell only'}
Path('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
