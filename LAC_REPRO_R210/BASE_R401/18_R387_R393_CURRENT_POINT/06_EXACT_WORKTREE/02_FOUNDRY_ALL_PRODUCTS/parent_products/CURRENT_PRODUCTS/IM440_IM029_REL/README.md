# Relational Evidence Localizer

REL turns **IM-440 → IM-029** into a working discrepancy-localization engine.

Different parties generate order, invoice, receipt, transport, and payment records because each has
its own operational or financial reason to do so. REL converts equality/tolerance relations among
those records into a violation pattern and ranks the smallest record set capable of producing it.

The localizer supports coherent two-record alteration: two changed records may still agree with each
other while disagreeing with independently generated evidence. This is why redundant cross-party
relations can locate a hidden error rather than merely flag a mismatch.

Pure XOR patterns can be symmetric between a culprit set and its graph complement. REL therefore
requires explicit alteration priors for evidence producers; independent anchor records should have
lower priors only when the operating design actually justifies that distinction.

## Run

```powershell
python -m unittest -v test_rel.py
python demo_relational_localization.py
```

## Product boundary

v0.1 supports numeric equality/tolerance relations, producer-specific alteration priors, and up to a
declared collusion size. Next layers are typed transformations, timestamps, missing documents, and a graph-design
module that recommends which new counterparty record would reduce localization ambiguity most.
