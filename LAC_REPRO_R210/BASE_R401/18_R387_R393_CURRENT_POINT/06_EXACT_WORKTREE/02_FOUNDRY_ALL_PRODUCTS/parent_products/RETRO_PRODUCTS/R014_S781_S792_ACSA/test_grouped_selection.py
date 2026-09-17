"""Algebraic regression checks; arrays here are not presented as field evidence."""
from dataclasses import asdict
import numpy as np
import pytest
from acsa import audit_adaptive_selection


def test_singleton_groups_recover_row_bootstrap_and_se():
    args = dict(selection_losses=[[0, 1], [1, 0], [2, 1], [1, 2], [0, 2]],
                holdout_losses=[[1, 0], [4, 1], [2, 3], [8, 4], [3, 2]],
                selection_tiebreak_scores=[[3, 0], [0, 1], [2, 1], [1, 0], [2, 0]],
                bootstrap_samples=200, random_seed=42)
    row = asdict(audit_adaptive_selection(**args))
    grouped = asdict(audit_adaptive_selection(**args, selection_groups=['a', 'b', 'c', 'd', 'e'],
                                             holdout_groups=['f', 'g', 'h', 'i', 'j']))
    for key in ('resampling_method', 'standard_error_method'):
        row.pop(key); grouped.pop(key)
    for key in ('pointwise_standard_error', 'pointwise_95_radius'):
        assert row.pop(key) == pytest.approx(grouped.pop(key), rel=1e-14)
    assert row == grouped


def test_unequal_group_sizes_preserve_pooled_mean_and_cr1():
    values = np.array([0., 3., 3., 3., 3., 3., 3.])
    r = audit_adaptive_selection([[0], [1], [2], [3], [4]], values[:, None],
        selection_groups=['s1', 's2', 's3', 's4', 's5'],
        holdout_groups=['h1', 'h2', 'h2', 'h2', 'h3', 'h4', 'h5'],
        bootstrap_samples=400, random_seed=7)
    assert r.selected_holdout_loss == pytest.approx(values.mean())
    residual = values-values.mean()
    totals = np.array([residual[[0]].sum(), residual[[1,2,3]].sum(),
                       residual[[4]].sum(), residual[[5]].sum(), residual[[6]].sum()])
    expected = np.sqrt(5/4*np.sum(totals**2))/len(values)
    assert r.pointwise_standard_error == pytest.approx(expected)
    assert r.holdout_unit_count == 5 and r.holdout_largest_unit_fraction == 3/7


def test_exact_cluster_selector_includes_loss_score_pairing():
    losses=np.array([[0,2],[1,0],[1,0],[0,2],[1,0],[0,0]],float)
    scores=np.array([[3,0],[0,2],[0,2],[3,0],[0,2],[0,0]],float)
    groups=[np.array([0]),np.array([1,2]),np.array([3]),np.array([4]),np.array([5])]
    samples=1000; seed=12
    r = audit_adaptive_selection(losses, np.zeros((5,2)),
        selection_tiebreak_scores=scores, selection_groups=['a','b','b','c','d','e'],
        holdout_groups=['f','g','h','i','j'], bootstrap_samples=samples, random_seed=seed)
    rng=np.random.default_rng(seed); counts=np.zeros(2,int)
    for _ in range(samples):
        rng.integers(0,5,5)  # holdout draw occurs first
        rows=np.concatenate([groups[g] for g in rng.integers(0,5,5)])
        means=losses[rows].mean(axis=0); means_score=scores[rows].mean(axis=0)
        counts[min(range(2),key=lambda j:(means[j],-means_score[j],j))]+=1
    np.testing.assert_allclose(r.selection_bootstrap_frequencies, counts/samples)


def test_duplicate_rows_within_sources_do_not_multiply_information():
    selection = np.array([[0,1],[1,0],[2,1],[1,2],[0,2]])
    holdout = np.array([[0,1],[6,2],[2,3],[4,1],[1,5]])
    original = audit_adaptive_selection(selection, holdout,
        selection_groups=['a','b','c','d','e'], holdout_groups=['f','g','h','i','j'],
        bootstrap_samples=200, random_seed=3)
    repeated = audit_adaptive_selection(np.repeat(selection, 20, axis=0),
        np.repeat(holdout, 20, axis=0), selection_groups=np.repeat(['a','b','c','d','e'],20),
        holdout_groups=np.repeat(['f','g','h','i','j'],20), bootstrap_samples=200, random_seed=3)
    assert repeated.pointwise_standard_error == pytest.approx(original.pointwise_standard_error)
    assert repeated.selected_holdout_loss_bootstrap_interval_95 == original.selected_holdout_loss_bootstrap_interval_95
    assert repeated.selection_bootstrap_frequencies == original.selection_bootstrap_frequencies


@pytest.mark.parametrize('selection_ids,holdout_ids', [
    (['a', 'b'], None), (None, ['c', 'd']), (['a', 'b'], ['a', 'c']),
    (['a', 'a'], ['c', 'd']), (['a'], ['c', 'd']),
    ([None, 'a'], ['c', 'd']), ([float('nan'), 'a'], ['c', 'd']),
    ([1., 2.], ['c', 'd']), ([True, 2], ['c', 'd']),
    ([['a'], ['b']], ['c', 'd']), (['', 'b'], ['c', 'd']),
    ('ab', ['c', 'd']), (1, ['c', 'd']),
])
def test_invalid_or_leaking_groups_rejected(selection_ids, holdout_ids):
    with pytest.raises(ValueError):
        audit_adaptive_selection([[0], [1]], [[0], [1]], bootstrap_samples=100,
            selection_groups=selection_ids, holdout_groups=holdout_ids)


def test_mixed_id_types_are_lossless_and_share_cross_partition_namespace():
    losses=[[0],[1],[2],[3],[4]]
    r = audit_adaptive_selection(losses, losses, bootstrap_samples=100,
        selection_groups=[1,'1',3,'3',4], holdout_groups=[2,'2',5,'5',6])
    assert r.selection_unit_count == 5
    with pytest.raises(ValueError, match='disjoint'):
        audit_adaptive_selection(losses, losses, bootstrap_samples=100,
            selection_groups=[np.int64(1),'1',3,'3',4], holdout_groups=[1,'2',5,'5',6])


def test_fewer_than_five_groups_fail_closed():
    with pytest.raises(ValueError, match='at least five'):
        audit_adaptive_selection([[0],[1],[2],[3]], [[0],[1],[2],[3]], bootstrap_samples=100,
            selection_groups=['a','b','c','d'], holdout_groups=['e','f','g','h'])
