# Evidence Version Intelligence — genuine many-file demonstration

This demonstration starts from one folder rather than a hand-selected A/B pair.
It assembles, without modifying the originals:

- the genuine Ofgem ED2 PCFM January 2025 workbook;
- the genuine January 2026 revision under an unrelated local filename;
- an exact byte copy of the 2025 file under another filename; and
- the unrelated genuine SONI financial model.

The import should produce three content-addressed `FileBlob` records, identify
one duplicate `FileOccurrence`, propose the two Ofgem blobs for confirmation,
and leave both
Ofgem/SONI pairings as no-confident-match assessments. Filename similarity is
reported only as context and is not a candidate rule.

Import does not silently create logical evidence versions. Confirmation creates
two `EvidenceVersion` records inside one `EvidenceArtifact`; each version belongs
to exactly that artifact and points to its immutable blob. The same blob may back
a separately and explicitly created version in another artifact without copying
the stored bytes.

Run from the repository root with a new output directory:

```sh
.venv/bin/python examples/evidence-version-workspace/reproduce.py \
  --output /tmp/evidence-version-demo
```

The script explicitly performs the human confirmation step on behalf of the
reproduction and supplies the 2025 version as `before`. It then generates the
confirmed comparison through the ordinary workbench engine and checks the
preserved Ofgem counts. Open `workspace/index.html` to inspect the artifact
history, blob occurrences and comparison link. `result.json` records the observed IDs, hashes,
candidate explanation, comparison counts and original-file immutability check.

Each confirmed relationship also receives `triage/index.html`. This view groups
nearby changes by deterministic change type, exposes formula/literal transitions,
uses supported row correspondence as movement evidence, and sorts or filters by
resolved terminal-formula reach. The raw same-layout report remains linked and
unchanged. [Mission #2 validation](mission-2-validation.json) preserves the
Ofgem metrics, synthetic edge-case outcomes and measured runtime.

Confirmed decisions are correctable without erasing history. The workspace CLI
supports `withdraw`, `reassign`, `correct-order`, and `rename-artifact`; every
correction requires a reason and appends a durable decision-history event. Old
relationships and comparison runs remain present with withdrawn or superseded
status.

The concise result preserved in this directory records the verified 18 September
2026 run. The reproduction writes its full run-specific result into the requested
output directory; random artifact/relationship IDs and absolute output paths are
intentionally not copied into the preserved summary.

This is software and real-file validation. A likely revision remains a proposal;
similar content does not prove provenance, and structural impact does not prove
numeric effect or an audit misstatement.
