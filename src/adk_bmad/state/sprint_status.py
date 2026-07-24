"""Typed, comment-preserving read/write for a BMAD project's `sprint-status.yaml`.

This file is the single source of truth for story/epic progress — real schema,
confirmed against a live BMAD-METHOD project (BMM v6.8.0):

    development_status:
      epic-1: backlog | in-progress | done
      1-1-some-story-slug: backlog | ready-for-dev | in-progress | review | done
      epic-1-retrospective: optional | done

Every write goes through `ruamel.yaml`'s round-trip mode so the file's comments
(including the STATUS DEFINITIONS legend BMAD writes at the top) and key order
survive — never trust an ADK agent's belief that a phase "looks done" over what
this file actually says.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from ruamel.yaml import YAML

_yaml = YAML()
_yaml.preserve_quotes = True
_yaml.width = 4096  # avoid re-wrapping long story-key lines


def _load(path: Path):
    with path.open("r") as f:
        return _yaml.load(f)


def _dump(path: Path, data) -> None:
    with path.open("w") as f:
        _yaml.dump(data, f)


def read_raw(sprint_status_path: Path) -> str:
    """The full file as text — handed to LLM agents that reason over it directly."""
    return Path(sprint_status_path).read_text()


def development_status(sprint_status_path: Path) -> dict[str, str]:
    """The parsed `development_status` map: epic/story/retro key -> status string."""
    data = _load(Path(sprint_status_path))
    return dict(data.get("development_status", {}))


def get_status(sprint_status_path: Path, key: str) -> str | None:
    """Current status for one key (a story key, `epic-N`, or `epic-N-retrospective`)."""
    return development_status(sprint_status_path).get(key)


def set_status(
    sprint_status_path: Path,
    key: str,
    new_status: str,
    *,
    today: str | None = None,
) -> str:
    """Set `development_status[key] = new_status`, preserving comments/structure.

    Returns the previous status (or "" if the key didn't exist yet). Only the
    agent that owns a given transition should call this — never the `select`
    orchestrator — matching BMAD's own rule that the source of truth is written
    exactly once, by the step responsible for it.
    """
    path = Path(sprint_status_path)
    data = _load(path)
    dev_status = data.setdefault("development_status", {})
    previous = dev_status.get(key, "")
    dev_status[key] = new_status
    data["last_updated"] = today or datetime.now(UTC).date().isoformat()
    _dump(path, data)
    return previous


def epic_key_for(story_key: str) -> str:
    """`"1-2-user-auth"` -> `"epic-1"`."""
    epic_num = story_key.split("-", 1)[0]
    return f"epic-{epic_num}"


def stories_in_epic(sprint_status_path: Path, epic_key: str) -> dict[str, str]:
    """All story keys (not the epic or retro keys themselves) belonging to one epic."""
    epic_num = epic_key.removeprefix("epic-")
    prefix = f"{epic_num}-"
    return {
        key: status
        for key, status in development_status(sprint_status_path).items()
        if key.startswith(prefix) and not key.startswith("epic-")
    }


def epic_fully_done(sprint_status_path: Path, epic_key: str) -> bool:
    stories = stories_in_epic(sprint_status_path, epic_key)
    return bool(stories) and all(status == "done" for status in stories.values())
