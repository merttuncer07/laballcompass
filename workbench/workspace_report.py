"""Static local review page for evidence identity workspaces."""
from __future__ import annotations

import html
from pathlib import Path


def _h(value):
    return html.escape(str(value))


def write_workspace_report(workspace):
    from .evidence_workspace import workspace_state
    root = Path(workspace).resolve()
    state = workspace_state(root)
    blobs = {blob["id"]: blob for blob in state["file_blobs"]}
    versions = {version["id"]: version for version in state["evidence_versions"]}
    proposals_by_blob = {}
    for candidate in state["candidates"]:
        if candidate["classification"] == "likely_revision" and candidate["status"] in ("pending", "withdrawn"):
            proposals_by_blob.setdefault(candidate["left_blob_id"], []).append(candidate["id"])
            proposals_by_blob.setdefault(candidate["right_blob_id"], []).append(candidate["id"])

    comparisons = {row["relationship_id"]: row for row in state["comparisons"]}
    artifact_sections = []
    for artifact in state["artifacts"]:
        history = []
        active = [row for row in artifact["relationships"] if row["status"] == "active"]
        relationship_by_after = {row["after_version_id"]: row for row in active}
        for index, version_id in enumerate(artifact["version_order"], 1):
            version = versions[version_id]
            blob = blobs[version["blob_id"]]
            links = ""
            relationship = relationship_by_after.get(version_id)
            if relationship and relationship["id"] in comparisons:
                comparison = comparisons[relationship["id"]]
                triage_path = Path("comparisons") / relationship["id"] / "triage" / "index.html"
                if (root / triage_path).is_file():
                    links = f' · <a href="{_h(triage_path.as_posix())}"><b>open revision triage</b></a>'
                links += f' · <a href="{_h(comparison["report_path"])}">raw comparison</a>'
                if comparison.get("structural_report_path"):
                    links += f' · <a href="{_h(comparison["structural_report_path"])}">structural correspondence</a>'
            history.append(
                f'<li><b>v{index}</b> {_h(blob["display_name"])} '
                f'<code>{_h(version_id)}</code> · blob <code>{_h(blob["sha256"][:16])}…</code>{links}</li>'
            )
        warning = '<p class="warning">Current ordering is incomplete or ambiguous.</p>' if artifact["ordering_ambiguous"] else ""
        past = [row for row in artifact["relationships"] if row["status"] != "active"]
        past_text = (f'<p class="muted">{len(past)} withdrawn or superseded relationship(s) remain in history.</p>'
                     if past else "")
        artifact_sections.append(
            f'<section><h2>{_h(artifact["name"])}</h2><p><code>{_h(artifact["id"])}</code></p>'
            f'{warning}<ol>{"".join(history)}</ol>{past_text}</section>'
        )

    pending = []
    assessments = []
    for candidate in state["candidates"]:
        left = blobs[candidate["left_blob_id"]]
        right = blobs[candidate["right_blob_id"]]
        evidence = candidate["evidence"]
        structure = evidence.get("structure", {})
        reasons = " ".join(evidence.get("reasons", []))
        ambiguity = (
            " <b>Ambiguous: one or both blobs have other plausible candidates.</b>"
            if len(proposals_by_blob.get(left["id"], [])) > 1
            or len(proposals_by_blob.get(right["id"], [])) > 1 else ""
        )
        details = (
            f'Sheet overlap {_h(structure.get("sheet_name_overlap", 0))}; '
            f'cell-count ratio {_h(structure.get("populated_cell_count_ratio", 0))}; '
            f'common formula texts {_h(structure.get("common_formula_text_hashes", 0))}. {_h(reasons)}'
        )
        if candidate["classification"] == "likely_revision":
            pending.append(
                f'<article><h3>{_h(left["display_name"])} ↔ {_h(right["display_name"])}</h3>'
                f'<p>{details}{ambiguity}</p><p>Candidate <code>{_h(candidate["id"])}</code> · '
                f'status <b>{_h(candidate["status"])}</b></p>'
                f'<pre>.venv/bin/python lab.py workbench workspace confirm "{_h(root)}" {_h(candidate["id"])} '
                f'--before {_h(left["id"])} --artifact-name "Artifact name"</pre>'
                f'<pre>.venv/bin/python lab.py workbench workspace reject "{_h(root)}" {_h(candidate["id"])}</pre></article>'
            )
        else:
            assessments.append(
                f'<li>{_h(left["display_name"])} ↔ {_h(right["display_name"])}: {_h(reasons)}</li>'
            )

    inventory = []
    for blob in state["file_blobs"]:
        names = ", ".join(sorted({row["observed_name"] for row in blob["occurrences"]}))
        inventory.append(
            f'<tr><td>{_h(blob["id"])}</td><td>{_h(names)}</td><td><code>{_h(blob["sha256"])}</code></td>'
            f'<td>{len(blob["occurrences"])}</td><td>{len(blob["version_ids"])}</td></tr>'
        )
    events = []
    for event in reversed(state["decision_history"]):
        events.append(
            f'<tr><td>{_h(event["recorded_at"])}</td><td>{_h(event["event_type"])}</td>'
            f'<td>{_h(event.get("reason") or "")}</td><td>{_h(event.get("artifact_id") or "")}</td></tr>'
        )
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_h(state["workspace"]["name"])} · Evidence identity</title>
<style>body{{max-width:1150px;margin:auto;padding:28px;font:15px system-ui;color:#18333d;background:#f3f6f7}}header,section,article{{background:white;border:1px solid #d4e0e3;border-radius:9px;padding:20px;margin:0 0 18px}}h1{{margin-top:0}}table{{width:100%;border-collapse:collapse}}th,td{{padding:9px;border-bottom:1px solid #dce5e8;text-align:left;vertical-align:top}}code,pre{{overflow-wrap:anywhere}}pre{{white-space:pre-wrap;background:#edf3f4;padding:12px;border-radius:6px}}.warning{{color:#8a4b00}}.caution{{border-left:4px solid #a87324;padding-left:12px}}.muted{{color:#60757d}}</style>
<header><h1>{_h(state["workspace"]["name"])}</h1><p>Local evidence identity workspace · schema v{state["schema_version"]}</p>
<p class="caution">File blob identity means exact bytes. Evidence version identity means one logical version inside one artifact. Likely revision is never automatic confirmation.</p></header>
<section><h2>Evidence artifacts and logical versions</h2>{''.join(artifact_sections) or '<p>No logical evidence version has been confirmed yet.</p>'}</section>
<section><h2>Likely revision proposals</h2>{''.join(pending) or '<p>No likely-revision proposal is available.</p>'}</section>
<section><h2>Exact file blobs and occurrences</h2><table><thead><tr><th>Blob ID</th><th>Observed names</th><th>SHA-256</th><th>Occurrences</th><th>Logical versions</th></tr></thead><tbody>{''.join(inventory)}</tbody></table></section>
<section><h2>Decision history</h2><table><thead><tr><th>Time</th><th>Event</th><th>Reason</th><th>Artifact</th></tr></thead><tbody>{''.join(events) or '<tr><td colspan="4">No decisions recorded.</td></tr>'}</tbody></table></section>
<section><details><summary>No-confident-match assessments</summary><ul>{''.join(assessments) or '<li>None</li>'}</ul></details></section>
</html>'''
    destination = root / "index.html"
    destination.write_text(page, encoding="utf-8")
    return destination
