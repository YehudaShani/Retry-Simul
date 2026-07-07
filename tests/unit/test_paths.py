from pathlib import Path

from helpers.paths import (
    PROBABILITIES_EXCHANGE_LEAK_WITH_LOSS_FILE,
    REPO_ROOT,
    SAVED_PROBABILITIES_FILE,
    data_path,
    repo_relative,
    repo_root,
)


def test_repo_root_points_at_project_root():
    root = repo_root()
    assert root == REPO_ROOT
    assert (root / "src" / "helpers").is_dir()
    assert (root / "tests").is_dir()


def test_data_path_resolves_under_repo_data():
    assert data_path("saved_lists") == REPO_ROOT / "data" / "saved_lists"


def test_repo_relative_resolves_from_repo_root():
    assert repo_relative("data/saved_lists/foo.json") == REPO_ROOT / "data" / "saved_lists" / "foo.json"
    absolute = Path("C:/tmp/example.json")
    assert repo_relative(absolute) == absolute


def test_saved_probability_files_exist():
    assert SAVED_PROBABILITIES_FILE.exists()
    assert PROBABILITIES_EXCHANGE_LEAK_WITH_LOSS_FILE.exists()
