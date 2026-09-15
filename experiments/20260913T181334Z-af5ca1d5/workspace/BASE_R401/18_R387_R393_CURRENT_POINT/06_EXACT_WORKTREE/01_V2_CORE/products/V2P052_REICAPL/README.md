# V2P052 REICAPL — Relational-Evidence Impact Constraint-Aware Policy Learner

Candidate composition: `FOUNDRY:P028 REIS -> PARENT:R041 CAPL`.

REIS's consequence-aware safeguard allocation is converted into an **asset-specific feasible-cap vector before policy optimization**. A selected evidence record must have an explicit caller-supplied record→asset alignment; the tool does not infer that semantic mapping. Selected assets receive `protected_asset_cap`, other assets retain `base_asset_cap`.

The mechanism-removing comparator uses the same data, evolutionary optimizer, random seed, turnover/risk/cost settings, and validation objective with uniform base caps. A second ablation preserves heterogeneous caps but chooses records by posterior probability only, removing REIS's posterior×consequence contribution.

Evidence boundary: synthetic executable mechanism testing only. Benefit is explicitly conditional on the selected/aligned asset entering an adverse region; benign regions can make the cap harmful. This is not empirical financial validation or a novel-theory claim.
