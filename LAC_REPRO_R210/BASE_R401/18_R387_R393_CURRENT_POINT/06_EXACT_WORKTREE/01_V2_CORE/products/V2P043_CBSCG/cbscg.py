
from __future__ import annotations
import numpy as np

def _project_cost(guard_cls, incidence, demand, project):
    r=guard_cls.wardrop(np.asarray(incidence,float),float(demand),np.asarray(project['slopes'],float),np.asarray(project['intercepts'],float))
    if not r['success']: raise RuntimeError('Wardrop solver failed')
    return float(r['average_user_cost'])

def boundary_information_capacity_choice(guard_cls, cbia_eval, incidence, projects, *, low_demand, high_demand,
                                         high_probability=.5, measurement_cost=.02, measurement_budget=1):
    """Use endogenous Wardrop response to decide whether demand information can change the capacity action.

    CBIA is invoked only on the action-changing shell. Its measurement value is the
    expected decision-regret avoided by resolving the low/high demand regime.
    """
    if len(projects)!=2: raise ValueError('exactly two projects required for V0')
    if not 0 < high_probability < 1 or measurement_cost < 0: raise ValueError('invalid probability/cost')
    names=sorted(projects)
    def costs(d): return {n:_project_cost(guard_cls,incidence,d,projects[n]) for n in names}
    low=costs(low_demand); high=costs(high_demand)
    low_best=min(low,key=low.get); high_best=min(high,key=high.get)
    midpoint=(1-high_probability)*float(low_demand)+high_probability*float(high_demand)
    mid=costs(midpoint); baseline=min(mid,key=mid.get)
    baseline_expected=(1-high_probability)*low[baseline]+high_probability*high[baseline]
    resolved_expected=(1-high_probability)*low[low_best]+high_probability*high[high_best]
    gross_gain=baseline_expected-resolved_expected
    boundary_crossed=low_best!=high_best
    selected=()
    if boundary_crossed:
        records=[{'name':'demand_probe','cost':1.0,'value':gross_gain-measurement_cost},
                 {'name':'skip_probe','cost':1.0,'value':0.0}]
        selected=tuple(cbia_eval(records,budget=measurement_budget)['selected'])
    measure='demand_probe' in selected
    candidate_expected=resolved_expected+measurement_cost if measure else baseline_expected
    return {
      'low_best':low_best,'high_best':high_best,'baseline_midpoint_project':baseline,
      'action_boundary_crossed':boundary_crossed,'cbia_selected':selected,'measurement_used':measure,
      'gross_information_value':gross_gain,'measurement_cost':measurement_cost,
      'baseline_expected_user_cost':baseline_expected,'candidate_expected_user_cost':candidate_expected,
      'gain_vs_removed_information_acquisition':baseline_expected-candidate_expected,
      'low_costs':low,'high_costs':high,'midpoint_costs':mid,
      'status':'STRATEGIC_RESPONSE_BOUNDARY_MEASURED' if measure else ('BOUNDARY_PRESENT_BUT_MEASUREMENT_NOT_WORTH_COST' if boundary_crossed else 'NO_ACTION_BOUNDARY_NO_MEASUREMENT')
    }
