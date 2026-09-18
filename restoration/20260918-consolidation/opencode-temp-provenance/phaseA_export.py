"""Phase A exporter: pre-anchor UnionAlpha session history -> RAW.md + RAW.json.
Read-only against a DB COPY. Base64 uploads referenced, never dumped.
"""
import sqlite3, json, os
from datetime import datetime, timezone

COPY = "/var/folders/87/7zcwj9x95fq3g0bv00f1t_gh0000gn/T/opencode/opencode_ro_copy.db"
SES = "ses_f51c4da05ffelXwgtSh3aHzGT3"
ANCHOR_T = 1789684860019  # msg_0b187c473001Kkt8ruwK8bLePI (Q195-CORE call)
ANCHOR_ID = "msg_0b187c473001Kkt8ruwK8bLePI"
OUTDIR = "/Users/mertalituncer/Documents/Default Project/laballcompass/LAC_REPRO_R210/ACTIVE_RESEARCH/R212_VOLTERRA_NO_RESET_INTRINSIC"

db = sqlite3.connect(f"file:{COPY}?mode=ro", uri=True)
cur = db.cursor()

msgs = cur.execute(
    "SELECT id, time_created, data FROM message WHERE session_id=? "
    "AND time_created < ? ORDER BY time_created, id", (SES, ANCHOR_T)).fetchall()
parts = cur.execute(
    "SELECT message_id, id, time_created, data FROM part WHERE session_id=? "
    "AND time_created < ? ORDER BY time_created, id", (SES, ANCHOR_T)).fetchall()

byparts = {}
for mid, pid, tc, data in parts:
    byparts.setdefault(mid, []).append((pid, tc, json.loads(data)))


def iso(tc):
    return datetime.fromtimestamp(tc / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


md = ["# UNIONALPHA Prehistory RAW (Phase A)",
      "",
      f"Session: {SES} (project: /Users/mertalituncer/Documents/Default Project)",
      f"Exported from read-only copy of opencode.db. {len(msgs)} messages pre-anchor.",
      f"Anchor: {ANCHOR_ID} @ {iso(ANCHOR_T)} (Q195-CORE bash call).",
      "Base64 upload bodies omitted by design (referenced only).",
      "",
      "<<< CURRENT MUSE CONTEXT STARTED HERE: \"What did we do so far?\" >>>",
      "(marker: everything BELOW this line predates the Q195-CORE call that",
      " opens the previously accessible context. Nothing below was visible",
      " to Muse before this recovery.)",
      "",
      "---",
      ""]
js = {"session": SES, "anchor_id": ANCHOR_ID, "anchor_time": iso(ANCHOR_T),
      "pre_anchor_messages": len(msgs), "messages": []}

for mid, tc, mdata in msgs:
    m = json.loads(mdata)
    role = m.get("role", "?")
    model = (m.get("model") or {}).get("modelID") or m.get("modelID", "")
    md.append(f"## {iso(tc)} | {role} | {mid} | model={model}")
    md.append("")
    jm = {"id": mid, "time": iso(tc), "role": role, "model": model, "parts": []}
    for pid, ptc, p in byparts.get(mid, []):
        t = p.get("type")
        if t == "text":
            md.append("```text")
            md.append(p.get("text", ""))
            md.append("```")
            md.append("")
            jm["parts"].append({"type": "text", "text": p.get("text", "")})
        elif t == "tool":
            st = p.get("state", {})
            md.append(f"TOOL-CALL [{p.get('tool')}] {pid} call={p.get('callID')}")
            md.append("input:")
            md.append("```")
            md.append(json.dumps(st.get("input", {}), indent=1)[:20000])
            md.append("```")
            out = st.get("output", st.get("error", ""))
            md.append("output/error:")
            md.append("```")
            md.append(str(out)[:60000])
            md.append("```")
            md.append("")
            jp = {"type": "tool", "tool": p.get("tool"),
                  "input": st.get("input", {})}
            jp["output"] = str(out)[:60000]
            jm["parts"].append(jp)
        elif t == "file":
            ref = {k: p.get(k) for k in ("mime", "filename", "url") if k in p}
            note = (f"FILE-UPLOAD mime={p.get('mime')} "
                    f"name={p.get('filename')} "
                    f"body_bytes_omitted={len(p.get('url', ''))}")
            md.append(note)
            md.append("")
            jm["parts"].append({"type": "file", "ref": note})
        elif t in ("step-start", "step-finish"):
            jm["parts"].append({"type": t})
        else:
            md.append(f"[{t} part {pid} omitted from md; kept in json]")
            md.append("")
            jm["parts"].append({"type": t, "raw": p})
    js["messages"].append(jm)

with open(os.path.join(OUTDIR, "UNIONALPHA_PREHISTORY_RAW.md"), "w") as f:
    f.write("\n".join(md))
with open(os.path.join(OUTDIR, "UNIONALPHA_PREHISTORY_RAW.json"), "w") as f:
    json.dump(js, f, indent=1)
print("msgs:", len(msgs))
print("md bytes:", os.path.getsize(os.path.join(OUTDIR, "UNIONALPHA_PREHISTORY_RAW.md")))
print("json bytes:", os.path.getsize(os.path.join(OUTDIR, "UNIONALPHA_PREHISTORY_RAW.json")))
