#!/usr/bin/env python3

import argparse
import json
import os
import re
import time
from typing import Any, Dict, Optional, Tuple


def read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
            return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def write_text(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)
        if not content.endswith("\n"):
            f.write("\n")
    os.replace(tmp, path)


def detect_project_key(directory: str) -> Optional[str]:
    d = os.path.abspath(directory)
    if not os.path.isdir(d):
        return None
    while True:
        if os.path.isdir(os.path.join(d, ".git")):
            base = os.path.basename(d)
            if base.startswith(".") and len(base) > 1:
                base = base[1:]
            return base
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def slugify(s: str, max_len: int = 60) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    if not s:
        return "untitled"
    return s[:max_len].rstrip("-")


def choose_output_dir(knowledge_root: str, personal: bool, project_key: str) -> str:
    if personal or not project_key:
        return os.path.join(knowledge_root, "personal")
    return os.path.join(knowledge_root, "projects", project_key)


def knowledge_object_template(
    *,
    ko_id: str,
    title: str,
    scope: str,
    project_key: str,
    topic_key: str,
    status: str,
    tool: str,
    session_id: str,
    session_dir: str,
    summary_md: str,
    candidates_md: str,
) -> str:
    # Keep the object high-signal; include session summary/candidates as references.
    lines = []
    lines.append("---")
    lines.append(f"id: {ko_id}")
    lines.append("type: decision")
    lines.append(f"scope: {scope}")
    if project_key:
        lines.append(f"project_key: {project_key}")
    lines.append(f"topic_key: {topic_key}")
    lines.append(f"status: {status}")
    lines.append(f"created_at_ms: {int(time.time() * 1000)}")
    lines.append(f"updated_at_ms: {int(time.time() * 1000)}")
    lines.append("sources:")
    lines.append(f"  - tool: {tool}")
    lines.append(f"    session_id: {session_id}")
    lines.append(f"    session_dir: {session_dir}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")
    lines.append("## Context")
    lines.append("-")
    lines.append("")
    lines.append("## What")
    lines.append("-")
    lines.append("")
    lines.append("## Why")
    lines.append("-")
    lines.append("")
    lines.append("## How")
    lines.append("-")
    lines.append("")
    lines.append("## Evidence")
    lines.append(f"- Session summary: {os.path.join(session_dir, 'summary.md')}")
    lines.append(f"- Session candidates: {os.path.join(session_dir, 'candidates.md')}")
    lines.append("-")
    lines.append("")
    lines.append("## Gotchas")
    lines.append("-")
    lines.append("")
    lines.append("## Next Steps")
    lines.append("-")

    if summary_md.strip():
        lines.append("")
        lines.append("## Session Summary (Reference)")
        lines.append("")
        lines.append(summary_md.strip())

    if candidates_md.strip():
        lines.append("")
        lines.append("## Session Candidates (Reference)")
        lines.append("")
        lines.append(candidates_md.strip())

    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Scaffold a knowledge object from a session"
    )
    ap.add_argument("--sessions-root", required=True)
    ap.add_argument("--knowledge-root", required=True)
    ap.add_argument("--tool", required=True)
    ap.add_argument("--session-id", required=True)
    ap.add_argument("--personal", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    session_dir = os.path.join(args.sessions_root, args.tool, args.session_id)
    meta_path = os.path.join(session_dir, "meta.json")
    summary_path = os.path.join(session_dir, "summary.md")
    candidates_path = os.path.join(session_dir, "candidates.md")

    if not os.path.isdir(session_dir) or not os.path.isfile(meta_path):
        raise SystemExit(f"Session not found or missing meta.json: {session_dir}")

    meta = read_json(meta_path)
    title = meta.get("title")
    if not isinstance(title, str) or not title.strip():
        title = f"Knowledge from session {args.session_id}"

    directory = meta.get("directory")
    if not isinstance(directory, str):
        directory = ""

    project_key = meta.get("project_key")
    if not isinstance(project_key, str):
        project_key = ""
    if not project_key and directory:
        project_key = detect_project_key(directory) or ""

    out_dir = choose_output_dir(args.knowledge_root, args.personal, project_key)
    scope = "personal" if (args.personal or not project_key) else "project"
    ko_id = f"ko_{int(time.time())}_{args.tool}_{args.session_id[:8]}"
    topic_key = f"computer/{scope}/sessions/{args.tool}/{args.session_id}"

    fname = f"{time.strftime('%Y-%m-%d')}-{slugify(title)}.md"
    out_path = os.path.join(out_dir, fname)
    if os.path.exists(out_path) and not args.force:
        raise SystemExit(
            f"Refusing to overwrite existing file (use --force): {out_path}"
        )

    summary_md = read_text(summary_path)
    candidates_md = read_text(candidates_path)
    body = knowledge_object_template(
        ko_id=ko_id,
        title=title,
        scope=scope,
        project_key=project_key,
        topic_key=topic_key,
        status="draft",
        tool=args.tool,
        session_id=args.session_id,
        session_dir=session_dir,
        summary_md=summary_md,
        candidates_md=candidates_md,
    )

    write_text(out_path, body)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
