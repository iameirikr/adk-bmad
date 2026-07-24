"""Edge Case Hunter — one of `bmad-code-review`'s three parallel adversarial layers.

Loads BMAD's own standalone `bmad-review-edge-case-hunter` skill verbatim. By
upstream design this layer gets the diff plus read access to the project (but
not the spec/story) and mechanically enumerates unhandled branches/boundaries,
reporting only gaps — never a style opinion. Runs as one branch of
`workflows/review_gate.py`'s `ParallelAgent`.
"""

from __future__ import annotations

from google.adk.agents.llm_agent import Agent

from adk_bmad import config, skills
from adk_bmad.agents._context import BMAD_CONFIG, PROJECT_ROOT
from adk_bmad.agents._prompting import wrap_instruction
from adk_bmad.tools import git_tools, story_tools

_SKILL_TEXT = skills.load(
    "bmad-review-edge-case-hunter", project_root=PROJECT_ROOT, placeholders=BMAD_CONFIG.placeholders()
)

_INSTRUCTION = wrap_instruction(
    _SKILL_TEXT,
    footer=(
        "Your `content` to review is this story's changes. Call `git_diff` with "
        f'project_root="{PROJECT_ROOT}" to get the diff, then use '
        "`read_text_file`/`list_directory` for read-only project context as "
        "needed (you may read, but never write or run commands). Output the "
        "JSON array the skill instructions describe, and nothing else."
    ),
)


def build_edge_case_hunter_agent() -> Agent:
    return Agent(
        name="edge_case_hunter",
        model=config.resolve_model("edge_case_hunter"),
        description="Exhaustive edge-case reviewer — one of three parallel review layers.",
        instruction=_INSTRUCTION,
        include_contents="none",
        tools=[git_tools.git_diff, story_tools.read_text_file, story_tools.list_directory],
        output_key="edge_case_hunter_findings",
    )
