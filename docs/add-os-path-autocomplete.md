# Feature: OS Path Autocomplete

## Summary

Add OS-level path autocomplete to the directory scan input field on the main page.

## Problem

Users must type the full directory path manually into the scan form. There is no feedback or assistance while typing, making it easy to enter an incorrect path and only discovering the error after submitting.

## Desired Behavior

- As the user types into the directory path input, the UI should suggest valid filesystem paths in real time.
- Suggestions should reflect the actual directory structure of the host OS.
- Selecting a suggestion should populate the input field with the chosen path.
- Only directories should be suggested (not individual files).

## Acceptance Criteria

- [ ] Typing a partial path shows a dropdown of matching subdirectories.
- [ ] Suggestions update as the user continues typing.
- [ ] Pressing Tab or clicking a suggestion completes the path in the input.
- [ ] Non-existent or invalid paths do not crash the server — return an empty suggestion list.
- [ ] Works on Linux and macOS (WSL paths included).

## Implementation Notes

- A new endpoint (e.g. `GET /api/path-autocomplete?q=<partial-path>`) should return a JSON list of matching directory paths.
- The frontend can use HTMX or a small vanilla JS handler to call this endpoint and render suggestions.
- Scope completions to directories only (`os.scandir` / `pathlib.Path.iterdir` filtering `is_dir()`).
- Limit results to a reasonable count (e.g. 20) to avoid large payloads.
