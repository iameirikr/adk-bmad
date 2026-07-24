from pathlib import Path

import pytest

from adk_bmad import skills


def _write_skill(root: Path, name: str, *, skill_md: str = "# SKILL\n", steps: dict[str, str] | None = None) -> None:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(skill_md)
    if steps:
        steps_dir = skill_dir / "steps"
        steps_dir.mkdir()
        for step_id, text in steps.items():
            (steps_dir / f"{step_id}.md").write_text(text)


def test_find_skill_root_prefers_project_over_vendor(tmp_path: Path, monkeypatch):
    _write_skill(tmp_path / ".claude" / "skills", "bmad-create-story", skill_md="# project copy\n")
    root = skills.find_skill_root(tmp_path, "bmad-create-story")
    assert root == tmp_path / ".claude" / "skills" / "bmad-create-story"


def test_find_skill_root_checks_all_three_roots(tmp_path: Path):
    _write_skill(tmp_path / ".agents" / "skills", "bmad-dev-story")
    root = skills.find_skill_root(tmp_path, "bmad-dev-story")
    assert root == tmp_path / ".agents" / "skills" / "bmad-dev-story"

    _write_skill(tmp_path / ".codex" / "skills", "bmad-retrospective")
    root = skills.find_skill_root(tmp_path, "bmad-retrospective")
    assert root == tmp_path / ".codex" / "skills" / "bmad-retrospective"


def test_find_skill_root_falls_back_to_vendor(tmp_path: Path):
    # bmad-create-story is genuinely vendored in this repo — no project install needed.
    root = skills.find_skill_root(tmp_path, "bmad-create-story")
    assert root == skills.VENDOR_DIR / "bmad-create-story"


def test_find_skill_root_raises_when_nowhere_found(tmp_path: Path):
    with pytest.raises(skills.SkillNotFoundError):
        skills.find_skill_root(tmp_path, "bmad-does-not-exist")


def test_skill_available(tmp_path: Path):
    assert skills.skill_available(tmp_path, "bmad-create-story") is True  # vendored fallback
    assert skills.skill_available(tmp_path, "bmad-does-not-exist") is False


def test_load_concatenates_skill_md_and_extras_and_substitutes_placeholders(tmp_path: Path):
    _write_skill(
        tmp_path / ".claude" / "skills",
        "fake-skill",
        skill_md="Root is {project-root} and skill is {skill-name}.\n",
    )
    (tmp_path / ".claude" / "skills" / "fake-skill" / "checklist.md").write_text("Checklist content.\n")

    text = skills.load("fake-skill", project_root=tmp_path)
    assert f"Root is {tmp_path} and skill is fake-skill." in text
    assert "Checklist content." in text


def test_load_includes_steps_in_order(tmp_path: Path):
    _write_skill(
        tmp_path / ".claude" / "skills",
        "stepped-skill",
        steps={"step-02-b": "second\n", "step-01-a": "first\n"},
    )
    text = skills.load("stepped-skill", project_root=tmp_path)
    assert text.index("first") < text.index("second")


def test_load_step_returns_only_that_step_plus_skill_md(tmp_path: Path):
    _write_skill(
        tmp_path / ".claude" / "skills",
        "stepped-skill",
        skill_md="# header\n",
        steps={"step-01": "one\n", "step-02": "two\n"},
    )
    text = skills.load_step("stepped-skill", "step-02", project_root=tmp_path)
    assert "# header" in text
    assert "two" in text
    assert "one" not in text


def test_load_step_missing_step_raises(tmp_path: Path):
    _write_skill(tmp_path / ".claude" / "skills", "stepped-skill", steps={"step-01": "one\n"})
    with pytest.raises(skills.SkillNotFoundError):
        skills.load_step("stepped-skill", "step-99", project_root=tmp_path)
