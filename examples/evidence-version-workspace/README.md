# Evidence Version Intelligence — genuine many-file demonstration

This demonstration starts from one folder rather than a hand-selected A/B pair.
It assembles, without modifying the originals:

- the genuine Ofgem ED2 PCFM January 2025 workbook;
- the genuine January 2026 revision under an unrelated local filename;
- an exact byte copy of the 2025 file under another filename; and
- the unrelated genuine SONI financial model.

The import should produce three exact evidence versions, identify one duplicate
occurrence, propose the two Ofgem versions for confirmation, and leave both
Ofgem/SONI pairings as no-confident-match assessments. Filename similarity is
reported only as context and is not a candidate rule.

Run from the repository root with a new output directory:

```sh
.venv/bin/python examples/evidence-version-workspace/reproduce.py \
  --output /tmp/evidence-version-demo
```

The script explicitly performs the human confirmation step on behalf of the
reproduction and supplies the 2025 version as `before`. It then generates the
confirmed comparison through the ordinary workbench engine and checks the
preserved Ofgem counts. Open `workspace/index.html` to inspect the artifact
history and comparison link. `result.json` records the observed IDs, hashes,
candidate explanation, comparison counts and original-file immutability check.

The concise result preserved in this directory records the verified 18 September
2026 run. The reproduction writes its full run-specific result into the requested
output directory; random artifact/relationship IDs and absolute output paths are
intentionally not copied into the preserved summary.

This is software and real-file validation. A likely revision remains a proposal;
similar content does not prove provenance, and structural impact does not prove
numeric effect or an audit misstatement.
