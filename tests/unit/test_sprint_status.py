from pathlib import Path

import pytest

from adk_bmad.state import sprint_status

SAMPLE = """\
# generated: 2026-07-24
# STATUS DEFINITIONS:
# ==================
# comment preserved above the data

generated: 2026-07-24
last_updated: 2026-07-24
project: TinyTodo

development_status:
  epic-1: backlog
  1-1-add-and-list-tasks: backlog
  1-2-mark-tasks-done: backlog
  epic-1-retrospective: optional
"""


@pytest.fixture
def sprint_status_path(tmp_path: Path) -> Path:
    path = tmp_path / "sprint-status.yaml"
    path.write_text(SAMPLE)
    return path


def test_development_status_parses_all_keys(sprint_status_path: Path):
    status = sprint_status.development_status(sprint_status_path)
    assert status == {
        "epic-1": "backlog",
        "1-1-add-and-list-tasks": "backlog",
        "1-2-mark-tasks-done": "backlog",
        "epic-1-retrospective": "optional",
    }


def test_get_status_missing_key_returns_none(sprint_status_path: Path):
    assert sprint_status.get_status(sprint_status_path, "no-such-key") is None


def test_set_status_updates_key_and_preserves_comments(sprint_status_path: Path):
    previous = sprint_status.set_status(sprint_status_path, "1-1-add-and-list-tasks", "ready-for-dev")
    assert previous == "backlog"

    text = sprint_status_path.read_text()
    assert "STATUS DEFINITIONS" in text  # comment block preserved
    assert sprint_status.get_status(sprint_status_path, "1-1-add-and-list-tasks") == "ready-for-dev"
    # untouched keys stay untouched
    assert sprint_status.get_status(sprint_status_path, "1-2-mark-tasks-done") == "backlog"


def test_set_status_updates_last_updated(sprint_status_path: Path):
    sprint_status.set_status(sprint_status_path, "epic-1", "in-progress", today="2026-08-01")
    data = sprint_status._load(sprint_status_path)
    assert data["last_updated"] == "2026-08-01"


def test_epic_key_for():
    assert sprint_status.epic_key_for("1-2-user-auth") == "epic-1"
    assert sprint_status.epic_key_for("12-3-something") == "epic-12"


def test_stories_in_epic_excludes_epic_and_retro_keys(sprint_status_path: Path):
    stories = sprint_status.stories_in_epic(sprint_status_path, "epic-1")
    assert stories == {
        "1-1-add-and-list-tasks": "backlog",
        "1-2-mark-tasks-done": "backlog",
    }


def test_epic_fully_done_false_when_any_story_incomplete(sprint_status_path: Path):
    assert sprint_status.epic_fully_done(sprint_status_path, "epic-1") is False


def test_epic_fully_done_true_when_all_done(sprint_status_path: Path):
    sprint_status.set_status(sprint_status_path, "1-1-add-and-list-tasks", "done")
    sprint_status.set_status(sprint_status_path, "1-2-mark-tasks-done", "done")
    assert sprint_status.epic_fully_done(sprint_status_path, "epic-1") is True


def test_epic_fully_done_false_when_epic_has_no_stories(sprint_status_path: Path):
    assert sprint_status.epic_fully_done(sprint_status_path, "epic-9") is False
