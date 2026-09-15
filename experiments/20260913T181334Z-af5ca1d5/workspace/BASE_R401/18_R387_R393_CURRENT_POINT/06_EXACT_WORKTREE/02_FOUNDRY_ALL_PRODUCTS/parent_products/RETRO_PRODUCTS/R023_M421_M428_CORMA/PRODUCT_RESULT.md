# Product Result — CORMA v0.1

**Retro candidate:** R-023 / M-421 + M-422 + M-427 + M-428  
**Historical decision:** merged into IM-177 / IM-179  
**Product:** Controllability, Observability, and Realization Minimality Auditor  
**Status:** independent working product

CORMA audits a discrete-time linear system's reachable and visible directions, four Kalman behavioral
categories, Gramian spectra, and input–output Hankel rank.

In the first four-state construction:

- controllability rank was **2** and observability rank was **2**;
- each of the four controllable/observable categories contained exactly one state;
- the minimal input–output realization dimension was **1**;
- **3 of 4 states** were therefore redundant for external behavior;
- a known one-state reduction reproduced ten impulse-response terms to **1.11e-16** maximum error.

Four tests pass, including a full minimal system, all four behavioral categories, a missing dynamic
channel, and shape validation. CORMA is a standalone system-architecture product; integration with
current products is unnecessary.

v0.1 diagnoses but does not automatically construct a similarity-transformed minimal realization.
The next standalone layer is explicit reduction, balanced truncation, noisy empirical identification,
sensor/actuator placement, and continuous-time support.
