from .ugim import *
def test_cash_exposure_compounds(): assert abs(ugim(100,[.51,.51,.51])['exposure_fraction']-.51**3)<1e-12
def test_control_separate_from_economics(): assert ugim(100,[.51,.51,.51])['controlled'] and ugim(100,[.51,.51,.51])['economic_incidence']<20
def test_residual_is_explicit(): assert ugim(100,[.51,.51,.51])['unassigned_residual']>80

