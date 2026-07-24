# adk-bmad

**The [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) implementation loop, built as
native [Google ADK 2.0](https://github.com/google/adk-python) agents and workflows.**

Point it at a BMAD-planned project (PRD, architecture, epics, `sprint-status.yaml` already in
place) and it runs **create story → dev story → optional test generation → parallel adversarial
review → commit → per-epic retrospective**, autonomously, across a single story, a range of
stories, or an entire epic — using real ADK primitives (`SequentialAgent` / `ParallelAgent` /
`LoopAgent`, tools, callbacks, sessions) rather than a bash state machine.

adk-bmad is a sibling project to [archon-bmad](https://github.com/iameirikr/archon-bmad) (same
author), which built this same loop as a single [Archon](https://archon.diy) workflow. This repo
decomposes it into ADK's actual multi-agent building blocks instead — see
[`docs/architecture.md`](docs/architecture.md) for why, and what that buys you (a real parallel
adversarial review fan-out instead of one inlined reviewer prompt, dynamic per-story model
routing, a genuine commit-gating callback, and instructions loaded live from your BMAD-METHOD
install instead of forked into this repo).

---

## 60-second quickstart

```bash
git clone https://github.com/iameirikr/adk-bmad.git
cd adk-bmad
uv sync
export GOOGLE_API_KEY=...   # https://aistudio.google.com/apikey
adk web src
```

Open the printed URL, pick **adk_bmad**, and try:

> implement epic 1

That runs against the bundled `examples/sample-bmad-project` (a two-story
sample project) — no BMAD-METHOD install, no existing codebase, no extra setup. It will create
both stories, implement them, run the parallel review gate, commit each one, and run the epic
retrospective, right there in that directory.

To run it against your own BMAD-METHOD project instead:

```bash
ADK_BMAD_PROJECT_ROOT=/path/to/your/project adk web src
```

Or from the terminal instead of the web UI: `adk run src`. Or as an HTTP API: `adk api_server src`.

## What it automates

| Phase | What happens | Instructions from |
|---|---|---|
| `select` | Reads `sprint-status.yaml`, decides the next story/epic to work on | original adk-bmad orchestration |
| `create_story` | Writes the next story file (exhaustive PRD/architecture/epic/previous-story/git analysis) | `bmad-create-story` |
| `dev_story` | Implements every task, red-green-refactor, until the story is done | `bmad-dev-story` |
| `test_gen` *(optional)* | Generates/augments end-to-end tests | `bmad-qa-generate-e2e-tests` |
| review gate | **Three adversarial reviewers in parallel** (diff-only, edge-case, acceptance-criteria) + a triage step that dedupes, classifies, auto-fixes, and decides the commit gate | `bmad-review-adversarial-general`, `bmad-review-edge-case-hunter`, `bmad-code-review` |
| `commit` | One atomic commit per story, only once the review gate is clear | original adk-bmad orchestration |
| `retrospective` | Fires once per epic when every story in it is done; non-blocking | `bmad-retrospective` |

adk-bmad does **not** reimplement BMAD's domain instructions — it loads the real upstream skill
files at runtime (see [`docs/architecture.md`](docs/architecture.md#instructions-are-loaded-from-real-bmad-method-skills-not-reimplemented)),
so updating BMAD-METHOD in your project is all it takes to pick up new instructions here too.

## Why this leans into ADK 2.0

- **A real parallel fan-out for review.** The three adversarial reviewers run as a genuine
  `ParallelAgent`, not three sequential calls or one crammed-together prompt — this is the direct
  ADK-native shape of upstream `bmad-code-review`'s own parallel layers.
- **Dynamic per-story model routing.** A `before_model_callback` escalates `dev_story` from a
  cheap default model to a heavier one, per story, based on a complexity score computed after
  `create_story` runs — not a static config choice.
- **A commit gate enforced via callbacks, twice.** A `before_agent_callback` skips the entire
  commit turn unless the review gate is clear, and a `before_tool_callback` independently refuses
  the `git_commit` tool call itself under the same condition.
- **Conditional phases inside a static workflow graph**, via `before_agent_callback` short-circuits
  — no bash `state.json` polling loop.
- **Sessions/state/artifacts done the ADK way** — ephemeral run state lives in `session.state`;
  `sprint-status.yaml`/story files on disk stay the actual source of truth.

See [`docs/architecture.md`](docs/architecture.md) for the full design, including what's
deliberately *not* used yet (the newer graph-based Workflow Runtime, MCP server exposure, A2A) and
why.

## Configuration

Every model, retry limit, and target project is one environment variable — see
[`docs/configuration.md`](docs/configuration.md). Quick taste:

```bash
# Use Claude for the heavy implementation phase instead of Gemini
ADK_BMAD_MODEL_DEV_STORY=anthropic/claude-opus-4-6 adk web src

# Point at a real project, skip the optional test-gen phase
ADK_BMAD_PROJECT_ROOT=~/code/my-app ADK_BMAD_SKIP_TEST_GEN=1 adk run src
```

## Requirements

- Python 3.11+, [`uv`](https://docs.astral.sh/uv/).
- A BMAD-METHOD project with planning complete — `_bmad/bmm/config.yaml` and
  `<implementation_artifacts>/sprint-status.yaml` both present (or just use the bundled sample
  project). See [`docs/bmad-compatibility.md`](docs/bmad-compatibility.md) for the exact schema.
- BMAD-METHOD's skill files installed in that project under `.claude/skills/`, `.agents/skills/`,
  or `.codex/skills/` — the same discovery archon-bmad uses. Not present? adk-bmad falls back to a
  vendored copy (fine for trying things out; see `docs/bmad-compatibility.md` to keep it current).
- A model provider credential — `GOOGLE_API_KEY` by default, or any
  [LiteLLM](https://docs.litellm.ai/docs/providers)-supported provider's credentials.

## Development

```bash
uv sync --group dev
uv run pytest tests/unit      # fast, no model calls
uv run ruff check src tests scripts
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for how to add a new phase/agent.

## Credits & license

`adk-bmad` loads instructions from [`bmad-code-org/BMAD-METHOD`](https://github.com/bmad-code-org/BMAD-METHOD)
(MIT) and is built on [`google/adk-python`](https://github.com/google/adk-python) (Apache-2.0) —
see [`NOTICE`](NOTICE) for full attribution. This repository is MIT-licensed — see
[`LICENSE`](LICENSE).

`adk-bmad` is not affiliated with or endorsed by Google, BMAD-METHOD, or `bmad-code-org`.
