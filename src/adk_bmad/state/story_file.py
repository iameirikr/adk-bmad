"""Minimal read/write helpers for BMAD story files.

Real format, confirmed against a live BMAD-METHOD project — YAML frontmatter
(`baseline_commit`), then `# Story N.M: <title>`, `Status: <value>`, `## Story`,
`## Acceptance Criteria`, `## Tasks / Subtasks`, `## Dev Notes`,
`## Dev Agent Record` (Agent Model Used / Debug Log / Completion Notes / File
List), `## Change Log`.

adk-bmad deliberately does not implement a full markdown/section AST here — the
LLM agents (following the loaded upstream skill instructions) read and write the
prose sections themselves via generic file tools. This module only handles the
two things orchestration code needs to touch mechanically: the `Status:` line and
the YAML frontmatter, both rewritten byte-precisely so nothing else in the file
is disturbed.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

_STATUS_LINE_RE = re.compile(r"^Status:\s*(.+)$", re.MULTILINE)
_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def story_path(implementation_artifacts: Path, story_key: str) -> Path:
    return Path(implementation_artifacts) / f"{story_key}.md"


def story_exists(implementation_artifacts: Path, story_key: str) -> bool:
    return story_path(implementation_artifacts, story_key).is_file()


def read_text(implementation_artifacts: Path, story_key: str) -> str:
    return story_path(implementation_artifacts, story_key).read_text()


def read_status(implementation_artifacts: Path, story_key: str) -> str | None:
    text = read_text(implementation_artifacts, story_key)
    match = _STATUS_LINE_RE.search(text)
    return match.group(1).strip() if match else None


def set_status(implementation_artifacts: Path, story_key: str, new_status: str) -> str:
    """Rewrite only the `Status: ...` line; every other byte in the file is untouched."""
    path = story_path(implementation_artifacts, story_key)
    text = path.read_text()
    match = _STATUS_LINE_RE.search(text)
    if not match:
        raise ValueError(f"No 'Status:' line found in {path}")
    previous = match.group(1).strip()
    path.write_text(_STATUS_LINE_RE.sub(f"Status: {new_status}", text, count=1))
    return previous


def read_frontmatter(implementation_artifacts: Path, story_key: str) -> dict:
    text = read_text(implementation_artifacts, story_key)
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    return yaml.safe_load(match.group(1)) or {}


def set_frontmatter_field(implementation_artifacts: Path, story_key: str, field: str, value: str) -> None:
    """Add or update one frontmatter field (e.g. `baseline_commit`), preserving the rest of the file.

    If the file has no frontmatter yet, one is created containing just this field.
    """
    path = story_path(implementation_artifacts, story_key)
    text = path.read_text()
    match = _FRONTMATTER_RE.match(text)
    if match:
        data = yaml.safe_load(match.group(1)) or {}
        data[field] = value
        new_frontmatter = "---\n" + yaml.safe_dump(data, sort_keys=False).strip() + "\n---\n"
        text = _FRONTMATTER_RE.sub(new_frontmatter, text, count=1)
    else:
        new_frontmatter = "---\n" + yaml.safe_dump({field: value}, sort_keys=False).strip() + "\n---\n\n"
        text = new_frontmatter + text
    path.write_text(text)
