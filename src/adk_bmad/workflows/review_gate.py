"""`ParallelAgent` (3 adversarial reviewers) -> `SequentialAgent` (triage).

The direct ADK-native analogue of upstream `bmad-code-review`'s own parallel
adversarial layers + triage step — a real fan-out/fan-in, not one inlined
reviewer prompt (which is how archon-bmad's Archon port had to do it, since
Archon's workflow engine has no native parallel-agent primitive).
"""

from __future__ import annotations

from google.adk.agents import ParallelAgent, SequentialAgent

from adk_bmad.agents._gating import phase_gate
from adk_bmad.agents.review.acceptance_auditor import build_acceptance_auditor_agent
from adk_bmad.agents.review.blind_hunter import build_blind_hunter_agent
from adk_bmad.agents.review.edge_case_hunter import build_edge_case_hunter_agent
from adk_bmad.agents.review.triage import build_triage_agent


def build_review_gate_workflow() -> SequentialAgent:
    """Gated as one unit on `state["phase"] == "dev"`, so when this iteration
    isn't at the review step, none of the three reviewer LLM calls fire at all.
    """
    reviewers = ParallelAgent(
        name="adversarial_reviewers",
        sub_agents=[
            build_blind_hunter_agent(),
            build_edge_case_hunter_agent(),
            build_acceptance_auditor_agent(),
        ],
    )
    return SequentialAgent(
        name="review_gate",
        sub_agents=[reviewers, build_triage_agent()],
        before_agent_callback=phase_gate("dev"),
    )
