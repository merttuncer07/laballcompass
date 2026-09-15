# Lab provenance

This product was extracted from the Lab rather than designed as a generic indicator bot.

## Frozen directional composition

1. `V2P032 LMDE`
   - MemoryKernelClosure;
   - ReliabilityTemperedEvidence;
   - EffectiveDiversityGuard;
   - DecisionFluctuationGuard.
2. `V2P033 DTEC`
   - decision-loss-aware action persistence;
   - transaction-cost comparison;
   - uncertainty-relative switching threshold.
3. `V2P029 TCEA` semantics
   - gross/net return separation;
   - turnover and cost erosion attribution.
4. Corrected Crypto V1 causal shell
   - signal after `close[t]`;
   - fill at `open[t+1]`;
   - drawdown-triggering loss is retained;
   - cooldown affects only later executable bars.

The product reruns the full composition and a DTEC-removal comparator on every research backtest.

## Why other mechanisms are absent

- KFEA was removed from the active historical runtime after underperforming the core on BTC 15m and
  ETH 1h.
- GTRO reduced drawdown in some samples but did not establish reliable marginal return contribution.
- DAPS and broad candidate-library additions did not earn authority for this product.
- The retired Bridge/Regime Router/control architecture is not present.

## Existing evidence boundary

The corrected historical Lab record reported four positive environments and one negative older-BTC
environment for LMDE→DTEC, with a 13.00% arithmetic mean net return and roughly 9.95% mean maximum
drawdown under 12 bps per position side. A frozen August BTC 1h probe returned 19.89% net but lagged
buy-and-hold by 4.34 percentage points. These are development observations, not future-return claims.

This extracted product must build a new paper ledger. It has no live-capital authority.

## Market-neutral carry composition

The public quant-mechanism reconstruction changed the product's economic core without importing
proprietary code:

1. `LMDE / ReliabilityTemperedEvidence` semantics blend a funding-persistence estimate, a
   basis-convergence estimate and direct realized carry according to their causal forecast errors.
2. `V2P033 DTEC` treats switching as a two-leg economic decision. It requires the expected carry over
   the declared holding horizon to exceed spot-plus-perpetual fees, slippage and uncertainty.
3. `V2P029 TCEA` semantics keep gross carry, paid costs and net carry separate.
4. Equal-notional long spot / short perpetual creates zero net entry delta without leverage. The
   sample-end position is forcibly closed and charged.

The 45-event decision horizon is an economic cost-recovery horizon (15 days at three settlements per
day), not a fitted candle pattern. The same frozen value is used for all five markets and all 15
chronological windows.

This composition is implemented in `carry_engine.py`. No Bridge, Regime Router, control-plane gate,
credential handler or live-order method is present.
