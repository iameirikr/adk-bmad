"""The `retro` phase — loads BMAD's own `bmad-retrospective` skill verbatim.

Fires once per epic, when `select` finds every story in that epic "done" but
its `<epic>-retrospective` status isn't yet "done". Non-blocking by design,
matching archon-bmad: if the model or a tool call fails for any reason, an
error callback logs it and produces a graceful fallback instead of raising —
a retrospective must never crash the run.
"""

from __future__ import annotations

from google.adk.agents.context import Context
from google.adk.agents.llm_agent import Agent
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from adk_bmad import config, skills
from adk_bmad.agents._context import BMAD_CONFIG, PROJECT_ROOT
from adk_bmad.agents._gating import phase_gate
from adk_bmad.agents._prompting import wrap_instruction
from adk_bmad.tools import exec_tools, sprint_tools, story_tools

_SKILL_TEXT = skills.load(
    "bmad-retrospective", project_root=PROJECT_ROOT, placeholders=BMAD_CONFIG.placeholders()
)


def mark_retrospective_done(epic_key: str, tool_context: ToolContext) -> dict:
    """Record that epic `epic_key`'s retrospective ran, for this run's final report."""
    completed = list(tool_context.state.get("completed_epics", []))
    if epic_key not in completed:
        completed.append(epic_key)
    tool_context.state["completed_epics"] = completed
    return {"epic_key": epic_key, "completed_epics": completed}


_INSTRUCTION = wrap_instruction(
    _SKILL_TEXT,
    footer=(
        "Facilitate the retrospective for epic `{current_epic_key}` now, fully "
        "autonomously (no human participants — synthesize observations from the "
        "story files' Dev Agent Records, dev notes, and sprint-status history "
        "yourself). When the retrospective document is written, set "
        '`development_status["{current_epic_key}-retrospective"]` to "done" via '
        "`set_development_status`, then call `mark_retrospective_done`."
    ),
)


async def _tolerate_tool_error(
    tool: BaseTool, args: dict, context: Context, error: Exception
) -> dict:
    return {
        "error": str(error),
        "note": "retrospective tool call failed; this phase is non-blocking, continuing",
    }


async def _tolerate_model_error(
    context: Context, llm_request: LlmRequest, error: Exception
) -> LlmResponse:
    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[types.Part(text=f"(retrospective failed non-blocking: {error})")],
        )
    )


def build_retrospective_agent() -> Agent:
    return Agent(
        name="retrospective",
        model=config.resolve_model("retrospective"),
        description="Facilitates the per-epic retrospective, using BMAD's retrospective workflow. Non-blocking.",
        instruction=_INSTRUCTION,
        include_contents="none",
        before_agent_callback=phase_gate("retro"),
        on_tool_error_callback=_tolerate_tool_error,
        on_model_error_callback=_tolerate_model_error,
        tools=[
            story_tools.read_text_file,
            story_tools.write_text_file,
            story_tools.list_directory,
            sprint_tools.read_sprint_status,
            sprint_tools.set_development_status,
            sprint_tools.stories_in_epic,
            exec_tools.run_command,
            mark_retrospective_done,
        ],
    )
