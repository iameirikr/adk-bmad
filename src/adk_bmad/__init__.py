"""adk-bmad: the BMAD-METHOD implementation loop as native Google ADK 2.0 agents.

Deliberately does NOT import `agent` here — ADK's CLI (`adk web`/`adk run`)
discovers `root_agent` by importing `adk_bmad.agent` directly, and keeping this
package's `__init__.py` empty lets `adk_bmad.state`/`adk_bmad.tools`/
`adk_bmad.skills`/`adk_bmad.config` be imported and unit-tested on their own,
without requiring a configured BMAD project or model credentials.
"""
