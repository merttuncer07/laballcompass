import json

from ppsa import Release, account_privacy


def main() -> None:
    releases = []
    for index in range(100):
        mechanism_id = f"query_{index:03d}"
        releases.append(Release(mechanism_id, "MECHANISM", epsilon=0.05, delta=1e-9))
        if index % 2 == 0:
            releases.append(
                Release(f"dashboard_{index:03d}", "POST_PROCESS", parent_release_id=mechanism_id)
            )
    account = account_privacy(
        releases, epsilon_budget=3.0, delta_budget=2e-6, advanced_delta_slack=1e-6
    )
    print(json.dumps({
        "account": account.to_dict(),
        "naive_error_if_dashboards_were_charged_as_queries": {
            "release_count": 150,
            "basic_epsilon": 7.5,
            "correct_charged_mechanism_count": account.mechanism_count,
        },
    }, indent=2))


if __name__ == "__main__":
    main()
