"""Adaptive Target-Relevance Retention Controller (ATRC) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class EvictionRecord:
    time_index: int
    evicted_index: int
    retained_indices: tuple[int, ...]
    audit_loss_after_eviction: float


@dataclass(frozen=True)
class RetentionResult:
    predictions: tuple[float, ...]
    target_aware_rmse: float
    fifo_rmse: float
    reservoir_rmse: float
    retained_indices: tuple[int, ...]
    evictions: tuple[EvictionRecord, ...]
    memory_budget: int
    maximum_realized_memory: int
    budget_violations: int
    improvement_vs_fifo: float
    improvement_vs_reservoir: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _predict(query: np.ndarray, memory: list[int], features: np.ndarray, targets: np.ndarray,
             neighbors: int, exclude: int | None = None) -> float:
    usable = [index for index in memory if index != exclude]
    if not usable:
        return 0.0
    distances = np.linalg.norm(features[usable] - query, axis=1)
    order = np.argsort(distances, kind="stable")[:min(neighbors, len(usable))]
    chosen = np.asarray(usable)[order]
    weights = 1.0 / (distances[order] + 1e-6)
    return float(np.sum(weights * targets[chosen]) / np.sum(weights))


def _stream_baseline(features: np.ndarray, targets: np.ndarray, budget: int, neighbors: int,
                     reservoir: bool, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    memory: list[int] = []
    predictions = np.zeros(len(targets))
    for index in range(len(targets)):
        predictions[index] = _predict(features[index], memory, features, targets, neighbors)
        if len(memory) < budget:
            memory.append(index)
        elif reservoir:
            slot = int(rng.integers(0, index + 1))
            if slot < budget:
                memory[slot] = index
        else:
            memory.pop(0); memory.append(index)
    return predictions


def control_memory_retention(
    features: Sequence[Sequence[float]],
    targets: Sequence[float],
    *,
    memory_budget: int,
    audit_horizon: int,
    neighbors: int = 3,
    age_penalty: float = 0.0,
    seed: int = 0,
) -> RetentionResult:
    """Retain stream observations by target loss under an exact item budget."""

    x = np.asarray(features, dtype=float)
    y = np.asarray(targets, dtype=float)
    if x.ndim != 2 or y.ndim != 1 or x.shape[0] != y.size or y.size < 10:
        raise ValueError("features/targets must contain at least ten matched observations")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("stream data must be finite")
    if memory_budget < 2 or audit_horizon < 2 or neighbors < 1 or age_penalty < 0:
        raise ValueError("budget/horizon/neighbors must be positive and budget >= 2")
    memory: list[int] = []
    predictions = np.zeros(y.size)
    evictions: list[EvictionRecord] = []
    maximum_memory = 0
    for index in range(y.size):
        predictions[index] = _predict(x[index], memory, x, y, neighbors)
        memory.append(index)
        if len(memory) > memory_budget:
            audit = range(max(0, index - audit_horizon + 1), index + 1)
            candidates = []
            for candidate in memory:
                reduced = [item for item in memory if item != candidate]
                errors = [(_predict(x[a], reduced, x, y, neighbors, exclude=a) - y[a]) ** 2 for a in audit]
                loss = float(np.mean(errors))
                eviction_score = loss - age_penalty * (index - candidate)
                candidates.append((eviction_score, loss, candidate))
            _, loss, evicted = min(candidates, key=lambda item: (item[0], item[2]))
            memory.remove(evicted)
            evictions.append(EvictionRecord(index, evicted, tuple(memory), loss))
        maximum_memory = max(maximum_memory, len(memory))
    fifo = _stream_baseline(x, y, memory_budget, neighbors, False, seed)
    reservoir = _stream_baseline(x, y, memory_budget, neighbors, True, seed)
    warmup = min(memory_budget, y.size - 1)
    target_rmse = float(np.sqrt(np.mean((predictions[warmup:] - y[warmup:]) ** 2)))
    fifo_rmse = float(np.sqrt(np.mean((fifo[warmup:] - y[warmup:]) ** 2)))
    reservoir_rmse = float(np.sqrt(np.mean((reservoir[warmup:] - y[warmup:]) ** 2)))
    return RetentionResult(
        predictions=tuple(map(float, predictions)), target_aware_rmse=target_rmse,
        fifo_rmse=fifo_rmse, reservoir_rmse=reservoir_rmse,
        retained_indices=tuple(memory), evictions=tuple(evictions), memory_budget=memory_budget,
        maximum_realized_memory=maximum_memory, budget_violations=int(maximum_memory > memory_budget),
        improvement_vs_fifo=float(1 - target_rmse / fifo_rmse) if fifo_rmse else 0.0,
        improvement_vs_reservoir=float(1 - target_rmse / reservoir_rmse) if reservoir_rmse else 0.0,
        status="TARGET_RELEVANCE_MEMORY_CONTROL_COMPLETE",
    )
