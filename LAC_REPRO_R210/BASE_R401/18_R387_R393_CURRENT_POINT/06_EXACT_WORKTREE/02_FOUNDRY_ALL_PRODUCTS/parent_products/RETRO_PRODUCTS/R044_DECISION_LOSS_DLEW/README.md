# DLEW v0.1 — Decision-Loss Evaluation Workbench

DLEW compares predictive models twice: first by ordinary prediction RMSE, then by the realized
payoff and regret of the actions their predictions induce. It learns the model-selection rule on a
training segment and measures the selected policy on a separate validation segment.

Users supply an explicit finite action set, outcome exposures, and transaction cost. The workbench
retains every chosen action, turnover, oracle-relative regret, action agreement, payoff, and
prediction error. Common-mode prediction errors can therefore look terrible statistically while
leaving a relative decision intact; small errors around an action boundary can do the reverse.

DLEW does not require decision selection to outperform. Agreement or failure is a measured result,
and every candidate remains visible.

Run `python -m unittest -v test_dlew.py` and `python demo_decision_loss.py`.
