
from __future__ import annotations
import numpy as np

def safety_boundary_information_choice(ccvc_cls, cbia_eval, *, low_state, high_state, prior_high=.5, nominal_control=.8, step=.1, measurement_cost=.01):
    """Resolve state only if the CCVC-filtered action differs across the calibrated shell.

    Removal control uses the prior-midpoint state to filter once and applies that control to
    either latent state. Candidate uses CBIA to buy the state measurement when the low/high
    CCVC-safe controls differ enough to justify cost.
    """
    if not 0 < prior_high < 1 or measurement_cost < 0: raise ValueError('invalid prior/cost')
    F=np.zeros((2,2)); B=np.array([[1.],[-1.]])
    C=np.array([[1.,1.]]); cv=np.array([1.])
    A=np.array([[1.,0.],[0.,1.],[-1.,0.],[0.,-1.]])
    b=np.array([.8,.8,0.,0.])
    sys=ccvc_cls(F,B,C,cv,A,b,np.array([-1.]),np.array([1.]))
    lo=np.asarray(low_state,float); hi=np.asarray(high_state,float)
    mid=(1-prior_high)*lo+prior_high*hi
    def filtered(x): return float(sys.filter_control(x,np.array([nominal_control]),step)[0])
    ulo,uhi,umid=filtered(lo),filtered(hi),filtered(mid)
    boundary=abs(ulo-uhi)>1e-9
    # one-step safety violation under the midpoint/removal control
    def next_state(x,u): return x+step*(B@np.array([u]))
    def violation(x,u): return max(0., float(np.max(A@next_state(x,u)-b)))
    removal_expected=(1-prior_high)*violation(lo,umid)+prior_high*violation(hi,umid)
    resolved_expected=(1-prior_high)*violation(lo,ulo)+prior_high*violation(hi,uhi)
    gross=removal_expected-resolved_expected
    selected=()
    if boundary:
        records=[{'name':'state_probe','cost':1.0,'value':gross-measurement_cost},{'name':'skip_probe','cost':1.0,'value':0.0}]
        selected=tuple(cbia_eval(records,budget=1)['selected'])
    measure='state_probe' in selected
    cand_violation=resolved_expected if measure else removal_expected
    cand_cost=cand_violation+measurement_cost if measure else cand_violation
    return {
      'low_safe_control':ulo,'high_safe_control':uhi,'midpoint_control':umid,
      'action_boundary_crossed':boundary,'measurement_used':measure,'cbia_selected':selected,
      'removal_expected_violation':removal_expected,'resolved_expected_violation':resolved_expected,
      'candidate_violation_plus_measurement_cost':cand_cost,
      'gain_vs_removed_information':removal_expected-cand_cost,
      'status':'SAFETY_BOUNDARY_MEASURED' if measure else ('BOUNDARY_PRESENT_BUT_MEASUREMENT_NOT_WORTH_COST' if boundary else 'NO_CONTROL_BOUNDARY')
    }
