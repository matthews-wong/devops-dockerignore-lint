"""Docker .dockerignore matching: root-anchored globs, `**`, last match wins."""

import re
from typing import Iterable, List, Tuple

Rule = Tuple[re.Pattern, bool]  # (compiled pattern, is_negation)


def _glob_to_regex(pattern: str) -> str:
    out = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
            continue
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
            continue
        if c == "*":
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        elif c == "[":
            end = pattern.find("]", i + 2)
            if end == -1:
                out.append(re.escape(c))
            else:
                body = pattern[i + 1:end]
                if body.startswith("^"):
                    body = "!" + body[1:]
                out.append("[" + body.replace("!", "^", 1) + "]" if body.startswith("!") else "[" + body + "]")
                i = end
        elif c == "\\" and i + 1 < len(pattern):
            i += 1
            out.append(re.escape(pattern[i]))
        else:
            out.append(re.escape(c))
        i += 1
    return "".join(out)


def parse(text: str) -> List[Rule]:
    rules: List[Rule] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        negated = line.startswith("!")
        if negated:
            line = line[1:].strip()
        line = line.lstrip("/").rstrip("/")
        if not line:
            continue
        rules.append((re.compile(_glob_to_regex(line) + r"\Z"), negated))
    return rules


def is_ignored(path: str, rules: Iterable[Rule]) -> bool:
    """True when the daemon would NOT receive `path` (a slash-separated relative path)."""
    parts = path.strip("/").split("/")
    # a pattern that matches a parent directory excludes everything below it
    candidates = ["/".join(parts[:n]) for n in range(1, len(parts) + 1)]
    ignored = False
    for regex, negated in rules:
        if any(regex.match(c) for c in candidates):
            ignored = not negated
    return ignored
