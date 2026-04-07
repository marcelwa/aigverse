"""Tests for the aigverse MCP server entry point and module structure.

These tests verify the CLI entry point, module importability, and server
object integrity. Live documentation integration checks are gated behind
the ``mcp_integration`` marker and ``--run-mcp-integration``.
"""

from __future__ import annotations

import json

import pytest

# ---------------------------------------------------------------------------
# Entry-point smoke tests (pytest-console-scripts)
# ---------------------------------------------------------------------------


@pytest.mark.script_launch_mode("subprocess")
class TestEntryPoint:
    """Verify the ``aigverse-mcp-server`` console_scripts entry point."""

    def test_help_flag_exits_cleanly(self, script_runner) -> None:
        """``--help`` should exit without crashing."""
        result = script_runner.run(["aigverse-mcp-server", "--help"])
        assert result.returncode == 0
        assert "Starting MCP server 'aigverse'" in result.stderr

    def test_invalid_flag_does_not_crash(self, script_runner) -> None:
        """An unrecognised flag should not crash the entry point."""
        result = script_runner.run(["aigverse-mcp-server", "--no-such-flag"])
        assert result.returncode == 0
        assert "Starting MCP server 'aigverse'" in result.stderr


# ---------------------------------------------------------------------------
# Module-level import tests
# ---------------------------------------------------------------------------


class TestModuleImports:
    """Verify the ``aigverse.mcp`` package is importable and well-formed."""

    def test_package_importable(self) -> None:
        """``import aigverse.mcp`` should succeed."""
        import aigverse.mcp

        assert hasattr(aigverse.mcp, "main")
        assert hasattr(aigverse.mcp, "mcp")

    def test_server_module_importable(self) -> None:
        """``import aigverse.mcp.server`` should succeed."""
        import aigverse.mcp.server

        assert hasattr(aigverse.mcp.server, "main")
        assert hasattr(aigverse.mcp.server, "mcp")

    def test_main_is_callable(self) -> None:
        """``main`` must be callable (the CLI entry point target)."""
        import aigverse.mcp

        assert callable(aigverse.mcp.main)


# ---------------------------------------------------------------------------
# FastMCP server-object tests
# ---------------------------------------------------------------------------


class TestServerObject:
    """Validate the FastMCP ``mcp`` instance exposed by the package."""

    @pytest.fixture
    def server(self):
        from aigverse.mcp.server import mcp

        return mcp

    def test_server_name(self, server) -> None:
        """Server name should be ``aigverse``."""
        assert server.name == "aigverse"

    def test_server_has_instructions(self, server) -> None:
        """Instructions string must be non-empty."""
        assert server.instructions
        assert isinstance(server.instructions, str)


# ---------------------------------------------------------------------------
# Page-listing resource tests (no network)
# ---------------------------------------------------------------------------


class TestPageListing:
    """Test the ``list_pages`` resource for structural correctness."""

    @pytest.fixture
    def pages_json(self):
        from aigverse.mcp.server import list_pages

        return json.loads(list_pages())

    def test_returns_valid_json(self, pages_json) -> None:
        """``list_pages()`` must return parseable JSON."""
        assert isinstance(pages_json, dict)

    def test_has_guide_pages_key(self, pages_json) -> None:
        """Top-level keys must include ``guide_pages``."""
        assert "guide_pages" in pages_json

    def test_has_api_pages_key(self, pages_json) -> None:
        """Top-level keys must include ``api_pages``."""
        assert "api_pages" in pages_json

    def test_guide_pages_non_empty(self, pages_json) -> None:
        """Guide page list must be non-empty."""
        assert len(pages_json["guide_pages"]) > 0

    def test_api_pages_non_empty(self, pages_json) -> None:
        """API page list must be non-empty."""
        assert len(pages_json["api_pages"]) > 0

    def test_guide_page_structure(self, pages_json) -> None:
        """Each guide page entry must have ``slug``, ``title``, ``url``."""
        for page in pages_json["guide_pages"]:
            assert "slug" in page
            assert "title" in page
            assert "url" in page
            assert page["url"].startswith("https://")

    def test_api_page_structure(self, pages_json) -> None:
        """Each API page entry must have ``slug``, ``title``, ``url``."""
        for page in pages_json["api_pages"]:
            assert "slug" in page
            assert "title" in page
            assert "url" in page
            assert page["url"].startswith("https://")


# ---------------------------------------------------------------------------
# HTML extraction helpers (no network, synthetic HTML)
# ---------------------------------------------------------------------------


class TestExtractArticle:
    """Test ``_extract_article`` with synthetic Furo-like HTML."""

    @pytest.fixture
    def extract(self):
        from aigverse.mcp.server import _extract_article

        return _extract_article

    def test_extracts_article_role_main(self, extract) -> None:
        """Content inside ``<article role='main'>`` is extracted."""
        html = "<html><body><nav>nav</nav><article role='main'><h1>Title</h1><p>Body</p></article></body></html>"
        md = extract(html)
        assert "Title" in md
        assert "Body" in md
        assert "nav" not in md.split("Title")[0]  # nav should not precede title

    def test_fallback_to_body(self, extract) -> None:
        """When no ``<article>`` exists, fall back to ``<body>``."""
        html = "<html><body><h2>Fallback</h2></body></html>"
        md = extract(html)
        assert "Fallback" in md

    def test_returns_string(self, extract) -> None:
        """Result is always a string."""
        assert isinstance(extract("<html><body>hello</body></html>"), str)


class TestExtractSymbolSection:
    """Test ``_extract_symbol_section`` with synthetic Sphinx-like HTML."""

    @pytest.fixture
    def extract(self):
        from aigverse.mcp.server import _extract_symbol_section

        return _extract_symbol_section

    def test_finds_exact_id(self, extract) -> None:
        """Finds a ``<dt>`` with an exact matching ``id``."""
        html = '<dl><dt id="aigverse.networks.Aig">class Aig</dt><dd>An AIG network.</dd></dl>'
        result = extract(html, "aigverse.networks.Aig")
        assert result is not None
        assert "Aig" in result

    def test_finds_short_name(self, extract) -> None:
        """Finds a symbol by short-name suffix match."""
        html = '<dl><dt id="aigverse.networks.Aig">class Aig</dt><dd>An AIG network.</dd></dl>'
        result = extract(html, "Aig")
        assert result is not None

    def test_returns_none_for_missing(self, extract) -> None:
        """Returns ``None`` when the symbol is not found."""
        html = '<dl><dt id="aigverse.networks.Aig">class Aig</dt><dd>Docs</dd></dl>'
        assert extract(html, "NonExistent") is None


# ---------------------------------------------------------------------------
# Live documentation integration tests (real HTML)
# ---------------------------------------------------------------------------


@pytest.mark.mcp_integration
class TestLiveDocumentationIntegration:
    """Integration tests against real ReadTheDocs HTML pages."""

    @pytest.fixture(scope="class")
    def installation_html(self) -> str:
        from aigverse.mcp.server import _fetch_page

        return _fetch_page("https://aigverse.readthedocs.io/en/latest/installation.html")

    @pytest.fixture(scope="class")
    def networks_api_html(self) -> str:
        from aigverse.mcp.server import _fetch_page

        return _fetch_page("https://aigverse.readthedocs.io/en/latest/api/aigverse/networks/index.html")

    def test_extract_article_from_live_installation_page(self, installation_html) -> None:
        """``_extract_article`` should parse real documentation content."""
        from aigverse.mcp.server import _extract_article

        md = _extract_article(installation_html)
        assert "installation" in md.lower()
        assert len(md.strip()) > 200

    def test_extract_symbol_from_live_api_page(self, networks_api_html) -> None:
        """``_extract_symbol_section`` should locate a real API symbol."""
        from aigverse.mcp.server import _extract_symbol_section

        section = _extract_symbol_section(networks_api_html, "aigverse.networks.Aig")
        assert section is not None
        assert "Aig" in section

    def test_get_documentation_live_page(self) -> None:
        """Public tool should return parsed Markdown from live docs."""
        from aigverse.mcp.server import get_documentation

        doc = get_documentation("installation")
        assert "installation" in doc.lower()

    def test_lookup_api_symbol_live(self, networks_api_html) -> None:  # noqa: ARG002
        """Public symbol lookup should find a known live API symbol."""
        from aigverse.mcp.server import lookup_api_symbol

        section = lookup_api_symbol("aigverse.networks.Aig")
        assert "not found" not in section.lower()
        assert "Aig" in section
