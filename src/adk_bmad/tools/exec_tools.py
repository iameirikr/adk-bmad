"""Shell execution — the one tool every implementation/test/review agent needs
to actually run installs, builds, linters, and test suites in the target
project. Same trust model as any autonomous coding agent (Claude Code, the
upstream BMAD skills, archon-bmad): adk-bmad is designed to write and execute
code in the project you point it at. Only run it against projects/environments
you'd extend that same trust to — see docs/configuration.md.
"""

from __future__ import annotations

import subprocess


def run_command(command: str, cwd: str, timeout_seconds: int = 600) -> dict:
    """Run a shell command (e.g. `npm test`, `pytest -q`, `flutter test`) in `cwd`.

    Returns `{"exit_code": int, "stdout": str, "stderr": str, "timed_out": bool}`.
    A non-zero `exit_code` is not raised as an error — the caller (the agent)
    decides what a failing command means for the current task.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "exit_code": -1,
            "stdout": (exc.stdout or ""),
            "stderr": (exc.stderr or "") + f"\n[timed out after {timeout_seconds}s]",
            "timed_out": True,
        }
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "timed_out": False,
    }
