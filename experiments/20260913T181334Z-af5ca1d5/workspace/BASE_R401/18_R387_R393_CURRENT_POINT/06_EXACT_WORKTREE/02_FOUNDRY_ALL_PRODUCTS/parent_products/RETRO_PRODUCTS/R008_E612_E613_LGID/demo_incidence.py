import json

from lgid import decompose_local_incidence


treated_before = {"wage": 3000, "amenity_value": 100, "rent": 900, "property_value": 180000, "population": 10000}
treated_after = {"wage": 3240, "amenity_value": 180, "rent": 1100, "property_value": 225000, "population": 11200}
control_before = {"wage": 2900, "amenity_value": 100, "rent": 850, "property_value": 170000, "population": 9500}
control_after = {"wage": 3000, "amenity_value": 110, "rent": 900, "property_value": 180000, "population": 9800}

result = decompose_local_incidence(
    treated_before, treated_after, control_before, control_after,
    households=5000, renter_share=0.60, owner_occupier_share=0.30,
    annual_discount_rate=0.05,
)
print(json.dumps(result.to_dict(), indent=2))
