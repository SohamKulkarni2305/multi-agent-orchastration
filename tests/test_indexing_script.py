import pytest
from pathlib import Path
from code_helper.index_codebase import build_index, filter_indexable_files

def test_filter_indexable_files_exclusion(tmp_path):
    (tmp_path / "main.py").write_text("# main", encoding="utf-8")
    (tmp_path / "config.py").write_text("# config", encoding="utf-8")
    
    helper_dir = tmp_path / "code_helper"
    helper_dir.mkdir()
    (helper_dir / "agent.py").write_text("# agent", encoding="utf-8")
    
    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()
    (venv_dir / "lib.py").write_text("# lib", encoding="utf-8")

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_dummy.py").write_text("# test", encoding="utf-8")

    files = filter_indexable_files(str(tmp_path))
    filenames = [Path(f).name for f in files]

    assert "main.py" in filenames
    assert "config.py" in filenames
    assert "agent.py" not in filenames      # Excludes code_helper implementation
    assert "lib.py" not in filenames        # Excludes .venv
    assert "test_dummy.py" not in filenames # Excludes tests

def test_build_index_dry_run():
    # Dry run scans files and chunks without network calls
    result = build_index(target_dir=".", chunk_size=500, overlap=50, dry_run=True)
    assert result["files_scanned"] >= 5
    assert result["chunks_processed"] > 0
    assert result["dry_run"] is True

def test_build_index_evaluate():
    result = build_index(target_dir=".", evaluate=True, dry_run=True)
    assert "evaluation" in result
    assert 200 in result["evaluation"]
    assert 500 in result["evaluation"]
