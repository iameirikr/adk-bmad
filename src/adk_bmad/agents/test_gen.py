"""The optional `test_gen` phase — loads BMAD's own `bmad-qa-generate-e2e-tests`
skill verbatim, when it's installed. Auto-skipped (no wasted model call) if the
skill isn't found under any BMAD skill root, or if `ADK_BMAD_SKIP_TEST_GEN` is
set — mirroring archon-bmad's `skipAutomate`. Runs after `dev_story`, still
within `state["phase"] == "dev"`.
"""

from __future__ import annotations

from google.adk.agents.context import Context
from google.adk.agents.llm_agent import Agent
from google.genai import types

from adk_bmad import config, skills
from adk_bmad.agents._context import BMAD_CONFIG, LOOP_SETTINGS, PROJECT_ROOT
from adk_bmad.agents._prompting import wrap_instruction
from adk_bmad.tools import exec_tools, story_tools

_SKILL_NAME = "bmad-qa-generate-e2e-tests"
_ENABLED = (not LOOP_SETTINGS.skip_test_gen) and skills.skill_available(PROJECT_ROOT, _SKILL_NAME)

if _ENABLED:
    _SKILL_TEXT = skills.load(_SKILL_NAME, project_root=PROJECT_ROOT, placeholders=BMAD_CONFIG.placeholders())
    _INSTRUCTION = wrap_instruction(
        _SKILL_TEXT,
        footer=(
            "Generate/augment automated tests for story `{current_story_key}`'s "
            "changes. Auto-apply every gap you find — there is no human to ask."
        ),
    )
else:
    _INSTRUCTION = "This phase is disabled for this run. Do nothing and end your turn immediately."


async def _gate(context: Context) -> types.Content | None:
    if not _ENABLED:
        return types.Content(
            role="model",
            parts=[types.Part(text=f"(skipped — {_SKILL_NAME} not installed or ADK_BMAD_SKIP_TEST_GEN set)")],
        )
    if context.state.get("phase") != "dev":
        return types.Content(role="model", parts=[types.Part(text="(skipped — phase is not 'dev')")])
    return None


def build_test_gen_agent() -> Agent:
    return Agent(
        name="test_gen",
        model=config.resolve_model("test_gen"),
        description="Generates/augments end-to-end tests for the story just implemented (optional phase).",
        instruction=_INSTRUCTION,
        include_contents="none",
        before_agent_callback=_gate,
        tools=[
            story_tools.read_text_file,
            story_tools.write_text_file,
            story_tools.edit_text_file,
            story_tools.list_directory,
            exec_tools.run_command,
        ],
    )
