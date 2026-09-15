"""Contrast a certified assignment relaxation with a fractional triangle cover."""

from __future__ import annotations

import json

import numpy as np

from ric import assignment_equalities, certify_total_unimodularity, compare_lp_and_integer


def main() -> None:
    assignment_matrix, assignment_rhs = assignment_equalities(3)
    assignment_cost = np.array([4.0, 1.0, 3.0, 2.0, 0.0, 5.0, 3.0, 2.0, 2.0])
    assignment_certificate = certify_total_unimodularity(assignment_matrix)
    assignment = compare_lp_and_integer(
        assignment_cost,
        equality_matrix=assignment_matrix,
        equality_bound=assignment_rhs,
    )

    # Minimum vertex cover of a triangle: x_i + x_j >= 1 for each edge.
    triangle_matrix = -np.array([[1, 1, 0], [0, 1, 1], [1, 0, 1]], dtype=float)
    triangle_bound = -np.ones(3)
    triangle_certificate = certify_total_unimodularity(triangle_matrix)
    triangle = compare_lp_and_integer(
        np.ones(3),
        inequality_matrix=triangle_matrix,
        inequality_bound=triangle_bound,
    )
    output = {
        "assignment": {
            "tu_certificate": assignment_certificate.__dict__,
            "lp_solution": assignment.lp_solution.tolist(),
            "integer_solution": assignment.integer_solution.tolist(),
            "lp_objective": assignment.lp_objective,
            "integer_objective": assignment.integer_objective,
            "integrality_gap": assignment.integrality_gap,
        },
        "triangle_vertex_cover": {
            "tu_certificate": triangle_certificate.__dict__,
            "lp_solution": triangle.lp_solution.tolist(),
            "integer_solution": triangle.integer_solution.tolist(),
            "lp_objective": triangle.lp_objective,
            "integer_objective": triangle.integer_objective,
            "integrality_gap": triangle.integrality_gap,
        },
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

