"""Blind Hunter — one of `bmad-code-review`'s three parallel adversarial layers.

Loads BMAD's own standalone `bmad-review-adversarial-general` skill verbatim.
By upstream design this layer sees the diff ONLY — no story, no spec, no
project read access — so its findings are unbiased by what the change claims
to do. Runs as one branch of `workflows/review_gate.py`'s `ParallelAgent`.
"""

from __future__ import annotations

from google.adk.agents.llm_agent import Agent

from adk_bmad import config, skills
from adk_bmad.agents._context import BMAD_CONFIG, PROJECT_ROOT
from adk_bmad.agents._prompting import wrap_instruction
from adk_bmad.tools import git_tools

_SKILL_TEXT = skills.load(
    "bmad-review-adversarial-general", project_root=PROJECT_ROOT, placeholders=BMAD_CONFIG.placeholders()
)

_INSTRUCTION = wrap_instruction(
    _SKILL_TEXT,
    footer=(
        "Your `content` to review is this story's changes. Call `git_diff` with "
        f'project_root="{PROJECT_ROOT}" to get it — that diff is your ONLY input. '
        "Do not call any file-reading tool; you are deliberately blind to the "
        "rest of the project. Output your findings as the markdown list the "
        "skill instructions describe, and nothing else."
    ),
)


def build_blind_hunter_agent() -> Agent:
    return Agent(
        name="blind_hunter",
        model=config.resolve_model("blind_hunter"),
        description="Adversarial diff-only reviewer — one of three parallel review layers.",
        instruction=_INSTRUCTION,
        include_contents="none",
        tools=[git_tools.git_diff],
        output_key="blind_hunter_findings",
    )
