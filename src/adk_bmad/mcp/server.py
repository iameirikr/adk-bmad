"""Optional: expose adk-bmad's tools as an MCP server via FastMCP.

Not on the core `adk web`/`adk run` story-cycle path — this is a starting point
for the "expose ADK tools as an MCP server" pattern the docs describe (see
docs/architecture.md's "Not yet used" section), so e.g. Claude Code or another
MCP client could call `find_next_story`/`read_sprint_status`/etc. directly.

Requires the optional `mcp` extra: `uv sync --extra mcp`.

Run with: `uv run --extra mcp python -m adk_bmad.mcp.server`
"""

from __future__ import annotations

from adk_bmad.tools import sprint_tools, story_tools

TOOLS = (
    sprint_tools.read_sprint_status,
    sprint_tools.get_development_status,
    sprint_tools.stories_in_epic,
    sprint_tools.epic_fully_done,
    story_tools.read_text_file,
    story_tools.story_exists,
    story_tools.get_story_status,
)


def main() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise SystemExit(
            "The 'mcp' extra isn't installed. Run: uv sync --extra mcp"
        ) from exc

    server = FastMCP("adk-bmad")
    for tool in TOOLS:
        server.add_tool(tool)
    server.run()


if __name__ == "__main__":
    main()
