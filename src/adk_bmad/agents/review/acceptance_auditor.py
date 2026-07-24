"""Acceptance Auditor — the third of `bmad-code-review`'s three parallel
adversarial layers.

Unlike Blind Hunter and Edge Case Hunter, upstream doesn't ship this layer as
its own standalone skill file — `bmad-code-review/steps/step-02-review.md`
defines it inline, as a short quoted prompt (reproduced verbatim below,
attributed) rather than a `SKILL.md`. This layer gets the diff plus the spec
(here, the story file itself — always available in this loop, so this layer
always runs) and checks the change against what was actually specified.
"""

from __future__ import annotations

from google.adk.agents.llm_agent import Agent

from adk_bmad import config
from adk_bmad.agents._context import BMAD_CONFIG, PROJECT_ROOT
from adk_bmad.agents._prompting import wrap_instruction
from adk_bmad.tools import git_tools, story_tools

# Quoted verbatim from bmad-code-review/steps/step-02-review.md (BMAD-METHOD, MIT).
_UPSTREAM_PROMPT = (
    "You are an Acceptance Auditor. Review this diff against the spec and context "
    "docs. Check for: violations of acceptance criteria, deviations from spec "
    "intent, missing implementation of specified behavior, contradictions between "
    "spec constraints and actual code. Output findings as a Markdown list. Each "
    "finding: one-line title, which AC/constraint it violates, and evidence from "
    "the diff."
)

_INSTRUCTION = wrap_instruction(
    _UPSTREAM_PROMPT,
    footer=(
        "Your `content` to review is this story's changes; your `spec` is the "
        "story file for `{current_story_key}`. Call `git_diff` with "
        f'project_root="{PROJECT_ROOT}" for the diff, and `read_text_file` on '
        f'"{BMAD_CONFIG.implementation_artifacts}/{{current_story_key}}.md" for '
        "the spec (its Acceptance Criteria section is the authoritative list to "
        "check against). Output only the markdown list the prompt above describes."
    ),
)


def build_acceptance_auditor_agent() -> Agent:
    return Agent(
        name="acceptance_auditor",
        model=config.resolve_model("acceptance_auditor"),
        description="Checks the diff against the story's acceptance criteria — one of three parallel review layers.",
        instruction=_INSTRUCTION,
        include_contents="none",
        tools=[git_tools.git_diff, story_tools.read_text_file],
        output_key="acceptance_auditor_findings",
    )
