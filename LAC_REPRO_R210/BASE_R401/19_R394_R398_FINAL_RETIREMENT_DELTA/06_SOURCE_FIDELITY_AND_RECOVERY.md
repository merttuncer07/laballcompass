# Source Fidelity and Recovery Boundary

## Exact byte boundary
The inherited R393 archive contains an exact R392 worktree under:

`18_R387_R393_CURRENT_POINT/06_EXACT_WORKTREE/`

It includes canonical V2P001–V2P053, all parents/Retro50, the 145 Foundry compositions, LCB material, routing/telemetry/authority code and R393 shadow-routing artifacts.

## What happened after R393
R394–R398 work was executed in ephemeral working directories. During the long conversation the execution runtime remounted. Only explicitly surfaced artifacts and earlier ZIP archives remained in `/mnt/data`; the unsurfaced late worktrees disappeared. This was discovered before final retirement packaging.

## Consequence
Logical authority/test history through R397 is preserved by completed receipts in the conversation, but exact late source bytes are unavailable. This archive therefore does **not** launder those receipts into a false exact source claim.

`RECOVERED_REFERENCE_CODE/` captures the core operators, input-authority checks, removal controls and failure/collapse semantics so another agent can reconstruct/replay the products. It is reference reconstruction only.

## Required successor behavior
If exact late source archives are later recovered from another machine/chat/export, prefer them and compare against the contracts in this final delta. Otherwise reconstruct V2P054–058 from the exact parent code in the embedded R392 worktree, rerun their hardened tests/sensitivity/telemetry, and replay authority transitions.
