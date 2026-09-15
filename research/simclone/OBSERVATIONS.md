# SimClone: paper versus released implementation

Examined 2026-09-14. Primary paper: https://arxiv.org/html/2407.12802v1 . Released package: https://zenodo.org/records/7613379 . Files and hashes are in SOURCES.json. Reference files were read, not run or imported into the product.

- `data_process.py` injects sampled rows or columns, assigns clone/non-clone labels using a fraction threshold, then shuffles rows and columns before producing value-similarity features. At the inclusive 10% boundary its positive and negative random ranges overlap. The code itself does not establish real audit utility.
- `train.py` performs a random split of pair-level feature rows (`train_test_split`, random_state=42). It does not group the split by original source table. This permits tables to occur on both sides; actual leakage frequency was not measured. Reported pair-level accuracy cannot simply be assumed to generalize to entirely unseen workbooks.
- This Zenodo record contains code and a 59 MB UCI pickle; it does not list the EUSES/Enron labeled real-pair corpus described in the paper. The pickle was not downloaded or deserialized. No reproduced SimClone score is claimed.
- Zenodo metadata says CC-BY-4.0; the package readme says CC-BY-NC-SA-4.0 for code. Both statements are retained in SOURCES.json. No reference implementation is incorporated into the app.
- Our typed-anchor matcher is an independently written deterministic review aid with narrower scope than SimClone: it searches translations, not arbitrary row/column permutations. Neither method's published name establishes superiority over a baseline. No new scientific novelty is claimed for clone matching.

Observed external fixture: Apache POI's independently authored FormulaEvalTestData_Copy.xlsx contains two rectangular tables with 63 identical literal positions and two formula/literal positions. The application found them without supplied cell coordinates. Its report makes that observation inspectable; it does not infer who copied whom, authenticity, audit opinion, or general precision/recall.
