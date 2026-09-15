import json

from mcris import Intervention, MonthlyTransitionRates, simulate_mortgage_intervention


result = simulate_mortgage_intervention(
    cohort_size=10_000,
    horizon_months=60,
    baseline_rates=MonthlyTransitionRates(.0025, .010, .008, .065, .004, .14),
    intervention=Intervention(
        performing_default_multiplier=.75,
        performing_delinquency_multiplier=.72,
        delinquent_default_multiplier=.60,
        delinquent_cure_multiplier=1.35,
        performing_prepay_multiplier=1.08,
        one_time_cost_per_loan=650,
    ),
    balance_per_loan=180_000,
    recovery_fraction=.55,
    prepayment_cost_fraction=.008,
)
print(json.dumps(result.to_dict(), indent=2))
