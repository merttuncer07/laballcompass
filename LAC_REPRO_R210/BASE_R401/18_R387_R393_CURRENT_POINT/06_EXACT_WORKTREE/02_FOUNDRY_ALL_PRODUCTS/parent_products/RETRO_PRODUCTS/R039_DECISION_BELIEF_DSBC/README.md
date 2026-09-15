# DSBC v0.1 — Decision-Sufficient Belief Compressor

DSBC compresses posterior belief vectors according to what a downstream decision actually needs.
It receives hidden-state/action utilities and merges beliefs only when one common action stays within
an explicit regret tolerance for every member.

The output contains cluster representatives, prescribed actions, assignments, action margins,
cluster and global regret, and a certificate that no remaining pairwise merge fits the requested
tolerance. It can therefore discard distinctions that are irrelevant to action while preserving two
statistically similar beliefs when they imply materially different decisions.

This v0.1 product certifies the observed belief set; it does not claim Markov closure for unseen
belief dynamics. That separate predictive/transition question remains explicit rather than being
smuggled into the compression claim.

Run `python -m unittest -v test_dsbc.py` and `python demo_belief_compression.py`.
