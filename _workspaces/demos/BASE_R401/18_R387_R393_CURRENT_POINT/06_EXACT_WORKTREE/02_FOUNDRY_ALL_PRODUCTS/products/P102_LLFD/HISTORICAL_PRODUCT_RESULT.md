# Product result — P102_LLFD v0.1

**Product:** Lock-In Localization Feasibility Designer  
**Parents:** SLERM + TFLD  
**Promotion state:** `WORKING_COMPOSITION`

## What materially changed

Uses measured dangerous lock-in frequency and episode duration to set an explicit joint time/frequency localization requirement, then asks TFLD for a window satisfying both.

## Measured evidence

- **dangerous_duration_s**: `19.0`
- **forcing_frequency_hz**: `5.0`
- **max_frequency_spread_hz**: `0.25`
- **max_time_spread_s**: `0.475`
- **selected_window_samples**: `256`
- **selected_time_spread_s**: `0.3621419129766201`
- **selected_frequency_spread_hz**: `0.22552743442893922`
- **feasible_candidates**: `1`
- **tests**: `6/6`

## Claim boundary

The episode-fraction localization requirement is user-declared; it is not a universal physical constant. No dangerous energy-transferring lock-in means no localization design is emitted.
