# V2P049 SACAPL — Support-Aware Covariance Portfolio Policy Learner

R037 SACPS is composed directly with R041 CAPL. CAPL's constrained linear-softmax action map and turnover/cap feasibility rules are retained, while SACPS covariance replaces the unstructured sample covariance inside the policy risk objective.

This targets a specific failure: a policy can satisfy every action constraint but still learn against spurious finite-sample covariance edges that violate declared dependency support. The mechanism-removing control holds the CAPL architecture, search seed, feasible set, returns, risk aversion, and transaction costs fixed and changes only the risk covariance back to the raw sample estimate.

The deterministic benchmark is synthetic. It establishes that the interaction changes the learned policy and can reduce realized validation variance/raise validation certainty-equivalent in a declared sparse-support working region. It is not evidence of market alpha. With dense support and zero shrinkage, SACPS equals raw covariance and the product collapses exactly to the control.

Status: **R388 shadow only; not canonical until full Lab quality/regression/authority promotion gates pass.**
