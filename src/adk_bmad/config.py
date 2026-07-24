"""Runtime configuration for adk-bmad: model tiers, BMAD project paths, and loop knobs.

Every knob here is overridable via environment variables so the same agent graph runs
against any BMAD-METHOD project without code changes — see docs/configuration.md.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from google.adk.models.lite_llm import LiteLlm

# ---------------------------------------------------------------------------
# Model tiers
# ---------------------------------------------------------------------------
#
# Every agent's model is one config value, resolved per-agent so the fleet can be
# deliberately mixed (a cheap model for select/triage/report-shaped agents, a
# heavier one for dev-story and the adversarial reviewers) rather than a single
# blanket setting. Defaults are Gemini (the lowest-friction path to `adk web`
# working with only a GOOGLE_API_KEY); set any ADK_BMAD_MODEL_<AGENT> env var to
# a LiteLLM-style "<provider>/<model>" string (e.g. "anthropic/claude-opus-4-6")
# to swap that agent to any other provider LiteLLM supports.

_DEFAULT_MODELS: dict[str, str] = {
    "select": "gemini-2.5-flash",
    "create_story": "gemini-2.5-pro",
    "dev_story": "gemini-2.5-flash",
    "dev_story_heavy": "gemini-2.5-pro",
    "test_gen": "gemini-2.5-flash",
    "blind_hunter": "gemini-2.5-pro",
    "edge_case_hunter": "gemini-2.5-pro",
    "acceptance_auditor": "gemini-2.5-pro",
    "triage": "gemini-2.5-flash",
    "commit": "gemini-2.5-flash",
    "retrospective": "gemini-2.5-flash",
    "report": "gemini-2.5-flash",
}
"""Per-agent-role default models. `dev_story` starts on the cheap tier and is
escalated to `dev_story_heavy` at runtime by a `before_model_callback` when the
story complexity scorer (`tools/complexity.py`) flags a story as complex — see
`agents/dev_story.py`. Override any single role via `ADK_BMAD_MODEL_<ROLE>`."""


def _env_var_for(agent_key: str) -> str:
    return f"ADK_BMAD_MODEL_{agent_key.upper()}"


def resolve_model(agent_key: str) -> str | LiteLlm:
    """Resolve the model for a given agent role.

    Reads `ADK_BMAD_MODEL_<AGENT_KEY>` (e.g. `ADK_BMAD_MODEL_DEV_STORY`), falling
    back to this repo's tiered default. A bare Gemini model id (`gemini-*`) is
    passed straight through — ADK's native provider. Anything else is assumed to
    be a LiteLLM model string (`anthropic/...`, `openai/...`, `ollama/...`, etc.)
    and wrapped in `LiteLlm(...)` so any provider ADK supports via LiteLLM works
    as a drop-in replacement for any single agent.
    """
    default = _DEFAULT_MODELS.get(agent_key)
    if default is None:
        raise KeyError(f"No default model registered for agent role {agent_key!r}")
    model_id = os.environ.get(_env_var_for(agent_key), default)
    if model_id.startswith("gemini"):
        return model_id
    return LiteLlm(model=model_id)


# ---------------------------------------------------------------------------
# Loop knobs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LoopSettings:
    """Retry/iteration limits for the story cycle, mirroring archon-bmad's gates."""

    max_review_retries: int = int(os.environ.get("ADK_BMAD_MAX_REVIEW_RETRIES", "8"))
    max_create_retries: int = int(os.environ.get("ADK_BMAD_MAX_CREATE_RETRIES", "2"))
    max_story_iterations: int = int(os.environ.get("ADK_BMAD_MAX_STORY_ITERATIONS", "150"))
    skip_test_gen: bool = os.environ.get("ADK_BMAD_SKIP_TEST_GEN", "").lower() in (
        "1",
        "true",
        "yes",
    )


# ---------------------------------------------------------------------------
# BMAD project configuration (_bmad/bmm/config.yaml)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BmadProjectConfig:
    """Resolved paths and metadata from a BMAD-METHOD project's `_bmad/bmm/config.yaml`."""

    project_root: Path
    output_folder: Path
    implementation_artifacts: Path
    planning_artifacts: Path
    project_knowledge: Path
    sprint_status: Path
    user_name: str = "there"
    project_name: str = "this project"
    communication_language: str = "English"
    document_output_language: str = "English"
    user_skill_level: str = "intermediate"

    def placeholders(self) -> dict[str, str]:
        """The substitution map used to resolve BMAD skill instruction placeholders."""
        return {
            "{project-root}": str(self.project_root),
            "{implementation_artifacts}": str(self.implementation_artifacts),
            "{planning_artifacts}": str(self.planning_artifacts),
            "{project_knowledge}": str(self.project_knowledge),
            "{user_name}": self.user_name,
            "{project_name}": self.project_name,
            "{communication_language}": self.communication_language,
            "{document_output_language}": self.document_output_language,
            "{user_skill_level}": self.user_skill_level,
        }


def _expand(raw: str, project_root: Path) -> Path:
    return Path(raw.replace("{project-root}", str(project_root)))


def load_bmad_config(project_root: Path) -> BmadProjectConfig:
    """Load and resolve `<project_root>/_bmad/bmm/config.yaml`.

    Raises FileNotFoundError with a message pointing at BMAD planning setup if the
    config (or the sprint-status.yaml it implies) doesn't exist yet — mirroring the
    same guard archon-bmad's `init` node runs before anything else.
    """
    project_root = project_root.resolve()
    config_path = project_root / "_bmad" / "bmm" / "config.yaml"
    if not config_path.is_file():
        raise FileNotFoundError(
            f"BMAD config not found at {config_path}. adk-bmad must run against a "
            "BMAD-METHOD project with planning already complete (run BMAD's planning "
            "workflows first, e.g. via `bmad-method install` + PRD/architecture/"
            "sprint-planning)."
        )
    raw = yaml.safe_load(config_path.read_text()) or {}

    output_folder = _expand(raw.get("output_folder", "{project-root}/_bmad-output"), project_root)
    implementation_artifacts = _expand(
        raw.get("implementation_artifacts", str(output_folder / "implementation-artifacts")),
        project_root,
    )
    planning_artifacts = _expand(
        raw.get("planning_artifacts", str(output_folder / "planning-artifacts")), project_root
    )
    project_knowledge = _expand(raw.get("project_knowledge", "{project-root}/docs"), project_root)

    sprint_status = implementation_artifacts / "sprint-status.yaml"
    if not sprint_status.is_file():
        raise FileNotFoundError(
            f"sprint-status.yaml not found at {sprint_status}. Run BMAD sprint planning "
            "before automating implementation."
        )

    return BmadProjectConfig(
        project_root=project_root,
        output_folder=output_folder,
        implementation_artifacts=implementation_artifacts,
        planning_artifacts=planning_artifacts,
        project_knowledge=project_knowledge,
        sprint_status=sprint_status,
        user_name=raw.get("user_name", "there"),
        project_name=raw.get("project_name", "this project"),
        communication_language=raw.get("communication_language", "English"),
        document_output_language=raw.get("document_output_language", "English"),
        user_skill_level=raw.get("user_skill_level", "intermediate"),
    )


def default_project_root() -> Path:
    """The BMAD project adk-bmad targets, in order:

    1. `ADK_BMAD_PROJECT_ROOT`, if set.
    2. The current working directory, if it has `_bmad/bmm/config.yaml`.
    3. `./examples/sample-bmad-project`, if it exists relative to cwd — so running
       `adk web` / `adk run` from a clone of this repo works with zero setup.
    4. Otherwise, the current working directory (and `load_bmad_config` will raise
       a descriptive error pointing at what's missing).
    """
    env_override = os.environ.get("ADK_BMAD_PROJECT_ROOT")
    if env_override:
        return Path(env_override).resolve()

    cwd = Path.cwd()
    if (cwd / "_bmad" / "bmm" / "config.yaml").is_file():
        return cwd

    bundled_example = cwd / "examples" / "sample-bmad-project"
    if (bundled_example / "_bmad" / "bmm" / "config.yaml").is_file():
        return bundled_example.resolve()

    return cwd
