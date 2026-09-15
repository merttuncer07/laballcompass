from __future__ import annotations

import unittest

from acra import AdaptiveConsequenceResolutionAllocator, DecisionRegion, ResolutionOption


class AdaptiveConsequenceResolutionAllocatorTests(unittest.TestCase):
    def test_time_sensitive_region_prefers_short_option_when_affordable(self) -> None:
        allocator = AdaptiveConsequenceResolutionAllocator(
            [DecisionRegion("onset", 10, 0, 1)],
            [ResolutionOption("short", 2, 1, 5), ResolutionOption("long", 2, 5, 1)],
        )
        result = allocator.allocate(2)
        self.assertEqual(result["allocations"][0]["option"], "short")

    def test_frequency_sensitive_region_prefers_long_option(self) -> None:
        allocator = AdaptiveConsequenceResolutionAllocator(
            [DecisionRegion("band", 0, 10, 1)],
            [ResolutionOption("short", 2, 1, 5), ResolutionOption("long", 2, 5, 1)],
        )
        result = allocator.allocate(2)
        self.assertEqual(result["allocations"][0]["option"], "long")

    def test_budget_is_respected(self) -> None:
        allocator = AdaptiveConsequenceResolutionAllocator(
            [DecisionRegion("a", 1, 1, 1), DecisionRegion("b", 1, 1, 1)],
            [ResolutionOption("cheap", 1, 5, 5), ResolutionOption("fine", 5, 1, 1)],
        )
        result = allocator.allocate(6)
        self.assertLessEqual(result["total_cost"], 6)


if __name__ == "__main__":
    unittest.main()
