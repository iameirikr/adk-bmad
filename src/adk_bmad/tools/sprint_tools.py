"""ADK FunctionTools over `state/sprint_status.py` — sprint-status.yaml is the
single source of truth for story/epic progress; these are the only sanctioned
way any agent reads or mutates it.
"""

from __future__ import annotations

from adk_bmad.state import sprint_status as _sprint_status


def read_sprint_status(sprint_status_path: str) -> str:
    """Read the full sprint-status.yaml file as text.

    Use this to see every epic/story/retrospective status at once and reason
    about ordering (sprint order is top-to-bottom in the `development_status`
    map). Story keys look like "1-2-user-auth"; epic keys look like "epic-1";
    retrospective keys look like "epic-1-retrospective".
    """
    return _sprint_status.read_raw(sprint_status_path)


def get_development_status(sprint_status_path: str, key: str) -> str:
    """Get the current status for one key (a story key, an "epic-N" key, or an
    "epic-N-retrospective" key). Returns "" if the key doesn't exist yet."""
    return _sprint_status.get_status(sprint_status_path, key) or ""


def set_development_status(sprint_status_path: str, key: str, new_status: str) -> dict:
    """Set `development_status[key] = new_status` in sprint-status.yaml.

    Preserves every comment and the rest of the file's structure. Only call this
    from the phase that actually owns the transition it represents (e.g. only
    dev_story sets a story to "review", only the review gate sets it back to
    "in-progress" or forward past review, only commit confirms "done") — never
    "correct" sprint-status.yaml from the orchestrating select step.
    """
    previous = _sprint_status.set_status(sprint_status_path, key, new_status)
    return {"key": key, "previous_status": previous, "new_status": new_status}


def epic_key_for_story(story_key: str) -> str:
    """The epic key a story belongs to, e.g. "1-2-user-auth" -> "epic-1"."""
    return _sprint_status.epic_key_for(story_key)


def stories_in_epic(sprint_status_path: str, epic_key: str) -> dict:
    """All story keys belonging to one epic (e.g. "epic-1") and their current statuses."""
    return _sprint_status.stories_in_epic(sprint_status_path, epic_key)


def epic_fully_done(sprint_status_path: str, epic_key: str) -> bool:
    """Whether every story in `epic_key` is "done" (and the epic has at least one story)."""
    return _sprint_status.epic_fully_done(sprint_status_path, epic_key)
