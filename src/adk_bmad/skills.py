"""Loader for real upstream BMAD-METHOD skill files.

adk-bmad does not reimplement BMAD's domain instructions (how to write a good
story, how dev-story does red-green-refactor, what the adversarial reviewers look
for, ...). A BMAD "skill" is plain markdown — `SKILL.md` plus optional
`steps/*.md`, `checklist.md`, `template.md`, using simple `<action>`/`<check>`
pseudo-XML — not code tied to any particular agentic CLI. This module loads that
markdown at runtime and returns it as instruction text for an ADK `LlmAgent`, so
when you update BMAD-METHOD in your project, the next adk-bmad run picks up the
new instructions automatically. See NOTICE and docs/bmad-compatibility.md.
"""

from __future__ import annotations

from pathlib import Path

#: Where BMAD-METHOD installs its skill files in a target project, in resolution
#: order — the same roots (and order) archon-bmad already searches.
SKILL_ROOTS: tuple[str, ...] = (".claude/skills", ".agents/skills", ".codex/skills")

#: Vendored fallback copy, refreshed by scripts/sync_bmad_skills.py, used only when
#: the target project doesn't have BMAD-METHOD's skills installed under any of
#: SKILL_ROOTS (e.g. the bundled examples/sample-bmad-project, for a zero-setup
#: `adk web` try-it experience).
VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "bmad-skills"


class SkillNotFoundError(RuntimeError):
    """Raised when a named BMAD skill can't be found in the project or the vendored fallback."""


def find_skill_root(project_root: Path, name: str) -> Path:
    """Resolve a BMAD skill's directory: live project install, else vendored fallback."""
    for rel in SKILL_ROOTS:
        candidate = project_root / rel / name
        if (candidate / "SKILL.md").is_file():
            return candidate
    vendored = VENDOR_DIR / name
    if (vendored / "SKILL.md").is_file():
        return vendored
    searched = ", ".join(str(project_root / rel / name) for rel in SKILL_ROOTS)
    raise SkillNotFoundError(
        f"BMAD skill '{name}' not found. Looked under: {searched}, and the vendored "
        f"fallback at {vendored}. Install BMAD-METHOD in the target project "
        "(https://github.com/bmad-code-org/BMAD-METHOD), or run "
        "`uv run python scripts/sync_bmad_skills.py` to refresh the vendored copy."
    )


def skill_available(project_root: Path, name: str) -> bool:
    """Whether a BMAD skill can be resolved — used to auto-skip the optional test_gen phase."""
    try:
        find_skill_root(project_root, name)
    except SkillNotFoundError:
        return False
    return True


def _substitute(text: str, mapping: dict[str, str]) -> str:
    for key, value in mapping.items():
        text = text.replace(key, value)
    return text


def _read_optional(path: Path) -> str | None:
    return path.read_text() if path.is_file() else None


def load(name: str, *, project_root: Path, placeholders: dict[str, str] | None = None) -> str:
    """Load a full BMAD skill's instruction text: SKILL.md + template/checklist/steps.

    This is the primary way adk-bmad agents get their domain instructions.
    """
    root = find_skill_root(project_root, name)
    parts = [(root / "SKILL.md").read_text()]

    for extra in ("discover-inputs.md", "template.md", "checklist.md"):
        text = _read_optional(root / extra)
        if text:
            parts.append(f"\n\n---\n# {extra}\n\n{text}")

    steps_dir = root / "steps"
    if steps_dir.is_dir():
        for step_file in sorted(steps_dir.glob("*.md")):
            parts.append(f"\n\n---\n# steps/{step_file.name}\n\n{step_file.read_text()}")

    text = "\n".join(parts)
    mapping = {
        "{project-root}": str(project_root),
        "{skill-root}": str(root),
        "{skill-name}": name,
        **(placeholders or {}),
    }
    return _substitute(text, mapping)


def load_step(
    name: str,
    step_id: str,
    *,
    project_root: Path,
    placeholders: dict[str, str] | None = None,
) -> str:
    """Load one `steps/<step_id>.md` from a skill, alongside its SKILL.md header.

    Used to give a single ADK sub-agent only its own slice of a multi-step BMAD
    skill — e.g. bmad-code-review's step-03-triage — rather than the whole
    workflow document.
    """
    root = find_skill_root(project_root, name)
    step_path = root / "steps" / f"{step_id}.md"
    if not step_path.is_file():
        raise SkillNotFoundError(f"Step '{step_id}' not found under skill '{name}' at {root}.")
    text = (
        f"{(root / 'SKILL.md').read_text()}\n\n---\n"
        f"# steps/{step_id}.md\n\n{step_path.read_text()}"
    )
    mapping = {
        "{project-root}": str(project_root),
        "{skill-root}": str(root),
        "{skill-name}": name,
        **(placeholders or {}),
    }
    return _substitute(text, mapping)
