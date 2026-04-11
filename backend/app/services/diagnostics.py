from __future__ import annotations

import importlib
import importlib.metadata
import shutil
import subprocess
from pathlib import Path

import httpx
from sqlalchemy import text


def _pkg_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return ""


def check_storage_writable(path: str = "./tmp") -> dict:
    base = Path(path)
    try:
        base.mkdir(parents=True, exist_ok=True)
        probe = base / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return {"ok": True, "path": str(base.resolve())}
    except Exception as exc:
        return {"ok": False, "path": str(base), "error": str(exc)}


def check_binary(command: str, fallback: str = "") -> dict:
    resolved = shutil.which(command) or (shutil.which(fallback) if fallback else None)
    output = ""
    if resolved:
        try:
            proc = subprocess.run([resolved, "--version"], capture_output=True, text=True, check=False, timeout=5)
            output = (proc.stdout or proc.stderr).strip().splitlines()[0] if (proc.stdout or proc.stderr) else ""
        except Exception as exc:
            output = f"version-check-failed: {exc}"
    return {"ok": bool(resolved), "command": command, "path": resolved or "", "version": output}


def check_transcript_dependency() -> dict:
    try:
        importlib.import_module("youtube_transcript_api")
        return {"ok": True, "version": _pkg_version("youtube-transcript-api")}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def check_faster_whisper() -> dict:
    try:
        mod = importlib.import_module("faster_whisper")
        return {"ok": hasattr(mod, "WhisperModel"), "version": _pkg_version("faster-whisper")}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def check_openai_connectivity(base_url: str, api_key: str) -> dict:
    if not api_key:
        return {"ok": False, "skipped": True, "reason": "missing_api_key"}
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{base_url.rstrip('/')}/models", headers={"Authorization": f"Bearer {api_key}"})
        return {"ok": resp.status_code < 500, "status_code": resp.status_code}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def check_lmstudio_connectivity(base_url: str) -> dict:
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(f"{base_url.rstrip('/')}/models")
        return {"ok": resp.status_code < 500, "status_code": resp.status_code}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def check_db(db) -> dict:
    try:
        db.execute(text("SELECT 1"))
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
