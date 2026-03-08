#!/bin/sh
# computer installer
# Works on: macOS (arm64/x86_64), Linux (x86_64, arm64, armv7l / Raspberry Pi)
# Requires: git, curl or wget
# Usage (fresh machine):
#   curl -fsSL https://raw.githubusercontent.com/jeronimoluza/computer/main/install.sh | sh
# Usage (already cloned):
#   computer install

set -e

COMPUTER_REPO="https://github.com/jeronimoluza/computer.git"
COMPUTER_HOME="${HOME}/.computer"
COMPUTER_BIN="${COMPUTER_HOME}/commands/bin"

# ── Helpers ───────────────────────────────────────────────────────────────────
bold()    { printf "\033[1m%s\033[0m\n" "$*"; }
info()    { printf "  \033[36m→\033[0m %s\n" "$*"; }
ok()      { printf "  \033[32m✓\033[0m %s\n" "$*"; }
warn()    { printf "  \033[33m!\033[0m %s\n" "$*"; }
fail()    { printf "  \033[31m✗\033[0m %s\n" "$*"; exit 1; }
sep()     { printf "\033[2m%s\033[0m\n" "──────────────────────────────────────────"; }

# ── Platform detection ────────────────────────────────────────────────────────
detect_platform() {
    OS=$(uname -s)
    ARCH=$(uname -m)

    case "$OS" in
        Darwin)
            PLATFORM="macos"
            ;;
        Linux)
            PLATFORM="linux"
            # Detect Raspberry Pi
            if [ -f /proc/cpuinfo ] && grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
                PLATFORM="linux-rpi"
            fi
            ;;
        *)
            warn "Unsupported OS: $OS. Proceeding anyway."
            PLATFORM="unknown"
            ;;
    esac

    case "$ARCH" in
        arm64|aarch64) ARCH_LABEL="arm64" ;;
        armv7l|armv6l) ARCH_LABEL="armv7" ;;
        x86_64)        ARCH_LABEL="x86_64" ;;
        *)             ARCH_LABEL="$ARCH" ;;
    esac
}

# ── Shell RC file detection ───────────────────────────────────────────────────
detect_shell_rc() {
    # Prefer $SHELL, fallback to checking what's running
    SHELL_NAME=$(basename "${SHELL:-sh}")

    case "$SHELL_NAME" in
        zsh)
            RC_FILE="${ZDOTDIR:-$HOME}/.zshrc"
            ;;
        bash)
            if [ "$PLATFORM" = "macos" ]; then
                # macOS bash uses .bash_profile for login shells
                RC_FILE="${HOME}/.bash_profile"
            else
                RC_FILE="${HOME}/.bashrc"
            fi
            ;;
        fish)
            RC_FILE="${HOME}/.config/fish/config.fish"
            warn "fish shell detected. You may need to add the PATH manually."
            ;;
        *)
            RC_FILE="${HOME}/.profile"
            ;;
    esac
}

# ── Dependency check ──────────────────────────────────────────────────────────
check_deps() {
    MISSING_REQUIRED=""
    MISSING_OPTIONAL=""

    for cmd in git; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            MISSING_REQUIRED="$MISSING_REQUIRED $cmd"
        fi
    done

    for cmd in sqlite3; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            MISSING_OPTIONAL="$MISSING_OPTIONAL $cmd"
        fi
    done

    if [ -n "$MISSING_REQUIRED" ]; then
        fail "Missing required dependencies:$MISSING_REQUIRED\n  Install with: $(install_hint)"
    fi

    if [ -n "$MISSING_OPTIONAL" ]; then
        warn "Missing optional dependencies:$MISSING_OPTIONAL"
        warn "Session history in dashboard will be unavailable."
        warn "Install with: $(install_hint_optional)"
    fi
}

install_hint() {
    case "$PLATFORM" in
        macos)       echo "brew install git" ;;
        linux-rpi)   echo "sudo apt-get install -y git" ;;
        linux)       echo "sudo apt-get install -y git  # or your distro's package manager" ;;
        *)           echo "your package manager" ;;
    esac
}

install_hint_optional() {
    case "$PLATFORM" in
        macos)       echo "brew install sqlite" ;;
        linux-rpi)   echo "sudo apt-get install -y sqlite3" ;;
        linux)       echo "sudo apt-get install -y sqlite3" ;;
        *)           echo "your package manager" ;;
    esac
}

# ── Clone or update repo ──────────────────────────────────────────────────────
setup_repo() {
    if [ -d "${COMPUTER_HOME}/.git" ]; then
        ok "~/.computer already exists, skipping clone."
    else
        info "Cloning computer into ~/.computer ..."
        git clone --depth=1 "$COMPUTER_REPO" "$COMPUTER_HOME"
        ok "Cloned."
    fi
}

# ── Install git hook ──────────────────────────────────────────────────────────
install_hook() {
    HOOK_SRC="${COMPUTER_HOME}/hooks/pre-commit"
    HOOK_DST="${COMPUTER_HOME}/.git/hooks/pre-commit"

    if [ ! -f "$HOOK_SRC" ]; then
        warn "hooks/pre-commit not found in repo, skipping."
        return
    fi

    cp "$HOOK_SRC" "$HOOK_DST"
    chmod +x "$HOOK_DST"
    ok "Git pre-commit hook installed."
}

# ── Add PATH to shell RC (idempotent) ─────────────────────────────────────────
setup_path() {
    PATH_LINE="export PATH=\"\$HOME/.computer/commands/bin:\$PATH\""
    PATH_MARKER="# computer CLI"

    if grep -q "\.computer/commands/bin" "$RC_FILE" 2>/dev/null; then
        ok "PATH already set in $RC_FILE"
        return
    fi

    printf "\n%s\n%s\n" "$PATH_MARKER" "$PATH_LINE" >> "$RC_FILE"
    ok "Added PATH to $RC_FILE"
}

# ── Bootstrap config files from examples ─────────────────────────────────────
setup_config() {
    for example in "${COMPUTER_HOME}/config/"*.conf.example; do
        [ -f "$example" ] || continue
        target="${example%.example}"
        if [ -f "$target" ]; then
            ok "Config already exists: $(basename "$target")"
        else
            cp "$example" "$target"
            ok "Created config: $(basename "$target") (from example)"
        fi
    done
}

# ── Print summary ─────────────────────────────────────────────────────────────
print_summary() {
    echo ""
    sep
    bold "  computer installed successfully!"
    sep
    info "Platform : $PLATFORM ($ARCH_LABEL)"
    info "Shell    : $SHELL_NAME → $RC_FILE"
    info "Home     : $COMPUTER_HOME"
    echo ""
    bold "  Next steps:"
    printf "  1. Reload your shell:\n"
    printf "       source %s\n" "$RC_FILE"
    printf "  2. Run the dashboard:\n"
    printf "       computer\n"
    printf "  3. Edit your project dirs:\n"
    printf "       %s/config/projects.conf\n" "$COMPUTER_HOME"
    printf "  4. Edit your settings:\n"
    printf "       %s/config/settings.conf\n" "$COMPUTER_HOME"
    echo ""
    sep
    echo ""
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
    echo ""
    bold "  Installing computer..."
    echo ""

    detect_platform
    detect_shell_rc
    info "Platform : $PLATFORM ($ARCH_LABEL)"
    info "Shell RC : $RC_FILE"
    echo ""

    check_deps
    setup_repo
    install_hook
    setup_path
    setup_config
    print_summary
}

main "$@"
