# V2P035 ISTAICC — Information-Search Tipping AICC

Ordinary information acquisition is myopic: channel value is immediate decision improvement minus cost. When acquisition friction and participation reinforce one another, a small measurement can move the system between low- and high-search equilibria. ISTAICC therefore adds the continuation value of the reachable participation equilibrium to the AICC-style channel score.

The fixed-point model is deliberately stylized and exposes all friction/network parameters. It demonstrates the mechanism only; it does not claim a calibrated social or market participation model.

Continuation value is incremental to the reachable no-action equilibrium at
`base_friction`. Both scenarios start at `current_participation`. Participation
that would occur without acquisition is not credited to a channel, and a fall
relative to no action reduces its score. A paid channel with no effect therefore
scores minus its cost. This does not establish calibrated real-world utility.
