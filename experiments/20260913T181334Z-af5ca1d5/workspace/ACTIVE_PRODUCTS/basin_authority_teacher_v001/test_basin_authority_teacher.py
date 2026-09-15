import numpy as np

from basin_authority_teacher import (
    FULL_AUTHORITY,
    AuthorityContext,
    TinyTanhXOR,
    authority_gate,
    designed_candidates,
)


def test_analytic_gradient_matches_finite_difference():
    model = TinyTanhXOR(3)
    theta = model.initialize(17, scale=0.4)
    analytic = model.gradient(theta)
    numeric = np.zeros_like(theta)
    epsilon = 1e-6
    for index in range(len(theta)):
        plus = theta.copy(); plus[index] += epsilon
        minus = theta.copy(); minus[index] -= epsilon
        numeric[index] = (model.loss(plus) - model.loss(minus)) / (2 * epsilon)
    assert np.allclose(analytic, numeric, atol=1e-6, rtol=1e-5)


def test_authority_gate_fails_closed_with_specific_reason():
    context = AuthorityContext(True, True, True, False, True, True, True)
    decision = authority_gate(context)
    assert decision.action == "ABSTAIN"
    assert decision.reasons == ("evidence is stale",)


def test_full_authority_allows_search():
    assert authority_gate(FULL_AUTHORITY).action == "SEARCH"


def test_designed_candidate_directions_have_unit_norm_and_scores():
    model = TinyTanhXOR(2)
    theta = model.initialize(3, scale=0.5)
    candidates = designed_candidates(model, theta, seed=2, random_count=4)
    assert len(candidates) >= 8
    assert all(np.isclose(np.linalg.norm(item.direction), 1.0) for item in candidates)
    assert all(np.isfinite(item.immediate_slope) for item in candidates)


def test_training_never_returns_nonfinite_state():
    model = TinyTanhXOR(4)
    result = model.train(model.initialize(8), max_steps=100)
    assert np.isfinite(result.loss)
    assert np.all(np.isfinite(result.theta))


def test_vectorized_gradient_matches_scalar_gradient():
    model = TinyTanhXOR(3)
    states = np.stack([model.initialize(1, scale=0.3), model.initialize(2, scale=0.3)])
    losses, gradients = model.batch_loss_and_gradient(states)
    assert np.allclose(losses, [model.loss(state) for state in states])
    assert np.allclose(gradients, [model.gradient(state) for state in states])
