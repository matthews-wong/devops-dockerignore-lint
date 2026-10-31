#!/usr/bin/env python3
"""Lint the .dockerignore of a Docker build context."""

import argparse
import re
import sys
from pathlib import Path
from typing import List, NamedTuple, Optional, Tuple

from ignorematch import is_ignored, parse

ERROR = "error"
WARNING = "warning"

MISSING_FILE = "DI001"
LEAKED_SECRET = "DI002"
BLOATED_CONTEXT = "DI003"

# (probe path, what it is). An error means a credential or history leak,
# a warning only slows the build and bloats the layer.
SECRET_PROBES: Tuple[Tuple[str, str], ...] = (
    (".git/config", "git history"),
    (".env", "environment file"),
    (".env.production", "environment file"),
    ("server.pem", "private key"),
    ("id_rsa", "ssh key"),
    ("terraform.tfstate", "terraform state"),
    (".aws/credentials", "cloud credentials"),
)
BLOAT_PROBES: Tuple[Tuple[str, str], ...] = (
    ("node_modules/left-pad/index.js", "node dependencies"),
    ("__pycache__/app.cpython-312.pyc", "python bytecode"),
    (".venv/bin/python", "virtualenv"),
    ("npm-debug.log", "debug log"),
)

BROAD_SOURCES = {".", "./", "*", "./*"}
INSTRUCTION = re.compile(r"^\s*(COPY|ADD)\s+(.*)$", re.IGNORECASE)


class Finding(NamedTuple):
    code: str
    severity: str
    message: str


def copies_whole_context(dockerfile_text: str) -> bool:
    """True when a COPY/ADD pulls the build context root into the image."""
    joined = re.sub(r"\\\s*\n", " ", dockerfile_text)
    for line in joined.splitlines():
        match = INSTRUCTION.match(line)
        if not match:
            continue
        args = [a for a in match.group(2).split() if not a.startswith("--")]
        if "--from" in match.group(2):
            continue  # copies from another stage, not the context
        if any(src in BROAD_SOURCES for src in args[:-1]):
            return True
    return False


def lint(dockerignore: Optional[str], dockerfile: str) -> List[Finding]:
    if dockerignore is None:
        severity = ERROR if copies_whole_context(dockerfile) else WARNING
        return [Finding(MISSING_FILE, severity, "no .dockerignore next to the Dockerfile")]
    rules = parse(dockerignore)
    findings = [
        Finding(LEAKED_SECRET, ERROR, f"{path} ({what}) is sent to the daemon")
        for path, what in SECRET_PROBES
        if not is_ignored(path, rules)
    ]
    findings += [
        Finding(BLOATED_CONTEXT, WARNING, f"{path} ({what}) is sent to the daemon")
        for path, what in BLOAT_PROBES
        if not is_ignored(path, rules)
    ]
    return findings


def read_optional(path: Path) -> Optional[str]:
    return path.read_text() if path.is_file() else None


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("context", type=Path, help="build context directory")
    parser.add_argument("--dockerfile", default="Dockerfile", help="Dockerfile name inside the context")
    args = parser.parse_args(argv)

    dockerfile = read_optional(args.context / args.dockerfile)
    if dockerfile is None:
        print(f"{args.context / args.dockerfile}: no such Dockerfile", file=sys.stderr)
        return 2
    findings = lint(read_optional(args.context / ".dockerignore"), dockerfile)
    for f in findings:
        print(f"{args.context}: {f.severity} {f.code} {f.message}")
    return 1 if any(f.severity == ERROR for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
