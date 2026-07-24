"""Conditional execution within a static `SequentialAgent`.

ADK's template workflow agents (`SequentialAgent`/`ParallelAgent`/`LoopAgent`) run
a fixed sub-agent list — there's no built-in "if" branching (that's what the
newer graph-based Workflow Runtime adds, and its Python API is still too new to
build a public example repo's backbone on; see docs/architecture.md). The
idiomatic way to get conditional phases out of a fixed `SequentialAgent` is a
`before_agent_callback` that short-circuits: returning a non-None `Content`
skips that agent's own model turn entirely and that content becomes its output.

`bmad_loop.py`'s `story_cycle` runs every sub-agent on every `LoopAgent`
iteration; these gates make sure only the phase(s) relevant to the current
`state["phase"]` actually do anything each tick.
"""

from __future__ import annotations

from collections.abc import Callable

from google.adk.agents.context import Context
from google.genai import types


def _skipped(reason: str) -> types.Content:
    return types.Content(role="model", parts=[types.Part(text=f"(skipped — {reason})")])


def phase_gate(*expected_phases: str) -> Callable[[Context], types.Content | None]:
    """Skip this agent unless `state["phase"]` is one of `expected_phases`."""

    async def _gate(context: Context) -> types.Content | None:
        phase = context.state.get("phase")
        if phase in expected_phases:
            return None
        return _skipped(f'phase is {phase!r}, expected one of {expected_phases!r}')

    return _gate


def flag_gate(state_key: str, expected: bool = True) -> Callable[[Context], types.Content | None]:
    """Skip this agent unless `state[state_key]` (coerced to bool) equals `expected`."""

    async def _gate(context: Context) -> types.Content | None:
        if bool(context.state.get(state_key)) == expected:
            return None
        return _skipped(f"{state_key} != {expected}")

    return _gate
