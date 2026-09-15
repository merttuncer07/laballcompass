# R-014 product result — ACSA v0.1

**Product route:** standalone adaptive candidate-selection audit  
**Result:** working product; 4/4 tests pass

ACSA retains every searched candidate and compares the data-selected winner with an untouched
evaluation sample. It reports optimism, holdout regret, family-wide gaps, uncertainty, and bootstrap
selection frequencies rather than converting the audit into an idea-deletion gate.

In the first construction, selection data chose `adaptive_decoy` with loss 0.17562. Its holdout loss
was 0.42906, while `real_improvement` achieved 0.27128. ACSA exposed 0.25344 optimism and 0.15778
holdout regret; the decoy's 95% holdout interval was [0.42232, 0.43556]. All candidate results remain
available for diagnosis and redesign.

The product works independently for model, prompt, policy, design, or process searches.
