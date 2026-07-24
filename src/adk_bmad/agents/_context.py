"""Resolved once, at import time, for the single BMAD project this process targets.

adk-bmad automates one BMAD project per run (`ADK_BMAD_PROJECT_ROOT`, see
`config.default_project_root`), so the project's paths are stable for the whole
process — every agent's static instruction can embed them directly as literal
text rather than routing them through session state, which is reserved for
values that actually change during the run (current phase, current story, retry
counters, review findings).
"""

from __future__ import annotations

import subprocess

from adk_bmad import config

PROJECT_ROOT = config.default_project_root()
BMAD_CONFIG = config.load_bmad_config(PROJECT_ROOT)
LOOP_SETTINGS = config.LoopSettings()


def _ensure_git_repo(project_root) -> None:
    """The dev/review/commit agents all need `project_root` under version control
    (to diff and commit story changes). Bootstrap a repo with one baseline commit
    if there isn't one yet — this only ever fires for a brand-new project (e.g.
    a first try of `examples/sample-bmad-project`); any project a user already
    tracks in git is untouched.
    """
    if (project_root / ".git").exists():
        return
    subprocess.run(["git", "init"], cwd=project_root, capture_output=True, check=False)
    subprocess.run(["git", "add", "-A"], cwd=project_root, capture_output=True, check=False)
    subprocess.run(
        ["git", "commit", "-m", "chore: baseline (planning artifacts, pre-adk-bmad)"],
        cwd=project_root,
        capture_output=True,
        check=False,
    )


_ensure_git_repo(PROJECT_ROOT)
