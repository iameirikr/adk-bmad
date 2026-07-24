"""Git FunctionTools: status/diff for the review layers, one atomic commit per story.

Every call shells out via `subprocess.run` with an explicit argv list (never a
shell string), so there's no command-injection surface even though some of these
arguments ultimately originate from LLM-authored text (commit messages, story
keys).
"""

from __future__ import annotations

import re
import subprocess

_ATTRIBUTION_LINE_RE = re.compile(
    r"^(co-authored-by:.*claude.*|generated with claude code.*)$",
    re.IGNORECASE | re.MULTILINE,
)


def _run(project_root: str, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", project_root, *args],
        capture_output=True,
        text=True,
        check=False,
    )


def git_status(project_root: str) -> str:
    """Porcelain `git status` output for `project_root` — untracked/modified files."""
    return _run(project_root, ["status", "--porcelain"]).stdout


def git_diff(project_root: str, staged: bool = False) -> str:
    """`git diff` (unstaged) or `git diff --cached` (staged) for `project_root`."""
    args = ["diff", "--cached"] if staged else ["diff", "HEAD"]
    return _run(project_root, args).stdout


def git_diff_stat(project_root: str) -> str:
    """`git diff HEAD --stat` — a compact summary of what changed, for review context."""
    return _run(project_root, ["diff", "HEAD", "--stat"]).stdout


def git_log(project_root: str, max_count: int = 10) -> str:
    """The last `max_count` commit subjects — used for create-story's git intelligence step."""
    return _run(project_root, ["log", f"--max-count={max_count}", "--oneline"]).stdout


def git_head_sha(project_root: str) -> str:
    """The current HEAD commit SHA, or `"NO_VCS"` if this isn't a git repo."""
    result = _run(project_root, ["rev-parse", "HEAD"])
    return result.stdout.strip() if result.returncode == 0 else "NO_VCS"


def git_commit(project_root: str, message: str) -> dict:
    """Stage everything and create exactly one commit for the current story.

    Strips any AI-attribution trailer (`Co-Authored-By: ... Claude ...`,
    "Generated with Claude Code", etc.) from the message before committing — no
    such credit is ever attached to a story commit, only the repo's configured
    git user. Returns `{"committed": bool, "sha": str|None, "output": str}`; if
    there is nothing to commit (working tree already clean), `committed` is
    `False` with no error.
    """
    add_result = _run(project_root, ["add", "-A"])
    if add_result.returncode != 0:
        return {"committed": False, "sha": None, "output": add_result.stderr}

    if not git_status(project_root).strip():
        return {"committed": False, "sha": None, "output": "nothing to commit"}

    clean_message = _ATTRIBUTION_LINE_RE.sub("", message).strip()
    commit_result = _run(project_root, ["commit", "-m", clean_message])
    if commit_result.returncode != 0:
        return {"committed": False, "sha": None, "output": commit_result.stdout + commit_result.stderr}

    return {"committed": True, "sha": git_head_sha(project_root), "output": commit_result.stdout}
