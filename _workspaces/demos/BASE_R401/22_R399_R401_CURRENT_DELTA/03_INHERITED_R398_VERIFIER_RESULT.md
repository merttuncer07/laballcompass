# Inherited R398 verifier result

## What was checked

The supplied file `LABALLCOMPASS_FINAL_RETIREMENT_HANDOFF_R398_2026-08-30.zip` was verified before
extraction against both supplied SHA-256 text files.

- Actual ZIP SHA-256: `ed3644144583921ac916c803511c08ba8caff72d030f5b1406580b2ff8f85abd`
- Both supplied SHA files contain the same digest.
- ZIP entries: 12,201.
- Extracted files: 10,320.
- Extracted file bytes: 889,427,476.
- The entry/file difference is directory entries; extracted file count and byte total match the ZIP.

## Inherited Windows verifier limitation

The byte-preserved R398 `09_VERIFY_ARCHIVE.py` was run after extraction. It checked 10,319 manifest
files but returned `FAIL`, reporting 539 `MISSING` paths. Inspection showed the reported files are
present. Their deeply nested absolute paths exceed the traditional Win32 path-length boundary, and
ordinary Python `pathlib` existence checks fail at this package location.

This means:

- R401 did not delete those 539 paths; they are present in the exact user-supplied R398 ZIP.
- Every byte actually present in the supplied ZIP is retained.
- The original verifier is preserved rather than silently rewritten.
- `25_VERIFY_R401_HANDOFF.py` uses the Windows extended path form and
  `24_R401_INTEGRITY_SHA256.tsv` is the accurate integrity surface for the R401 package.

## Authority consequence

Do not cite the inherited R398 verifier as PASS **on this deep Windows path**. Use the original
source-fidelity boundaries and the new long-path-aware R401 verifier. This path issue does not change
the separate R398 source-fidelity warning: recovered reference implementations must not be promoted
to byte-identical canonical source where the archive itself says those source bytes were lost.
