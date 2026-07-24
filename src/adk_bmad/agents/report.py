"""The final `report` step — original adk-bmad orchestration, not a BMAD skill.

Runs once, after `bmad_loop` finishes, and summarizes the run from session
state and git history — mirroring archon-bmad's own cheap final-summary node.
"""

from __future__ import annotations

from google.adk.agents.llm_agent import Agent
from google.adk.utils.instructions_utils import inject_session_state

from adk_bmad import config
from adk_bmad.agents._context import BMAD_CONFIG, PROJECT_ROOT
from adk_bmad.tools import git_tools, sprint_tools

_STATIC_TEXT = f"""\
# Run report

Summarize this adk-bmad run for the user. You have:

- `completed_stories` (this run): {{completed_stories?}}
- `completed_epics` (this run): {{completed_epics?}}
- `escalated_stories` (needs a human — review-retry budget exhausted): {{escalated_stories?}}
- `run_status`: {{run_status?}}

Call `read_sprint_status` (sprint_status_path="{BMAD_CONFIG.sprint_status}") for
final per-story/epic status, and `git_log` (project_root="{PROJECT_ROOT}",
max_count=30) for the commits this run produced.

Write a concise markdown report with these sections:

### Outcome
Final run status, and — if any stories are in `escalated_stories` — call that
out clearly with the reason each was escalated.

### Stories
A table of every story touched this run: final sprint-status, and whether it
was committed.

### Epics & retrospectives
Which epics completed, and which had a retrospective run.

### Next steps
Anything a human should look at: escalated stories, and how to inspect/verify
the commits (`git -C {PROJECT_ROOT} log --oneline -n 30`).

Output the report directly as your response.
"""


async def _instruction(readonly_context) -> str:
    return await inject_session_state(_STATIC_TEXT, readonly_context)


def build_report_agent() -> Agent:
    return Agent(
        name="report",
        model=config.resolve_model("report"),
        description="Summarizes the run once the story/epic loop finishes.",
        instruction=_instruction,
        include_contents="none",
        tools=[sprint_tools.read_sprint_status, git_tools.git_log],
    )
