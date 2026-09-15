import unittest

import numpy as np

from invariant_scout import SparseInvariantScout, affine_quotient, lifted_library
from r194_benchmark import generate_scenes


class TestInvariantScout(unittest.TestCase):
    def test_affine_quotient_is_invariant(self):
        rng = np.random.default_rng(3)
        z = rng.normal(size=(10, 6))
        transformed = 7.3 * z - 11.2
        np.testing.assert_allclose(affine_quotient(z), affine_quotient(transformed), atol=1e-11)

    def test_library_shape_and_names(self):
        f, names = lifted_library(np.ones((4, 6)))
        self.assertEqual(f.shape, (4, 20))
        self.assertEqual(len(names), 20)
        self.assertIn("d0*d3", names)

    def test_discovers_product_relation(self):
        pos = generate_scenes(1, "product_equality", 18, True, 0.005)
        neg = generate_scenes(2, "product_equality", 18, False, 0.005)
        z = np.vstack([pos, neg])
        y = np.concatenate([np.ones(18, dtype=np.int8), np.zeros(18, dtype=np.int8)])
        model = SparseInvariantScout().fit(z, y)
        self.assertFalse(model.abstained_)
        names = {name for name, _ in model.relation()}
        self.assertEqual(names, {"d0*d1", "d2*d3"})

    def test_predict_before_fit_fails(self):
        with self.assertRaises(RuntimeError):
            SparseInvariantScout().predict(np.zeros((2, 6)))


if __name__ == "__main__":
    unittest.main()
