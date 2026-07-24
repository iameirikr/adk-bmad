#!/usr/bin/env python3
"""Refresh the vendored BMAD skill fallback (`src/adk_bmad/vendor/bmad-skills/`).

This vendored copy is only a fallback — used when the project adk-bmad is
running against doesn't have BMAD-METHOD's skills installed under
`.claude/skills`, `.agents/skills`, or `.codex/skills` (see `src/adk_bmad/
skills.py`). It exists so the bundled `examples/sample-bmad-project` works with
`adk web` out of the box. When running against a *real* BMAD-METHOD project,
that project's own (possibly newer) skill files are used instead — this
vendored copy is never on the resolution path in that case.

Usage:
    uv run python scripts/sync_bmad_skills.py /path/to/a/bmad-method/project

The source project must have `.claude/skills/<name>/` for each skill listed in
`SKILLS` below (i.e. it has BMAD-METHOD installed and up to date — run
`bmad-method update` there first if you want the latest upstream instructions).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

SKILLS = (
    "bmad-create-story",
    "bmad-dev-story",
    "bmad-code-review",
    "bmad-review-adversarial-general",
    "bmad-review-edge-case-hunter",
    "bmad-qa-generate-e2e-tests",
    "bmad-retrospective",
)

# Only the files src/adk_bmad/skills.py actually reads — see its docstring.
_FILES_TO_COPY = ("SKILL.md", "discover-inputs.md", "template.md", "checklist.md")

VENDOR_DIR = Path(__file__).resolve().parent.parent / "src" / "adk_bmad" / "vendor" / "bmad-skills"


def _find_skill_source(source_project: Path, name: str) -> Path | None:
    for root in (".claude/skills", ".agents/skills", ".codex/skills"):
        candidate = source_project / root / name
        if (candidate / "SKILL.md").is_file():
            return candidate
    return None


def sync_skill(source_project: Path, name: str) -> str:
    source = _find_skill_source(source_project, name)
    if source is None:
        return f"SKIPPED {name}: not found under {source_project}'s skill roots"

    dest = VENDOR_DIR / name
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    for filename in _FILES_TO_COPY:
        src_file = source / filename
        if src_file.is_file():
            shutil.copy2(src_file, dest / filename)

    steps_src = source / "steps"
    if steps_src.is_dir():
        steps_dest = dest / "steps"
        steps_dest.mkdir()
        for step_file in steps_src.glob("*.md"):
            shutil.copy2(step_file, steps_dest / step_file.name)

    return f"OK      {name}: synced from {source}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "source_project",
        type=Path,
        help="Path to a BMAD-METHOD project with .claude/skills (or .agents/.codex) installed",
    )
    parser.add_argument("--bmm-version", default="unknown", help="BMM version string to record in MANIFEST.json")
    args = parser.parse_args()

    source_project = args.source_project.resolve()
    if not source_project.is_dir():
        print(f"error: {source_project} is not a directory", file=sys.stderr)
        raise SystemExit(1)

    results = [sync_skill(source_project, name) for name in SKILLS]
    for line in results:
        print(line)

    manifest = {
        "source": "https://github.com/bmad-code-org/BMAD-METHOD",
        "license": "MIT",
        "vendored_from": f"{source_project} (synced {datetime.now(UTC).isoformat()})",
        "bmm_version": args.bmm_version,
        "note": (
            "This is a fallback copy used only when the target project doesn't "
            "have BMAD-METHOD's skills installed under .claude/skills, "
            ".agents/skills, or .codex/skills (see src/adk_bmad/skills.py) — "
            "e.g. the bundled examples/sample-bmad-project. When running "
            "against a real BMAD-METHOD project, its own installed (and "
            "possibly newer) skill files are used instead — see NOTICE."
        ),
        "skills": list(SKILLS),
        "synced_on": datetime.now(UTC).date().isoformat(),
    }
    (VENDOR_DIR / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\nMANIFEST.json updated at {VENDOR_DIR / 'MANIFEST.json'}")


if __name__ == "__main__":
    main()
