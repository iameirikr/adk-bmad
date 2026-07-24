from pathlib import Path

import pytest
from google.adk.models.lite_llm import LiteLlm

from adk_bmad import config


def _write_bmad_project(root: Path) -> None:
    bmm_dir = root / "_bmad" / "bmm"
    bmm_dir.mkdir(parents=True)
    (bmm_dir / "config.yaml").write_text(
        """\
user_name: Ada
project_name: Analytical Engine
communication_language: English
output_folder: "{project-root}/_bmad-output"
"""
    )
    impl = root / "_bmad-output" / "implementation-artifacts"
    impl.mkdir(parents=True)
    (impl / "sprint-status.yaml").write_text("development_status: {}\n")


def test_load_bmad_config_expands_project_root_placeholder(tmp_path: Path):
    _write_bmad_project(tmp_path)
    bmad_config = config.load_bmad_config(tmp_path)
    assert bmad_config.output_folder == tmp_path / "_bmad-output"
    assert bmad_config.implementation_artifacts == tmp_path / "_bmad-output" / "implementation-artifacts"
    assert bmad_config.sprint_status == tmp_path / "_bmad-output" / "implementation-artifacts" / "sprint-status.yaml"
    assert bmad_config.user_name == "Ada"
    assert bmad_config.project_name == "Analytical Engine"


def test_load_bmad_config_missing_config_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="BMAD config not found"):
        config.load_bmad_config(tmp_path)


def test_load_bmad_config_missing_sprint_status_raises(tmp_path: Path):
    (tmp_path / "_bmad" / "bmm").mkdir(parents=True)
    (tmp_path / "_bmad" / "bmm" / "config.yaml").write_text("output_folder: \"{project-root}/_bmad-output\"\n")
    with pytest.raises(FileNotFoundError, match="sprint-status.yaml not found"):
        config.load_bmad_config(tmp_path)


def test_placeholders_map(tmp_path: Path):
    _write_bmad_project(tmp_path)
    bmad_config = config.load_bmad_config(tmp_path)
    placeholders = bmad_config.placeholders()
    assert placeholders["{project-root}"] == str(tmp_path)
    assert placeholders["{user_name}"] == "Ada"


def test_resolve_model_gemini_passthrough(monkeypatch):
    monkeypatch.delenv("ADK_BMAD_MODEL_SELECT", raising=False)
    model = config.resolve_model("select")
    assert model == "gemini-2.5-flash"


def test_resolve_model_env_override_wraps_non_gemini_in_litellm(monkeypatch):
    monkeypatch.setenv("ADK_BMAD_MODEL_DEV_STORY", "anthropic/claude-opus-4-6")
    model = config.resolve_model("dev_story")
    assert isinstance(model, LiteLlm)
    assert model.model == "anthropic/claude-opus-4-6"


def test_resolve_model_unknown_role_raises():
    with pytest.raises(KeyError):
        config.resolve_model("not_a_real_role")


def test_default_project_root_env_override(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ADK_BMAD_PROJECT_ROOT", str(tmp_path))
    assert config.default_project_root() == tmp_path.resolve()
