# TinyTodo — sample BMAD project

A deliberately tiny BMAD-METHOD project (one epic, two stories, zero real
product value) bundled so `adk web` / `adk run` works the moment you clone
adk-bmad — no BMAD-METHOD install, no API keys beyond a model provider key,
no existing codebase required.

- `_bmad/bmm/config.yaml` — BMAD project config (paths, project name).
- `_bmad-output/planning-artifacts/` — `prd.md`, `architecture.md`, `epics.md`.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — both stories
  start `backlog`.

Point adk-bmad at this directory (the default when you run `adk web`/`adk run`
from the adk-bmad repo root and haven't set `ADK_BMAD_PROJECT_ROOT`) and try:

> implement epic 1

It will create both stories, implement `tinytodo.py` + `test_tinytodo.py`
directly in this directory, run them through the parallel adversarial review
gate, commit each story, and run the epic-1 retrospective. A `.git` repo is
bootstrapped here automatically on first run if one doesn't exist yet.
