# Q195 Recovery — Source Inventory (Step 1)

Frozen before any recovery file was created. No listed file was edited.
`q195_suffix_lift.py` is historical evidence and remains untouched.

Base directory for R212 files:

`/Users/mertalituncer/Documents/Default Project/laballcompass/LAC_REPRO_R210/ACTIVE_RESEARCH/R212_VOLTERRA_NO_RESET_INTRINSIC/`

## R212 Volterra files

| File | Bytes | mtime | SHA-256 |
|---|---|---|---|
| `R212_STATE.md` | 14834 | Sep 18 01:46 2026 | `ba9d546827cc6acce9b8d0174cd6f3668cb005c75e605013b1f27748ea71065f` |
| `q195_suffix_lift.py` | 3996 | Sep 18 01:40 2026 | `82f8b1a036668cba641bb97659f937d3e0af0ac17c680314f24649090f2b81e1` |
| `VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE.py` | 14527 | Sep 18 01:10 2026 | `610f757d1d2f5209a0f82a3bf09cdd783595385acd84652a17d94ce30a9fe8be` |
| `intrinsic_no_reset.py` | 2356 | Sep 18 01:18 2026 | `d11da379cd6add3c795e173728b004b99c21664d1b13a1a729ccd4a99c21a980` |
| `validate_all.py` | 4823 | Sep 18 01:23 2026 | `68a29d1addf7f04f850e2efd6db60f90cb8c5ef99bb63b55e75a3475c527e5cc` |
| `phasezero_replay.py` | 5477 | Sep 18 01:10 2026 | `b9e383179fc5465de7a2e75e5fc14072758e4ed780dba12439a73722fdbf5634` |
| `phasezero_bipartite_unimodular_standalone.py` | 2583 | Sep 18 01:10 2026 | `daa00573abb000fbc58f77264f6186d93657a5a80fa911ef9253df7cbc01a47c` |
| `resonant_boundary_cubic_cert.py` | 2032 | Sep 18 01:10 2026 | `1fc23ab9687d1d646d8d6ec73e6146a558bab42674cf9382a9ec268b00cd7b94` |
| `R212_VALIDATION.txt` | 489 | Sep 18 01:26 2026 | (not hashed; 489-byte validation receipt) |

## Upstream source documents (read-only, outside R212 dir)

| File | Bytes | mtime | SHA-256 |
|---|---|---|---|
| `/Users/mertalituncer/Developer/AI_NATIVE_MATH_MASTER_HANDOFF_2026-09-08.md` (S1) | 50483 | Sep 18 01:37 2026 | `876f1ab1d1ba3621e4bcfbe94cfe5836f54cbff9c5d573671141d478f7209bf5` |
| `/Users/mertalituncer/Developer/AI_NATIVE_MATH_Q193_Q194_INTERVAL_CODE_SOURCE.md` (Q193/Q194) | 4391 | Sep 18 01:37 2026 | `47a00907af9e583794c9be568fc6c41174991a814c3c2c2b317697f264865735` |

## What each frozen file contributes to the recovery

- `R212_STATE.md` — audit record + Q195 session-2 verdict entry (lines 200–228). Provenance: persisted before recovery.
- `q195_suffix_lift.py` — `physical_word`, `suffix_histograms`, `affine_rows_A`, anti-periodic ring ops; `helical_label()` is an unfinished stub (`raise NotImplementedError`). Provenance: persisted before recovery; stub documented in `Q195_CONVENTIONS.md`, never edited.
- `VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE.py` — `schedule_L3(d, n0)` returning `(r, n, e, U, B, F, Fs, g)`; `states_int`, `shift_int`. Dependency: sympy only. Provenance: persisted before recovery; vendored as explicit dependency for the clean replay.
- S1 — Q189 (shifted-head lineage, `P = R_d = h_{d-1}`), F\* surgery, Q193 repeat, defect quotient. Provenance: read-only source.
- Q193/Q194 file — sections 14 (Q193) and 15 (Q194) in full (339 lines). Provenance: read-only source; conventions extracted into `Q195_CONVENTIONS.md`.

## Name-collision warning (recorded, not resolved)

The cert's `schedule_L3` returns a set named `F` (gap-index/times set used for the
fixed-state computation) which is a DIFFERENT object from the modal surface set
`F` of S1 section 11 / Q193. The recovered harness uses only `(r, n, g)` from
`schedule_L3` and builds the modal chronology independently, mirroring chat.
