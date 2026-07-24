"""The outer loop: repeats `story_cycle` until `select` escalates completion
(`state["run_status"] == "complete"`, via `EventActions.escalate` set in
`agents/select.py`'s `record_selection` tool) or `max_story_iterations` is hit
as a safety valve — the ADK-native replacement for archon-bmad's
`until_bash`-polled `state.json` loop.
"""

from __future__ import annotations

from google.adk.agents import LoopAgent

from adk_bmad.agents._context import LOOP_SETTINGS
from adk_bmad.workflows.story_cycle import build_story_cycle_workflow


def build_bmad_loop() -> LoopAgent:
    return LoopAgent(
        name="bmad_loop",
        sub_agents=[build_story_cycle_workflow()],
        max_iterations=LOOP_SETTINGS.max_story_iterations,
    )
