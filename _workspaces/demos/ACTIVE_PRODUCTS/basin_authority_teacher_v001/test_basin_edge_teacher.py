import numpy as np
import pytest

from basin_authority_teacher import CandidateDirection, TinyTanhXOR
from basin_edge_teacher import estimate_edge, rank_by_soft_modes, rank_candidates, soft_mode_geometry


def candidate(direction, slope):
    return CandidateDirection((0.0, 0.0), 1.0, np.asarray(direction, dtype=float), slope)


def test_edge_ranking_uses_boundary_alignment_not_loss_slope():
    toward_edge = candidate([1.0, 0.0], 2.0)
    greedy = candidate([0.0, 1.0], -3.0)
    ranked = rank_candidates([greedy, toward_edge], method="edge", edge_direction=np.asarray([1.0, 0.0]))
    assert ranked[0] is toward_edge
    assert rank_candidates([greedy, toward_edge], method="greedy")[0] is greedy


def test_unknown_ranker_is_rejected():
    with pytest.raises(ValueError):
        rank_candidates([], method="magic")


def test_edge_estimator_rejects_unverified_good_reference():
    model = TinyTanhXOR(2)
    bad = model.train(model.initialize(0), max_steps=100).theta
    with pytest.raises(ValueError, match="good reference"):
        estimate_edge(model, bad, bad + 1e-3, retrain_steps=20)


def test_parameter_path_direction_is_normalized_for_valid_reference():
    model = TinyTanhXOR(2)
    bad = model.train(model.initialize(0), max_steps=500).theta
    good = model.train(model.initialize(4), max_steps=3500).theta
    edge = estimate_edge(model, bad, good, retrain_steps=100, bisection_steps=2)
    assert np.isclose(np.linalg.norm(edge.direction), 1.0)
    assert edge.retraining_units == 2
    assert 0.0 < edge.upper_good_fraction <= 1.0


def test_soft_mode_geometry_is_finite_and_functional_rank_is_total():
    model = TinyTanhXOR(2)
    bad = model.train(model.initialize(0), max_steps=300).theta
    values, modes, evaluations = soft_mode_geometry(model, bad, modes=2)
    assert values.shape == (2,)
    assert modes.shape == (model.parameter_count, 2)
    assert evaluations == 2 * model.parameter_count
    candidates = [candidate([1.0] + [0.0] * (model.parameter_count - 1), 0.0)]
    assert rank_by_soft_modes(model, bad, candidates, modes) == candidates
