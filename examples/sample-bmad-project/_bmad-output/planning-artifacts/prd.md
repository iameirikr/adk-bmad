# TinyTodo — Product Requirements

## Overview

TinyTodo is a minimal command-line to-do list, implemented in Python, used only
to demonstrate the adk-bmad implementation loop end to end. Keep every story
small — this project exists to be built by the agents, not to be a real
product.

## Functional requirements

FR1: `tinytodo add "<text>"` appends a new task to the list, stored in a local
`todos.json` file in the project root, with fields `id` (int, auto-incrementing),
`text` (str), and `done` (bool, default false).

FR2: `tinytodo list` prints every task, one per line, formatted as
`[ ] <id>: <text>` for incomplete tasks and `[x] <id>: <text>` for done tasks,
in ascending id order.

FR3: `tinytodo done <id>` marks the task with that id as done. If no task with
that id exists, print `No task with id <id>` and exit with a non-zero status.

## Non-functional requirements

NFR1: `todos.json` must not exist until the first `add` — `list`/`done` on a
project with no file yet behave as if the list is empty (for `list`) or report
"no task with id" (for `done`), never crash.

NFR2: Every command is covered by at least one automated test.
