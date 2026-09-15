# R-034 product result — RSPI v0.1

**Product route:** reconstructed standalone remote-synchronization pathway identifier  
**Result:** working product; 4/4 tests pass

RSPI joins measured phase locking with network adjacency. A remote pair must be nonadjacent,
synchronized above the endpoint threshold, connected by a graph path, and separated from every
intermediate mediator by the lower mediator ceiling.

In the first A–B–C construction, A and C had PLV 0.99367 despite no direct edge. Their required
mediator B had PLV only 0.04579 with A and 0.04364 with C, producing a decoupling margin 0.40421. A
fully synchronized chain was correctly retained as ordinary pathway synchrony, not remote synchrony.

The product applies to oscillator, power, biological, and coordination networks.
