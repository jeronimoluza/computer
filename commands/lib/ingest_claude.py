#!/usr/bin/env python3

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from redact import redact_text


def parse_iso_to_ms(s: str) -> Optional[int]:
    try:
        # Example: 2026-03-08T15:40:26.227Z
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception:
        return None


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


def detect_project_key(directory: str) -> Optional[str]:
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


def build_summary_md(meta: Dict[str, Any]) -> str:
    title = meta.get("title") or "(untitled)"
    tool = meta.get("tool") or "claude"
    sid = meta.get("session_id") or ""
    project_key = meta.get("project_key") or ""
    directory = meta.get("directory") or ""

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


def iter_session_files(root: str) -> List[str]:
    out: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip subagent logs for now (can be added later).
        if "subagents" in dirnames:
            dirnames.remove("subagents")
        for fn in filenames:
            if not fn.endswith(".jsonl"):
                continue
            out.append(os.path.join(dirpath, fn))
    return out


def normalize_role(rec_type: Any) -> str:
    if rec_type == "user":
        return "user"
    if rec_type == "assistant":
        return "assistant"
    if rec_type == "system":
        return "system"
    if rec_type == "tool":
        return "tool"
    return "system"


def ingest_one(path: str, out_root: str, dry_run: bool) -> Tuple[int, Optional[int]]:
    mtime = int(os.path.getmtime(path))
    session_id = os.path.splitext(os.path.basename(path))[0]
    session_dir = os.path.join(out_root, session_id)
    raw_dir = os.path.join(session_dir, "raw")

    # Read JSONL
    recs: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    recs.append(obj)
            except Exception:
                continue

    if not recs:
        if dry_run:
            print(f"would ingest: claude {session_id} (empty)")
        return 0, mtime

    cwd = None
    title = None
    created_ms = None
    updated_ms = None
    git_branch = None
    version = None

    for r in recs:
        if cwd is None and isinstance(r.get("cwd"), str):
            cwd = r.get("cwd")
        if git_branch is None and isinstance(r.get("gitBranch"), str):
            git_branch = r.get("gitBranch")
        if version is None and isinstance(r.get("version"), str):
            version = r.get("version")
        ts = r.get("timestamp")
        if isinstance(ts, str):
            ms = parse_iso_to_ms(ts)
            if ms is not None:
                created_ms = ms if created_ms is None else min(created_ms, ms)
                updated_ms = ms if updated_ms is None else max(updated_ms, ms)

        # Heuristic title: first user message with non-empty content
        content_val = r.get("content")
        if title is None and r.get("type") == "user" and isinstance(content_val, str):
            c = content_val.strip()
            if c:
                title = c.splitlines()[0][:80]

    directory = cwd or ""
    project_key = detect_project_key(directory) or ""

    meta = {
        "tool": "claude",
        "session_id": session_id,
        "title": title or f"Claude session {session_id}",
        "directory": directory,
        "project_key": project_key,
        "git_branch": git_branch or "",
        "version": version or "",
        "time_created_ms": created_ms,
        "time_updated_ms": updated_ms,
        "source": {
            "path": path,
        },
    }

    if dry_run:
        print(f"would ingest: claude {session_id}  {meta['title']}")
        return 0, mtime

    os.makedirs(raw_dir, exist_ok=True)
    write_json_file(os.path.join(session_dir, "meta.json"), meta)

    # Copy raw jsonl verbatim into raw/
    raw_copy_path = os.path.join(raw_dir, "session.jsonl")
    with (
        open(path, "r", encoding="utf-8") as src,
        open(f"{raw_copy_path}.tmp", "w", encoding="utf-8") as dst,
    ):
        for line in src:
            dst.write(line)
    os.replace(f"{raw_copy_path}.tmp", raw_copy_path)

    normalized: List[Dict[str, Any]] = []
    for r in recs:
        rid = r.get("uuid")
        if not isinstance(rid, str):
            continue
        role = normalize_role(r.get("type"))
        ts = r.get("timestamp")
        created = None
        if isinstance(ts, str):
            created = parse_iso_to_ms(ts)
        content = r.get("content")
        if not isinstance(content, str):
            content = ""
        normalized.append(
            {
                "id": rid,
                "role": role,
                "created_ms": created,
                "content": content,
            }
        )

    write_jsonl(os.path.join(session_dir, "messages.jsonl"), normalized)
    write_text(os.path.join(session_dir, "summary.md"), build_summary_md(meta))
    write_text(os.path.join(session_dir, "candidates.md"), build_candidates_md(meta))
    return 1, mtime


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest Claude Code JSONL sessions")
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    state = read_json_file(args.state)
    files_state: Dict[str, int] = {}
    if isinstance(state.get("claude"), dict) and isinstance(
        state["claude"].get("files"), dict
    ):
        for k, v in state["claude"]["files"].items():
            if isinstance(k, str) and isinstance(v, int):
                files_state[k] = v

    os.makedirs(args.out, exist_ok=True)

    files = iter_session_files(args.root)
    files.sort(key=lambda p: os.path.getmtime(p))

    to_ingest: List[str] = []
    for p in files:
        mtime = int(os.path.getmtime(p))
        prev = files_state.get(p)
        if prev is None or mtime > prev:
            to_ingest.append(p)

    if args.limit is not None:
        to_ingest = to_ingest[: args.limit]

    if not to_ingest:
        if args.dry_run:
            print("no sessions to ingest")
        else:
            print("No new Claude sessions to ingest.")
        return 0

    ingested = 0
    for p in to_ingest:
        did, mtime = ingest_one(p, args.out, args.dry_run)
        ingested += did
        if not args.dry_run and mtime is not None:
            files_state[p] = int(mtime)

    if not args.dry_run:
        state.setdefault("claude", {})
        if not isinstance(state["claude"], dict):
            state["claude"] = {}
        state["claude"]["files"] = files_state
        write_json_file(args.state, state)

    if args.dry_run:
        print(f"would ingest {len(to_ingest)} session file(s)")
    else:
        print(f"Ingested {ingested} Claude session file(s) into {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
