"""Shared instruction scaffolding for every agent whose domain instructions are
loaded from a real upstream BMAD skill (`skills.load`/`skills.load_step`).

Every such agent needs the same three things bolted on top of the raw skill
text: (1) an explicit autonomous-mode framing, since the upstream skills were
written assuming an interactive human on the other end and this loop has none;
(2) a mapping from the tools the skill text assumes (a coding-agent IDE's
Read/Write/Edit/Bash) to this repo's actual FunctionTools; (3) this run's fixed
paths. `{current_story_key}`/`{current_epic_key}`-style placeholders in the
footer are resolved from session state at call time via
`inject_session_state` — the story/epic being worked on changes every
iteration, unlike the paths above.
"""

from __future__ import annotations

from collections.abc import Callable

from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.utils.instructions_utils import inject_session_state

from adk_bmad.agents._context import BMAD_CONFIG, PROJECT_ROOT

_HEADER = f"""\
# Autonomous mode (#YOLO)

You are running fully autonomously inside a BMAD implementation loop — there is
no human to ask. Wherever the instructions below say to ask the user, present a
menu, or HALT and wait for a choice, instead make the most reasonable
autonomous decision yourself (from sprint-status.yaml, the story file, the PRD,
the architecture doc, and prior stories) and continue. Never stop for
"milestones" or "session boundaries" — finish this phase in one turn, using as
many tool calls as you need.

# Tool mapping

You have these tools in place of a coding-agent IDE's built-ins:
- `read_text_file(path)` / `write_text_file(path, content)` /
  `edit_text_file(path, old_string, new_string, replace_all=False)` instead of
  Read/Write/Edit.
- `list_directory(path)` instead of a directory-listing tool.
- `run_command(command, cwd)` instead of a Bash tool — `cwd` should almost
  always be the project_root below.
- Whenever these instructions say to update `development_status` in
  sprint-status.yaml, call the `set_development_status` tool instead of
  hand-editing the YAML — it preserves every comment and the file's structure.
- Whenever these instructions say to update a story file's `Status:` line, call
  the `set_story_status` tool instead of hand-editing that line.

# This run's fixed paths

- project_root = "{PROJECT_ROOT}"
- sprint_status = "{BMAD_CONFIG.sprint_status}"
- implementation_artifacts = "{BMAD_CONFIG.implementation_artifacts}"
- planning_artifacts = "{BMAD_CONFIG.planning_artifacts}"

---

"""


def wrap_instruction(skill_text: str, *, footer: str = "") -> Callable[[ReadonlyContext], str]:
    """Build an ADK instruction-provider: header + loaded skill text + a footer
    that may reference session-state placeholders (e.g. `{current_story_key}`),
    resolved fresh on every call via `inject_session_state`.
    """
    static_text = _HEADER + skill_text
    if footer:
        static_text += f"\n\n---\n\n{footer}"

    async def _provider(readonly_context: ReadonlyContext) -> str:
        return await inject_session_state(static_text, readonly_context)

    return _provider
