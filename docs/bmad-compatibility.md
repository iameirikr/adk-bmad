# BMAD-METHOD compatibility

adk-bmad targets projects using [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)'s
BMM module, confirmed against a real BMM v6.8.0 project. If your project's
files look like the below, adk-bmad should work against it as-is.

## Required layout

```
<your-project>/
├── _bmad/
│   └── bmm/
│       └── config.yaml              # BMAD project config (paths, project name, ...)
├── _bmad-output/                    # default output_folder; configurable
│   ├── planning-artifacts/
│   │   ├── prd.md
│   │   ├── architecture.md
│   │   └── epics.md
│   └── implementation-artifacts/
│       ├── sprint-status.yaml       # the source of truth
│       └── <epic>-<story>-<slug>.md # one file per story
└── .claude/skills/  (or .agents/skills/ or .codex/skills/)
    ├── bmad-create-story/
    ├── bmad-dev-story/
    ├── bmad-code-review/
    ├── bmad-review-adversarial-general/
    ├── bmad-review-edge-case-hunter/
    ├── bmad-qa-generate-e2e-tests/   (optional)
    └── bmad-retrospective/
```

The skills directory is what `src/adk_bmad/skills.py` loads instructions from
at runtime (see `docs/architecture.md`). If your project doesn't have these
installed under any of the three roots, adk-bmad falls back to the vendored
copy under `src/adk_bmad/vendor/bmad-skills/` (see below) — but a live project
install is preferred, since it's whatever version you actually have.

## `_bmad/bmm/config.yaml`

Fields adk-bmad reads (`src/adk_bmad/config.py::load_bmad_config`):

| Field | Default if absent |
|---|---|
| `output_folder` | `{project-root}/_bmad-output` |
| `implementation_artifacts` | `<output_folder>/implementation-artifacts` |
| `planning_artifacts` | `<output_folder>/planning-artifacts` |
| `project_knowledge` | `{project-root}/docs` |
| `user_name`, `project_name` | `"there"`, `"this project"` |
| `communication_language`, `document_output_language` | `"English"` |
| `user_skill_level` | `"intermediate"` |

`{project-root}` in any of these values is expanded to the actual absolute
path — BMAD writes it as a literal placeholder, not a template variable.

## `sprint-status.yaml`

The single source of truth for progress. adk-bmad never trusts an agent's
belief that something "looks done" over what this file says, and only ever
writes to it through `src/adk_bmad/state/sprint_status.py`, which preserves
every comment and the file's structure (via `ruamel.yaml` round-trip mode).

```yaml
development_status:
  epic-1: backlog | in-progress | done
  1-1-some-story-slug: backlog | ready-for-dev | in-progress | review | done
  epic-1-retrospective: optional | done
```

Story keys follow `<epic-number>-<story-number>-<slug>` (e.g.
`2-3-currency-service`). Epic keys are `epic-<N>`. A retrospective key is
`epic-<N>-retrospective`.

## Story file format

One markdown file per story under `implementation_artifacts`, named
`<story-key>.md`:

```markdown
---
baseline_commit: <sha, set on first dev pass>
---

# Story N.M: <title>

Status: ready-for-dev | in-progress | review | done

## Story
As a <role>, I want <capability>, so that <benefit>.

## Acceptance Criteria
1. Given ..., when ..., then ...

## Tasks / Subtasks
- [ ] Task 1: ...
  - [ ] Subtask
- [ ] [AI-Review] <follow-up from a review pass>

## Dev Notes
<architecture/context guidance for the implementer>

## Dev Agent Record
### Agent Model Used
### Debug Log References
### Completion Notes List
### File List

## Change Log
| Date | Change |
|---|---|
```

adk-bmad's `state/story_file.py` only mechanically touches the YAML
frontmatter and the `Status:` line — every other section is authored and
maintained by the LLM agents themselves (following the loaded skill
instructions), the same way a human developer would edit the file directly.

## Vendored skill fallback

`src/adk_bmad/vendor/bmad-skills/` ships a copy of the skills above (vendored
from a real BMM v6.8.0 install — see `MANIFEST.json` in that directory for
exact provenance), used only when the target project doesn't have BMAD-METHOD
installed under any of the three skill roots — chiefly so the bundled
`examples/sample-bmad-project` works with `adk web` out of the box. Refresh it
from a project with a newer BMAD-METHOD install:

```bash
uv run python scripts/sync_bmad_skills.py /path/to/a/bmad-method/project --bmm-version 6.9.0
```

This never affects a real project run — a live `.claude/skills/` (or
`.agents/`/`.codex/`) install always takes priority.
