# Contributing

Thanks for considering a contribution to adk-bmad. This is a fairly small, opinionated repo — read
[`docs/architecture.md`](docs/architecture.md) first to understand the shape before proposing a
change to it.

## Setup

```bash
uv sync --group dev
```

## Running checks

```bash
uv run pytest tests/unit       # fast — pure Python, no model calls, no BMAD project needed
uv run ruff check src tests scripts
```

`tests/eval/` has a scaffolded (currently empty) `adk eval` EvalSet for the review gate — see
`tests/eval/README.md` for how to populate it from a real recorded run (eval cases assert against
an actual trajectory, so we didn't hand-fabricate any). Contributions adding real eval cases here
— the review gate blocking a commit, the loop's completion condition, the complexity-based model
escalation — are very welcome. Run an eval set with:

```bash
uv run adk eval src tests/eval/<evalset>.evalset.json
```

## Adding a new phase/agent

1. If the phase corresponds to a real upstream BMAD skill, load its instructions via
   `adk_bmad.skills.load()`/`load_step()` (see `src/adk_bmad/agents/create_story.py` for the
   simple case, `src/adk_bmad/agents/review/triage.py` for loading a single step). Don't
   reimplement the skill's instructions in Python — that's exactly the drift problem this repo's
   loader design avoids (see `docs/architecture.md`).
2. If it's original orchestration (no upstream skill maps to it), write the instruction directly
   — see `src/adk_bmad/agents/select.py` or `commit.py` for the pattern, and say so in a docstring
   the way those two do.
3. Wrap the loaded/authored instruction with `adk_bmad.agents._prompting.wrap_instruction()` so it
   gets the shared autonomous-mode framing and tool-mapping header.
4. Give it a `before_agent_callback` from `adk_bmad.agents._gating` (`phase_gate(...)` or
   `flag_gate(...)`) if it should only run under specific conditions within a `story_cycle` tick.
5. Wire it into `src/adk_bmad/workflows/story_cycle.py` (or a new workflow file, for something more
   involved — see `workflows/review_gate.py` for a `ParallelAgent` + `SequentialAgent` example).
6. Add unit tests for any new pure-Python logic (a new tool, a new `state/` helper) under
   `tests/unit/` — these should never require a model call or a real BMAD project.

## Vendored BMAD skills

`src/adk_bmad/vendor/bmad-skills/` is a fallback copy used only when the target project doesn't
have BMAD-METHOD installed under `.claude/skills`/`.agents/skills`/`.codex/skills` — see
`docs/bmad-compatibility.md`. Refresh it with `scripts/sync_bmad_skills.py` pointed at a project
with a current BMAD-METHOD install; don't hand-edit the vendored files directly.

## Style

- `ruff` (config in `pyproject.toml`) is the source of truth for formatting/lint; run it before
  opening a PR.
- Docstrings that explain *why* something is the way it is (a design tradeoff, a correction versus
  archon-bmad's approach, an upstream quirk being worked around) are welcome and encouraged in this
  repo specifically, since the whole point is to be a legible example of ADK patterns — but avoid
  restating what the code already makes obvious.

## Reporting issues

Open a GitHub issue. If it's about BMAD-METHOD's own skill behavior (not this repo's ADK
integration), it likely belongs upstream at
[`bmad-code-org/BMAD-METHOD`](https://github.com/bmad-code-org/BMAD-METHOD) instead.
