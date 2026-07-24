"""Triage — the step that follows `workflows/review_gate.py`'s `ParallelAgent`.

Loads `bmad-code-review`'s own `step-03-triage` verbatim: normalize the three
reviewers' outputs into one list, deduplicate, and classify each finding as
`decision_needed` / `patch` / `defer` / `dismiss`.

Upstream's own next step (`step-04-present`) is interactive by design — it HALTs
to ask a human how to handle `decision_needed` and `patch` findings. This loop
has no human, so — exactly like every other phase here — this agent is
instructed to make the autonomous call upstream's own UI would offer as the
default: resolve `decision_needed` findings itself from available context, and
always choose "apply every patch" for `patch` findings (fix the code, adjust
tests, re-run them). The gate this agent decides: commit is allowed only once
zero `decision_needed` and zero unresolved `patch` findings remain — `defer`
and `dismiss` never block, matching upstream's own severity model exactly
(not the CRITICAL/HIGH taxonomy archon-bmad's inlined reviewer invented).
"""

from __future__ import annotations

from google.adk.agents.llm_agent import Agent
from google.adk.tools.tool_context import ToolContext

from adk_bmad import config, skills
from adk_bmad.agents._context import BMAD_CONFIG, LOOP_SETTINGS, PROJECT_ROOT
from adk_bmad.agents._prompting import wrap_instruction
from adk_bmad.tools import exec_tools, git_tools, sprint_tools, story_tools

_SKILL_TEXT = skills.load_step(
    "bmad-code-review", "step-03-triage", project_root=PROJECT_ROOT, placeholders=BMAD_CONFIG.placeholders()
)


def record_review_outcome(
    story_key: str,
    gate_clear: bool,
    decision_needed_count: int,
    unresolved_patch_count: int,
    deferred_count: int,
    dismissed_count: int,
    tool_context: ToolContext,
) -> dict:
    """Record this review pass's outcome. Call exactly once, as your LAST action,
    after triaging every finding and applying every `patch` fix you could.

    `gate_clear` must be True only if, after your fixes, zero `decision_needed`
    and zero `patch` findings remain unresolved (defer/dismiss never block).
    If not clear, the story reverts to "in-progress" for another dev pass; if
    this happens `max_review_retries` times for the same story, it's escalated
    for a human instead of retried forever.
    """
    state = tool_context.state
    state["review_gate_clear"] = gate_clear
    result = {
        "gate_clear": gate_clear,
        "decision_needed_count": decision_needed_count,
        "unresolved_patch_count": unresolved_patch_count,
        "deferred_count": deferred_count,
        "dismissed_count": dismissed_count,
    }
    if gate_clear:
        return result

    retries = int(state.get("review_retry_count", 0)) + 1
    state["review_retry_count"] = retries
    result["review_retry_count"] = retries

    if retries >= LOOP_SETTINGS.max_review_retries:
        escalated = dict(state.get("escalated_stories", {}))
        escalated[story_key] = (
            f"review failed after {LOOP_SETTINGS.max_review_retries} cycles "
            f"({decision_needed_count} decision-needed, {unresolved_patch_count} unresolved patch remaining)"
        )
        state["escalated_stories"] = escalated
        result["escalated"] = True
    return result


_INSTRUCTION = wrap_instruction(
    _SKILL_TEXT,
    footer="""\
The three review layers' raw findings for story `{current_story_key}` are:

## Blind Hunter (diff-only)
{blind_hunter_findings}

## Edge Case Hunter (diff + read access)
{edge_case_hunter_findings}

## Acceptance Auditor (diff + spec)
{acceptance_auditor_findings}

Normalize, deduplicate, and classify these per the triage instructions above.
Then — since you are autonomous, not the interactive human upstream's own
step-04 would ask — do what that step's "apply every patch" option does
yourself: for every `patch` finding, fix the code directly (use
`edit_text_file`/`write_text_file`), add or adjust tests as needed, and re-run
the project's test command with `run_command` to confirm green. For every
`decision_needed` finding, make the most conservative, best-documented choice
available from the story/spec/architecture context and treat it as resolved
(reclassify it as `patch` and fix it, or `defer` with a one-line reason) —
never leave a `decision_needed` finding unresolved by choice; only report a
gate failure if you genuinely could not safely resolve or fix something.

Append a `### Review Findings` section to the story file (matching the
`- [ ] [Review][Patch] <Title> [<file>:<line>]` / `- [x] [Review][Defer] ...`
format the upstream skill uses) recording what you found and did.

If, after your fix pass, any `decision_needed` or `patch` finding genuinely
remains unresolved, call `set_story_status` and `set_development_status` to set
story `{current_story_key}` back to "in-progress" (it must not stay "review").
If everything is resolved, leave both statuses as "review" — `commit` sets the
final "done" status once the commit itself lands.

Call `record_review_outcome` exactly once, as your last action.""",
)


def build_triage_agent() -> Agent:
    return Agent(
        name="review_triage",
        model=config.resolve_model("triage"),
        description="Normalizes/dedupes/classifies the three reviewers' findings and decides the commit gate.",
        instruction=_INSTRUCTION,
        include_contents="none",
        tools=[
            story_tools.read_text_file,
            story_tools.write_text_file,
            story_tools.edit_text_file,
            story_tools.set_story_status,
            sprint_tools.set_development_status,
            git_tools.git_diff,
            git_tools.git_diff_stat,
            exec_tools.run_command,
            record_review_outcome,
        ],
    )
