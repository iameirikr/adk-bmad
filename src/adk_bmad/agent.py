"""adk-bmad's root agent — the full BMAD-METHOD implementation-loop workflow,
discovered by `adk web` / `adk run` / `adk api_server` as `root_agent`.

Tree: `SequentialAgent(adk_bmad)`
  -> `LoopAgent(bmad_loop)`
       -> `SequentialAgent(story_cycle)`  [one phase per iteration]
            -> `select`                    (always runs; decides the phase)
            -> `create_story`              (gated: phase == "create")
            -> `dev_story`                 (gated: phase == "dev")
            -> `test_gen`                  (gated: phase == "dev", optional)
            -> `SequentialAgent(review_gate)` (gated: phase == "dev")
                 -> `ParallelAgent(adversarial_reviewers)`
                      -> `blind_hunter` / `edge_case_hunter` / `acceptance_auditor`
                 -> `review_triage`
            -> `commit`                    (gated: phase == "dev" AND review clear)
            -> `retrospective`             (gated: phase == "retro", non-blocking)
  -> `report`                              (runs once, after the loop finishes)

See docs/architecture.md for the full design and NOTICE for BMAD/ADK attribution.
"""

from __future__ import annotations

from google.adk.agents import SequentialAgent

from adk_bmad.agents.report import build_report_agent
from adk_bmad.workflows.bmad_loop import build_bmad_loop

root_agent = SequentialAgent(
    name="adk_bmad",
    description=(
        "Automates the BMAD-METHOD implementation loop — create story, dev "
        "story, optional test generation, parallel adversarial review, commit, "
        "and per-epic retrospectives — across a story, a range of stories, or "
        "an entire epic."
    ),
    sub_agents=[build_bmad_loop(), build_report_agent()],
)
