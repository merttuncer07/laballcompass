"""Hodge Flow Attribution Decomposer (HFAD)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class HodgeFlowResult:
    potential_flow: np.ndarray
    local_cycle_flow: np.ndarray
    harmonic_flow: np.ndarray
    potential_energy: float
    local_cycle_energy: float
    harmonic_energy: float
    reconstruction_residual: float
    divergence_residual_for_cycles: float
    face_curl_residual_for_potential_harmonic: float


class HodgeFlowAttributionDecomposer:
    """Orthogonally decompose edge flow on an oriented graph/2-complex."""

    def __init__(self, node_edge_incidence: np.ndarray, edge_face_incidence: np.ndarray | None = None):
        self.boundary_1 = np.asarray(node_edge_incidence, dtype=float)
        if self.boundary_1.ndim != 2 or not np.all(np.isfinite(self.boundary_1)):
            raise ValueError("node-edge incidence must be a finite matrix")
        edge_count = self.boundary_1.shape[1]
        self.boundary_2 = (
            np.zeros((edge_count, 0), dtype=float)
            if edge_face_incidence is None
            else np.asarray(edge_face_incidence, dtype=float)
        )
        if self.boundary_2.ndim != 2 or not np.all(np.isfinite(self.boundary_2)):
            raise ValueError("incidence operators must be matrices")
        if self.boundary_2.shape[0] != edge_count:
            raise ValueError("edge dimensions differ")
        chain_residual = self.boundary_1 @ self.boundary_2
        if chain_residual.size and np.max(np.abs(chain_residual)) > 1e-9:
            raise ValueError("invalid complex: boundary of a face boundary must be zero")

    def decompose(self, edge_flow: np.ndarray) -> HodgeFlowResult:
        flow = np.asarray(edge_flow, dtype=float)
        if flow.shape != (self.boundary_1.shape[1],) or not np.all(np.isfinite(flow)):
            raise ValueError("edge flow dimension differs from incidence matrix")
        # Projection onto exact/gradient flows im(B1^T).
        potential_coefficients = np.linalg.lstsq(self.boundary_1.T, flow, rcond=None)[0]
        potential = self.boundary_1.T @ potential_coefficients
        residual = flow - potential
        # Projection onto coexact/local face-boundary flows im(B2).
        if self.boundary_2.shape[1]:
            cycle_coefficients = np.linalg.lstsq(self.boundary_2, residual, rcond=None)[0]
            local_cycle = self.boundary_2 @ cycle_coefficients
        else:
            local_cycle = np.zeros_like(flow)
        harmonic = flow - potential - local_cycle
        reconstructed = potential + local_cycle + harmonic
        cycle_divergence = self.boundary_1 @ (local_cycle + harmonic)
        nonlocal_face_curl = self.boundary_2.T @ (potential + harmonic)
        return HodgeFlowResult(
            potential_flow=potential,
            local_cycle_flow=local_cycle,
            harmonic_flow=harmonic,
            potential_energy=float(potential @ potential),
            local_cycle_energy=float(local_cycle @ local_cycle),
            harmonic_energy=float(harmonic @ harmonic),
            reconstruction_residual=float(np.max(np.abs(reconstructed - flow))) if flow.size else 0.0,
            divergence_residual_for_cycles=float(np.max(np.abs(cycle_divergence)))
            if cycle_divergence.size
            else 0.0,
            face_curl_residual_for_potential_harmonic=float(np.max(np.abs(nonlocal_face_curl)))
            if nonlocal_face_curl.size
            else 0.0,
        )


def incidence_from_edges(node_count: int, oriented_edges: list[tuple[int, int]]) -> np.ndarray:
    if not isinstance(node_count, int) or node_count < 0:
        raise ValueError("node_count must be a non-negative integer")
    incidence = np.zeros((node_count, len(oriented_edges)))
    for edge_index, (source, target) in enumerate(oriented_edges):
        if not isinstance(source, (int, np.integer)) or not isinstance(target, (int, np.integer)) or not 0 <= source < node_count or not 0 <= target < node_count:
            raise ValueError("edge endpoint outside node range")
        incidence[source, edge_index] -= 1.0
        incidence[target, edge_index] += 1.0
    return incidence

