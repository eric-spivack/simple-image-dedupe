from pathlib import Path

from bs4 import BeautifulSoup


def _parse(name: str) -> BeautifulSoup:
    html = (Path(__file__).parent.parent / "templates" / name).read_text()
    return BeautifulSoup(html, "html.parser")


def test_escape_key_clears_autocomplete_results():
    """Input keydown handler clears results on Escape."""
    inp = _parse("index.html").find("input", {"id": "dir"})
    handler = inp.get("hx-on:keydown", "")
    assert "Escape" in handler
    assert "autocomplete-results" in handler


def test_html_height_allows_body_to_fill_viewport():
    """html must have height: 100% so body can expand to fill the full viewport."""
    css = (Path(__file__).parent.parent / "static" / "style.css").read_text()
    assert "html" in css
    assert "height: 100%" in css


def test_dismiss_handler_is_on_body_element():
    """Click handler must be on <body> — HTMX does not process hx-on on <html>."""
    soup = _parse("index.html")
    html_tag = soup.find("html")
    body_tag = soup.find("body")
    assert "autocomplete-results" in body_tag.get("hx-on:click", "")
    assert "autocomplete-results" not in html_tag.get("hx-on:click", "")


def test_path_suggestions_has_backdrop():
    """A full-viewport backdrop div must appear when dropdown is open.

    The backdrop sits at z-index 1049, below the dropdown (1050), so clicks
    anywhere outside the suggestion list — including areas intercepted by
    Bootstrap's JS — hit the backdrop and dismiss the dropdown.
    """
    soup = _parse("partials/path_suggestions.html")
    backdrop = soup.find("div", {"id": "autocomplete-backdrop"})
    assert backdrop is not None
    assert "autocomplete-results" in backdrop.get("onclick", "")


def test_path_suggestions_uses_data_path_attribute():
    """Suggestion items use data-path to avoid XSS via inline string interpolation."""
    soup = _parse("partials/path_suggestions.html")
    anchor = soup.find("a", class_="dropdown-item")
    assert anchor is not None
    assert anchor.has_attr("data-path")
    assert "this.dataset.path" in anchor.get("onclick", "")
