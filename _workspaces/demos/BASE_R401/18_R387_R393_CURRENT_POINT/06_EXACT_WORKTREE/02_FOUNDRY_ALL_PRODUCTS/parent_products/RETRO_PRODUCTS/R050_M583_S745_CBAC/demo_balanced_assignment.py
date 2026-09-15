import json

import numpy as np

from cbac import design_balanced_assignment


def main() -> None:
    rng = np.random.default_rng(50)
    n = 80
    latent = rng.normal(size=(n, 2))
    covariates = np.column_stack([
        latent[:, 0], latent[:, 1], latent[:, 0] + 0.5 * latent[:, 1] + rng.normal(scale=0.3, size=n),
        np.exp(0.3 * latent[:, 0]), rng.normal(size=n),
    ])
    result = design_balanced_assignment(
        covariates, treated_count=40, randomization_draws=8_000, acceptance_fraction=0.01, seed=744
    )
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
