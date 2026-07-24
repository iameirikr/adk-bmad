"""`adk-bmad` console entry point.

adk-bmad's actual runtime IS the ADK CLI — `adk run`, `adk web`, or
`adk api_server` pointed at this package — not a bespoke wrapper. This entry
point validates the target BMAD project up front (the same check `agent.py`
would trigger on import, just with a friendlier message before handing off)
and points you at the right `adk` command.
"""

from __future__ import annotations

import sys
from pathlib import Path

from adk_bmad import config


def main() -> None:
    project_root = config.default_project_root()
    try:
        bmad_config = config.load_bmad_config(project_root)
    except FileNotFoundError as exc:
        print(f"adk-bmad: {exc}", file=sys.stderr)
        print(
            "\nSet ADK_BMAD_PROJECT_ROOT to a BMAD-METHOD project, or run this "
            "from the adk-bmad repo root (which bundles examples/sample-bmad-project).",
            file=sys.stderr,
        )
        raise SystemExit(1)

    package_dir = Path(__file__).resolve().parent
    print(f"adk-bmad: targeting BMAD project at {project_root}")
    print(f"  sprint-status: {bmad_config.sprint_status}")
    print("\nRun one of:")
    print(f"  adk web {package_dir.parent}      # chat UI")
    print(f"  adk run {package_dir}             # terminal")
    print(f"  adk api_server {package_dir.parent}  # HTTP API")


if __name__ == "__main__":
    main()
