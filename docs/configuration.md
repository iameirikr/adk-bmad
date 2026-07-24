# Configuration

Every knob is an environment variable — no code changes needed to point
adk-bmad at a different project, swap models, or tune retry limits.

## Which project

| Variable | Default |
|---|---|
| `ADK_BMAD_PROJECT_ROOT` | cwd if it has `_bmad/bmm/config.yaml`, else `./examples/sample-bmad-project` if that exists, else cwd (and you'll get a descriptive error) |

Set this to point adk-bmad at any BMAD-METHOD project, from anywhere:

```bash
ADK_BMAD_PROJECT_ROOT=/path/to/your/project adk web src
```

## Model tiers

Every agent's model is one config value (`src/adk_bmad/config.py`), resolved
per-agent role so the fleet can be deliberately mixed — a cheap model for
select/triage/report-shaped agents, a heavier one for dev-story and the
adversarial reviewers, mirroring both archon-bmad's own
opus-for-heavy/haiku-for-report split and upstream `bmad-story-automator`'s
complexity-based agent routing.

| Role | Default model | Env var to override |
|---|---|---|
| `select` | `gemini-2.5-flash` | `ADK_BMAD_MODEL_SELECT` |
| `create_story` | `gemini-2.5-pro` | `ADK_BMAD_MODEL_CREATE_STORY` |
| `dev_story` | `gemini-2.5-flash` | `ADK_BMAD_MODEL_DEV_STORY` |
| `dev_story_heavy` | `gemini-2.5-pro` | `ADK_BMAD_MODEL_DEV_STORY_HEAVY` |
| `test_gen` | `gemini-2.5-flash` | `ADK_BMAD_MODEL_TEST_GEN` |
| `blind_hunter` | `gemini-2.5-pro` | `ADK_BMAD_MODEL_BLIND_HUNTER` |
| `edge_case_hunter` | `gemini-2.5-pro` | `ADK_BMAD_MODEL_EDGE_CASE_HUNTER` |
| `acceptance_auditor` | `gemini-2.5-pro` | `ADK_BMAD_MODEL_ACCEPTANCE_AUDITOR` |
| `triage` | `gemini-2.5-flash` | `ADK_BMAD_MODEL_TRIAGE` |
| `commit` | `gemini-2.5-flash` | `ADK_BMAD_MODEL_COMMIT` |
| `retrospective` | `gemini-2.5-flash` | `ADK_BMAD_MODEL_RETROSPECTIVE` |
| `report` | `gemini-2.5-flash` | `ADK_BMAD_MODEL_REPORT` |

`dev_story_heavy` is used automatically, not directly — `dev_story` starts on
the cheap tier and a `before_model_callback` escalates it per-story when
`tools/complexity.py`'s scorer flags a story as complex (see
`docs/architecture.md`).

**Any other provider ADK supports via [LiteLLM](https://docs.litellm.ai/)**
works as a drop-in replacement for any single role — set the env var to a
LiteLLM-style `<provider>/<model>` string instead of a bare `gemini-*` id:

```bash
ADK_BMAD_MODEL_DEV_STORY=anthropic/claude-opus-4-6 adk web src
```

This requires the corresponding provider credentials (`ANTHROPIC_API_KEY`,
etc.) in the environment; see [LiteLLM's provider docs](https://docs.litellm.ai/docs/providers)
for the exact env vars each provider expects.

## Loop knobs

| Variable | Default | Meaning |
|---|---|---|
| `ADK_BMAD_MAX_REVIEW_RETRIES` | `8` | Review-gate passes before a story is escalated instead of retried again |
| `ADK_BMAD_MAX_CREATE_RETRIES` | `2` | (reserved for future create-story retry handling) |
| `ADK_BMAD_MAX_STORY_ITERATIONS` | `150` | Outer `LoopAgent` safety valve across the whole run |
| `ADK_BMAD_SKIP_TEST_GEN` | unset | Set to `1`/`true`/`yes` to skip the optional test-generation phase even if `bmad-qa-generate-e2e-tests` is installed |

## Model provider credentials

- **Gemini (default)**: `GOOGLE_API_KEY` (or Vertex AI application-default
  credentials — see [ADK's model docs](https://google.github.io/adk-docs/agents/models/)).
- **Any LiteLLM provider**: whatever that provider needs — see
  [LiteLLM's provider docs](https://docs.litellm.ai/docs/providers).

## Security note

adk-bmad is designed to write and execute code in the project you point it at
(`tools/exec_tools.py::run_command` runs arbitrary shell commands the agents
choose — installs, linters, test suites). This is the same trust model as any
autonomous coding agent (Claude Code, the upstream BMAD skills, archon-bmad).
Only point `ADK_BMAD_PROJECT_ROOT` at a project/environment you'd extend that
same trust to.
