# TinyTodo — Epic Breakdown

## Epic 1 — Core to-do commands (AD-1..AD-4)

Implements the whole PRD in three small, sequential stories sharing one file.

### Story 1.1: Add and list tasks

As a user,
I want to add a task and list all tasks,
So that I can keep track of what I need to do.

Acceptance criteria:
1. Given no `todos.json` exists, when I run `tinytodo.py list`, then it prints
   nothing and exits 0 (empty list, no crash — NFR1).
2. Given I run `tinytodo.py add "buy milk"`, then `todos.json` is created (if
   absent) containing one task: `id=1`, `text="buy milk"`, `done=false`.
3. Given one task exists, when I run `tinytodo.py add "walk dog"`, then a
   second task is appended with `id=2` (auto-incrementing, never reusing ids).
4. Given two tasks exist, when I run `tinytodo.py list`, then it prints:
   ```
   [ ] 1: buy milk
   [ ] 2: walk dog
   ```
5. Automated tests cover: listing with no file, adding the first task, adding a
   second task, and listing after two adds (NFR2).

Depends on: nothing (first story).

### Story 1.2: Mark tasks done

As a user,
I want to mark a task as done,
So that my list reflects what's actually left to do.

Acceptance criteria:
1. Given task id 1 exists, when I run `tinytodo.py done 1`, then task 1's
   `done` field becomes `true` and this is persisted to `todos.json`.
2. Given task 1 is done and task 2 is not, when I run `tinytodo.py list`, then
   it prints `[x] 1: buy milk` and `[ ] 2: walk dog`.
3. Given no task with id 99 exists, when I run `tinytodo.py done 99`, then it
   prints `No task with id 99` and exits with a non-zero status (FR3, NFR1).
4. Automated tests cover: marking an existing task done, listing after done,
   and the not-found case (NFR2).

Depends on: Story 1.1 (needs add/list working first).
