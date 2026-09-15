from __future__ import annotations

from surface_sweep import (
    delsarte_intertwiner_boundary,
    diliberto_cycle_certificate,
    gdr_thinning_tomography,
    ivakhnenko_empirical_quotient,
    kaczmarz_inconsistent_order,
    lavrentiev_extrapolation,
    setun_carry_locality,
    ville_mixture_test,
    yakubovich_triangle_counterexample,
    zhuravlev_gf2_corrector,
)


def test_zhuravlev_affine_corrector_is_exact_and_can_abstain():
    result = zhuravlev_gf2_corrector()
    assert result["exact_planted_correction"]
    assert result["unreachable_target_certified"]


def test_ivakhnenko_quotient_is_exact_only_on_observed_sample():
    result = ivakhnenko_empirical_quotient()
    assert result["evaluation_quotient_rank"] <= result["sample_size"]
    assert result["on_sample_projection_error"] < 1e-8
    assert not result["off_sample_equivalence_guaranteed"]


def test_ville_mixture_respects_time_uniform_bound():
    result = ville_mixture_test(paths=10_000, horizon=120)
    assert result["ville_bound_respected"]


def test_multi_constraint_scalar_s_procedure_has_triangle_gap():
    result = yakubovich_triangle_counterexample()
    assert result["box_max_xLx"] == 8.0
    assert abs(result["duality_gap"] - 1.0) < 1e-10


def test_balanced_ternary_shortens_average_carry_runs_not_worst_case():
    result = setun_carry_locality()
    assert result["mean_run_ratio_binary_over_ternary"] > 1.5
    assert result["worst_case_linear_in_word_length_for_both"]


def test_thinning_tomography_is_exact_but_high_order_is_ill_conditioned():
    result = gdr_thinning_tomography()
    assert max(result["exact_max_abs_error_by_K"].values()) < 1e-8
    assert result["high_order_ill_conditioning_visible"]


def test_diliberto_leveling_matches_discrete_cycle_optimum():
    result = diliberto_cycle_certificate()
    assert result["leveling_matches_cycle_optimum"]
    assert result["rectangle_invariant_lower_bound"] <= result["cycle_optimal_linf_error"] + 1e-9


def test_inconsistent_kaczmarz_depends_on_row_order():
    result = kaczmarz_inconsistent_order()
    assert result["forward_reverse_solution_distance"] > 1e-3
    assert result["least_squares_residual"] <= min(result["forward_residual"], result["reverse_residual"])


def test_lavrentiev_extrapolation_cancels_bias_but_amplifies_noise():
    result = lavrentiev_extrapolation()
    assert result["bias_reduced"]
    assert result["noise_tradeoff_present"]


def test_delsarte_exact_invertible_map_has_spectral_boundary():
    result = delsarte_intertwiner_boundary()
    assert result["known_invertible_intertwiner_residual"] < 1e-9
    assert result["disjoint_spectrum_nullity"] == 0
