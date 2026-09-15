# RSPI v0.1 — Remote Synchronization Pathway Identifier

RSPI combines oscillator phase measurements with the physical/network adjacency graph. It searches
for nonadjacent endpoint pairs with strong phase locking, reconstructs their shortest mediator path,
and requires every intermediate node to remain below a separate synchronization ceiling with both
endpoints.

Ordinary adjacent synchrony and a fully synchronized chain are not called remote synchronization.
The product is useful for oscillator networks, power systems, neural/biological networks, and remote
coordination diagnostics.

Run `python -m unittest -v test_rspi.py` and `python demo_remote_sync.py`.
