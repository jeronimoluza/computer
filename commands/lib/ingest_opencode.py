#!/usr/bin/env python3

import argparse
import json
import os
import re
import sqlite3
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from redact import redact_text


def eprint(*args: Any) -> None:
    print(*args, file=sys.stderr)


def read_json_file(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def write_json_file(path: str, obj: Dict[str, Any]) -> None:
    tmp = f"{path}.tmp"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def safe_mkdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def detect_project_key(directory: str) -> Optional[str]:
    # Repo slug = git top-level dir basename. We avoid calling git; just walk up
    # and detect a .git directory.
    d = os.path.abspath(directory)
    if not os.path.isdir(d):
        return None
    while True:
        if os.path.isdir(os.path.join(d, ".git")):
            return os.path.basename(d)
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def json_loads_best_effort(s: str) -> Dict[str, Any]:
    try:
        val = json.loads(s)
        if isinstance(val, dict):
            return val
        return {"_": val}
    except Exception:
        return {"_raw": s}


@dataclass
class SessionRow:
    id: str
    title: str
    directory: str
    time_created: int
    time_updated: int


def load_sessions(
    conn: sqlite3.Connection, since_updated_ms: int, limit: Optional[int]
) -> List[SessionRow]:
    q = (
        "SELECT id, title, directory, time_created, time_updated "
        "FROM session WHERE time_updated > ? ORDER BY time_updated ASC"
    )
    params: Tuple[Any, ...] = (since_updated_ms,)
    if limit is not None:
        q += " LIMIT ?"
        params = (since_updated_ms, limit)

    out: List[SessionRow] = []
    for row in conn.execute(q, params):
        out.append(SessionRow(*row))
    return out


def load_messages(
    conn: sqlite3.Connection, session_id: str
) -> List[Tuple[str, int, int, Dict[str, Any]]]:
    out: List[Tuple[str, int, int, Dict[str, Any]]] = []
    for row in conn.execute(
        "SELECT id, time_created, time_updated, data FROM message WHERE session_id = ? ORDER BY time_created ASC",
        (session_id,),
    ):
        mid, tc, tu, data_s = row
        out.append((mid, tc, tu, json_loads_best_effort(data_s)))
    return out


def load_parts(
    conn: sqlite3.Connection, session_id: str
) -> List[Tuple[str, str, int, int, Dict[str, Any]]]:
    out: List[Tuple[str, str, int, int, Dict[str, Any]]] = []
    for row in conn.execute(
        "SELECT id, message_id, time_created, time_updated, data FROM part WHERE session_id = ? ORDER BY time_created ASC",
        (session_id,),
    ):
        pid, mid, tc, tu, data_s = row
        out.append((pid, mid, tc, tu, json_loads_best_effort(data_s)))
    return out


def normalize_parts_to_text(parts: List[Dict[str, Any]]) -> str:
    chunks: List[str] = []
    for p in parts:
        p_type = p.get("type")
        if p_type == "text":
            text = p.get("text")
            if isinstance(text, str) and text.strip():
                chunks.append(text)
        elif p_type == "tool":
            tool = p.get("tool")
            state = p.get("state", {})
            status = None
            if isinstance(state, dict):
                status = state.get("status")
            if isinstance(tool, str):
                if isinstance(status, str):
                    chunks.append(f"[tool] {tool} ({status})")
                else:
                    chunks.append(f"[tool] {tool}")
        else:
            # Fallback: avoid dumping raw JSON; keep a one-liner.
            if isinstance(p_type, str):
                chunks.append(f"[{p_type}]")
    return "\n".join(chunks).strip()


def write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=True))
            f.write("\n")
    os.replace(tmp, path)


def write_text(path: str, content: str) -> None:
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(redact_text(content))
        if not content.endswith("\n"):
            f.write("\n")
    os.replace(tmp, path)


def build_summary_md(meta: Dict[str, Any]) -> str:
    title = meta.get("title") or "(untitled)"
    tool = meta.get("tool") or "opencode"
    sid = meta.get("session_id") or meta.get("id") or ""
    project_key = meta.get("project_key") or ""
    directory = meta.get("directory") or ""
    created = meta.get("time_created_ms")
    updated = meta.get("time_updated_ms")

    def fmt_ms(x: Any) -> str:
        if isinstance(x, int):
            return str(x)
        return ""

    lines: List[str] = []
    lines.append(f"# Session: {title}")
    lines.append("")
    lines.append("## Metadata")
    lines.append(f"- tool: {tool}")
    if sid:
        lines.append(f"- session_id: {sid}")
    if project_key:
        lines.append(f"- project_key: {project_key}")
    if directory:
        lines.append(f"- directory: {directory}")
    if created is not None:
        lines.append(f"- time_created_ms: {fmt_ms(created)}")
    if updated is not None:
        lines.append(f"- time_updated_ms: {fmt_ms(updated)}")
    lines.append("")
    lines.append("## Goal")
    lines.append("-")
    lines.append("")
    lines.append("## Decisions")
    lines.append("-")
    lines.append("")
    lines.append("## Discoveries")
    lines.append("-")
    lines.append("")
    lines.append("## Accomplished")
    lines.append("-")
    lines.append("")
    lines.append("## Next Steps")
    lines.append("-")
    return "\n".join(lines)


def build_candidates_md(meta: Dict[str, Any]) -> str:
    title = meta.get("title") or "(untitled)"
    lines: List[str] = []
    lines.append(f"# Candidates: {title}")
    lines.append("")
    lines.append("Promote high-signal items into durable knowledge objects.")
    lines.append("")
    lines.append("## Candidates")
    lines.append("-")
    return "\n".join(lines)


def ingest_one(
    conn: sqlite3.Connection,
    out_root: str,
    s: SessionRow,
    dry_run: bool,
) -> Tuple[int, Optional[int]]:
    session_dir = os.path.join(out_root, s.id)
    raw_dir = os.path.join(session_dir, "raw")

    project_key = detect_project_key(s.directory) or ""

    meta = {
        "tool": "opencode",
        "session_id": s.id,
        "title": s.title,
        "directory": s.directory,
        "project_key": project_key,
        "time_created_ms": s.time_created,
        "time_updated_ms": s.time_updated,
        "source": {
            "db": os.path.expanduser("~/.local/share/opencode/opencode.db"),
            "tables": ["session", "message", "part"],
        },
    }

    if dry_run:
        print(f"would ingest: opencode {s.id}  {s.title}")
        return 0, s.time_updated

    safe_mkdir(raw_dir)
    write_json_file(os.path.join(session_dir, "meta.json"), meta)

    # Raw exports (minimal, but enough for debugging and reprocessing)
    write_json_file(
        os.path.join(raw_dir, "session.json"),
        {
            "id": s.id,
            "title": s.title,
            "directory": s.directory,
            "time_created": s.time_created,
            "time_updated": s.time_updated,
        },
    )

    msgs = load_messages(conn, s.id)
    parts = load_parts(conn, s.id)

    raw_messages = []
    for mid, tc, tu, data in msgs:
        raw_messages.append(
            {"id": mid, "time_created": tc, "time_updated": tu, "data": data}
        )
    write_jsonl(os.path.join(raw_dir, "message.jsonl"), raw_messages)

    raw_parts = []
    for pid, mid, tc, tu, data in parts:
        raw_parts.append(
            {
                "id": pid,
                "message_id": mid,
                "time_created": tc,
                "time_updated": tu,
                "data": data,
            }
        )
    write_jsonl(os.path.join(raw_dir, "part.jsonl"), raw_parts)

    parts_by_message: Dict[str, List[Dict[str, Any]]] = {}
    for _, mid, _, _, pdata in parts:
        d = pdata
        if "data" in d and isinstance(d.get("data"), dict):
            # Some rows may wrap the actual payload under data.
            inner = d.get("data")
            if isinstance(inner, dict):
                d = inner
        parts_by_message.setdefault(mid, []).append(d)

    normalized: List[Dict[str, Any]] = []
    for mid, tc, _tu, mdata in msgs:
        role = mdata.get("role")
        if not isinstance(role, str):
            role = "assistant"
        created_ms = tc
        mtime = mdata.get("time")
        if isinstance(mtime, dict) and isinstance(mtime.get("created"), int):
            created_ms = mtime["created"]

        text = normalize_parts_to_text(parts_by_message.get(mid, []))
        normalized.append(
            {
                "id": mid,
                "role": role,
                "created_ms": created_ms,
                "content": text,
            }
        )

    write_jsonl(os.path.join(session_dir, "messages.jsonl"), normalized)
    write_text(os.path.join(session_dir, "summary.md"), build_summary_md(meta))
    write_text(os.path.join(session_dir, "candidates.md"), build_candidates_md(meta))
    return 1, s.time_updated


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Ingest OpenCode sessions into ~/.computer/local/sessions"
    )
    ap.add_argument("--db", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    state = read_json_file(args.state)
    since = 0
    if isinstance(state.get("opencode"), dict) and isinstance(
        state["opencode"].get("last_time_updated_ms"), int
    ):
        since = state["opencode"]["last_time_updated_ms"]

    safe_mkdir(args.out)

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row  # type: ignore
    try:
        sessions = load_sessions(conn, since_updated_ms=since, limit=args.limit)
        if not sessions:
            if args.dry_run:
                print("no sessions to ingest")
            else:
                print("No new OpenCode sessions to ingest.")
            return 0

        ingested = 0
        max_updated: Optional[int] = None
        for s in sessions:
            did, updated = ingest_one(conn, args.out, s, args.dry_run)
            ingested += did
            if updated is not None:
                max_updated = (
                    updated if max_updated is None else max(max_updated, updated)
                )

        if not args.dry_run and max_updated is not None:
            state.setdefault("opencode", {})
            if not isinstance(state["opencode"], dict):
                state["opencode"] = {}
            state["opencode"]["last_time_updated_ms"] = int(max_updated)
            write_json_file(args.state, state)

        if args.dry_run:
            print(f"would ingest {len(sessions)} session(s)")
        else:
            print(f"Ingested {ingested} OpenCode session(s) into {args.out}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
