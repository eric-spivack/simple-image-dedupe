# OS Path Autocomplete Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real-time directory path autocomplete to the scan form, suggesting matching subdirectories as the user types.

**Architecture:**
- Backend: new `GET /api/path-autocomplete` endpoint that returns an HTML dropdown fragment (or nothing if no matches). Path resolution logic is extracted into a testable helper function.
- Frontend: HTMX fires on keyup with 300ms delay, sends the partial path, swaps the response into a target div below the input.
- Templates: Add Bootstrap 5 CDN, wrap the input in a relative-positioned container, add HTMX attributes.

**Tech Stack:** FastAPI (backend), Jinja2 (templates), HTMX 2.0.4 (existing), Bootstrap 5 (new via CDN), pytest (existing test framework).

---

## Task 1: Path Resolution Helper Function & Unit Tests

**Files:**
- Create: `tests/test_path_resolution.py`
- Modify: `main.py` (add helper function)

**Context:** Build a testable function that resolves a partial path to a list of matching subdirectories. This is the core business logic — test it thoroughly before wiring it into the endpoint.

- [ ] **Step 1: Write failing test for existing directory case**

Create `tests/test_path_resolution.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/eric/projects/simple-image-dedupe
uv run pytest tests/test_path_resolution.py::test_resolve_existing_directory -v
```

Expected output:
```
FAILED tests/test_path_resolution.py::test_resolve_existing_directory - ImportError: cannot import name 'resolve_path_suggestions' from 'main'
```

- [ ] **Step 3: Write failing test for partial path case**

```python
def test_resolve_partial_path():
    """If given a non-existent path, use parent and filter by prefix."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "apple").mkdir()
        (base / "apricot").mkdir()
        (base / "banana").mkdir()

        # Pass "apple" (non-existent) — should filter on parent
        partial = str(base / "app")
        results = resolve_path_suggestions(partial, limit=20)

        assert len(results) == 2
        assert str(base / "apple") in results
        assert str(base / "apricot") in results
        assert str(base / "banana") not in results
```

- [ ] **Step 4: Run tests to verify both fail**

```bash
uv run pytest tests/test_path_resolution.py -v
```

Expected: 2 failures.

- [ ] **Step 5: Implement resolve_path_suggestions in main.py**

Add this function to `main.py` (after imports, before the FastAPI app definition):

```python
from pathlib import Path
from typing import List


def resolve_path_suggestions(partial_path: str, limit: int = 20) -> List[str]:
    """
    Resolve a partial path to a list of matching subdirectories.

    If partial_path is an existing directory, list its immediate subdirectories.
    If partial_path is not a directory, use its parent and filter by name prefix.

    Returns sorted list of full paths (up to limit), or empty list on any OS error.
    """
    try:
        path = Path(partial_path).expanduser()

        if path.is_dir():
            # Existing directory — list subdirectories
            subdirs = [
                str(p) for p in path.iterdir()
                if p.is_dir()
            ]
        else:
            # Non-existent or file — use parent and filter by prefix
            parent = path.parent
            if not parent.is_dir():
                return []

            name_prefix = path.name
            subdirs = [
                str(p) for p in parent.iterdir()
                if p.is_dir() and p.name.startswith(name_prefix)
            ]

        return sorted(subdirs)[:limit]

    except (PermissionError, FileNotFoundError, OSError):
        return []
```

- [ ] **Step 6: Run tests to verify both pass**

```bash
uv run pytest tests/test_path_resolution.py -v
```

Expected: 2 passes.

- [ ] **Step 7: Write test for limit cap**

```python
def test_resolve_respects_limit():
    """Results are capped at the limit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        for i in range(25):
            (base / f"dir{i:02d}").mkdir()

        results = resolve_path_suggestions(str(base), limit=10)

        assert len(results) == 10
```

- [ ] **Step 8: Run test to verify it passes**

```bash
uv run pytest tests/test_path_resolution.py::test_resolve_respects_limit -v
```

Expected: 1 pass.

- [ ] **Step 9: Write test for OS error handling**

```python
def test_resolve_handles_permission_error():
    """Permission errors return empty list."""
    # Non-existent path that can't be accessed
    results = resolve_path_suggestions("/nonexistent/path/that/does/not/exist", limit=20)

    assert results == []
```

- [ ] **Step 10: Run all path resolution tests**

```bash
uv run pytest tests/test_path_resolution.py -v
```

Expected: 4 passes.

- [ ] **Step 11: Commit path resolution tests and helper**

```bash
git add tests/test_path_resolution.py main.py
git commit -m "feat: add path resolution helper with unit tests"
```

---

## Task 2: API Endpoint Implementation

**Files:**
- Modify: `main.py` (add endpoint)

**Context:** Wire the path resolution helper into a FastAPI endpoint. The endpoint accepts a `dir` query param, calls the helper, and returns an HTML fragment.

- [ ] **Step 1: Add the endpoint to main.py**

Add this function to `main.py` after the path resolution function and before the existing endpoints:

```python
@app.get("/api/path-autocomplete")
async def path_autocomplete(dir: str = "") -> str:
    """
    Return HTML suggestions for a partial directory path.

    Query param: dir (partial path)
    Returns: HTML fragment (Bootstrap dropdown or empty)
    """
    suggestions = resolve_path_suggestions(dir, limit=20)

    return templates.TemplateResponse(
        "partials/path_suggestions.html",
        {"request": None, "matches": suggestions}
    )
```

Wait — `request` object is required by Jinja2's context. Let me revise:

```python
@app.get("/api/path-autocomplete")
async def path_autocomplete(request: Request, dir: str = "") -> str:
    """
    Return HTML suggestions for a partial directory path.

    Query param: dir (partial path)
    Returns: HTML fragment (Bootstrap dropdown or empty)
    """
    suggestions = resolve_path_suggestions(dir, limit=20)

    return templates.TemplateResponse(
        "partials/path_suggestions.html",
        {"request": request, "matches": suggestions}
    )
```

(Note: `Request` is already imported from fastapi in main.py.)

- [ ] **Step 2: Test the endpoint manually**

Start the server:

```bash
uv run main.py
```

In a new terminal, test the endpoint with a single directory path:

```bash
curl "http://127.0.0.1:8000/api/path-autocomplete?dir=/home"
```

Expected: HTML fragment with a dropdown (if subdirectories exist) or empty response.

Test with a non-existent deep path:

```bash
curl "http://127.0.0.1:8000/api/path-autocomplete?dir=/nonexistent/path"
```

Expected: Empty response (no error, no 500).

- [ ] **Step 3: Commit the endpoint**

```bash
git add main.py
git commit -m "feat: add /api/path-autocomplete endpoint"
```

---

## Task 3: Create Path Suggestions Partial Template

**Files:**
- Create: `templates/partials/path_suggestions.html`

**Context:** This partial is returned by the endpoint. It renders a Bootstrap dropdown if matches exist, or nothing if the list is empty.

- [ ] **Step 1: Create the partial**

Create `templates/partials/path_suggestions.html`:

```html
{% if matches %}
<ul class="dropdown-menu show" style="width: 100%; position: absolute; top: 100%; left: 0; max-height: 300px; overflow-y: auto;">
  {% for path in matches %}
  <li>
    <a class="dropdown-item" href="#"
       onclick="document.getElementById('dir').value='{{ path }}';
                document.getElementById('autocomplete-results').innerHTML='';
                return false;">
      {{ path }}
    </a>
  </li>
  {% endfor %}
</ul>
{% endif %}
```

- [ ] **Step 2: Verify the file exists**

```bash
ls -la /home/eric/projects/simple-image-dedupe/templates/partials/path_suggestions.html
```

Expected: file listed.

- [ ] **Step 3: Commit the partial**

```bash
git add templates/partials/path_suggestions.html
git commit -m "feat: add path_suggestions partial template"
```

---

## Task 4: Add Bootstrap 5 CDN to Main Template

**Files:**
- Modify: `templates/index.html`

**Context:** Add Bootstrap CSS and JS via CDN. CSS goes in `<head>`, JS before `</body>`.

- [ ] **Step 1: Read the current index.html**

```bash
head -20 /home/eric/projects/simple-image-dedupe/templates/index.html
tail -10 /home/eric/projects/simple-image-dedupe/templates/index.html
```

This helps you see the structure.

- [ ] **Step 2: Add Bootstrap CSS to <head>**

Find the `<head>` section. After the existing `<link>` or `<meta>` tags, add:

```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
```

- [ ] **Step 3: Add Bootstrap JS before </body>**

Find the closing `</body>` tag. Before it, add:

```html
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
```

- [ ] **Step 4: Verify changes**

Open `templates/index.html` and confirm:
- Bootstrap CSS link is in `<head>`
- Bootstrap JS is before `</body>`
- Existing content is unchanged

- [ ] **Step 5: Commit Bootstrap CDN**

```bash
git add templates/index.html
git commit -m "feat: add Bootstrap 5 CDN"
```

---

## Task 5: Update Input Field with HTMX Attributes & Container

**Files:**
- Modify: `templates/index.html`

**Context:** Wrap the `<input name="dir">` in a `position: relative` container, add HTMX attributes to the input, and add a sibling `<div id="autocomplete-results">` as the swap target.

- [ ] **Step 1: Find the current dir input**

```bash
grep -n 'name="dir"' /home/eric/projects/simple-image-dedupe/templates/index.html
```

This shows the line number.

- [ ] **Step 2: Replace the input with wrapped version**

Find the line with `<input ... name="dir" ...>` and replace it with:

```html
<div style="position: relative;">
  <input type="text" id="dir" name="dir" required
         hx-get="/api/path-autocomplete"
         hx-trigger="keyup changed delay:300ms"
         hx-target="#autocomplete-results"
         hx-include="this"
         autocomplete="off">
  <div id="autocomplete-results"></div>
</div>
```

Notes:
- Keep any existing attributes on the input (e.g. `class`, `placeholder`), merge them with the new HTMX ones.
- The `hx-include="this"` automatically sends the input's value as `dir=` query param.
- The `autocomplete="off"` disables browser autocomplete.

- [ ] **Step 3: Verify input has id="dir"**

```bash
grep 'id="dir"' /home/eric/projects/simple-image-dedupe/templates/index.html
```

Expected: one match for the input.

- [ ] **Step 4: Commit input and container changes**

```bash
git add templates/index.html
git commit -m "feat: add HTMX autocomplete attributes and dropdown container"
```

---

## Task 6: Manual End-to-End Test

**Files:**
- No new files

**Context:** Start the server, open the UI, type a partial path, and verify the dropdown appears and selection works.

- [ ] **Step 1: Start the server**

```bash
uv run main.py
```

Expected output includes: `Application startup complete` and `Uvicorn running on http://127.0.0.1:8000`.

- [ ] **Step 2: Open the UI**

Open a browser to `http://127.0.0.1:8000` (or use curl + inspect network if headless).

- [ ] **Step 3: Test autocomplete**

In the directory input, type a partial path (e.g. `/h` for `/home`, or `/u/bin` from `/usr/bin`).

Expected behavior:
- After 300ms of no typing, a dropdown appears below the input.
- The dropdown shows matching subdirectories (e.g. `home` if you typed `/h`).
- Clicking a suggestion fills the input with the full path and closes the dropdown.

- [ ] **Step 4: Test error handling**

Type an invalid/non-existent path (e.g. `/nonexistent/xyz/abc`).

Expected: No dropdown appears (empty suggestions).

- [ ] **Step 5: Test existing directory**

Type an existing directory path (e.g. `/home`).

Expected: Dropdown shows immediate subdirectories of `/home`.

- [ ] **Step 6: Verify no 500 errors**

Check browser console (F12) or server logs for any 500 errors.

Expected: No errors; server logs show `GET /api/path-autocomplete` requests with `200` responses.

- [ ] **Step 7: Commit all work**

```bash
git status
```

Expected: all files staged and committed (no untracked or modified files).

If any changes remain (e.g. a typo fix), commit them:

```bash
git add <files>
git commit -m "fix: <description>"
```

---

## Summary

After completing all tasks:
- ✅ Path resolution helper is tested and working
- ✅ Backend endpoint returns HTML dropdown or empty
- ✅ Frontend input has HTMX and Bootstrap attributes
- ✅ New partial renders the dropdown correctly
- ✅ E2E manual test passes
- ✅ All commits are clean and logical

The feature is ready for code review and merging.
