"""Static local review page for evidence-version workspaces."""
from __future__ import annotations

import html
from pathlib import Path


def _h(value):
    return html.escape(str(value))


def write_workspace_report(workspace):
    # Import lazily to avoid a module cycle with mutation functions.
    from .evidence_workspace import workspace_state
    root = Path(workspace).resolve()
    state = workspace_state(root)
    versions = {version["id"]: version for version in state["versions"]}
    proposals_by_version = {}
    for candidate in state["candidates"]:
        if candidate["classification"] == "likely_revision" and candidate["status"] == "pending":
            proposals_by_version.setdefault(candidate["left_version_id"], []).append(candidate["id"])
            proposals_by_version.setdefault(candidate["right_version_id"], []).append(candidate["id"])

    artifact_sections = []
    comparisons = {row["relationship_id"]: row for row in state["comparisons"]}
    for artifact in state["artifacts"]:
        history = []
        relationship_by_after = {row["after_version_id"]: row for row in artifact["relationships"]}
        for index, version_id in enumerate(artifact["version_order"], 1):
            version = versions[version_id]
            links = ""
            relationship = relationship_by_after.get(version_id)
            if relationship and relationship["id"] in comparisons:
                comparison = comparisons[relationship["id"]]
                links = f' · <a href="{_h(comparison["report_path"])}">open comparison</a>'
                if comparison.get("structural_report_path"):
                    links += f' · <a href="{_h(comparison["structural_report_path"])}">structural correspondence</a>'
            history.append(
                f'<li><b>v{index}</b> {_h(version["first_name"])} '
                f'<code>{_h(version["sha256"][:16])}…</code>{links}</li>'
            )
        warning = '<p class="warning">Ordering is incomplete or ambiguous.</p>' if artifact["ordering_ambiguous"] else ""
        artifact_sections.append(
            f'<section><h2>{_h(artifact["name"])}</h2>{warning}<ol>{"".join(history)}</ol></section>'
        )

    pending = []
    assessments = []
    for candidate in state["candidates"]:
        left = versions[candidate["left_version_id"]]
        right = versions[candidate["right_version_id"]]
        evidence = candidate["evidence"]
        structure = evidence.get("structure", {})
        reasons = " ".join(evidence.get("reasons", []))
        ambiguity = (
            " <b>Ambiguous: one or both files have other plausible candidates.</b>"
            if len(proposals_by_version.get(left["id"], [])) > 1 or len(proposals_by_version.get(right["id"], [])) > 1
            else ""
        )
        details = (
            f'Sheet overlap {_h(structure.get("sheet_name_overlap", 0))}; '
            f'cell-count ratio {_h(structure.get("populated_cell_count_ratio", 0))}; '
            f'common formula texts {_h(structure.get("common_formula_text_hashes", 0))}. '
            f'{_h(reasons)}'
        )
        if candidate["classification"] == "likely_revision":
            pending.append(
                f'<article><h3>{_h(left["first_name"])} ↔ {_h(right["first_name"])}</h3>'
                f'<p>{details}{ambiguity}</p><p>Candidate <code>{_h(candidate["id"])}</code> · '
                f'status <b>{_h(candidate["status"])}</b></p>'
                f'<pre>.venv/bin/python lab.py workbench workspace confirm "{_h(root)}" {_h(candidate["id"])} '
                f'--before {_h(left["id"])} --artifact-name "Artifact name"</pre>'
                f'<pre>.venv/bin/python lab.py workbench workspace reject "{_h(root)}" {_h(candidate["id"])}</pre></article>'
            )
        else:
            assessments.append(
                f'<li>{_h(left["first_name"])} ↔ {_h(right["first_name"])}: {_h(reasons)}</li>'
            )

    inventory = []
    for version in state["versions"]:
        names = ", ".join(sorted({row["observed_name"] for row in version["occurrences"]}))
        inventory.append(
            f'<tr><td>{_h(version["id"])}</td><td>{_h(names)}</td>'
            f'<td><code>{_h(version["sha256"])}</code></td>'
            f'<td>{len(version["occurrences"])}</td></tr>'
        )
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_h(state["workspace"]["name"])} · Evidence versions</title>
<style>body{{max-width:1100px;margin:auto;padding:28px;font:15px system-ui;color:#18333d;background:#f3f6f7}}header,section,article{{background:white;border:1px solid #d4e0e3;border-radius:9px;padding:20px;margin:0 0 18px}}h1{{margin-top:0}}table{{width:100%;border-collapse:collapse}}th,td{{padding:9px;border-bottom:1px solid #dce5e8;text-align:left;vertical-align:top}}code,pre{{overflow-wrap:anywhere}}pre{{white-space:pre-wrap;background:#edf3f4;padding:12px;border-radius:6px}}.warning{{color:#8a4b00}}.caution{{border-left:4px solid #a87324;padding-left:12px}}</style>
<header><h1>{_h(state["workspace"]["name"])}</h1><p>Local evidence version workspace</p>
<p class="caution">Likely revision is never automatic confirmation. Similar content does not prove provenance. Structural downstream impact does not establish numeric effect or audit misstatement.</p></header>
<section><h2>Confirmed artifact histories</h2>{''.join(artifact_sections) or '<p>No confirmed version family yet.</p>'}</section>
<section><h2>Likely revision proposals</h2>{''.join(pending) or '<p>No pending proposals.</p>'}</section>
<section><h2>Inventory</h2><table><thead><tr><th>Version ID</th><th>Observed names</th><th>SHA-256</th><th>Locations seen</th></tr></thead><tbody>{''.join(inventory)}</tbody></table></section>
<section><details><summary>No-confident-match assessments</summary><ul>{''.join(assessments) or '<li>None</li>'}</ul></details></section>
</html>'''
    destination = root / "index.html"
    destination.write_text(page, encoding="utf-8")
    return destination
