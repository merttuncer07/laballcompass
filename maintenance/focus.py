"""Small, read-only work briefs. No model calls, catalog scan, or automatic promotion."""
import argparse
import json
from pathlib import Path

from maintenance.runner import BASE

MAX_BRIEF_BYTES = 6000
REQUIRED_TEXT = ("goal", "baseline", "success", "stop", "next_action", "verification")


def load(base=BASE):
    base = Path(base).resolve()
    data = json.loads((base / "lab-focus.json").read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported focus schema")
    missions = data.get("missions", {})
    if not missions or data.get("active") not in missions:
        raise ValueError("Select one existing active mission")
    for name, mission in missions.items():
        for field in REQUIRED_TEXT:
            if not isinstance(mission.get(field), str) or not mission[field].strip():
                raise ValueError(f"{name}: missing {field}")
        if mission.get("status") not in ("active", "parked", "complete"):
            raise ValueError(f"{name}: invalid status")
        for field in ("read", "evidence"):
            paths = mission.get(field)
            if not isinstance(paths, list) or not paths:
                raise ValueError(f"{name}: {field} must contain local paths")
            for value in paths:
                if not isinstance(value, str):
                    raise ValueError(f"{name}: invalid path")
                path = (base / value).resolve()
                if Path(value).is_absolute() or not path.is_relative_to(base) or not path.is_file():
                    raise ValueError(f"{name}: missing or unsafe path: {value}")
    active = [name for name, m in missions.items() if m["status"] == "active"]
    if active != [data["active"]]:
        raise ValueError("Exactly one mission must be active; park the others")
    return data


def brief(data, name=None):
    name = name or data["active"]
    if name not in data["missions"]:
        raise ValueError("Unknown mission; use focus --list")
    mission = data["missions"][name]
    lines = [f"Focus: {name} [{mission['status']}]", ""]
    for field in REQUIRED_TEXT:
        lines.extend([f"{field.replace('_', ' ').capitalize()}: {mission[field]}", ""])
    for field in ("read", "evidence"):
        lines.append(f"{field.capitalize()} (retrieve only when relevant):")
        lines.extend(f"- {path}" for path in mission[field])
        lines.append("")
    lines.append("Evidence is historical and scoped. Check source/data changes before relying on it. "
                 "Tests do not establish product advantage. No automatic test skipping or promotion.")
    result = "\n".join(lines) + "\n"
    if len(result.encode("utf-8")) > MAX_BRIEF_BYTES:
        raise ValueError(f"Brief exceeds {MAX_BRIEF_BYTES} bytes; move history into linked evidence")
    return result


def main(args):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mission", nargs="?")
    parser.add_argument("--list", action="store_true", help="List mission IDs without loading their history")
    options = parser.parse_args(args)
    try:
        data = load()
        if options.list:
            for name, mission in data["missions"].items():
                print(f"{name}: {mission['status']}")
        else:
            print(brief(data, options.mission), end="")
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.error(str(error))
