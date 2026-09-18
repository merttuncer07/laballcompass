"""SQLite schema and v1-to-v2 migration for evidence identity workspaces."""
from __future__ import annotations

import hashlib
import json


SCHEMA_VERSION = 2


TABLES_V2 = (
    """CREATE TABLE workspace (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""",
    """CREATE TABLE file_blobs (
        id TEXT PRIMARY KEY,
        sha256 TEXT NOT NULL UNIQUE,
        extension TEXT NOT NULL,
        object_path TEXT NOT NULL UNIQUE,
        size_bytes INTEGER NOT NULL,
        first_seen_at TEXT NOT NULL,
        last_seen_at TEXT NOT NULL,
        fingerprint_json TEXT NOT NULL
    )""",
    """CREATE TABLE file_occurrences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        blob_id TEXT NOT NULL REFERENCES file_blobs(id),
        source_path TEXT NOT NULL,
        observed_name TEXT NOT NULL,
        first_seen_at TEXT NOT NULL,
        last_seen_at TEXT NOT NULL,
        UNIQUE(blob_id, source_path)
    )""",
    """CREATE TABLE artifacts (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""",
    """CREATE TABLE evidence_versions (
        id TEXT PRIMARY KEY,
        artifact_id TEXT NOT NULL REFERENCES artifacts(id),
        blob_id TEXT NOT NULL REFERENCES file_blobs(id),
        created_at TEXT NOT NULL,
        UNIQUE(artifact_id, blob_id)
    )""",
    """CREATE TABLE candidates (
        id TEXT PRIMARY KEY,
        left_blob_id TEXT NOT NULL REFERENCES file_blobs(id),
        right_blob_id TEXT NOT NULL REFERENCES file_blobs(id),
        classification TEXT NOT NULL,
        status TEXT NOT NULL,
        evidence_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        decided_at TEXT,
        UNIQUE(left_blob_id, right_blob_id)
    )""",
    """CREATE TABLE version_relationships (
        id TEXT PRIMARY KEY,
        artifact_id TEXT NOT NULL REFERENCES artifacts(id),
        before_version_id TEXT NOT NULL REFERENCES evidence_versions(id),
        after_version_id TEXT NOT NULL REFERENCES evidence_versions(id),
        candidate_id TEXT REFERENCES candidates(id),
        status TEXT NOT NULL,
        confirmed_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        withdrawn_at TEXT,
        supersedes_relationship_id TEXT REFERENCES version_relationships(id),
        CHECK(before_version_id <> after_version_id)
    )""",
    """CREATE UNIQUE INDEX active_version_relationship_pair
        ON version_relationships(artifact_id, before_version_id, after_version_id)
        WHERE status = 'active'""",
    """CREATE TABLE decision_history (
        id TEXT PRIMARY KEY,
        event_type TEXT NOT NULL,
        artifact_id TEXT REFERENCES artifacts(id),
        version_id TEXT REFERENCES evidence_versions(id),
        relationship_id TEXT REFERENCES version_relationships(id),
        candidate_id TEXT REFERENCES candidates(id),
        before_json TEXT,
        after_json TEXT,
        reason TEXT,
        recorded_at TEXT NOT NULL
    )""",
    """CREATE TABLE comparison_runs (
        id TEXT PRIMARY KEY,
        relationship_id TEXT NOT NULL UNIQUE REFERENCES version_relationships(id),
        report_path TEXT NOT NULL,
        structural_report_path TEXT,
        created_at TEXT NOT NULL
    )""",
)


def blob_id(sha256):
    return "blob_" + sha256[:20]


def create_schema_v2(connection):
    for statement in TABLES_V2:
        connection.execute(statement)
    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


def migrate_v1_to_v2(connection):
    """Preserve v1 state while separating exact blobs from logical versions."""
    if connection.execute("PRAGMA user_version").fetchone()[0] != 1:
        raise ValueError("Only schema v1 can be migrated to schema v2")
    old_tables = (
        "workspace", "evidence_versions", "occurrences", "artifacts",
        "artifact_versions", "candidates", "version_relationships",
        "confirmations", "comparison_runs",
    )
    connection.execute("PRAGMA foreign_keys = OFF")
    try:
        connection.execute("BEGIN IMMEDIATE")
        for table in old_tables:
            connection.execute(f"ALTER TABLE {table} RENAME TO {table}_v1")
        create_schema_v2(connection)
        connection.execute("INSERT INTO workspace SELECT * FROM workspace_v1")
        connection.execute(
            """INSERT INTO artifacts(id, name, created_at, updated_at)
               SELECT id, name, created_at, created_at FROM artifacts_v1"""
        )

        old_versions = connection.execute("SELECT * FROM evidence_versions_v1").fetchall()
        version_to_blob = {}
        for row in old_versions:
            bid = blob_id(row["sha256"])
            version_to_blob[row["id"]] = bid
            fingerprint = json.loads(row["fingerprint_json"])
            fingerprint.pop("analyzed_name", None)
            connection.execute(
                """INSERT INTO file_blobs
                   (id, sha256, extension, object_path, size_bytes, first_seen_at,
                    last_seen_at, fingerprint_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (bid, row["sha256"], row["extension"], row["object_path"],
                 row["size_bytes"], row["first_seen_at"], row["last_seen_at"],
                 json.dumps(fingerprint, ensure_ascii=False, sort_keys=True)),
            )
        for row in connection.execute("SELECT * FROM occurrences_v1"):
            connection.execute(
                """INSERT INTO file_occurrences
                   (id, blob_id, source_path, observed_name, first_seen_at, last_seen_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (row["id"], version_to_blob[row["version_id"]], row["source_path"],
                 row["observed_name"], row["first_seen_at"], row["last_seen_at"]),
            )
        for row in connection.execute("SELECT * FROM artifact_versions_v1"):
            connection.execute(
                """INSERT INTO evidence_versions(id, artifact_id, blob_id, created_at)
                   VALUES (?, ?, ?, ?)""",
                (row["version_id"], row["artifact_id"], version_to_blob[row["version_id"]], row["added_at"]),
            )
        for row in connection.execute("SELECT * FROM candidates_v1"):
            connection.execute(
                """INSERT INTO candidates
                   (id, left_blob_id, right_blob_id, classification, status,
                    evidence_json, created_at, decided_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (row["id"], version_to_blob[row["left_version_id"]],
                 version_to_blob[row["right_version_id"]], row["classification"],
                 row["status"], row["evidence_json"], row["created_at"], row["decided_at"]),
            )
        for row in connection.execute("SELECT * FROM version_relationships_v1"):
            connection.execute(
                """INSERT INTO version_relationships
                   (id, artifact_id, before_version_id, after_version_id, candidate_id,
                    status, confirmed_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, 'active', ?, ?)""",
                (row["id"], row["artifact_id"], row["before_version_id"],
                 row["after_version_id"], row["candidate_id"], row["confirmed_at"],
                 row["confirmed_at"]),
            )
        for row in connection.execute("SELECT * FROM confirmations_v1"):
            event_type = "candidate_confirmed" if row["decision"] == "confirmed" else "candidate_rejected"
            after = {
                "decision": row["decision"],
                "artifact_id": row["artifact_id"],
                "before_version_id": row["before_version_id"],
                "after_version_id": row["after_version_id"],
            }
            relationship = connection.execute(
                "SELECT id FROM version_relationships WHERE candidate_id = ?", (row["candidate_id"],)
            ).fetchone()
            connection.execute(
                """INSERT INTO decision_history
                   (id, event_type, artifact_id, relationship_id, candidate_id,
                    after_json, reason, recorded_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (row["id"], event_type, row["artifact_id"],
                 relationship["id"] if relationship else None, row["candidate_id"],
                 json.dumps(after, ensure_ascii=False, sort_keys=True),
                 "Migrated Mission #1 decision", row["recorded_at"]),
            )
        connection.execute(
            """INSERT INTO comparison_runs
               SELECT id, relationship_id, report_path, structural_report_path, created_at
               FROM comparison_runs_v1"""
        )
        for table in reversed(old_tables):
            connection.execute(f"DROP TABLE {table}_v1")
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise ValueError("Schema migration produced foreign-key violations")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.execute("PRAGMA foreign_keys = ON")


def candidate_id(left_blob_id, right_blob_id):
    left_blob_id, right_blob_id = sorted((left_blob_id, right_blob_id))
    return "cand_" + hashlib.sha256((left_blob_id + "\0" + right_blob_id).encode()).hexdigest()[:20]
