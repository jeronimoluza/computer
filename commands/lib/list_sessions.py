#!/usr/bin/env python3

import argparse
import json
import os
import time
from typing import Any, Dict, List, Optional


def read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
            return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def rel_time_from_ms(ms: Optional[int]) -> str:
    if not isinstance(ms, int) or ms <= 0:
        return ""
    now = int(time.time() * 1000)
    age_s = max(0, (now - ms) // 1000)
    if age_s < 3600:
        return f"{age_s // 60}m ago"
    if age_s < 86400:
        return f"{age_s // 3600}h ago"
    return f"{age_s // 86400}d ago"


def iter_meta_files(root: str) -> List[str]:
    out: List[str] = []
    if not os.path.isdir(root):
        return out
    for tool in os.listdir(root):
        tool_dir = os.path.join(root, tool)
        if not os.path.isdir(tool_dir):
            continue
        for sid in os.listdir(tool_dir):
            sdir = os.path.join(tool_dir, sid)
            if not os.path.isdir(sdir):
                continue
            meta = os.path.join(sdir, "meta.json")
            if os.path.isfile(meta):
                out.append(meta)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="List ingested sessions")
    ap.add_argument("--root", required=True)
    ap.add_argument("--tool", default="")
    ap.add_argument("--project", default="")
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()

    metas = iter_meta_files(args.root)
    rows: List[Dict[str, Any]] = []
    for mp in metas:
        meta = read_json(mp)
        tool = meta.get("tool")
        if not isinstance(tool, str) or not tool:
            tool = os.path.basename(os.path.dirname(os.path.dirname(mp)))
        if args.tool and tool != args.tool:
            continue
        pk = meta.get("project_key")
        if not isinstance(pk, str):
            pk = ""
        if args.project and pk != args.project:
            continue

        updated = meta.get("time_updated_ms")
        if not isinstance(updated, int):
            try:
                updated = int(os.path.getmtime(mp) * 1000)
            except Exception:
                updated = 0

        rows.append(
            {
                "tool": tool,
                "session_id": meta.get("session_id")
                or meta.get("id")
                or os.path.basename(os.path.dirname(mp)),
                "title": meta.get("title") or "(untitled)",
                "project_key": pk,
                "directory": meta.get("directory") or "",
                "updated": updated,
                "meta_path": os.path.dirname(mp),
            }
        )

    rows.sort(key=lambda r: r.get("updated", 0), reverse=True)
    rows = rows[: max(0, args.limit)]

    if not rows:
        print("No sessions found.")
        return 0

    for r in rows:
        title = str(r["title"])
        tool = str(r["tool"])
        pk = str(r["project_key"]) if r.get("project_key") else ""
        when = rel_time_from_ms(int(r["updated"]))
        sid = str(r["session_id"])
        loc = str(r["meta_path"])

        pk_part = f" {pk}" if pk else ""
        when_part = f" {when}" if when else ""
        print(f"{title}  [{tool}{pk_part}]{when_part}")
        print(f"  {sid}")
        print(f"  {loc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
