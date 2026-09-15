from __future__ import annotations
import json
from pathlib import Path
from test_swcapl import case

shares=[.20,.35,.50,.65,.80]
seeds=range(3)
rows=[]
for share in shares:
    gains=[]; cand_b=[]; ctl_a=[]
    for seed in seeds:
        r=case(seed=seed,target_share=share)
        gain=r.target_validation_gain_vs_removed_mechanism
        gains.append(gain)
        cand_b.append(sum(w[1] for w in r.candidate_validation_weights)/len(r.candidate_validation_weights))
        ctl_a.append(sum(w[0] for w in r.control_validation_weights)/len(r.control_validation_weights))
    rows.append({
        'target_regime1_share':share,
        'seeds':len(gains),
        'mean_gain_vs_removed_mechanism':sum(gains)/len(gains),
        'min_gain':min(gains),'max_gain':max(gains),
        'positive_seeds':sum(g>0 for g in gains),
        'mean_candidate_weight_target_asset':sum(cand_b)/len(cand_b),
        'mean_control_weight_source_asset':sum(ctl_a)/len(ctl_a),
    })
out={
 'product_id':'V2P053','release':'R392_SHADOW','sweep':rows,
 'working_region':'declared target distribution is sufficiently shifted toward regime1 and supplied source-to-target weights are correct',
 'failure_region':'using the same target-shift weights when the actual target remains source-like can worsen target validation objective',
 'nonclaim':'synthetic sensitivity only; not empirical transportability or financial performance evidence'
}
Path('BENCHMARK_SWEEP_RESULT.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
