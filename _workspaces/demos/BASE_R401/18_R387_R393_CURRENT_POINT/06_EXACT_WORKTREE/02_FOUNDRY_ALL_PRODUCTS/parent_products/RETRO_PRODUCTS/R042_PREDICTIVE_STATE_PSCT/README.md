# PSCT v0.1 — Predictive-State Discovery and Closure Tester

PSCT defines state by observable consequences rather than an invented latent regime. It estimates
the next-symbol distribution of every observed history, merges histories only within a declared
probability tolerance, and reports the resulting predictive compression and log-loss gain.

The second stage is essential: after each possible new observation, all histories inside one state
should update into the same next predictive state. PSCT measures violations and unresolved updates
separately. Thus a partition that forecasts one step well but is not recursively updateable remains a
useful failed state candidate rather than being advertised as a closed model.

The current shell handles finite observed alphabets and finite history suffixes. It is immediately
usable for event-coded market, machine, biological, and operational streams.

Run `python -m unittest -v test_psct.py` and `python demo_predictive_state.py`.
