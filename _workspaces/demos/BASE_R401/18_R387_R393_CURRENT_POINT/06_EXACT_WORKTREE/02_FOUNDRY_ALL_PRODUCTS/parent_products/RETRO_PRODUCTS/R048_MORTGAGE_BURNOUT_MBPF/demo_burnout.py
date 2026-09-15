import json

from mbpf import forecast_burnout_prepayment


result = forecast_burnout_prepayment(
    cohort_size=20_000,
    base_monthly_prepayment_rates=[.025] * 72,
    propensity_multipliers=[.25, 1.0, 3.0],
    initial_class_weights=[.45, .40, .15],
    monthly_default_rates=.0015,
)
print(json.dumps(result.to_dict(), indent=2))
