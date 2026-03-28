import tempfile
from pathlib import Path

from main import resolve_path_suggestions


def test_resolve_existing_directory():
    """If given an existing directory, list its immediate subdirectories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "dir1").mkdir()
        (base / "dir2").mkdir()
        (base / "dir3").mkdir()
        (base / "file.txt").touch()  # File, should be ignored

        results = resolve_path_suggestions(str(base), limit=20)

        # Should return subdirectories only, sorted
        assert len(results) == 3
        assert str(base / "dir1") in results
        assert str(base / "dir2") in results
        assert str(base / "dir3") in results
        assert results == sorted(results)  # Verify sorted


def test_resolve_partial_path():
    """If given a non-existent path, use parent and filter by prefix."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "apple").mkdir()
        (base / "apricot").mkdir()
        (base / "banana").mkdir()

        # Pass "ap" (non-existent) — should filter on parent
        partial = str(base / "ap")
        results = resolve_path_suggestions(partial, limit=20)

        assert len(results) == 2
        assert str(base / "apple") in results
        assert str(base / "apricot") in results
        assert str(base / "banana") not in results


def test_resolve_respects_limit():
    """Results are capped at the limit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        for i in range(25):
            (base / f"dir{i:02d}").mkdir()

        results = resolve_path_suggestions(str(base), limit=10)

        assert len(results) == 10


def test_resolve_handles_nonexistent_path():
    results = resolve_path_suggestions(
        "/nonexistent/path/that/does/not/exist", limit=20
    )

    assert results == []


def test_resolve_expands_tilde():
    home = Path.home()
    results = resolve_path_suggestions("~/", limit=20)
    assert all(str(Path(r)).startswith(str(home)) for r in results)
    assert all(Path(r).is_dir() for r in results)
