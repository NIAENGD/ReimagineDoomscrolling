from __future__ import annotations

import re
from datetime import datetime

from app.models.entities import LogEvent

_SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[A-Za-z0-9._-]+"),
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)[^\s,;]+"),
]


def redact_secrets(value: str) -> str:
    sanitized = value or ""
    for pattern in _SECRET_PATTERNS:
        sanitized = pattern.sub(lambda m: (m.group(1) if m.lastindex else "") + "***redacted***", sanitized)
    return sanitized


def log_event(db, severity: str, context: str, message: str, *, source_id: int | None = None, item_id: int | None = None, trace_id: str = ""):
    scoped_context = context
    if source_id is not None:
        scoped_context = f"{scoped_context} source_id={source_id}".strip()
    if item_id is not None:
        scoped_context = f"{scoped_context} item_id={item_id}".strip()
    if trace_id:
        scoped_context = f"{scoped_context} trace_id={trace_id}".strip()

    db.add(
        LogEvent(
            severity=(severity or "INFO").upper(),
            context=redact_secrets(scoped_context),
            message=redact_secrets(message),
            created_at=datetime.utcnow(),
        )
    )
