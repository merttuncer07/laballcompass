# Value-first benchmark batch 2

## RX-070 — RelationalMotif search
The specific color-coding transfer fails the product gate. On coherent motifs, beam-5000 and
color-coding both reach 100% detection and 100% planted-edge recall, but color-coding is ~41.6x
slower across scaling. Exact calibration shows beam reaches the exact optimum 6/6 times.
However isolated top-edge detection has only 16.7% power, proving that relational motif aggregation
itself is valuable. Product salvage: beam/specialized relational motif engine, not color-coding.

## RX-025 — ZeroCauseMetadata
All observed values are zero. Adding observation threshold/gap/policy metadata to a strong
context/history baseline moves hidden-nonzero AUC .6717 -> .7543 and log-loss .4010 -> .3503,
10/10 seeds. Downstream escalation AUC .5985 -> .6338. Metadata shuffle and an uninformative
observation-process control remove the gain.

## RX-047 — ReliabilityTemperedEvidence
Against a hard switch that already knows source variances, continuous reliability weighting lowers
MSE by 24–44% and decision regret by 19–38% during the proxy-to-direct transition. But stale proxy
bias can make the blend worse than switching fully to direct; a bias/drift monitor is mandatory.

## RX-058 — OptionValueCapacityReserver
State-contingent reserve raises median revenue 160.01 -> 185.50 (+15.93%) over an already optimized
single reserve and increases high-value service rate by 43.6 percentage points. Uninformative signal
and no-premium controls collapse the gain. Flipped signal semantics cause -19.5% harm, so the product
must fall back to static protection when signal calibration breaks.

## RX-029 — ClusterCauseDiscriminator
Pooled association strength is deliberately matched between direct-interaction and latent-intensity
worlds. Pooled baseline AUC is .4896; environment-invariance features reach .7773 and improve
log-loss .6938 -> .5605. No-environment-shift control returns to chance. If environment changes
the candidate mechanism itself, the method misclassifies 100% of direct-interaction systems as
latent; qualified environments are a hard gate.
