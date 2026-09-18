# 2026-09-18 consolidation checkpoint

Canonical working tree: `/Users/mertalituncer/Developer/lab`.

The OpenCode temporary research files copied under `opencode-temp-provenance/`
were verified byte-for-byte against their original paths. The originals remain
untouched. `opencode-temp-SHA256.tsv` records source path, durable path, size,
and SHA-256.

R211 and R212 were imported from the `laballcompass` tree with cache files
excluded; 6 R211 files and 125 R212 files matched their source hashes.

The `laballcompass-fixes` tracked differences were not force-merged where the
canonical tree already had competing edits. Its complete tracked diff and
small untracked output/run provenance are retained under
`laballcompass-fixes-provenance/` for later reviewed reconciliation.

Heavy archives remain outside Git. `artifact-manifest.tsv` records hashes and
canonical/duplicate-candidate status. Session databases, OpenCode/Codex state,
temporary research originals, large restored trees, and uncertain material
were retained.
