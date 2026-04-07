"""aigverse MCP Server — Expose documentation and API reference to LLM agents.

This module implements a Model Context Protocol (MCP) server that gives
LLM-based agents on-demand access to the aigverse documentation and
Python API reference hosted on ReadTheDocs.

Run via the installed entry-point::

.. code-block:: console

    $ aigverse-mcp-server

Or directly::

.. code-block:: console

    $ python -m aigverse.mcp
"""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import httpx
import markdownify
from bs4 import BeautifulSoup
from fastmcp import FastMCP

if TYPE_CHECKING:
    from bs4 import Tag

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_RTD_BASE = "https://aigverse.readthedocs.io/en/latest"

_GUIDE_PAGES: dict[str, str] = {
    "installation": "Installation",
    "aigs": "And-Inverter Graphs (AIGs)",
    "truth_tables": "Truth Tables",
    "algorithms": "Algorithms",
    "generators": "Generators",
    "machine_learning": "Machine Learning Integration",
    "mcp": "MCP Server",
    "contributing": "Contributing",
    "support": "Support",
    "DevelopmentGuide": "Development Guide",
}

_API_SUBMODULES: list[str] = [
    "aigverse",
    "aigverse.adapters",
    "aigverse.algorithms",
    "aigverse.generators",
    "aigverse.io",
    "aigverse.networks",
    "aigverse.utils",
]

# Map short convenience names to the submodule page slug that autoapi
# generates under ``api/aigverse/<slug>/index.html``.
_SUBMODULE_SLUGS: dict[str, str] = {
    "aigverse": ".",
    "adapters": "adapters",
    "algorithms": "algorithms",
    "generators": "generators",
    "io": "io",
    "networks": "networks",
    "utils": "utils",
    # Allow fully-qualified names too
    "aigverse.adapters": "adapters",
    "aigverse.algorithms": "algorithms",
    "aigverse.generators": "generators",
    "aigverse.io": "io",
    "aigverse.networks": "networks",
    "aigverse.utils": "utils",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_client = httpx.Client(follow_redirects=True, timeout=30.0)


def _fetch_page(url: str) -> str:
    """Fetch *url* and return the raw HTML body, or raise on error.

    Returns:
        The raw HTML string of the fetched page.

    Raises:
        ValueError: If *url* is not an HTTPS URL.
        httpx.HTTPError: If both httpx and urllib-based fetch attempts fail.
    """
    parsed = urlparse(url)
    if parsed.scheme != "https":
        msg = f"Unsupported URL scheme for documentation fetch: {parsed.scheme!r}"
        raise ValueError(msg)

    try:
        resp = _client.get(url)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        # Some docs hosts intermittently deny certain TLS/client fingerprints.
        # Fall back to stdlib urllib to avoid false negatives in live integration.
        logger.debug("httpx fetch failed for %s, attempting urllib fallback", url, exc_info=exc)
        request = Request(  # noqa: S310
            url,
            headers={
                "User-Agent": "aigverse-mcp-server/1.0 (+https://github.com/marcelwa/aigverse)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:  # noqa: S310
                encoding = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(encoding, errors="replace")
        except (HTTPError, URLError) as urllib_exc:
            raise exc from urllib_exc
    else:
        return resp.text


def _extract_article(html: str) -> str:
    """Extract the main article content from a Furo/Sphinx HTML page.

    Strips sidebar navigation, header/footer chrome, and theme widgets so
    that only the documentation body remains.

    Returns:
        The article content converted to Markdown.
    """
    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one("article[role='main']") or soup.select_one("div.body")
    if article is None:
        # Last resort: return the whole body
        article = soup.body or soup
    return markdownify.markdownify(str(article), heading_style="ATX", strip=["img", "script", "style"])


def _extract_symbol_section(html: str, symbol: str) -> str | None:
    """Extract the documentation section for a single API symbol.

    Sphinx/autoapi generates ``<dt id="aigverse.module.Symbol">`` anchors.
    This helper locates the matching ``<dl>`` block and converts only that
    fragment to Markdown.

    Returns:
        The symbol's documentation as Markdown, or ``None`` if not found.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Try exact id match first (e.g. "aigverse.networks.Aig")
    anchor = soup.find(id=re.compile(re.escape(symbol), re.IGNORECASE))
    if anchor is None:
        # Try matching just the short name at the end of the id
        anchor = soup.find(id=re.compile(rf"\.{re.escape(symbol)}$", re.IGNORECASE))
    if anchor is None:
        return None

    # Walk up to the enclosing <dl> (Sphinx uses description lists for API items)
    node: Tag | None = anchor
    while node and node.name != "dl":
        node = node.parent

    if node is None:
        # Fallback: grab the anchor's parent section
        node = anchor.parent

    return markdownify.markdownify(str(node), heading_style="ATX", strip=["script", "style"])


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "aigverse",
    instructions=(
        "This server provides access to the aigverse Python library documentation "
        "and API reference. Use 'get_documentation' to read guide pages, "
        "'lookup_api_symbol' to get docs for a specific class or function, "
        "and 'search_documentation' for keyword search."
    ),
)


# ---- Resource: page listing ------------------------------------------------


@mcp.resource("aigverse://pages")
def list_pages() -> str:
    """Return a JSON listing of all available documentation pages.

    Each entry contains the page slug (to pass to ``get_documentation``),
    a human-readable title, and the full URL on ReadTheDocs.
    """
    pages = [{"slug": slug, "title": title, "url": f"{_RTD_BASE}/{slug}.html"} for slug, title in _GUIDE_PAGES.items()]
    api_pages = [
        {
            "slug": f"api/{mod.replace('.', '/')}",
            "title": f"API: {mod}",
            "url": f"{_RTD_BASE}/api/{mod.replace('.', '/')}/index.html",
        }
        for mod in _API_SUBMODULES
    ]
    return json.dumps({"guide_pages": pages, "api_pages": api_pages}, indent=2)


# ---- Tool: get documentation page ------------------------------------------


@mcp.tool()
def get_documentation(slug: str) -> str:
    """Fetch a documentation page by its slug and return its content as Markdown.

    Use the ``aigverse://pages`` resource to discover available slugs.

    Args:
        slug: Page identifier, e.g. ``"installation"``, ``"aigs"``,
              ``"algorithms"``, or ``"api/aigverse/networks"`` for API pages.

    Returns:
        The page content converted to Markdown.
    """
    # Normalise: strip leading/trailing slashes
    slug = slug.strip("/")

    url = f"{_RTD_BASE}/{slug}/index.html" if slug.startswith("api/") else f"{_RTD_BASE}/{slug}.html"

    try:
        html = _fetch_page(url)
    except httpx.HTTPStatusError as exc:
        return (
            f"Error: could not fetch page '{slug}' ({exc.response.status_code}). "
            f"Use the aigverse://pages resource to see available pages."
        )

    return _extract_article(html)


# ---- Tool: per-symbol API lookup -------------------------------------------


@mcp.tool()
def lookup_api_symbol(symbol: str) -> str:
    """Look up the documentation for a single API symbol (class, function, constant).

    This returns only the relevant section, not the whole API page — keeping
    the context compact.

    Args:
        symbol: The symbol name to look up.  Can be a short name like
                ``"Aig"`` or ``"aig_resubstitution"``, or fully qualified
                like ``"aigverse.networks.Aig"``.

    Returns:
        The symbol's documentation as Markdown, or an error message if not found.
    """
    # If fully qualified, we can infer the submodule
    parts = symbol.split(".")
    if len(parts) >= 3 and parts[0] == "aigverse":
        # e.g. "aigverse.networks.Aig" → submodule "networks", symbol_name "Aig"
        submodule = parts[1]
        submodule_slugs = [submodule] if submodule in _SUBMODULE_SLUGS else list(_SUBMODULE_SLUGS.values())
    elif len(parts) == 2 and parts[0] in _SUBMODULE_SLUGS:
        submodule_slugs = [_SUBMODULE_SLUGS[parts[0]]]
    else:
        # Short name — search across all submodule pages
        submodule_slugs = list(dict.fromkeys(_SUBMODULE_SLUGS.values()))

    for slug in submodule_slugs:
        url = f"{_RTD_BASE}/api/aigverse/index.html" if slug == "." else f"{_RTD_BASE}/api/aigverse/{slug}/index.html"

        try:
            html = _fetch_page(url)
        except httpx.HTTPStatusError:
            continue

        result = _extract_symbol_section(html, symbol)
        if result is not None:
            return result

        # Also try the short name (last part)
        short_name = parts[-1]
        if short_name != symbol:
            result = _extract_symbol_section(html, short_name)
            if result is not None:
                return result

    return (
        f"Symbol '{symbol}' not found in the API reference. "
        f"Available submodules: {', '.join(_API_SUBMODULES)}. "
        f"Try 'search_documentation' to find the correct name."
    )


# ---- Tool: search -----------------------------------------------------------


@mcp.tool()
def search_documentation(query: str, max_results: int = 5) -> str:
    """Search the aigverse documentation for pages matching a query.

    Uses the ReadTheDocs server-side search API to find relevant pages.

    Args:
        query: Search terms (e.g. ``"resubstitution"``, ``"read AIGER file"``).
        max_results: Maximum number of results to return (default 5).

    Returns:
        A JSON array of search results, each with title, URL, and a text snippet.
    """
    search_url = "https://readthedocs.org/api/v3/search/"
    params = {"q": f"project:aigverse {query}", "page_size": max_results}

    try:
        resp = _client.get(search_url, params=params)
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return f"Search failed: {exc.response.status_code}"

    data = resp.json()
    results = []
    for hit in data.get("results", []):
        # Each result has 'title', 'domain', 'path', 'highlights'
        path = hit.get("path", "")
        results.append({
            "title": hit.get("title", ""),
            "url": f"{_RTD_BASE}/{path}" if not path.startswith("http") else path,
            "highlights": [
                block.get("content", {}).get("highlighted", "")
                for block in hit.get("blocks", [])
                if block.get("content", {}).get("highlighted")
            ],
        })

    if not results:
        return f"No results found for '{query}'."

    return json.dumps(results, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the aigverse MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
