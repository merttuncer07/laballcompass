from .lida import *
def test_subcritical_persistence_can_alarm(): assert lida([1]*10,[.8]*10,dangerous_rms=1,baseline_rms=.7,scale=.1,cap=1,alarm_sum=5,min_cycles=5)['alarm']
def test_no_single_dangerous_window_required(): assert lida([1]*10,[.8]*10,dangerous_rms=1,baseline_rms=.7,scale=.1,cap=1,alarm_sum=5,min_cycles=5)['dangerous_windows']==0
def test_quadrature_no_work_no_alarm(): assert not lida([0]*10,[.8]*10,dangerous_rms=1,baseline_rms=.7,scale=.1,cap=1,alarm_sum=5,min_cycles=5)['alarm']

