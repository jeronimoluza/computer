import re
from typing import Pattern


_PRIVATE_BLOCK_RE: Pattern[str] = re.compile(
    r"<private>.*?</private>", re.DOTALL | re.IGNORECASE
)


_SECRET_PATTERNS: list[Pattern[str]] = [
    # Generic API keys / tokens (keep conservative to avoid false positives)
    re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z\-_]{20,}\b"),
    # JWT-ish (very common; avoid over-redacting random base64 by requiring 2 dots)
    re.compile(r"\beyJ[A-Za-z0-9_\-]+=*\.[A-Za-z0-9_\-]+=*\.[A-Za-z0-9_\-]+=*\b"),
    # PEM blocks
    re.compile(
        r"-----BEGIN [A-Z0-9 ]+PRIVATE KEY-----[\s\S]+?-----END [A-Z0-9 ]+PRIVATE KEY-----"
    ),
]


def redact_text(s: str) -> str:
    if not s:
        return s
    out = _PRIVATE_BLOCK_RE.sub("[REDACTED]", s)
    for pat in _SECRET_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    return out
