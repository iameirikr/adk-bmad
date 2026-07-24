"""The `dev` phase — loads BMAD's own `bmad-dev-story` skill verbatim.

Implements every unchecked task via red-green-refactor (or, on a retry after a
failed review gate, addresses the `### Review Findings` follow-ups the triage
step appended), then sets the story to "review". Only runs when `select` set
`state["phase"] == "dev"`.

Demonstrates genuine dynamic per-story model routing: a `before_model_callback`
escalates this agent from the cheap default model to the heavier configured
tier when `create_story`'s complexity scorer flagged the story as complex —
mutating `LlmRequest.model` in place, not just picking a model once at
construction time.
"""

from __future__ import annotations

from google.adk.agents.context import Context
from google.adk.agents.llm_agent import Agent
from google.adk.models.llm_request import LlmRequest

from adk_bmad import config, skills
from adk_bmad.agents._context import BMAD_CONFIG, PROJECT_ROOT
from adk_bmad.agents._gating import phase_gate
from adk_bmad.agents._prompting import wrap_instruction
from adk_bmad.tools import exec_tools, git_tools, sprint_tools, story_tools

_SKILL_TEXT = skills.load(
    "bmad-dev-story", project_root=PROJECT_ROOT, placeholders=BMAD_CONFIG.placeholders()
)

_INSTRUCTION = wrap_instruction(
    _SKILL_TEXT,
    footer=(
        "You are implementing story `{current_story_key}` right now. If a "
        '"### Review Findings" section already exists in the story file with '
        "unchecked `[Review][Patch]` or `[Review][Decision]` items, prioritize "
        "those follow-ups before any other remaining task. Record the current "
        "git HEAD as this story's `baseline_commit` (via "
        "`set_story_baseline_commit`) the first time you start work on it, if "
        "the frontmatter doesn't already have one."
    ),
)


async def _escalate_model_for_complex_stories(context: Context, llm_request: LlmRequest) -> None:
    """Swap to the heavier configured model when this story was scored complex."""
    if context.state.get("story_complexity_tier") == "heavy":
        llm_request.model = config.resolve_model("dev_story_heavy")


def build_dev_story_agent() -> Agent:
    return Agent(
        name="dev_story",
        model=config.resolve_model("dev_story"),
        description="Implements a story's tasks (or addresses review follow-ups), using BMAD's dev-story workflow.",
        instruction=_INSTRUCTION,
        include_contents="none",
        before_agent_callback=phase_gate("dev"),
        before_model_callback=_escalate_model_for_complex_stories,
        tools=[
            story_tools.read_text_file,
            story_tools.write_text_file,
            story_tools.edit_text_file,
            story_tools.list_directory,
            story_tools.get_story_status,
            story_tools.set_story_status,
            story_tools.set_story_baseline_commit,
            sprint_tools.get_development_status,
            sprint_tools.set_development_status,
            git_tools.git_status,
            git_tools.git_diff,
            git_tools.git_head_sha,
            exec_tools.run_command,
        ],
    )
