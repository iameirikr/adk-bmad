"""One phase per `bmad_loop` tick: `select` decides, then every other sub-agent
below gates itself on that decision (see `agents/_gating.py`) — so only the
phase(s) relevant to the current story/epic actually do anything this tick.

`select` runs unconditionally every tick. `create_story` runs only when phase
is "create". `dev_story` / `test_gen` / `review_gate` / `commit` all run
(subject to their own finer-grained gates) when phase is "dev" — a full
create-vs-dev split, but within "dev" a story rides through
implement -> (optional) test-gen -> parallel adversarial review -> commit in
one tick when review clears, or bounces back to another `dev_story` pass on the
next tick when it doesn't (LoopAgent re-invokes this whole sequence; `select`
re-derives "dev" for the same story since sprint-status still shows it
in-progress). `retrospective` runs only when phase is "retro".
"""

from __future__ import annotations

from google.adk.agents import SequentialAgent

from adk_bmad.agents.commit import build_commit_agent
from adk_bmad.agents.create_story import build_create_story_agent
from adk_bmad.agents.dev_story import build_dev_story_agent
from adk_bmad.agents.retrospective import build_retrospective_agent
from adk_bmad.agents.select import build_select_agent
from adk_bmad.agents.test_gen import build_test_gen_agent
from adk_bmad.workflows.review_gate import build_review_gate_workflow


def build_story_cycle_workflow() -> SequentialAgent:
    return SequentialAgent(
        name="story_cycle",
        sub_agents=[
            build_select_agent(),
            build_create_story_agent(),
            build_dev_story_agent(),
            build_test_gen_agent(),
            build_review_gate_workflow(),
            build_commit_agent(),
            build_retrospective_agent(),
        ],
    )
