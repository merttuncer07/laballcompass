import json

from mlhpe import audit_three_lists, chapman_two_list


def main() -> None:
    counts = {"100": 120, "010": 100, "001": 160, "110": 90, "101": 35, "011": 30, "111": 45}
    audit = audit_three_lists(counts)
    two_list = chapman_two_list(255, 265, 135)
    print(json.dumps({
        "three_list_audit": audit.to_dict(),
        "two_list_chapman_reference": two_list.__dict__,
    }, indent=2))


if __name__ == "__main__":
    main()
