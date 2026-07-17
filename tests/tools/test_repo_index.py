from pathlib import Path

from orchestrator.tools.repo_index import RepoIndex


def _area_by_file(areas):
    return {area.files[0]: area for area in areas}


def test_build_extracts_symbols_and_import_graph() -> None:
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures" / "sample_repo"

    index = RepoIndex()
    index.build(str(fixture_root))

    auth_symbols = {symbol.name for symbol in index.file_symbols["auth.py"]}
    assert "AuthService" in auth_symbols
    assert "authenticate_user" in auth_symbols

    assert index.import_graph["main.py"] == {"auth.py", "user.py"}
    assert index.import_graph["user.py"] == {"auth.py"}
    assert index.import_graph["auth.py"] == {"utils.py"}


def test_find_impacted_matches_keywords_and_importers() -> None:
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures" / "sample_repo"

    index = RepoIndex()
    index.build(str(fixture_root))

    areas = index.find_impacted(["authentication", "user"])
    by_file = _area_by_file(areas)

    assert "auth.py" in by_file
    assert "Matched keyword(s):" in by_file["auth.py"].reason

    assert "user.py" in by_file
    assert "Matched keyword(s):" in by_file["user.py"].reason

    assert "main.py" in by_file
    assert "Imports matched file:" in by_file["main.py"].reason
