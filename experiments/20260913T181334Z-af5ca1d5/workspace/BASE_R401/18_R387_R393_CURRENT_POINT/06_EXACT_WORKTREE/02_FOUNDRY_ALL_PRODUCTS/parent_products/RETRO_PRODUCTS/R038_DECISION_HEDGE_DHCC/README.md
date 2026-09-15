# DHCC v0.1 — Decision-focused Hedge Covariance Calibrator

DHCC chooses covariance regularization by the actual validation loss of the hedge it creates. For
each ridge candidate it builds hedge coefficients from training covariances, then measures untouched
residual variance, turnover, conditioning, and the declared combined decision loss.

This intentionally differs from selecting the covariance matrix that looks best in isolation. The
output compares the chosen hedge with both no hedge and the unregularized sample-covariance hedge.
Prior-art overlap remains provenance; realized action quality determines whether this shell works.

Run `python -m unittest -v test_dhcc.py` and `python demo_hedge.py`.
