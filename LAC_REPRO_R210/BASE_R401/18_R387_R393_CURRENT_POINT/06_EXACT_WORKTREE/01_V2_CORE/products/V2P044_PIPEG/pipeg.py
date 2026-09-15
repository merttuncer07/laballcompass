
from __future__ import annotations
import numpy as np

def _channel_total_variation(design):
    # Binary-state experiment informativeness: TV distance between signal laws.
    return 0.5*sum(abs(float(s.probability_given_state_one)-float(s.probability_given_state_zero)) for s in design.signals)

def producer_incentive_aware_persuasion(design_fn, equilibrium_fn, *, prior_state_one,
        action_names, receiver_payoffs, sender_payoffs, base_copy_friction,
        disclosure_to_friction=0.8, producer_values=(1.,1.,1.), producer_costs=(.55,.55,.55),
        spillover=.10, future_information_weight=.50):
    """Compare unrestricted persuasion with no-information after endogenous producer response.

    The supplier's implementable channel changes disclosure intensity.  That intensity
    changes the copy-friction input of the information-production equilibrium.  The
    mechanism-removing comparator optimizes current sender payoff only and therefore
    ignores the downstream equilibrium externality.
    """
    if not 0 <= disclosure_to_friction <= 1: raise ValueError('disclosure_to_friction must be in [0,1]')
    if not 0 < base_copy_friction <= 1 or future_information_weight < 0: raise ValueError('invalid friction/weight')
    design=design_fn(prior_state_one=prior_state_one, action_names=action_names,
                     receiver_payoffs=receiver_payoffs, sender_payoffs=sender_payoffs)
    info=_channel_total_variation(design)
    persuasion_friction=max(0., float(base_copy_friction)*(1-float(disclosure_to_friction)*info))
    eq_p=equilibrium_fn(persuasion_friction, producer_values, producer_costs, spillover=spillover)
    eq_n=equilibrium_fn(float(base_copy_friction), producer_values, producer_costs, spillover=spillover)
    current_p=float(design.optimized_sender_value); current_n=float(design.no_information_sender_value)
    total_p=current_p+float(future_information_weight)*float(eq_p['accessible_information'])
    total_n=current_n+float(future_information_weight)*float(eq_n['accessible_information'])
    candidate='PERSUASION' if total_p>=total_n else 'NO_INFORMATION'
    removed='PERSUASION' if current_p>=current_n else 'NO_INFORMATION'
    candidate_total=max(total_p,total_n)
    removed_total=total_p if removed=='PERSUASION' else total_n
    return {
      'channel_total_variation':info,'persuasion_copy_friction':persuasion_friction,
      'persuasion_active_producers':int(eq_p['discoveries']),'noinfo_active_producers':int(eq_n['discoveries']),
      'persuasion_accessible_information':float(eq_p['accessible_information']),
      'noinfo_accessible_information':float(eq_n['accessible_information']),
      'current_sender_payoff_persuasion':current_p,'current_sender_payoff_noinfo':current_n,
      'candidate_choice':candidate,'mechanism_removed_choice':removed,
      'candidate_total_value':candidate_total,'mechanism_removed_total_value':removed_total,
      'gain_vs_removed_production_externality':candidate_total-removed_total,
      'status':'PRODUCER_INCENTIVE_CHANGES_DISCLOSURE_POLICY' if candidate!=removed else 'PRODUCTION_EXTERNALITY_DOES_NOT_CHANGE_POLICY'
    }
