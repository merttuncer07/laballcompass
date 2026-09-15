import itertools
import unittest

from symbolic_favorable import (
    Rule,
    compile_bdd_fixed_point,
    compile_circuit_acyclic,
    compile_explicit,
    independent_choice_program,
)


class SymbolicFavorableTests(unittest.TestCase):
    def test_symbolic_and_explicit_semantics_match(self):
        rules, bases, order = independent_choice_program(4)
        explicit = compile_explicit(rules, bases)["goal"]
        circuit, circuit_values = compile_circuit_acyclic(rules, bases, order)
        bdd, bdd_values, _ = compile_bdd_fixed_point(
            rules, bases, [f"{side}{i}" for i in range(4) for side in "ab"]
        )
        labels = tuple(bases.values())
        for bits in itertools.product((False, True), repeat=len(labels)):
            enabled = {label for label, bit in zip(labels, bits) if bit}
            direct = any(support <= enabled for support in explicit)
            self.assertEqual(direct, circuit.evaluate(circuit_values["goal"], enabled))
            self.assertEqual(direct, bdd.evaluate(bdd_values["goal"], enabled))

    def test_minimal_support_family_is_exponential(self):
        rules, bases, _ = independent_choice_program(10)
        supports = compile_explicit(rules, bases)["goal"]
        self.assertEqual(len(supports), 2**10)
        self.assertTrue(all(len(support) == 10 for support in supports))

    def test_factored_circuit_is_linear_on_choice_family(self):
        rules, bases, order = independent_choice_program(128)
        circuit, values = compile_circuit_acyclic(rules, bases, order)
        self.assertLessEqual(circuit.reachable_count(values["goal"]), 4 * 128 + 1)
        enabled = {f"a{i}" for i in range(128)}
        self.assertTrue(circuit.evaluate(values["goal"], enabled))

    def test_bdd_variable_order_has_an_exposed_failure_boundary(self):
        rules, bases, _ = independent_choice_program(10)
        interleaved = [f"{side}{i}" for i in range(10) for side in "ab"]
        split = [f"a{i}" for i in range(10)] + [f"b{i}" for i in range(10)]
        good, good_values, _ = compile_bdd_fixed_point(rules, bases, interleaved)
        bad, bad_values, _ = compile_bdd_fixed_point(rules, bases, split)
        self.assertGreater(
            bad.reachable_count(bad_values["goal"]),
            10 * good.reachable_count(good_values["goal"]),
        )

    def test_canonical_bdd_fixed_point_handles_cycles(self):
        rules = [Rule("p", ("seed",)), Rule("q", ("p",)), Rule("p", ("q",))]
        bases = {"seed": "seed"}
        bdd, values, iterations = compile_bdd_fixed_point(rules, bases, ["seed"])
        self.assertTrue(bdd.evaluate(values["q"], {"seed"}))
        self.assertFalse(bdd.evaluate(values["q"], set()))
        self.assertLess(iterations, 6)


if __name__ == "__main__":
    unittest.main()

