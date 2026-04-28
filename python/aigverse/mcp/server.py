"""aigverse MCP Server — Expose documentation and API reference to LLM agents.

This module implements a Model Context Protocol (MCP) server that gives
LLM-based agents on-demand access to the aigverse documentation and
Python API reference hosted on ReadTheDocs. The stable documentation is
used by default for end-user queries. Agents working on unreleased
features, local source checkouts, or aigverse development can opt into
the latest documentation instead.

Run via the installed entry-point::

.. code-block:: console

    $ aigverse-mcp-server

Or directly::

.. code-block:: console

    $ python -m aigverse.mcp
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import TYPE_CHECKING
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

import httpx
import markdownify
from bs4 import BeautifulSoup
from fastmcp import FastMCP

from aigverse import __version__

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from bs4 import Tag

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_RTD_ROOT = "https://aigverse.readthedocs.io"
_DEFAULT_DOCS_VERSION = "stable"
_SUPPORTED_DOCS_VERSIONS = frozenset({_DEFAULT_DOCS_VERSION, "latest"})
_USER_AGENT = f"aigverse-mcp-server/{__version__} (+https://github.com/marcelwa/aigverse)"

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
    "aigverse.mcp",
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
    "mcp": "mcp",
    "networks": "networks",
    "utils": "utils",
    # Allow fully-qualified names too
    "aigverse.adapters": "adapters",
    "aigverse.algorithms": "algorithms",
    "aigverse.generators": "generators",
    "aigverse.io": "io",
    "aigverse.mcp": "mcp",
    "aigverse.networks": "networks",
    "aigverse.utils": "utils",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_client = httpx.Client(follow_redirects=True, timeout=30.0)


@lru_cache(maxsize=64)
def _fetch_page_cached(url: str) -> str:
    """Fetch and cache a documentation page for the lifetime of the process.

    Only use this for stable-docs URLs, which are immutable for a given
    release.  Latest-docs pages may change and must not be cached.

    Returns:
        The raw HTML string of the fetched page (cached after first fetch).
    """
    return _fetch_page(url)


def _normalize_docs_version(version: str) -> str | None:
    """Normalize a documentation version selector.

    Returns:
        The normalized version if supported, otherwise ``None``.
    """
    normalized = version.strip().lower()
    if normalized in _SUPPORTED_DOCS_VERSIONS:
        return normalized
    return None


def _invalid_docs_version_message(version: str) -> str:
    """Return a user-facing error message for an unsupported docs version."""
    return (
        f"Invalid documentation version '{version}'. Use '{_DEFAULT_DOCS_VERSION}' for released docs "
        "or 'latest' when working on aigverse itself or unreleased changes."
    )


def _get_docs_base_url(version: str = _DEFAULT_DOCS_VERSION) -> str:
    """Return the ReadTheDocs base URL for a supported documentation version."""
    return f"{_RTD_ROOT}/en/{version}"


def _build_docs_page_url(slug: str, version: str = _DEFAULT_DOCS_VERSION) -> str:
    """Build a guide or API page URL for the selected docs version.

    Returns:
        The absolute URL for the requested documentation page.
    """
    base_url = _get_docs_base_url(version)
    return f"{base_url}/{slug}/index.html" if slug.startswith("api/") else f"{base_url}/{slug}.html"


def _build_api_page_url(submodule_slug: str, version: str = _DEFAULT_DOCS_VERSION) -> str:
    """Build an API page URL for a submodule slug and docs version.

    Returns:
        The absolute URL for the requested API page.
    """
    base_url = _get_docs_base_url(version)
    if submodule_slug == ".":
        return f"{base_url}/api/aigverse/index.html"
    return f"{base_url}/api/aigverse/{submodule_slug}/index.html"


def _rewrite_docs_hit_url(path: str, version: str = _DEFAULT_DOCS_VERSION) -> str:
    """Rewrite a ReadTheDocs search hit URL or path to the selected docs version.

    Returns:
        The absolute URL rewritten to the requested documentation version.
    """
    docs_base_url = _get_docs_base_url(version)
    parsed_base = urlparse(docs_base_url)
    base_url = f"{parsed_base.scheme}://{parsed_base.netloc}"

    if path.startswith("http"):
        parsed_path = urlparse(path)
        if parsed_path.netloc and parsed_path.netloc != parsed_base.netloc:
            return path
        normalized_path = parsed_path.path or "/"
    else:
        normalized_path = path or "/"

    if not normalized_path.startswith("/"):
        normalized_path = f"/{normalized_path}"

    if re.match(r"^/en/(stable|latest)(?:/|$)", normalized_path):
        normalized_path = re.sub(r"^/en/(stable|latest)", f"/en/{version}", normalized_path, count=1)
    elif not normalized_path.startswith("/en/"):
        normalized_path = f"/en/{version}{normalized_path}"

    return urljoin(base_url, normalized_path)


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
        request = Request(  # noqa: S310 — URL is validated to HTTPS-only above before reaching this branch.
            url,
            headers={
                "User-Agent": _USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:  # noqa: S310 — same validation as above; HTTPS enforced by caller.
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
    anchor = soup.find(id=re.compile(rf"^{re.escape(symbol)}$", re.IGNORECASE))
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


@asynccontextmanager
async def _server_lifespan(server: FastMCP) -> AsyncIterator[None]:  # noqa: ARG001
    """Manage the lifecycle of the shared httpx client.

    Ensures the connection pool is properly closed when the MCP server shuts
    down, preventing resource leaks in long-running processes.
    """
    try:
        yield
    finally:
        await asyncio.to_thread(_client.close)


mcp = FastMCP(
    "aigverse",
    instructions=(
        "This server provides access to the aigverse Python library documentation "
        "and API reference. Use stable documentation by default for released-package usage. "
        "If you are developing aigverse itself, working from source, or need unreleased APIs/docs, "
        "switch to version='latest' or use the 'aigverse://pages/stable' and 'aigverse://pages/latest' resources. Use "
        "'get_documentation' to read guide pages, 'lookup_api_symbol' to get docs for a specific "
        "class or function, and 'search_documentation' for keyword search."
    ),
    lifespan=_server_lifespan,
)


# ---- Resource: page listing ------------------------------------------------


def get_pages_listing(version: str = _DEFAULT_DOCS_VERSION) -> dict[str, list[dict[str, str]]]:
    """Build the documentation page index payload for a docs version.

    Args:
        version: Documentation version to index. Use ``"stable"`` by default
                 and ``"latest"`` for unreleased or source-build workflows.

    Returns:
        A mapping with ``guide_pages`` and ``api_pages`` entries.
    """
    pages = [
        {"slug": slug, "title": title, "url": _build_docs_page_url(slug, version)}
        for slug, title in _GUIDE_PAGES.items()
    ]
    api_pages = [
        {
            "slug": f"api/{mod.replace('.', '/')}",
            "title": f"API: {mod}",
            "url": _build_docs_page_url(f"api/{mod.replace('.', '/')}", version),
        }
        for mod in _API_SUBMODULES
    ]
    return {"guide_pages": pages, "api_pages": api_pages}


@mcp.resource("aigverse://pages/stable")
def list_pages() -> str:
    """Return a JSON listing of stable documentation pages.

    Each entry contains the page slug (to pass to ``get_documentation``),
    a human-readable title, and the full URL on ReadTheDocs. This is the
    default entry point for end users and released-package workflows.
    """
    return json.dumps(get_pages_listing(_DEFAULT_DOCS_VERSION), indent=2)


@mcp.resource("aigverse://pages/latest")
def list_pages_latest() -> str:
    """Return a JSON listing of latest documentation pages.

    Use this resource when you are developing aigverse itself, working from
    a source checkout, or need unreleased documentation content.
    """
    return json.dumps(get_pages_listing("latest"), indent=2)


# ---- Tool: get documentation page ------------------------------------------


@mcp.tool()
def get_documentation(slug: str, version: str = _DEFAULT_DOCS_VERSION) -> str:
    """Fetch a documentation page by slug and return its content as Markdown.

    Use the ``aigverse://pages/stable`` resource for stable docs or
    ``aigverse://pages/latest`` when working with unreleased documentation.

    Args:
        slug: Page identifier, e.g. ``"installation"``, ``"aigs"``,
              ``"algorithms"``, or ``"api/aigverse/networks"`` for API pages.
        version: Documentation version to query. Use ``"stable"`` by default
                 and ``"latest"`` for aigverse development or source builds.

    Returns:
        The page content converted to Markdown.
    """
    normalized_version = _normalize_docs_version(version)
    if normalized_version is None:
        return _invalid_docs_version_message(version)

    # Normalise: strip leading/trailing slashes
    slug = slug.strip("/")

    # Allowlist check — only permit known guide slugs or api/aigverse/* paths.
    # This prevents an adversarial agent from using the tool to fetch arbitrary
    # pages on ReadTheDocs by supplying a path-traversal slug.
    if slug not in _GUIDE_PAGES and not slug.startswith("api/aigverse/"):
        return (
            f"Unknown page slug '{slug}'. "
            "Use the aigverse://pages/stable or aigverse://pages/latest resource "
            "to list all available page slugs."
        )

    url = _build_docs_page_url(slug, normalized_version)

    try:
        html = _fetch_page(url)
    except httpx.HTTPError as exc:
        detail = str(exc.response.status_code) if isinstance(exc, httpx.HTTPStatusError) else str(exc)
        return (
            f"Error: could not fetch page '{slug}' from the {normalized_version} docs ({detail}). "
            "Use the aigverse://pages/stable or aigverse://pages/latest resource to see available pages."
        )

    return _extract_article(html)


# ---- Tool: per-symbol API lookup -------------------------------------------


@mcp.tool()
def lookup_api_symbol(symbol: str, version: str = _DEFAULT_DOCS_VERSION) -> str:
    """Look up the documentation for a single API symbol (class, function, constant).

    This returns only the relevant section, not the whole API page — keeping
    the context compact.

    Args:
        symbol: The symbol name to look up.  Can be a short name like
                ``"Aig"`` or ``"aig_resubstitution"``, or fully qualified
                like ``"aigverse.networks.Aig"``.
        version: Documentation version to query. Use ``"stable"`` by default
                 and ``"latest"`` for aigverse development or unreleased docs.

    Returns:
        The symbol's documentation as Markdown, or an error message if not found.
    """
    normalized_version = _normalize_docs_version(version)
    if normalized_version is None:
        return _invalid_docs_version_message(version)

    # If fully qualified, we can infer the submodule
    parts = symbol.split(".")
    if len(parts) >= 3 and parts[0] == "aigverse":
        # e.g. "aigverse.networks.Aig" → submodule "networks", symbol_name "Aig"
        submodule = parts[1]
        submodule_slugs = [submodule, "."] if submodule in _SUBMODULE_SLUGS else list(_SUBMODULE_SLUGS.values())
    elif len(parts) == 2 and parts[0] in _SUBMODULE_SLUGS:
        submodule_slugs = [_SUBMODULE_SLUGS[parts[0]], "."]
    else:
        # Short name — search across all submodule pages
        submodule_slugs = list(dict.fromkeys(_SUBMODULE_SLUGS.values()))

    for slug in submodule_slugs:
        url = _build_api_page_url(slug, normalized_version)

        # Use cached fetches for stable docs (immutable per release) to avoid
        # redundant HTTP requests when scanning multiple submodule pages.
        fetch = _fetch_page_cached if normalized_version == _DEFAULT_DOCS_VERSION else _fetch_page

        try:
            html = fetch(url)
        except httpx.HTTPError:
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
        f"Symbol '{symbol}' not found in the {normalized_version} API reference. "
        f"Available submodules: {', '.join(_API_SUBMODULES)}. "
        f"Try 'search_documentation' to find the correct name."
    )


# ---- Tool: search -----------------------------------------------------------


@mcp.tool()
def search_documentation(query: str, max_results: int = 5, version: str = _DEFAULT_DOCS_VERSION) -> str:
    """Search the aigverse documentation for pages matching a query.

    Uses the ReadTheDocs server-side search API to find relevant pages and
    rewrites result URLs to the selected docs version.

    Args:
        query: Search terms (e.g. ``"resubstitution"``, ``"read AIGER file"``).
        max_results: Maximum number of results to return (default 5).
        version: Documentation version to query. Use ``"stable"`` by default
                 and ``"latest"`` when working with unreleased docs.

    Returns:
        A JSON string.  On success, a JSON array of result objects each with
        ``title``, ``url``, and ``highlights`` keys.  On empty results, a JSON
        object with ``results`` (empty array) and ``message`` keys.  On error,
        a JSON object with an ``error`` key.
    """
    normalized_version = _normalize_docs_version(version)
    if normalized_version is None:
        return _invalid_docs_version_message(version)

    search_url = "https://readthedocs.org/api/v3/search/"
    params: dict[str, str | int] = {"q": f"project:aigverse {query}", "page_size": max_results}

    try:
        resp = _client.get(search_url, params=params)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        if isinstance(exc, httpx.HTTPStatusError):
            return json.dumps({"error": f"Search failed: HTTP {exc.response.status_code}"})
        return json.dumps({"error": f"Search failed: {exc}"})

    data = resp.json()
    results: list[dict[str, str | list[str]]] = []
    for hit in data.get("results", []):
        # Each result has 'title', 'domain', 'path', 'highlights'
        path = hit.get("path", "")
        highlights: list[str] = []
        for block in hit.get("blocks", []):
            block_highlights = block.get("highlights", {}).get("content", [])
            if isinstance(block_highlights, list):
                content_highlights = [text for text in block_highlights if isinstance(text, str) and text]
                highlights.extend(content_highlights)

        results.append({
            "title": hit.get("title", ""),
            "url": (
                _rewrite_docs_hit_url(path, normalized_version)
                if isinstance(path, str)
                else _get_docs_base_url(normalized_version)
            ),
            "highlights": highlights,
        })

    if not results:
        return json.dumps({"results": [], "message": f"No results found for '{query}'."})

    return json.dumps(results, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the aigverse MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
