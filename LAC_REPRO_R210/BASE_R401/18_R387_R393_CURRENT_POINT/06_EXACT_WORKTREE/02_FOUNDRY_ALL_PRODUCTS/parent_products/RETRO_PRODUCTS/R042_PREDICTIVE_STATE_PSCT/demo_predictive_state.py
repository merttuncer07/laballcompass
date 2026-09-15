import json

import numpy as np

from psct import discover_predictive_states


rng = np.random.default_rng(42)
transition = np.array([
    [.45, .45, .05, .05], [.45, .45, .05, .05],
    [.10, .10, .40, .40], [.10, .10, .40, .40],
])
sequence = [0]
for _ in range(29999):
    sequence.append(int(rng.choice(4, p=transition[sequence[-1]])))

closed = discover_predictive_states(sequence, history_length=1, probability_tolerance=.03)

parity = [0, 1]
for _ in range(29998):
    probability_one = .8 if parity[-1] == parity[-2] else .2
    parity.append(int(rng.random() < probability_one))
not_closed = discover_predictive_states(parity, history_length=2, probability_tolerance=.03)

print(json.dumps({
    "closed_construction": {
        "observable_contexts": closed.observed_context_count,
        "predictive_states": closed.predictive_state_count,
        "compression_fraction": closed.compression_fraction,
        "log_loss_improvement_vs_memoryless": closed.predictive_log_loss_improvement,
        "closure_violation_rate": closed.closure_violation_rate,
        "state_contexts": [[list(context) for context in state.contexts] for state in closed.states],
        "status": closed.status,
    },
    "one_step_accurate_but_not_closed_construction": {
        "contexts": not_closed.observed_context_count,
        "predictive_states": not_closed.predictive_state_count,
        "closure_violation_rate": not_closed.closure_violation_rate,
        "status": not_closed.status,
    },
}, indent=2))
