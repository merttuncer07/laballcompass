from .dder import *
def test_unequal_transport_instability_detected(): assert dder(.1,-.1,.2,exposure_threshold=.1)['unequal_transport_instability']
def test_material_exposure_alerts(): assert dder(.1,-.1,.2,exposure_threshold=.1)['alert']
def test_tiny_current_exposure_suppresses_alert(): assert not dder(.1,-.1,.001,exposure_threshold=.1)['alert']

