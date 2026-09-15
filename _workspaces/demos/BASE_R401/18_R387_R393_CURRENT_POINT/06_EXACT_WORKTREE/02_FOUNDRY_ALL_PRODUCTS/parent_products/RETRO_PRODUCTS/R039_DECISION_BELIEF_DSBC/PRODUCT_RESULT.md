# R-039 product result — DSBC v0.1

**Product route:** standalone decision-sufficient belief-state compressor  
**Result:** working product; 4/4 focused tests pass

DSBC replaces hidden-state accuracy as the sole compression target with a direct bound on downstream
decision loss. Every accepted cluster carries a per-belief regret certificate; refused merges remain
separate rather than being forced to hit a predetermined compression count.

Prior-art overlap remains attached as provenance and does not block the working decision service.

In the first eight-hidden-state construction, DSBC compressed 120 posterior beliefs into three
decision states—a 97.5% reduction in stored belief cases—with exactly zero realized decision regret.
Each resulting cluster selected one of the three intended actions and contained 40 beliefs. A
separate counterexample showed that two beliefs sharing the same most-likely hidden state remain
separate when their optimal actions differ.
