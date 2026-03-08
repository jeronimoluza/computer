# computer - shared helpers
# Source this file in any command: source "$(dirname "$0")/../lib/common.sh"

COMPUTER_HOME="${HOME}/.computer"
COMPUTER_CONFIG="${COMPUTER_HOME}/config"
COMPUTER_SETTINGS="${COMPUTER_CONFIG}/settings.conf"
COMPUTER_PROJECTS="${COMPUTER_CONFIG}/projects.conf"

# ── Colors ────────────────────────────────────────────────────────────────────
BOLD="\033[1m"
DIM="\033[2m"
CYAN="\033[36m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"

# ── Output helpers ────────────────────────────────────────────────────────────
sep()     { printf "${DIM}%s${RESET}\n" "──────────────────────────────────────────"; }
info()    { printf "  ${CYAN}→${RESET} %s\n" "$*"; }
ok()      { printf "  ${GREEN}✓${RESET} %s\n" "$*"; }
warn()    { printf "  ${YELLOW}!${RESET} %s\n" "$*"; }
err()     { printf "  ${RED}✗${RESET} %s\n" "$*" >&2; }

# ── Load settings (safe: missing keys get defaults) ───────────────────────────
load_settings() {
    COMPUTER_REPO_URL="https://github.com/jeronimoluza/computer"
    COMPUTER_PROJECTS_LIMIT=5
    COMPUTER_SESSIONS_LIMIT=5

    if [ -f "$COMPUTER_SETTINGS" ]; then
        # shellcheck disable=SC1090
        . "$COMPUTER_SETTINGS"
    fi
}

# ── Load project dirs from config/projects.conf ───────────────────────────────
# Outputs one expanded path per line, skipping comments and non-existent dirs.
load_project_dirs() {
    if [ ! -f "$COMPUTER_PROJECTS" ]; then
        return
    fi
    while IFS= read -r line; do
        # Skip comments and empty lines
        case "$line" in
            '#'*|'') continue ;;
        esac
        # Expand ~ manually (POSIX-safe)
        expanded="${line/#\~/$HOME}"
        if [ -d "$expanded" ]; then
            printf '%s\n' "$expanded"
        fi
    done < "$COMPUTER_PROJECTS"
}
