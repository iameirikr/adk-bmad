"""ADK FunctionTools for reading/writing story files and general project text
files. BMAD story files are prose documents the LLM agents author and maintain
themselves (following the loaded skill instructions); this module gives them
generic, precise file I/O rather than a bespoke section-by-section API — the
same shape of tool a coding-agent harness like Claude Code already provides,
which is what these skill files were originally written against.
"""

from __future__ import annotations

from pathlib import Path

from adk_bmad.state import story_file as _story_file


def read_text_file(path: str) -> str:
    """Read a UTF-8 text file (a story file, epics.md, prd.md, architecture.md, ...)."""
    return Path(path).read_text()


def write_text_file(path: str, content: str) -> dict:
    """Write `content` to `path`, overwriting it (or creating it, including parent dirs)."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return {"path": str(target), "bytes_written": len(content.encode())}


def edit_text_file(path: str, old_string: str, new_string: str, replace_all: bool = False) -> dict:
    """Replace `old_string` with `new_string` in `path`.

    Fails if `old_string` isn't found, or (unless `replace_all` is true) if it
    isn't unique — the same precise-match discipline as a normal editor tool, so
    an ambiguous edit can't silently clobber the wrong occurrence.
    """
    target = Path(path)
    text = target.read_text()
    count = text.count(old_string)
    if count == 0:
        raise ValueError(f"old_string not found in {path}")
    if count > 1 and not replace_all:
        raise ValueError(
            f"old_string is not unique in {path} ({count} occurrences) — "
            "pass replace_all=True or give more surrounding context"
        )
    new_text = text.replace(old_string, new_string) if replace_all else text.replace(
        old_string, new_string, 1
    )
    target.write_text(new_text)
    return {"path": str(target), "replacements": count if replace_all else 1}


def list_directory(path: str) -> list[str]:
    """List entries (files and directories) directly under `path`."""
    return sorted(p.name for p in Path(path).iterdir())


def story_exists(implementation_artifacts: str, story_key: str) -> bool:
    """Whether a story file for `story_key` already exists in `implementation_artifacts`."""
    return _story_file.story_exists(Path(implementation_artifacts), story_key)


def get_story_status(implementation_artifacts: str, story_key: str) -> str:
    """The story file's own `Status:` line value (independent of sprint-status.yaml)."""
    return _story_file.read_status(Path(implementation_artifacts), story_key) or ""


def set_story_status(implementation_artifacts: str, story_key: str, new_status: str) -> dict:
    """Rewrite only the story file's `Status:` line — every other byte is untouched."""
    previous = _story_file.set_status(Path(implementation_artifacts), story_key, new_status)
    return {"story_key": story_key, "previous_status": previous, "new_status": new_status}


def set_story_baseline_commit(implementation_artifacts: str, story_key: str, sha: str) -> dict:
    """Record `baseline_commit` in the story's YAML frontmatter (set once, on first dev pass)."""
    _story_file.set_frontmatter_field(
        Path(implementation_artifacts), story_key, "baseline_commit", sha
    )
    return {"story_key": story_key, "baseline_commit": sha}
