# TinyTodo — Architecture

## AD-1: Single-file CLI, no dependencies

`tinytodo.py` at the project root is the entire application — a single Python
3 file using only the standard library (`argparse`, `json`, `pathlib`). No
third-party dependencies, no package layout — this is intentionally the
smallest possible real codebase for demonstrating the adk-bmad loop.

## AD-2: Storage format

Tasks are stored in `todos.json` at the project root as a JSON array of
objects: `{"id": int, "text": str, "done": bool}`. `tinytodo.py` reads the
whole file, mutates the in-memory list, and rewrites the whole file on every
command that changes state (`add`, `done`) — no partial writes, no locking
needed for this scale.

## AD-3: Testing

Tests live in `test_tinytodo.py` at the project root, using `unittest` (stdlib,
no pytest dependency) so the project truly has zero third-party deps. Each test
should use a temporary directory (`tempfile.TemporaryDirectory`) for
`todos.json` so tests never touch a real file or interfere with each other.

## AD-4: CLI entry point

`if __name__ == "__main__":` at the bottom of `tinytodo.py` calls a `main()`
function that parses `sys.argv` via `argparse` with three subcommands: `add`,
`list`, `done`. `python3 tinytodo.py add "buy milk"` is the invocation shape.
