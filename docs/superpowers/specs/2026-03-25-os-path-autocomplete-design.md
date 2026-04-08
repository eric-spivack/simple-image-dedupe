# Design: OS Path Autocomplete

**Date:** 2026-03-25
**Branch:** eric-spivack/add-os-path-autocomplete

## Summary

Add real-time directory path autocomplete to the scan form's directory input. As the user types, a Bootstrap dropdown appears below the input showing matching subdirectories from the host filesystem. Selecting a suggestion fills the input and closes the dropdown.

## Dependencies

Add Bootstrap 5 via CDN to `templates/index.html`:
- CSS link in `<head>`
- JS bundle script before `</body>`

No npm, no build step. Bootstrap is added globally and serves as the foundation for future UI improvements.

## Backend

**New endpoint:** `GET /api/path-autocomplete?dir=<partial-path>`

Resolution logic:
- If `dir` is an existing directory → list its immediate subdirectories
- If `dir` is not a directory → use `Path(dir).parent` and filter subdirectory names by `Path(dir).name` as a prefix
- Cap results at 20, sorted alphabetically
- On any OS error (PermissionError, FileNotFoundError, etc.) → return empty fragment

Returns: HTML fragment (`templates/partials/path_suggestions.html`)

## Frontend

Wrap the existing `dir` input in a `position: relative` container. Add a sibling `<div id="autocomplete-results">` as the HTMX swap target.

HTMX attributes on the input:
- `hx-get="/api/path-autocomplete"` — endpoint to call
- `hx-trigger="keyup changed delay:300ms"` — fires 300ms after the user stops typing
- `hx-target="#autocomplete-results"` — where to swap the response
- `hx-include="this"` — sends the current input value as `dir=`
- `autocomplete="off"` — disables browser's native autocomplete

## New Partial: `templates/partials/path_suggestions.html`

Renders a Bootstrap `dropdown-menu show` list when matches exist; renders nothing (emptying the target div) when the list is empty.

Each item is a Bootstrap `dropdown-item` anchor with an inline `onclick` that:
1. Sets `document.getElementById('dir').value` to the full path
2. Clears `#autocomplete-results` to close the dropdown

No separate JS file is introduced. The inline handler is the only JavaScript added.

## Error Handling

All OS errors are caught at the endpoint level and result in an empty response (no dropdown shown). The server never returns a 500 for a bad or unreadable path.

## Files Changed

| File | Change |
|---|---|
| `main.py` | Add `GET /api/path-autocomplete` endpoint |
| `templates/index.html` | Add Bootstrap CDN; wrap dir input in relative container; add `#autocomplete-results` div |
| `templates/partials/path_suggestions.html` | New partial — Bootstrap dropdown fragment |

## Out of Scope

- Styling other existing UI elements with Bootstrap (deferred to future features)
- File (non-directory) suggestions
- Keyboard navigation within the dropdown (Tab/arrow keys)
