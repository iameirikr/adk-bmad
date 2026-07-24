# Architecture

adk-bmad automates the BMAD-METHOD implementation loop — **create story → dev
story → (optional) generate tests → parallel adversarial review → commit →
per-epic retrospective** — as a tree of real [Google ADK
2.0](https://github.com/google/adk-python) agents, runnable against a story, a
range of stories, or an entire epic.

This is a sibling project to [archon-bmad](https://github.com/iameirikr/archon-bmad)
(same author), which built the same loop as a single Archon workflow — a
`loop:` node driven by a bash/`state.json` state machine. adk-bmad instead
decomposes the loop into ADK's actual multi-agent primitives
(`SequentialAgent`/`ParallelAgent`/`LoopAgent`, tools, callbacks, session
state), because the point of this repo is to show what BMAD looks like built
*with* ADK's building blocks, not just ported to a different YAML dialect.

## The agent tree

```
SequentialAgent(adk_bmad)                          <- root_agent
├── LoopAgent(bmad_loop)                            one iteration per phase
│   └── SequentialAgent(story_cycle)
│       ├── select                                  always runs; decides the phase
│       ├── create_story          [gated: phase == "create"]
│       ├── dev_story             [gated: phase == "dev"]
│       ├── test_gen              [gated: phase == "dev", optional]
│       ├── SequentialAgent(review_gate)  [gated: phase == "dev"]
│       │   ├── ParallelAgent(adversarial_reviewers)
│       │   │   ├── blind_hunter          (diff only)
│       │   │   ├── edge_case_hunter      (diff + read access)
│       │   │   └── acceptance_auditor    (diff + spec)
│       │   └── review_triage              normalize, dedupe, classify, fix, gate
│       ├── commit                [gated: phase == "dev" AND review_gate_clear]
│       └── retrospective         [gated: phase == "retro", non-blocking]
└── report                                          runs once, after the loop
```

See `src/adk_bmad/agent.py` for the literal construction and
`src/adk_bmad/workflows/` for how the pieces are composed.

## Design decisions

### Instructions are loaded from real BMAD-METHOD skills, not reimplemented

A BMAD "skill" (`SKILL.md` + `steps/*.md` + `checklist.md`/`template.md`) is
plain markdown using simple `<action>`/`<check>` pseudo-XML — not code tied to
any particular agentic CLI. `src/adk_bmad/skills.py` loads that markdown at
runtime and uses it as an ADK `LlmAgent`'s `instruction=`, resolved against
whichever of `.claude/skills/`, `.agents/skills/`, or `.codex/skills/` the
target project has BMAD-METHOD installed under (falling back to a vendored
copy — see below). When you update BMAD-METHOD in your project, the next
adk-bmad run picks up the new instructions automatically — no manual
re-porting, no drift.

| Agent | Instruction source |
|---|---|
| `create_story` | `bmad-create-story` (verbatim) |
| `dev_story` | `bmad-dev-story` (verbatim) |
| `test_gen` | `bmad-qa-generate-e2e-tests` (verbatim, optional) |
| `blind_hunter` | `bmad-review-adversarial-general` (verbatim) |
| `edge_case_hunter` | `bmad-review-edge-case-hunter` (verbatim) |
| `acceptance_auditor` | a short prompt quoted from `bmad-code-review/steps/step-02-review.md` (upstream doesn't ship this layer as its own skill file) |
| `review_triage` | `bmad-code-review/steps/step-03-triage.md` (verbatim) |
| `retrospective` | `bmad-retrospective` (verbatim) |
| `select`, `commit`, `report` | **original adk-bmad orchestration** — there's no single upstream skill for "which phase runs next," so these are written directly (the same role archon-bmad's own `select` phase and `orchestrator-rules.md` play) |

See `docs/bmad-compatibility.md` for the vendoring/sync mechanism and NOTICE for
attribution.

### The review gate matches upstream's own severity model, not archon-bmad's

Upstream `bmad-code-review` classifies findings as `decision_needed` / `patch`
/ `defer` / `dismiss` — not the `CRITICAL`/`HIGH`/`MEDIUM`/`LOW` taxonomy
archon-bmad's inlined reviewer invented for the Archon port. Since adk-bmad
loads `bmad-code-review`'s real triage step verbatim, it uses upstream's actual
categories: the commit gate is **zero unresolved `decision_needed` and zero
unresolved `patch` findings** (`defer`/`dismiss` never block). Upstream's own
next step is interactive (it HALTs to ask a human how to handle `decision_needed`
and `patch` findings, offering "apply every patch" as the default). Since this
loop is autonomous, `review_triage` is instructed to make the call that
option would: resolve `decision_needed` findings from available context and
always apply every `patch` finding itself (fix the code, adjust tests, re-run
them) — see `src/adk_bmad/agents/review/triage.py`.

### Conditional phases inside a static `SequentialAgent`

ADK's template workflow agents (`SequentialAgent`/`ParallelAgent`/`LoopAgent`)
run a fixed sub-agent list — there's no built-in "if" branching (ADK 2.0 adds a
lower-level graph-based Workflow Runtime that does, but its Python API is still
thin in the docs; see "Not yet used" below). The idiomatic way to get
conditional phases out of a fixed `SequentialAgent` is a `before_agent_callback`
that returns a non-`None` `Content` to skip that agent's own turn entirely —
see `src/adk_bmad/agents/_gating.py`. `story_cycle` runs every sub-agent on
every `LoopAgent` iteration; the gates make sure only the phase(s) relevant to
`state["phase"]` (set by `select`) actually do anything each tick.

### One phase per `LoopAgent` iteration, `select` re-derives it every time

`select` reads `sprint-status.yaml` fresh every iteration — never trusting a
previous iteration's belief that a phase "looks done" — and decides exactly one
of `create` / `dev` / `retro` / `complete`. Within a `dev` iteration,
`dev_story` → `test_gen` → `review_gate` → `commit` all run in sequence and,
if review clears, the story lands as one commit in that same iteration. If
review does *not* clear, `commit`'s gate simply doesn't open; the next
`LoopAgent` iteration starts over at `select`, which re-derives `dev` for the
*same* story (sprint-status still shows it not-`done`) — this is what drives
the review-retry loop, using a `review_retry_count` in session state rather
than a nested loop. After `max_review_retries` (default 8) failed passes, the
story is escalated (recorded in session state, surfaced in the final report)
rather than retried forever — `select` skips escalated stories when picking
the next target, matching archon-bmad's own escalation behavior.

### Dynamic per-story model routing

`tools/complexity.py` ports upstream `bmad-story-automator`'s regex/structural
complexity scorer. `create_story` scores the story it just wrote and records a
`"standard"`/`"heavy"` tier in session state; `dev_story`'s
`before_model_callback` (`agents/dev_story.py`) mutates `LlmRequest.model` in
place to escalate to a heavier configured model when the story was scored
complex — genuine dynamic routing per story, not just a static config choice.

### `include_contents="none"` everywhere — a fresh turn per phase

Every phase agent sets `include_contents="none"`, so it gets no prior
conversation history — matching archon-bmad's `fresh_context: true` and, more
importantly, matching how these BMAD skills are written: each one insists on
reading the *complete* current file state itself ("read the FULL sprint-status
file", "read the COMPLETE story file") rather than trusting memory of a prior
turn. This also keeps a long multi-story run's context bounded.

### The commit gate is enforced twice

`commit`'s `before_agent_callback` skips its entire turn unless
`state["review_gate_clear"]` is true (so the model never even runs when it
shouldn't) — and its `before_tool_callback` *additionally* refuses the
`git_commit` tool call itself under the same condition, independent of what the
agent's turn decides to do. See `src/adk_bmad/agents/commit.py`.

### Sessions, state, and artifacts

`sprint-status.yaml` and story files on disk remain the actual source of
truth — read/written through typed helpers (`src/adk_bmad/state/`) that
preserve YAML comments and file structure. ADK `session.state` carries only
this run's ephemeral state (current phase/story/epic, retry counters, review
findings) between `story_cycle`'s steps. A production deployment can swap
`InMemorySessionService`/`InMemoryArtifactService` for database/GCS-backed
services without any agent code changing — that's the whole point of ADK's
service abstraction.

## Not yet used (candidates for future work)

- **The graph-based Workflow Runtime.** ADK 2.0 added a lower-level
  alternative to `SequentialAgent`/`ParallelAgent`/`LoopAgent` with native
  conditional routing and retry/backoff — it could replace the
  `before_agent_callback` gating above with first-class branches. Its Python
  API is still thin in the current docs; worth adopting once it's better
  documented.
- **MCP server exposure.** `src/adk_bmad/mcp/server.py` sketches exposing this
  repo's tools as an MCP server (via FastMCP) so e.g. Claude Code could call
  into them directly — ADK's MCP support is first-class, but this isn't on the
  core story-cycle path.
- **A2A.** Individual agents (e.g. `dev_story`) could be exposed over the
  Agent2Agent protocol for cross-organization reuse — not needed for a
  single-repo loop, but a natural extension point.
- **Git worktree isolation**, the way archon-bmad uses Archon's worktree
  feature — out of scope for v1; run adk-bmad in a branch/worktree you create
  yourself if you want that isolation today.
- **Planning-phase workflows** (PRD/architecture/epics generation) — this repo
  covers the *implementation* loop only, mirroring archon-bmad's own scope so
  far.
