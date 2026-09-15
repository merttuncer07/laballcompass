from .rala import *
def test_exact_lumpability_can_be_unsafe(): assert rala(lumpability_error=0,hidden_eigenvalue=.94,current_exposure=2,recovery_steps=60)['status']=='EXACTLY_LUMPABLE_BUT_RESILIENCE_UNSAFE'
def test_fast_hidden_mode_passes(): assert rala(lumpability_error=0,hidden_eigenvalue=.4,current_exposure=2,recovery_steps=2)['safe']
def test_inexact_not_certified_safe(): assert not rala(lumpability_error=.1,hidden_eigenvalue=.4,current_exposure=0,recovery_steps=0)['safe']

