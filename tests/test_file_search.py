import os
from pathlib import Path

import config as config_module
import tools.files as files_module


def _isolated_config(tmp_path, monkeypatch):
    """Point CONFIG.search_roots at a throwaway temp directory for these tests."""
    fake_config = config_module.ZyroConfig(search_roots=(tmp_path,))
    monkeypatch.setattr(config_module, "CONFIG", fake_config)
    monkeypatch.setattr(files_module, "CONFIG", fake_config)
    return fake_config


def test_search_files_finds_match(tmp_path, monkeypatch):
    _isolated_config(tmp_path, monkeypatch)
    (tmp_path / "physics_notes.pdf").write_text("dummy")
    (tmp_path / "unrelated.txt").write_text("dummy")

    result = files_module.search_files(query="physics")
    assert result["success"] is True
    names = [r["filename"] for r in result["data"]["results"]]
    assert "physics_notes.pdf" in names
    assert "unrelated.txt" not in names


def test_search_files_extension_filter(tmp_path, monkeypatch):
    _isolated_config(tmp_path, monkeypatch)
    (tmp_path / "resume.pdf").write_text("dummy")
    (tmp_path / "resume.docx").write_text("dummy")

    result = files_module.search_files(query="resume", extension="pdf")
    names = [r["filename"] for r in result["data"]["results"]]
    assert names == ["resume.pdf"]


def test_search_files_no_match(tmp_path, monkeypatch):
    _isolated_config(tmp_path, monkeypatch)
    result = files_module.search_files(query="nonexistent_file_xyz")
    assert result["success"] is True
    assert result["data"]["results"] == []


def test_get_file_info_outside_roots_is_denied(tmp_path, monkeypatch):
    _isolated_config(tmp_path, monkeypatch)
    outside = tmp_path.parent / "outside_file.txt"
    outside.write_text("dummy")
    try:
        result = files_module.get_file_info(str(outside))
        assert result["success"] is False
    finally:
        outside.unlink(missing_ok=True)


def test_create_folder_mock_mode(tmp_path, monkeypatch):
    _isolated_config(tmp_path, monkeypatch)
    target = tmp_path / "new_folder"
    result = files_module.create_folder(str(target), mock_mode=True)
    assert result["success"] is True
    assert not target.exists()  # mock mode must not touch the real filesystem


def test_create_folder_real(tmp_path, monkeypatch):
    _isolated_config(tmp_path, monkeypatch)
    target = tmp_path / "new_folder"
    result = files_module.create_folder(str(target), mock_mode=False)
    assert result["success"] is True
    assert target.exists()


def test_create_folder_rejects_existing(tmp_path, monkeypatch):
    _isolated_config(tmp_path, monkeypatch)
    target = tmp_path / "already_here"
    target.mkdir()
    result = files_module.create_folder(str(target), mock_mode=False)
    assert result["success"] is False
