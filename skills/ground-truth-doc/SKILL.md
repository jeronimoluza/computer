---
name: ground-truth-doc
description: >
  Use this skill whenever the user wants a "ground truth" document to drive development:
  creating or updating a paper/spec with sections (Introduction, Motivation, Area of Study,
  Data Sources, Methodology, Results, Discussion, Conclusion, Appendix), managing session logs,
  updating references/links, reviewing TODO backlog, or exporting to PDF/DOCX.
  Prefer token-light progressive disclosure and human-in-the-loop Q&A.
  If Engram is available, rely on it heavily for memory, summaries, bookmarks, and restoration.
---

# Ground Truth Document Protocol

## Goals
- Maintain a single document that drives downstream coding and decisions.
- Keep changes auditable via session logs (`sessions/...-proposal.md` and `sessions/...-change.md`).
- Avoid rereading everything: use progressive disclosure + short snapshots.

## Project Root Detection (cwd-based)
Determine `PROJECT_ROOT` using this order:
1) Closest parent directory containing `docs/paper/`
2) Else closest parent containing `.git/`
3) Else current working directory

All paths below are relative to `PROJECT_ROOT`.

## Canonical Files
- Paper: `docs/paper/paper.md`
- Fast restore snapshot: `docs/paper/STATE.md` (keep short; target < 200 lines)
- Backlog: `TODO.md`
- Session logs:
  - `sessions/YYYY-MM-DD-<title>-proposal.md` (new doc or major reframe)
  - `sessions/YYYY-MM-DD-<title>-change.md` (incremental updates)

## Startup: Token-Light Dashboard
ALWAYS start by showing the current state without rereading the whole paper.

1) If Engram MCP tools are available, use them first:
   - Prefer: search for topic key `doc/<slug>/state` (compact snapshot)
   - If needed, drill down with progressive disclosure:
     - `mem_search` -> `mem_timeline` -> `mem_get_observation`
   - If you don't know the slug yet, use `PROJECT_ROOT` basename as a provisional slug.
2) Read `docs/paper/STATE.md` if it exists.
3) Read top items from `TODO.md` if it exists.

Then render a compact dashboard:
- About (1-2 lines)
- Goal (1-2 lines)
- Section status (1 line per section)
- Latest decisions (3-7 bullets)
- Session overview table (last 3-7 sessions; show rough token estimate and a focus tag)
- Top TODO items (3-7)

## Choose Mode (ask one question)
Ask exactly one question:
"What do you want to do right now?"

Offer choices:
- Create new doc
- Improve a section
- Update references / data sources / method links
- Add plots/figures plan (no auto-generation unless asked)
- Review/prioritize TODO backlog
- Export (PDF/DOCX)
- Restore/recap a prior decision/session

After the user chooses a mode, proceed with mode-specific Q&A (one question at a time).

## Modes

### Mode: Create New Doc
If files are missing, create:
- `docs/paper/paper.md`
- `docs/paper/STATE.md`
- `TODO.md`
- A session log: `sessions/YYYY-MM-DD-<title>-proposal.md`

Q&A (one at a time; stop early once sufficient):
- Title + doc slug
- Audience + intended use (research paper vs internal spec vs hybrid)
- One-sentence problem statement
- Success criteria / expected outputs
- Primary data sources (names/URLs/paths) + access constraints
- Methodology outline (high-level steps)

Write the skeleton sections into `docs/paper/paper.md` using `references/document-template.md`.
Update `docs/paper/STATE.md` with a short snapshot.

### Mode: Improve a Section
- Ask which section (or suggest based on the dashboard).
- Load only what is needed:
  - Prefer Engram topic key for that section if available
  - Otherwise read just the relevant section from `docs/paper/paper.md`

Q&A focuses on:
- What is wrong/missing
- Target depth (outline vs draft prose vs final polish)
- Required references/links
- Acceptance check ("what makes this section done today?")

Apply edits and update `docs/paper/STATE.md` + write a session entry (`...-change.md`).

### Mode: Update References / Links
Maintain in the Appendix:
- "References and Links"
- "Data Sources Index"
- "Methods Index" (optional)

Q&A:
- What reference is changing (add/update/remove)?
- Canonical URL/path and access method (public, auth, local)
- Citation style preference (if any)

Update Appendix + (optionally) add a short references index to `docs/paper/STATE.md`.

### Mode: Review/Prioritize TODO
- Read `TODO.md`.
- Ask for prioritization constraints (deadline, dependencies, risk).

Output:
- A prioritized short list for next session
- Optional: tag TODO items with section affinity (e.g. [methodology], [data], [export])

### Mode: Export (On-Demand Only)
- Ask output format: `pdf`, `docx`, or both.
- Use pandoc commands from `references/export.md`.
- If PDF fails due to missing LaTeX engine, diagnose and propose installs; do not auto-install.

### Mode: Restore/Recap
Goal: restore state without rereading everything.

Prefer Engram:
- `mem_search` for topic keys (state/section/refs)
- `mem_timeline` around key decisions

Fallback to filesystem:
- `docs/paper/STATE.md`
- latest `sessions/*-change.md`

Return:
- 5-10 bullet recap
- Links to relevant session files and paper sections

## Session Logs (required)
Every substantive interaction must update or create a session log.

Session log format must include:
- Title, date, doc slug
- Tags (short)
- Bookmarks (stable ids)
- What changed (bullets)
- Decisions (bullets)
- Open questions
- Next actions
- Files touched

## Efficient Restoration Strategy (no rereading)
Maintain three layers:
1) `docs/paper/STATE.md` (fast local snapshot)
2) Engram topic-key upserts (fast semantic snapshot, if available)
3) Full paper + full sessions (only drill in when needed)

## Engram (if available)
Suggested topic keys:
- `doc/<slug>/state` (upsert each session)
- `doc/<slug>/section/introduction` (etc)
- `doc/<slug>/refs`
- `doc/<slug>/decisions`

When ending a session:
- Update `doc/<slug>/state` with the current snapshot
- Save `mem_session_summary` with Goal / Discoveries / Decisions / Files

Token discipline:
- Prefer `mem_search` -> `mem_timeline` -> `mem_get_observation`
