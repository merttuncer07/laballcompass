import json

from ofls import simulate_redemption


def run(gate, swing):
    return simulate_redemption(
        fund_units=1000, nav_per_unit=100, cash_buffer=5000, requested_units=300,
        liquidatable_asset_book_value=95000, linear_sale_cost=0.02, market_impact=0.20,
        gate_fraction=gate, swing_capture_fraction=swing,
    ).to_dict()


def main():
    print(json.dumps({
        "ordinary_nav": run(1.0, 0.0), "full_swing": run(1.0, 1.0),
        "ten_percent_gate": run(0.10, 0.0), "gate_plus_swing": run(0.10, 1.0),
    }, indent=2))


if __name__ == "__main__": main()
