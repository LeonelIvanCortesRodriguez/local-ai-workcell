"""Bounded public-release scan; the independent auditor must still review context."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDED = {".git", "__pycache__", ".pytest_cache", "_demo", "_tmp", "out", "out-v2", "release", "node_modules", "test-results", ".venv"}
BINARY = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".zip", ".sqlite3", ".db"}
slash = chr(92)
patterns = {
    "Windows user path": re.compile(r"[A-Za-z]:" + re.escape(slash) + "Users" + re.escape(slash) + r"[A-Za-z0-9_.-]+", re.I),
    "Unix home path": re.compile(r"/(?:home|Users)/[A-Za-z0-9_.-]+"),
    "private directory": re.compile(r"\.private[/\\]", re.I),
    "assigned token": re.compile(r"(?i)(?:api[_-]?key|access[_-]?token|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "IPv4 address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "email address": re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"),
}
findings = []
scanned = 0
for path in sorted(ROOT.rglob("*")):
    if not path.is_file() or any(part in EXCLUDED for part in path.relative_to(ROOT).parts):
        continue
    if path.suffix.lower() in BINARY:
        continue
    scanned += 1
    if path.name == "privacy_scan.py":
        continue  # This file contains the detector expressions themselves.
    data = path.read_text(encoding="utf-8")
    for label, pattern in patterns.items():
        matches = pattern.findall(data)
        if label == "IPv4 address":
            matches = [value for value in matches if value != "127.0.0.1"]
        if matches:
            findings.append((path.relative_to(ROOT).as_posix(), label))
if findings:
    raise SystemExit("PRIVACY_SCAN_FAIL " + "; ".join(f"{name}: {label}" for name, label in findings))
print(f"PRIVACY_SCAN_OK text_files={scanned} findings=0")
