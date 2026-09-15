
from __future__ import annotations

def tipping_aware_testing_wealth(explore_fn, mechanism_cls, controller_cls, *, mechanisms,
        baseline_retention, retention_grid, required_energy, p_values, alpha=.10,
        baseline_gamma_power=1.6, near_tipping_gamma_power=2.5, proximity_threshold=.20):
    """Use failure-path tipping proximity to choose the time profile of a fixed alpha budget.

    Removal control uses the identical TestingWealthController and p-value stream but
    never receives the FPTE state, so it keeps the baseline gamma profile.
    """
    tip=explore_fn(mechanisms,baseline_retention=baseline_retention,retention_grid=retention_grid,required_energy=required_energy)
    if tip.tipping_retention is None:
        proximity=float('inf')
    else:
        proximity=abs(float(baseline_retention)-float(tip.tipping_retention))
    gp=float(near_tipping_gamma_power if proximity<=proximity_threshold else baseline_gamma_power)
    def run(power):
        c=controller_cls(len(p_values),alpha=alpha,gamma_power=power)
        out=[c.test(p) for p in p_values]
        return {'gamma_power':power,'discoveries':sum(int(x['reject']) for x in out),'trajectory':out}
    cand=run(gp); ctrl=run(float(baseline_gamma_power))
    return {'tipping_status':tip.status,'tipping_retention':tip.tipping_retention,'tipping_proximity':proximity,
            'candidate':cand,'mechanism_removed':ctrl,
            'discovery_gain':cand['discoveries']-ctrl['discoveries'],
            'status':'TIPPING_PROXIMITY_REALLOCATES_TESTING_WEALTH' if gp!=baseline_gamma_power else 'TIPPING_STATE_DOES_NOT_REALLOCATE_WEALTH'}
