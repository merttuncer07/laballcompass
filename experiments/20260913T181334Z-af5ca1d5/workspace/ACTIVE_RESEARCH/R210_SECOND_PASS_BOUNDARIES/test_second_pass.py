from __future__ import annotations

from second_pass import gdr_amplification_curve, gdr_blind_direction, zhuravlev_bounded_degree_corrector


def test_gdr_finite_difference_identity_and_positive_pair():
    result = gdr_blind_direction(12)
    assert result["spectra_nonnegative"]
    assert result["closed_form_max_error"] < 1e-12
    assert max(abs(value) for value in result["annihilated_raw_moments_degrees_0_to_r_minus_1"]) < 1e-8


def test_gdr_inverse_amplification_grows_rapidly():
    curve = gdr_amplification_curve()
    assert curve["20"] > 1_000 * curve["8"]


def test_zhuravlev_quadratic_closure_strictly_extends_affine():
    result = zhuravlev_bounded_degree_corrector()
    assert not result["affine_can_represent_target"]
    assert result["quadratic_exact"]
    assert result["rank_quotient_degree2_upper_bound"] < result["raw_degree2_feature_count"]

