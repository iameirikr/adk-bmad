"""The `select` phase: original adk-bmad orchestration logic (not loaded from a
BMAD skill — there's no single upstream skill for "which phase runs next across
an entire story/epic run"; this is the same orchestration role archon-bmad's own
`select` phase and `orchestrator-rules.md` play, reimplemented as a real ADK
agent+tool rather than a bash/state.json state machine).

Runs first in every `story_cycle` iteration. Reads sprint-status.yaml (the
source of truth — never trusts session state alone) and decides exactly one of:
create the next story, continue/implement the next story, run a due
retrospective, or end the run.
"""

from __future__ import annotations

from google.adk.agents.llm_agent import Agent
from google.adk.tools.tool_context import ToolContext

from adk_bmad import config
from adk_bmad.agents._context import BMAD_CONFIG
from adk_bmad.tools import sprint_tools, story_tools


def get_escalated_stories(tool_context: ToolContext) -> dict:
    """Story keys this run has already given up on (review-retry budget exhausted),
    with the reason — skip these when scanning for the next not-"done" story;
    they still need a human, but retrying them forever would stall the run."""
    return dict(tool_context.state.get("escalated_stories", {}))


def record_selection(
    phase: str,
    tool_context: ToolContext,
    story_key: str = "",
    epic_key: str = "",
    reason: str = "",
) -> dict:
    """Record this iteration's selection decision. Call this exactly once, last.

    `phase` must be one of:
    - "create": `story_key` is the next story to create (no story file exists yet).
    - "dev": `story_key` is the next story to implement/continue (story file
      exists, sprint-status shows it not yet "done").
    - "retro": `epic_key` is a fully-"done" epic that hasn't had its
      retrospective yet (development_status["<epic_key>-retrospective"] is not
      "done").
    - "complete": every targeted story is "done" and every completed epic has
      had its retrospective. This ends the run.

    `reason` is a one-sentence explanation, recorded for the final report.
    """
    state = tool_context.state
    if phase in ("create", "dev") and story_key != state.get("current_story_key"):
        state["review_retry_count"] = 0
        state["create_retry_count"] = 0
    state["phase"] = phase
    state["current_story_key"] = story_key or None
    state["current_epic_key"] = epic_key or None
    if phase == "complete":
        state["run_status"] = "complete"
        tool_context.actions.escalate = True
    return {"phase": phase, "story_key": story_key, "epic_key": epic_key, "reason": reason}


INSTRUCTION = f"""\
You are the selection step of an automated BMAD-METHOD implementation loop. You
run once per iteration, before any implementation work happens. Your only job
is to decide what happens THIS iteration and record that decision by calling
`record_selection` exactly once, as your last action.

## Ground truth

`sprint-status.yaml` at `{BMAD_CONFIG.sprint_status}` is the single source of
truth for what's done. Read it fresh every iteration with `read_sprint_status` —
never assume a previous iteration's belief still holds.

## What the user asked for

The user's original request (e.g. "epic 2", "stories 2-1 through 2-4", "all
pending stories") is the first message in this conversation. Interpret it
against the sprint-status story keys:
- A bare epic reference ("epic 2") means every story whose key starts with
  "2-" (i.e. belongs to `epic-2`).
- A story range ("stories 2-1 through 2-4") means exactly those story keys.
- Empty, "all", or "everything left" means every story in sprint-status that is
  not yet "done".

## Algorithm

1. Call `read_sprint_status` and parse `development_status`. Call
   `get_escalated_stories` too — these story keys already exhausted their
   review-retry budget in this run and need a human, not another attempt;
   exclude them from step 3 as if they were "done" for selection purposes
   (they are NOT actually done in sprint-status, and must stay reported as
   needing attention in the final report — just don't target them again here).
2. Resolve the user's request into a target set of story keys (see above).
3. Scan the target set **in sprint order (top to bottom in the file)**,
   excluding escalated story keys, for the first story whose status is not
   "done".
4. If found:
   - Call `story_exists` (implementation_artifacts = "{BMAD_CONFIG.implementation_artifacts}")
     for that story's key.
   - If it does NOT exist yet, this iteration's phase is "create".
   - If it DOES exist, this iteration's phase is "dev" (this covers a story
     that's ready-for-dev, in-progress, or bounced back from review — dev_story
     itself figures out where to resume).
   - Call `record_selection(phase=..., story_key=<that story's key>, reason=...)`.
5. Else (every targeted story is "done") — check each targeted story's epic:
   - Call `epic_key_for_story` for each, dedupe, and for every resulting epic
     call `epic_fully_done` and `get_development_status` on
     "<epic_key>-retrospective".
   - If any such epic is fully done AND its retrospective status is not "done":
     phase is "retro". Call `record_selection(phase="retro", epic_key=..., reason=...)`.
   - Else (every completed epic already has its retrospective, or there are no
     epics left to check): phase is "complete". Call
     `record_selection(phase="complete", reason=...)` — if any stories were
     excluded as escalated in step 1, say so in `reason` so the final report
     can surface them; otherwise note that all targeted work is done. This
     ends the run either way.

Call `record_selection` exactly once. Do not narrate your reasoning outside of
the `reason` argument — end your turn immediately after the call.
"""


def build_select_agent() -> Agent:
    return Agent(
        name="select",
        model=config.resolve_model("select"),
        description=(
            "Reads sprint-status.yaml and decides the next unit of work "
            "(create a story, continue a story, run a retrospective, or finish)."
        ),
        instruction=INSTRUCTION,
        tools=[
            sprint_tools.read_sprint_status,
            sprint_tools.get_development_status,
            sprint_tools.epic_key_for_story,
            sprint_tools.stories_in_epic,
            sprint_tools.epic_fully_done,
            story_tools.story_exists,
            get_escalated_stories,
            record_selection,
        ],
    )
