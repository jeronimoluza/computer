# computer

A portable personal toolkit for CLI commands, AI skills, and dev tooling.
Works on macOS, Linux, and Raspberry Pi 4+.

## Install

```sh
curl -fsSL https://raw.githubusercontent.com/jeronimoluza/computer/main/install.sh | sh
```

Then reload your shell:

```sh
source ~/.zshrc   # or ~/.bashrc / ~/.bash_profile
```

## Usage

```sh
computer            # dashboard: commands, projects, recent sessions
computer install    # (re)install hooks, PATH, config files
computer update     # pull latest from GitHub
computer version    # show version
```

## Structure

```
~/.computer/
├── install.sh              # bootstrap installer (curl-safe, POSIX sh)
├── hooks/
│   └── pre-commit          # git hook: blocks secrets before commit
├── commands/
│   ├── bin/
│   │   └── computer        # main CLI entry point
│   └── lib/
│       └── common.sh       # shared helpers (colors, config loaders)
├── config/
│   ├── projects.conf       # your project dirs (gitignored, local only)
│   ├── projects.conf.example
│   ├── settings.conf       # your settings (gitignored, local only)
│   └── settings.conf.example
├── skills/                 # AI framework skills (opencode, claude code)
└── templates/              # reusable code templates
```

## Configuration

After install, edit your local config files (these are **never committed**):

```sh
# Project directories shown in the dashboard
~/.computer/config/projects.conf

# Settings: repo URL, limits, etc.
~/.computer/config/settings.conf
```

## Security

- **Pre-commit hook** scans every commit for secrets (API keys, tokens, private keys)
- **`config/*.conf`** files are gitignored — personal settings never leave your machine
- **`.gitignore`** blocks common secret file patterns (`.env`, `*.pem`, `*.key`, etc.)

## Adding commands

Drop any executable into `commands/bin/` and it becomes a subcommand:

```sh
chmod +x ~/.computer/commands/bin/my-script
computer my-script   # works immediately
```

## Forking

1. Fork this repo
2. Edit `config/settings.conf` and set `COMPUTER_REPO_URL` to your fork's URL
3. The `computer update` and install curl URL will use your fork

## Platforms

| Platform | Status |
|---|---|
| macOS (Apple Silicon / Intel) | Supported |
| Linux x86_64 | Supported |
| Raspberry Pi 4+ (arm64/armv7) | Supported |
