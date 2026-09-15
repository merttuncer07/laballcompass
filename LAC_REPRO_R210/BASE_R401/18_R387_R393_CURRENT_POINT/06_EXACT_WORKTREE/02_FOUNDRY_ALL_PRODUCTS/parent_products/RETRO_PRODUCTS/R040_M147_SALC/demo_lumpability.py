import json

from salc import audit_lumpability


def main() -> None:
    exact = [
        [0.60, 0.20, 0.10, 0.10], [0.30, 0.50, 0.15, 0.05],
        [0.10, 0.10, 0.50, 0.30], [0.05, 0.15, 0.20, 0.60],
    ]
    approximate = [row[:] for row in exact]
    approximate[1] = [0.25, 0.50, 0.20, 0.05]
    partition = ["CALM", "CALM", "STRESS", "STRESS"]
    print(json.dumps({
        "exact": audit_lumpability(exact, partition, horizon=30).to_dict(),
        "approximate": audit_lumpability(
            approximate, partition, horizon=30, allowed_horizon_tv=0.08
        ).to_dict(),
    }, indent=2))


if __name__ == "__main__":
    main()
