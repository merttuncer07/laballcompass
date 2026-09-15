import unittest

from lgid import decompose_local_incidence


def row(wage, amenity, rent, value, population):
    return {"wage": wage, "amenity_value": amenity, "rent": rent, "property_value": value, "population": population}


class Tests(unittest.TestCase):
    def test_common_trends_are_removed_and_incidence_is_split(self):
        result = decompose_local_incidence(
            row(100, 10, 40, 1000, 1000), row(130, 25, 60, 1500, 1150),
            row(100, 10, 40, 1000, 1000), row(110, 15, 45, 1100, 1050),
            households=500, renter_share=.6, owner_occupier_share=.3, annual_discount_rate=.05,
        )
        self.assertEqual(result.wage_gain_per_household_month, 20)
        self.assertEqual(result.amenity_gain_per_household_month, 10)
        self.assertEqual(result.rent_increase_per_household_month, 15)
        self.assertAlmostEqual(result.capitalization_fraction_of_direct_flow, .5)
        self.assertEqual(result.renter_net_gain_per_household_year, 180)

    def test_rent_can_overrun_direct_gain(self):
        result = decompose_local_incidence(
            row(0, 0, 0, 0, 100), row(10, 0, 20, 100, 100),
            row(0, 0, 0, 0, 100), row(0, 0, 0, 0, 100),
            households=10, renter_share=1, owner_occupier_share=0, annual_discount_rate=.1,
        )
        self.assertLess(result.renter_net_gain_per_household_year, 0)
        self.assertEqual(result.status, "RENTERS_LOSE_DESPITE_LOCAL_GAIN")

    def test_asset_residual_compares_price_with_rent_capitalization(self):
        result = decompose_local_incidence(
            row(0, 0, 0, 0, 100), row(10, 0, 10, 1500, 100),
            row(0, 0, 0, 0, 100), row(0, 0, 0, 0, 100),
            households=10, renter_share=.5, owner_occupier_share=.5, annual_discount_rate=.1,
        )
        self.assertAlmostEqual(result.unexplained_property_value_residual_per_unit, 300)

    def test_invalid_tenure_shares_are_rejected(self):
        with self.assertRaises(ValueError):
            decompose_local_incidence(
                row(0, 0, 0, 0, 100), row(1, 1, 1, 1, 101),
                row(0, 0, 0, 0, 100), row(0, 0, 0, 0, 100),
                households=10, renter_share=.8, owner_occupier_share=.5, annual_discount_rate=.1,
            )


if __name__ == "__main__":
    unittest.main()
