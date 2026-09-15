import json

from ebc import HistoricalEstimate, borrow_evidence


def main() -> None:
    history = [
        HistoricalEstimate("similar_market_A", 1.10, 0.12),
        HistoricalEstimate("similar_market_B", 1.25, 0.15),
        HistoricalEstimate("structurally_changed_market", 2.40, 0.10),
    ]
    adaptive = borrow_evidence(
        1.20, 0.25, history, compatibility_scale=1.25, borrowing_cap_ratio=2.0
    )
    full_pool = borrow_evidence(
        1.20, 0.25, history, compatibility_scale=1e9, borrowing_cap_ratio=1e9
    )
    current_only = borrow_evidence(1.20, 0.25, [], borrowing_cap_ratio=0.0)
    print(json.dumps({
        "current_only": current_only.to_dict(),
        "adaptive_borrowing": adaptive.to_dict(),
        "uncontrolled_full_pooling": full_pool.to_dict(),
        "adaptive_shift_from_current": adaptive.posterior_estimate - 1.20,
        "full_pool_shift_from_current": full_pool.posterior_estimate - 1.20,
    }, indent=2))


if __name__ == "__main__":
    main()
