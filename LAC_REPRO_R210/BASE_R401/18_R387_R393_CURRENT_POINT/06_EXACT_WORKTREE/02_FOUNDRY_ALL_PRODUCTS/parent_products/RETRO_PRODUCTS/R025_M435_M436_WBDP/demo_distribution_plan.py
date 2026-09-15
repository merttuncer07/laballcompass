import json

from wbdp import Distribution, displacement_interpolation, wasserstein_barycenter, wasserstein_distance


def main():
    west = Distribution("WEST", (0.0, 2.0), (0.7, 0.3))
    east = Distribution("EAST", (8.0, 12.0), (0.4, 0.6))
    midpoint = displacement_interpolation(west, east, 0.5)
    barycenter = wasserstein_barycenter([west, east], [0.35, 0.65])
    point_a, point_b = Distribution("A", (0.0,), (1.0,)), Distribution("B", (10.0,), (1.0,))
    moving_midpoint = displacement_interpolation(point_a, point_b, 0.5)
    print(json.dumps({
        "midpoint": midpoint.to_dict(), "weighted_barycenter": barycenter.to_dict(),
        "point_mass_comparison": {
            "displacement_midpoint": moving_midpoint.to_dict(),
            "ordinary_mixture_positions": [0.0, 10.0], "ordinary_mixture_variance": 25.0,
            "endpoint_wasserstein_distance": wasserstein_distance(point_a, point_b),
        },
    }, indent=2))


if __name__ == "__main__": main()
