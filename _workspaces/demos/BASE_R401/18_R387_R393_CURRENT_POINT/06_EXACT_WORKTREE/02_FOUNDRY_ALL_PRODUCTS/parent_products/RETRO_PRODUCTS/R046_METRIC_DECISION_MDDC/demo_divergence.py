import json
from mddc import diagnose_metric_decision_divergence
r=diagnose_metric_decision_divergence(
 [[.51,.48,.01],[.46,.52,.02]],
 {'near_metric':[[.48,.51,.01],[.51,.46,.03]],'far_but_safe':[[.70,.29,.01],[.25,.70,.05]],'exact':[[.51,.48,.01],[.46,.52,.02]]},
 [[1,0],[0,1],[0,0]])
print(json.dumps({'scores':[s.__dict__ for s in r.scores],'strongest_inversion':r.inversions[0].__dict__,
 'action_inversions':r.action_inversions,'ranking_inversions':r.ranking_inversions,'status':r.status},indent=2))
