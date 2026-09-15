# Liquidity Conversion Map

LCM turns **IM-452 → IM-015** into a working borrowing-base and verification-value engine.

It keeps four quantities separate:

`nominal claim → verified claim → financeable face → deployable liquidity`.

Verified claims can be allocated across funding channels subject to eligibility, advance rates,
liquidity capacity, time horizon, and anchor concentration. A linear program maximizes currently
deployable liquidity. The tool can also compute how much additional liquidity a specific
verification action would unlock.

## Run

```powershell
python -m unittest -v test_lcm.py
python demo_liquidity_conversion.py
```

## Product boundary

v0.1 assumes deterministic verification and channel terms. Next layers are verification failure,
document discrepancy, recourse/credit risk, financing cost, and time-dependent cash requirements.
