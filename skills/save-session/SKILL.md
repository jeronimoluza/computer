---
name: save-session
description: >
  Use this skill whenever the user says "save this session" / "capture this session" / "store this" / "turn this into knowledge"
  or asks to persist what happened in the current chat into the computer local sessions + curated knowledge system.
  This skill ingests the current tool session into ~/.computer/local/sessions, then promotes it into a durable markdown
  knowledge object under ~/.computer/local/knowledge/projects/<repo-slug>/ (or personal), with evidence pointers and
  basic redaction for safety.
---

## Goal

Turn the current conversation into:

1) A canonical local session record under `~/.computer/local/sessions/`
2) A durable, human-curated knowledge object under `~/.computer/local/knowledge/`

This is "information compression": store a small, high-signal artifact, and keep raw/log-heavy data local-only.

## Workflow

### 1) Ingest the session into the canonical local store

1. Run the appropriate ingestor:
   - OpenCode: `computer ingest opencode`
   - Claude Code: `computer ingest claude`
   - Or: `computer ingest all`

2. Verify it exists:
   - `computer sessions --limit 5`
   - Optionally filter: `computer sessions --tool opencode --limit 5`

Notes:
- Session records live under `~/.computer/local/sessions/<tool>/<session_id>/`.
- `summary.md` and `candidates.md` are redacted (basic secret patterns + `<private>...</private>` blocks).
- Raw exports remain local-only under `raw/`.

### 2) Promote to a durable knowledge object (human-in-the-loop)

1. Identify the session_id you want to promote (usually the newest).
2. Create a draft knowledge object:
   - `computer curate <tool> <session_id>`
   - If it must be personal: `computer curate <tool> <session_id> --personal`

This writes a draft markdown file to:
- Project scope: `~/.computer/local/knowledge/projects/<project_key>/...md`
- Personal scope: `~/.computer/local/knowledge/personal/...md`

Project key is the repo slug (git top-level dir basename), with a leading dot stripped (e.g. `~/.computer` -> `computer`).

### 3) Fill the draft with a compressed, durable summary

Edit the generated knowledge object and:

- Keep **What/Why/How** tight and durable.
- Include **Evidence** inline only if it is small and stable (short command output, small tables).
- For large evidence, link to session files under `~/.computer/local/sessions/.../raw/`.
- Add Gotchas and Next Steps if there is future work.

### 4) Success criteria

- The session appears in `computer sessions`.
- A knowledge object exists under `~/.computer/local/knowledge/` and contains the durable learnings.
- No secrets are promoted into durable knowledge; redact or link to raw local-only evidence if unsure.

## Recommended output format (when reporting back)

- Mention the ingested session directory path.
- Mention the knowledge object path.
- List 3-6 bullet learnings captured in the knowledge object.
