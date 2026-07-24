"""The `commit` phase — original adk-bmad orchestration, not a BMAD skill.

The only phase that ever runs `git commit`. Every other phase leaves its
changes uncommitted so a story lands as ONE atomic commit: implementation +
review fixes + the story file's `Status: done` + sprint-status's
`development_status[<story_key>] = done`, together — mirroring archon-bmad's
own commit discipline.

Gated twice, deliberately: a `before_agent_callback` skips this agent's entire
turn unless the review gate is clear (so the model never even runs when it
shouldn't), and a `before_tool_callback` additionally refuses the `git_commit`
tool call itself if `review_gate_clear` isn't true — the idiomatic ADK
replacement for archon-bmad's bash pre-commit check, and a real safety net
independent of what the agent's turn decides to do.
"""

from __future__ import annotations

from google.adk.agents.context import Context
from google.adk.agents.llm_agent import Agent
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext

from adk_bmad import config
from adk_bmad.agents._context import PROJECT_ROOT
from adk_bmad.agents._gating import flag_gate, phase_gate
from adk_bmad.tools import git_tools, sprint_tools, story_tools


def record_story_committed(story_key: str, sha: str, tool_context: ToolContext) -> dict:
    """Record that `story_key` landed in commit `sha`, for this run's final report.
    Call this once, right after a successful `git_commit`."""
    completed = list(tool_context.state.get("completed_stories", []))
    if story_key not in completed:
        completed.append(story_key)
    tool_context.state["completed_stories"] = completed
    return {"story_key": story_key, "sha": sha, "completed_stories": completed}

_INSTRUCTION = f"""\
# Commit — original adk-bmad orchestration (not a BMAD skill)

You are the only phase in this loop allowed to run `git commit`. Every other
phase leaves its changes uncommitted so this story lands as ONE atomic commit:
implementation + review fixes + the story file's `Status: done` + sprint-status
`development_status[<story_key>] = done`, all together.

Story `{{current_story_key}}` has just cleared the review gate (zero
unresolved decision-needed/patch findings). Do the following, in order:

1. Re-assert completion: set the story file's status to "done"
   (`set_story_status`), and sprint-status's `development_status` entry for
   `{{current_story_key}}` to "done" (`set_development_status`). An earlier
   fresh-context phase may have left either in a non-final state — make both
   final now, before committing.
2. Write a Conventional Commits message: subject
   `feat({{current_story_key}}): <concise summary>`, plus a short body
   summarizing the key changes and the test result. Read `git_diff_stat` with
   project_root="{PROJECT_ROOT}" if you need the details.
3. Call `git_commit` with that message and project_root="{PROJECT_ROOT}".
   Never add an AI-attribution trailer (`Co-Authored-By:`, "Generated with
   Claude Code", or similar) — the tool also strips these defensively, but do
   not include one regardless. Author/committer stay as the repo's configured
   git user only.
4. If `git_commit` reports `committed: true`, call `record_story_committed`
   with the returned `sha`.

If `git_commit` reports `committed: false` with output "nothing to commit",
that's fine — everything was already committed by a prior pass; just confirm
both statuses read "done", call `record_story_committed` with sha="" (unknown,
already committed earlier), and end your turn.
"""


def _block_commit_unless_gate_clear(tool: BaseTool, args: dict, context: Context) -> dict | None:
    if tool.name == "git_commit" and not context.state.get("review_gate_clear"):
        return {"committed": False, "blocked": True, "reason": "review gate is not clear"}
    return None


def build_commit_agent() -> Agent:
    return Agent(
        name="commit",
        model=config.resolve_model("commit"),
        description="Finalizes statuses and creates the one atomic commit for a story that cleared review.",
        instruction=_INSTRUCTION,
        include_contents="none",
        before_agent_callback=[phase_gate("dev"), flag_gate("review_gate_clear", True)],
        before_tool_callback=_block_commit_unless_gate_clear,
        tools=[
            story_tools.set_story_status,
            sprint_tools.set_development_status,
            git_tools.git_diff_stat,
            git_tools.git_commit,
            record_story_committed,
        ],
    )
