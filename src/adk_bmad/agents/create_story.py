"""The `create` phase — loads BMAD's own `bmad-create-story` skill verbatim.

Writes the next story file, using exhaustive analysis of the epics/PRD/
architecture/UX docs, the previous story, and recent git history, exactly as
upstream's own multi-step workflow describes. Only runs when `select` set
`state["phase"] == "create"`.
"""

from __future__ import annotations

from pathlib import Path

from google.adk.agents.llm_agent import Agent
from google.adk.tools.tool_context import ToolContext

from adk_bmad import config, skills
from adk_bmad.agents._context import BMAD_CONFIG, PROJECT_ROOT
from adk_bmad.agents._gating import phase_gate
from adk_bmad.agents._prompting import wrap_instruction
from adk_bmad.state import story_file as _story_file
from adk_bmad.tools import complexity, exec_tools, git_tools, sprint_tools, story_tools

_SKILL_TEXT = skills.load(
    "bmad-create-story", project_root=PROJECT_ROOT, placeholders=BMAD_CONFIG.placeholders()
)


def assess_story_complexity(implementation_artifacts: str, story_key: str, tool_context: ToolContext) -> dict:
    """Score this story's complexity (regex + structural heuristics over its text)
    and record the recommended dev-story model tier ("standard" or "heavy") for
    this run. Call this once, after the story file is fully written.
    """
    text = _story_file.read_text(Path(implementation_artifacts), story_key)
    score = complexity.score_story_text(text)
    tier = complexity.tier_for_score(score)
    tool_context.state["story_complexity_tier"] = tier
    return {"score": score, "tier": tier, "matched_rules": complexity.matched_rules(text)}


_INSTRUCTION = wrap_instruction(
    _SKILL_TEXT,
    footer=(
        "You are creating the story file for story `{current_story_key}` right "
        "now. After writing the file and setting its status (and syncing "
        "sprint-status.yaml to \"ready-for-dev\"), call `assess_story_complexity` "
        "once so the dev-story phase can pick an appropriately-sized model for "
        "this story."
    ),
)


def build_create_story_agent() -> Agent:
    return Agent(
        name="create_story",
        model=config.resolve_model("create_story"),
        description="Writes the next story file, using BMAD's create-story workflow.",
        instruction=_INSTRUCTION,
        include_contents="none",
        before_agent_callback=phase_gate("create"),
        tools=[
            story_tools.read_text_file,
            story_tools.write_text_file,
            story_tools.edit_text_file,
            story_tools.list_directory,
            story_tools.story_exists,
            story_tools.get_story_status,
            story_tools.set_story_status,
            sprint_tools.get_development_status,
            sprint_tools.set_development_status,
            git_tools.git_log,
            git_tools.git_diff_stat,
            exec_tools.run_command,
            assess_story_complexity,
        ],
    )
