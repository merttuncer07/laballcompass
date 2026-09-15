# V2P002 MFQA — Multi-Fidelity Quasineutral Acquisition

## Composition

LCB `MultiFidelityBudgetControllerV0` + Foundry `P136 QAIG`.

QAIG first asks whether a charge-imbalance measurement can change the quasineutral validity decision
enough to justify its cost. Only after that gate does MFQA use pilot cross-fidelity correlation to divide
a fixed program budget between fine and cheap measurements. Low correlation or negative cheap-channel
decision value routes back to fine-only measurement; a far-from-boundary case buys nothing.

## Product roles

Standalone: measurement-program design for a declared batch of transport packets/locations. Component:
budget router for QAIG/APTC pipelines.

## Boundary

The Gaussian belief variance, pilot correlation, channel noise and costs are declared calibration inputs.
The LCB variance proxy is a program-design approximation; it is not the QAIG decision loss itself and is
kept as a separate output. Failure in a field shell triggers correlation/noise/cost recalibration or a
fine-only route, not product deletion.
