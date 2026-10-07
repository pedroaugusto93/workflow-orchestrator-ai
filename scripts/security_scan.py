from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DENY_FILE = ROOT / "config" / "forbidden_terms.txt"
TEXT_SUFFIXES = {".py", ".md", ".toml", ".txt", ".yml", ".yaml", ".json", ".html", ".css"}
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(password|secret|token)\s*=\s*['\"][^'\"]{8,}['\"]"),
]


def main() -> int:
    forbidden = []
    if DENY_FILE.exists():
        forbidden = [line.strip() for line in DENY_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]

    findings = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in {".git", ".venv", "venv", "private_connectors"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for term in forbidden:
            if term.casefold() in text.casefold():
                findings.append(f"{path.relative_to(ROOT)}: forbidden term {term!r}")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(f"{path.relative_to(ROOT)}: possible secret")

    if findings:
        print("Security scan FAILED")
        print("\n".join(findings))
        return 1
    print("Security scan OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
