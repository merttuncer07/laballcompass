import json

from mcpr import Offer, clear_uniform_price_market


def main() -> None:
    offers = [
        Offer("solar", 30.0, 0.0),
        Offer("wind", 40.0, 10.0),
        Offer("gas_A", 50.0, 45.0),
        Offer("gas_B", 60.0, 70.0),
    ]
    cases = {str(demand): clear_uniform_price_market(offers, demand).to_dict() for demand in [119.0, 120.0, 121.0, 150.0]}
    shortage = clear_uniform_price_market(offers, 200.0, scarcity_price=300.0).to_dict()
    print(json.dumps({"demand_sweep": cases, "shortage_case": shortage}, indent=2))


if __name__ == "__main__":
    main()
