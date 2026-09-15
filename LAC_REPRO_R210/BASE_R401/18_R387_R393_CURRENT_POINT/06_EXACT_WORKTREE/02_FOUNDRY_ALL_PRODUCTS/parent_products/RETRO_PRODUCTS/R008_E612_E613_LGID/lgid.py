"""Local Gain Incidence Decomposer (LGID) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping


@dataclass(frozen=True)
class LocalIncidenceResult:
    wage_gain_per_household_month: float
    amenity_gain_per_household_month: float
    rent_increase_per_household_month: float
    property_value_increase_per_unit: float
    gross_resident_gain_per_household_year: float
    renter_net_gain_per_household_year: float
    capitalization_fraction_of_direct_flow: float | None
    annual_total_direct_resident_gain: float
    annual_renter_transfer_to_landlords: float
    owner_occupier_asset_gain: float
    absentee_landlord_asset_gain: float
    unexplained_property_value_residual_per_unit: float
    population_change_fraction: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _effect(treated_before: Mapping[str, float], treated_after: Mapping[str, float], control_before: Mapping[str, float], control_after: Mapping[str, float], key: str) -> float:
    values = [treated_before[key], treated_after[key], control_before[key], control_after[key]]
    if not all(isinstance(value, (int, float)) for value in values):
        raise ValueError(f"{key} values must be numeric")
    return float((treated_after[key] - treated_before[key]) - (control_after[key] - control_before[key]))


def decompose_local_incidence(
    treated_before: Mapping[str, float],
    treated_after: Mapping[str, float],
    control_before: Mapping[str, float],
    control_after: Mapping[str, float],
    *,
    households: int,
    renter_share: float,
    owner_occupier_share: float,
    annual_discount_rate: float,
) -> LocalIncidenceResult:
    """Difference out common change, then allocate local gains across residents and landowners.

    Required monthly/per-unit keys are ``wage``, ``amenity_value``, ``rent``, ``property_value``,
    and ``population``. Shares describe housing units; the remainder is absentee-owned.
    """

    required = ("wage", "amenity_value", "rent", "property_value", "population")
    for mapping in (treated_before, treated_after, control_before, control_after):
        missing = [key for key in required if key not in mapping]
        if missing:
            raise ValueError(f"missing keys: {missing}")
    if not isinstance(households, int) or households <= 0:
        raise ValueError("households must be a positive integer")
    if not (0 <= renter_share <= 1 and 0 <= owner_occupier_share <= 1 and renter_share + owner_occupier_share <= 1 + 1e-12):
        raise ValueError("tenure shares must be nonnegative and sum to at most one")
    if annual_discount_rate <= 0:
        raise ValueError("annual_discount_rate must be positive")

    wage = _effect(treated_before, treated_after, control_before, control_after, "wage")
    amenity = _effect(treated_before, treated_after, control_before, control_after, "amenity_value")
    rent = _effect(treated_before, treated_after, control_before, control_after, "rent")
    property_value = _effect(treated_before, treated_after, control_before, control_after, "property_value")
    population_level = _effect(treated_before, treated_after, control_before, control_after, "population")
    baseline_population = float(treated_before["population"])
    if baseline_population <= 0:
        raise ValueError("treated baseline population must be positive")

    direct_monthly = wage + amenity
    direct_annual = 12.0 * direct_monthly
    annual_rent = 12.0 * rent
    implied_asset_value = annual_rent / annual_discount_rate
    renter_net = direct_annual - annual_rent
    renter_units = households * renter_share
    owner_units = households * owner_occupier_share
    absentee_units = max(0.0, households - renter_units - owner_units)
    fraction = None if abs(direct_monthly) < 1e-12 else rent / direct_monthly
    residual = property_value - implied_asset_value

    if direct_monthly > 0 and rent > direct_monthly:
        status = "RENTERS_LOSE_DESPITE_LOCAL_GAIN"
    elif rent > 0:
        status = "GAIN_PARTLY_CAPITALIZED_INTO_IMMOBILE_ASSET"
    else:
        status = "NO_POSITIVE_RENT_CAPITALIZATION_DETECTED"

    return LocalIncidenceResult(
        wage_gain_per_household_month=wage,
        amenity_gain_per_household_month=amenity,
        rent_increase_per_household_month=rent,
        property_value_increase_per_unit=property_value,
        gross_resident_gain_per_household_year=direct_annual,
        renter_net_gain_per_household_year=renter_net,
        capitalization_fraction_of_direct_flow=fraction,
        annual_total_direct_resident_gain=households * direct_annual,
        annual_renter_transfer_to_landlords=renter_units * annual_rent,
        owner_occupier_asset_gain=owner_units * property_value,
        absentee_landlord_asset_gain=(renter_units + absentee_units) * property_value,
        unexplained_property_value_residual_per_unit=residual,
        population_change_fraction=population_level / baseline_population,
        status=status,
    )
