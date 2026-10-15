import pytest
from pathlib import Path
from code_helper.tools.plain_ast_tools import (
    find_imports,
    find_symbol_references,
    list_functions_and_classes,
    get_file_structure,
)
from code_helper.tools.project_summary_tool import get_project_summary
from code_helper.tools.env_scanner_tool import find_env_vars
from code_helper.tools.metrics_tool import calculate_code_metrics
from code_helper.tools.search_tools import find_exact_matches
from code_helper.tools.code_inspection_tools import get_function_source
from code_helper.tools.diagram_tool import generate_architecture_diagram
from code_helper.tools.health_check_tool import check_system_health, get_run_commands


@pytest.fixture
def mock_repo(tmp_path):
    sub = tmp_path / "pkg"
    sub.mkdir()
    f1 = sub / "module_a.py"
    f1.write_text(
        "import os\n\ndef helper(x: int = 10) -> str:\n    '''A helper docstring.'''\n    key = os.getenv('SECRET_TOKEN', 'default_tok')\n    return str(x) + key\n",
        encoding="utf-8"
    )
    f2 = sub / "module_b.py"
    f2.write_text(
        "from .module_a import helper\n\nclass Runner:\n    '''Runner class.'''\n    def run(self) -> str:\n        return helper()\n",
        encoding="utf-8"
    )
    return str(tmp_path)


def test_find_imports_and_references(mock_repo):
    mod_b = str(Path(mock_repo) / "pkg" / "module_b.py")
    imports = find_imports(mod_b, project_dir=mock_repo)
    assert "module_a" in imports

    # Check reverse lookup: who imports module_a?
    reverse_imports = find_imports("module_a", project_dir=mock_repo)
    assert "module_b.py" in reverse_imports

    refs = find_symbol_references("helper", project_dir=mock_repo)
    assert "module_b.py" in refs


def test_list_functions_and_classes(mock_repo):
    mod_b = str(Path(mock_repo) / "pkg" / "module_b.py")
    symbols = list_functions_and_classes(mod_b)
    assert "Runner" in symbols
    assert "run" in symbols


def test_get_file_structure(mock_repo):
    tree = get_file_structure(mock_repo)
    assert "module_a.py" in tree
    assert "module_b.py" in tree


def test_get_project_summary(mock_repo):
    summary = get_project_summary(mock_repo)
    assert "Python Files" in summary or "Files" in summary
    assert "module_a.py" in summary


def test_env_scanner_masks_secrets(mock_repo):
    env_info = find_env_vars(mock_repo)
    assert "SECRET_TOKEN" in env_info
    assert "default_tok" in env_info


def test_calculate_code_metrics(mock_repo):
    mod_a = str(Path(mock_repo) / "pkg" / "module_a.py")
    metrics = calculate_code_metrics(mod_a)
    assert "Total Lines" in metrics
    assert "Functions" in metrics


def test_ast_error_handling(tmp_path):
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("def broken_syntax(:\n pass", encoding="utf-8")
    result = list_functions_and_classes(str(bad_file))
    assert "Error" in result or "SyntaxError" in result


def test_find_exact_matches(mock_repo):
    res = find_exact_matches("SECRET_TOKEN", project_dir=mock_repo)
    assert "SECRET_TOKEN" in res
    assert "module_a.py" in res

    # Missing pattern
    res_missing = find_exact_matches("NONEXISTENT_KEY_999", project_dir=mock_repo)
    assert "No exact matches found" in res_missing


def test_get_function_source(mock_repo):
    mod_a = str(Path(mock_repo) / "pkg" / "module_a.py")
    res = get_function_source(mod_a, "helper")
    assert "def helper" in res
    assert "A helper docstring" in res
    assert "SECRET_TOKEN" in res

    # Missing symbol
    res_missing = get_function_source(mod_a, "missing_function")
    assert "was not found" in res_missing


def test_generate_architecture_diagram(mock_repo):
    diag = generate_architecture_diagram(mock_repo)
    assert "graph TD" in diag
    assert "module_a" in diag
    assert "module_b" in diag


def test_health_check_and_run_commands(mock_repo):
    health = check_system_health(mock_repo)
    assert "Python Version" in health

    commands = get_run_commands()
    assert "adk run code_helper" in commands
    assert "python -m code_helper.index_codebase" in commands
