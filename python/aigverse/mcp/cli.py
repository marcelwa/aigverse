"""CLI entry point wrapper for the optional MCP server."""

from __future__ import annotations


def main() -> None:
    """Run the MCP server entry point.

    Raises:
        SystemExit: If optional MCP dependencies are not installed.
    """
    try:
        from aigverse.mcp.server import main as server_main
    except ModuleNotFoundError as exc:
        msg = 'The MCP server requires optional dependencies. Install them with: pip install "aigverse[mcp]"'
        raise SystemExit(msg) from exc

    server_main()
