"""Tests del script de inferencia ``ml/predict.py``.

Estrategia:
- Tests unitarios de ``parse_diff`` y ``filter_supported`` (puros, sin modelo).
- Tests de integraci├│n que cargan el ``.joblib`` y validan que el
  veredicto agregado coincide con la realidad obvia de los fixtures.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from ml.predict import (
    EXIT_OK,
    EXIT_VULNERABLE,
    aggregate,
    filter_supported,
    parse_diff,
    predict_diff,
)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def model():
    import joblib
    return joblib.load(str(FIXTURES.parent.parent / "modelo_seguridad.joblib"))


def test_parse_diff_extracts_added_lines():
    diff = (
        "diff --git a/app/x.py b/app/x.py\n"
        "--- a/app/x.py\n"
        "+++ b/app/x.py\n"
        "@@ -1,3 +1,4 @@\n"
        " line1\n"
        "-old line\n"
        "+new line\n"
        "+another new\n"
    )
    files = parse_diff(diff)
    assert len(files) == 1
    path, lines = files[0]
    assert path == "app/x.py"
    assert lines == ["new line", "another new"]


def test_parse_diff_handles_new_file():
    diff = (
        "diff --git a/app/new.py b/app/new.py\n"
        "new file mode 100644\n"
        "--- /dev/null\n"
        "+++ b/app/new.py\n"
        "@@ -0,0 +1,2 @@\n"
        "+def hello():\n"
        '+    return "hi"\n'
    )
    files = parse_diff(diff)
    assert files == [("app/new.py", ['def hello():', '    return "hi"'])]


def test_filter_supported_skips_non_code_files():
    files = [
        ("app/x.py", ["a = 1"]),
        ("README.md", ["text"]),
        ("app/y.js", ["const x = 1"]),
        ("image.png", []),
    ]
    supported, skipped = filter_supported(files)
    assert len(supported) == 1
    assert skipped == 3
    assert {p for p, _ in supported} == {"app/x.py"}


def test_aggregate_empty_is_safe():
    assert aggregate([]).label == "SEGURO"


def test_aggregate_picks_worst_file():
    from ml.predict import FileVerdict
    verdicts = [
        FileVerdict(path="a.py", label="SEGURO", proba=0.1, added_lines=1),
        FileVerdict(path="b.py", label="VULNERABLE", proba=0.8, added_lines=2),
    ]
    result = aggregate(verdicts)
    assert result.label == "VULNERABLE"
    assert result.proba == 0.8


def test_predict_vulnerable_fixture(model):
    diff = (FIXTURES / "vulnerable_diff.txt").read_text(encoding="utf-8")
    result = predict_diff(model, diff)
    assert result.overall.label == "VULNERABLE"
    assert result.supported_files >= 1
    assert any(f.label == "VULNERABLE" for f in result.files)


def test_predict_safe_fixture(model):
    diff = (FIXTURES / "safe_diff.txt").read_text(encoding="utf-8")
    result = predict_diff(model, diff)
    assert result.overall.label == "SEGURO"
    assert result.supported_files >= 1
    assert all(f.label == "SEGURO" for f in result.files)


def test_predict_mixed_fixture_is_vulnerable(model):
    diff = (FIXTURES / "mixed_diff.txt").read_text(encoding="utf-8")
    result = predict_diff(model, diff)
    assert result.overall.label == "VULNERABLE"


def test_predict_no_code_fixture(model):
    diff = (FIXTURES / "no_code_diff.txt").read_text(encoding="utf-8")
    result = predict_diff(model, diff)
    assert result.supported_files == 0
    assert result.overall.label == "SEGURO"


def test_cli_vulnerable_exits_with_2():
    project_root = FIXTURES.parent.parent.parent
    proc = subprocess.run(
        [sys.executable, "-W", "ignore", "-m", "ml.predict", "--diff", str(FIXTURES / "vulnerable_diff.txt")],
        capture_output=True,
        text=True,
        cwd=str(project_root),
    )
    payload = json.loads(proc.stdout)
    assert payload["overall"]["label"] == "VULNERABLE"
    assert proc.returncode == EXIT_VULNERABLE


def test_cli_safe_exits_with_0():
    project_root = FIXTURES.parent.parent.parent
    proc = subprocess.run(
        [sys.executable, "-W", "ignore", "-m", "ml.predict", "--diff", str(FIXTURES / "safe_diff.txt")],
        capture_output=True,
        text=True,
        cwd=str(project_root),
    )
    payload = json.loads(proc.stdout)
    assert payload["overall"]["label"] == "SEGURO"
    assert proc.returncode == EXIT_OK
