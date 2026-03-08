# Export Commands (pandoc)

All commands assume you run them from `PROJECT_ROOT`.

## DOCX
pandoc docs/paper/paper.md -o docs/paper/paper.docx

## PDF
pandoc docs/paper/paper.md -o docs/paper/paper.pdf

## Notes
- PDF export usually requires a LaTeX engine (e.g. MacTeX). If export fails, show the error and
  suggest the install; do not auto-install.
