import re
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from main import _normalize_path, _to_windows_path, resolve_path_suggestions


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


def test_normalize_path_passes_through_linux_path():
    assert _normalize_path("/home/eric/pictures") == "/home/eric/pictures"
    assert _normalize_path("~/documents") == "~/documents"
    assert _normalize_path("") == ""


def test_normalize_path_windows_backslash_on_wsl():
    with (
        patch("main._is_wsl", return_value=True),
        patch.object(sys, "platform", "linux"),
    ):
        assert _normalize_path("C:\\Users\\eric") == "/mnt/c/Users/eric"
        assert _normalize_path("D:\\Photos\\vacation") == "/mnt/d/Photos/vacation"
        assert _normalize_path("C:\\") == "/mnt/c/"
        assert _normalize_path("C:") == "/mnt/c/"


def test_normalize_path_windows_forward_slash_on_wsl():
    with (
        patch("main._is_wsl", return_value=True),
        patch.object(sys, "platform", "linux"),
    ):
        assert _normalize_path("C:/Users/eric") == "/mnt/c/Users/eric"
        assert _normalize_path("c:/users/eric") == "/mnt/c/users/eric"


def test_normalize_path_windows_native():
    with patch.object(sys, "platform", "win32"):
        assert _normalize_path("C:\\Users\\eric") == "C:/Users/eric"
        assert _normalize_path("c:/users/eric") == "C:/users/eric"
        assert _normalize_path("D:\\Photos") == "D:/Photos"
        assert _normalize_path("C:") == "C:/"


def test_to_windows_path_converts_mnt_paths():
    assert _to_windows_path("/mnt/c/Users/eric") == "C:\\Users\\eric"
    assert _to_windows_path("/mnt/d/Photos/vacation") == "D:\\Photos\\vacation"
    assert _to_windows_path("/mnt/c/") == "C:\\"
    assert _to_windows_path("/mnt/c") == "C:\\"


def test_to_windows_path_passes_through_non_mnt():
    assert _to_windows_path("/home/eric") == "/home/eric"
    assert _to_windows_path("") == ""


def test_resolve_skips_inaccessible_entries():
    """Per-entry OSError (e.g. Windows system dirs on WSL) does not abort the whole listing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "accessible").mkdir()
        (base / "also_accessible").mkdir()

        good_entry = MagicMock()
        good_entry.path = str(base / "accessible")
        good_entry.name = "accessible"
        good_entry.is_dir.return_value = True

        bad_entry = MagicMock()
        bad_entry.path = str(base / "system_dir")
        bad_entry.name = "system_dir"
        bad_entry.is_dir.side_effect = OSError("permission denied")

        another_good = MagicMock()
        another_good.path = str(base / "also_accessible")
        another_good.name = "also_accessible"
        another_good.is_dir.return_value = True

        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(
            return_value=iter([good_entry, bad_entry, another_good])
        )
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("main.os.scandir", return_value=mock_ctx):
            results = resolve_path_suggestions(str(base), limit=20)

        assert str(base / "accessible") in results
        assert str(base / "also_accessible") in results
        assert str(base / "system_dir") not in results


def test_resolve_returns_windows_format_when_input_is_windows():
    with (
        patch("main._is_wsl", return_value=True),
        patch.object(sys, "platform", "linux"),
    ):
        results = resolve_path_suggestions("C:\\", limit=5)
        assert all(re.match(r"^[A-Z]:\\", r) for r in results)
