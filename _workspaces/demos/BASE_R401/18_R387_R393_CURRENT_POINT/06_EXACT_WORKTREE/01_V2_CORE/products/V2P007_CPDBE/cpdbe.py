from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import sys
from typing import Mapping, Sequence

# Reuse only the packaged P026 consumer implementation.  The K009 pressure
# mechanism is re-derived independently here; the historical LCB prototype
# module is intentionally not imported.
_REPO = Path(__file__).resolve().parents[3]
_P026 = _REPO / "02_FOUNDRY_ALL_PRODUCTS" / "products" / "P026_DBTE"
if str(_P026) not in sys.path:
    sys.path.insert(0, str(_P026))

from dbte import Edge, DeployabilityTippingResult, deployable_on_series_path, explore_deployable_tipping  # noqa: E402


@dataclass(frozen=True)
class EdgePressure:
    edge_name: str
    incoming_amount: float
    capacity: float
    minimum_cap_correction: float
    output_after_yield: float


@dataclass(frozen=True)
class PressureGuidedTippingResult:
    tipping: DeployabilityTippingResult
    edge_pressure: tuple[EdgePressure, ...]
    scanned_edges: tuple[str, ...]
    pruned_edges: tuple[str, ...]
    full_grid_points: int
    scanned_grid_points: int
    pruning_fraction: float
    certificate_applicable: bool
    status: str

    def to_dict(self) -> dict:
        return {
            "tipping": asdict(self.tipping),
            "edge_pressure": [asdict(x) for x in self.edge_pressure],
            "scanned_edges": list(self.scanned_edges),
            "pruned_edges": list(self.pruned_edges),
            "full_grid_points": self.full_grid_points,
            "scanned_grid_points": self.scanned_grid_points,
            "pruning_fraction": self.pruning_fraction,
            "certificate_applicable": self.certificate_applicable,
            "status": self.status,
        }


def _pressure_trace(active_stock: float, edges: Sequence[Edge], horizon: float) -> tuple[EdgePressure, ...]:
    """Independent K009-style cap-correction trace for P026's series shell."""
    if active_stock < 0 or horizon < 0:
        raise ValueError("stock and horizon must be nonnegative")
    amount = float(active_stock)
    trace = []
    # Even if lead time makes delivery impossible, pressure is still a valid
    # local cap diagnostic; the P026 result remains the authority on delivery.
    for edge in edges:
        if not 0 <= edge.yield_fraction <= 1 or edge.capacity < 0:
            raise ValueError("invalid edge")
        incoming = amount
        correction = max(0.0, incoming - float(edge.capacity))
        amount = min(incoming, float(edge.capacity)) * float(edge.yield_fraction)
        trace.append(EdgePressure(edge.name, incoming, float(edge.capacity), correction, amount))
    return tuple(trace)


def pressure_guided_deployable_tipping(
    active_stock: float,
    edges: Sequence[Edge],
    *,
    horizon: float,
    target: float,
    capacity_grid: Mapping[str, Sequence[float]],
) -> PressureGuidedTippingResult:
    """Exact safe pruning for P026 single-edge *capacity-increase* scans.

    Certificate shell
    -----------------
    For a fixed series path with fixed topology, yields, lead times, stock and
    horizon, consider only one-edge-at-a-time capacity increases.  Let q_i be
    the amount entering edge i under the baseline path.  If q_i <= c_i, then
    increasing c_i alone leaves min(q_i,c_i') == q_i, hence every downstream
    amount is unchanged.  Such an edge can be removed from P026's capacity
    grid exactly.

    The certificate is deliberately refused when:
      * target is already met at baseline (P026's nearest-grid semantics are no
        longer a target-crossing question), or
      * any proposed grid value decreases a capacity.

    In refused shells the function calls full P026 without pruning.
    Positive pressure is only a candidate signal, not proof that an edge is the
    unique deployable bottleneck; all positive-pressure edges remain scanned.
    """
    edges = list(edges)
    by_name = {e.name: e for e in edges}
    if len(by_name) != len(edges):
        raise ValueError("edge names must be unique")
    for name in capacity_grid:
        if name not in by_name:
            raise KeyError(name)
    normalized = {str(k): [float(x) for x in v] for k, v in capacity_grid.items()}
    full_points = sum(len(v) for v in normalized.values())
    baseline = deployable_on_series_path(active_stock, edges, horizon)
    trace = _pressure_trace(active_stock, edges, horizon)

    monotone_increase = all(value >= by_name[name].capacity for name, values in normalized.items() for value in values)
    target_crossing_shell = float(target) > float(baseline)
    if not monotone_increase or not target_crossing_shell:
        result = explore_deployable_tipping(
            active_stock, edges, horizon=horizon, target=target, capacity_grid=normalized
        )
        reason = "NONMONOTONE_CAPACITY_GRID" if not monotone_increase else "TARGET_ALREADY_MET_AT_BASELINE"
        return PressureGuidedTippingResult(
            tipping=result,
            edge_pressure=trace,
            scanned_edges=tuple(normalized),
            pruned_edges=(),
            full_grid_points=full_points,
            scanned_grid_points=full_points,
            pruning_fraction=0.0,
            certificate_applicable=False,
            status=f"FULL_P026_SCAN_FAIL_CLOSED::{reason}",
        )

    pressure = {x.edge_name: x.minimum_cap_correction for x in trace}
    scanned = tuple(name for name in normalized if pressure.get(name, 0.0) > 0.0)
    pruned = tuple(name for name in normalized if name not in scanned)
    reduced = {name: normalized[name] for name in scanned}
    scanned_points = sum(len(v) for v in reduced.values())
    result = explore_deployable_tipping(
        active_stock, edges, horizon=horizon, target=target, capacity_grid=reduced
    )
    frac = 0.0 if full_points == 0 else (full_points - scanned_points) / full_points
    return PressureGuidedTippingResult(
        tipping=result,
        edge_pressure=trace,
        scanned_edges=scanned,
        pruned_edges=pruned,
        full_grid_points=full_points,
        scanned_grid_points=scanned_points,
        pruning_fraction=float(frac),
        certificate_applicable=True,
        status="PRESSURE_ZERO_EDGES_PRUNED_EXACTLY_FOR_SINGLE_EDGE_CAPACITY_INCREASE_SHELL",
    )
