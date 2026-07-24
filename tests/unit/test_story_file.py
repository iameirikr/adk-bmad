from pathlib import Path

import pytest

from adk_bmad.state import story_file

STORY_TEXT = """\
---
baseline_commit: abc123
---

# Story 1.1: Add and list tasks

Status: ready-for-dev

## Story

As a user, I want to add and list tasks.

## Acceptance Criteria

1. Given no todos.json exists, when I run list, then it prints nothing.

## Tasks / Subtasks

- [ ] Task 1: implement add
- [ ] Task 2: implement list

## Dev Agent Record

### File List

(none yet)
"""


@pytest.fixture
def implementation_artifacts(tmp_path: Path) -> Path:
    (tmp_path / "1-1-add-and-list-tasks.md").write_text(STORY_TEXT)
    return tmp_path


def test_story_exists(implementation_artifacts: Path):
    assert story_file.story_exists(implementation_artifacts, "1-1-add-and-list-tasks") is True
    assert story_file.story_exists(implementation_artifacts, "9-9-nope") is False


def test_read_status(implementation_artifacts: Path):
    assert story_file.read_status(implementation_artifacts, "1-1-add-and-list-tasks") == "ready-for-dev"


def test_set_status_rewrites_only_status_line(implementation_artifacts: Path):
    previous = story_file.set_status(implementation_artifacts, "1-1-add-and-list-tasks", "in-progress")
    assert previous == "ready-for-dev"

    text = story_file.read_text(implementation_artifacts, "1-1-add-and-list-tasks")
    assert "Status: in-progress" in text
    # everything else byte-identical
    assert "baseline_commit: abc123" in text
    assert "- [ ] Task 1: implement add" in text
    assert text.count("Status:") == 1


def test_read_frontmatter(implementation_artifacts: Path):
    frontmatter = story_file.read_frontmatter(implementation_artifacts, "1-1-add-and-list-tasks")
    assert frontmatter == {"baseline_commit": "abc123"}


def test_read_frontmatter_missing_returns_empty_dict(tmp_path: Path):
    (tmp_path / "no-frontmatter.md").write_text("# Story\n\nStatus: backlog\n")
    assert story_file.read_frontmatter(tmp_path, "no-frontmatter") == {}


def test_set_frontmatter_field_updates_existing(implementation_artifacts: Path):
    story_file.set_frontmatter_field(implementation_artifacts, "1-1-add-and-list-tasks", "baseline_commit", "def456")
    frontmatter = story_file.read_frontmatter(implementation_artifacts, "1-1-add-and-list-tasks")
    assert frontmatter == {"baseline_commit": "def456"}


def test_set_frontmatter_field_creates_when_absent(tmp_path: Path):
    (tmp_path / "no-frontmatter.md").write_text("# Story\n\nStatus: backlog\n")
    story_file.set_frontmatter_field(tmp_path, "no-frontmatter", "baseline_commit", "xyz")
    frontmatter = story_file.read_frontmatter(tmp_path, "no-frontmatter")
    assert frontmatter == {"baseline_commit": "xyz"}
    # original content preserved after the new frontmatter
    text = story_file.read_text(tmp_path, "no-frontmatter")
    assert "Status: backlog" in text
