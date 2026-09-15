# V2P046 MTCWC — Mechanism-Tipping Calibration Width Controller

MCST maps a declared stress/mechanism parameter to the point where the nominal calibration width begins violating its miss-rate target. Crossing that surface resets CWC state rather than forcing CWC to learn the new width only through accumulated misses. The removal comparator keeps the same residuals and CWC but removes the tipping signal/reset.

Status: SHADOW_RETRO_SWEEP. Synthetic Gaussian stress shell only; externally observed stress semantics are a required contract.
