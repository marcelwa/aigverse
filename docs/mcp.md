# MCP Server

`aigverse` includes an optional [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that gives
LLM-based coding agents — such as those in Claude Desktop, Cursor, or Windsurf — on-demand access to the full
`aigverse` documentation and Python API reference. This lets the agent look up classes, functions, and usage guides
without you having to copy-paste documentation into the chat.

## Installation

Install `aigverse` with the `mcp` extra to pull in the server and its dependencies:

::::{tab-set}
:sync-group: installer

:::{tab-item} uv _(recommended)_
:sync: uv

```console
$ uv pip install "aigverse[mcp]"
```

:::

:::{tab-item} pip
:sync: pip

```console
(.venv) $ python -m pip install "aigverse[mcp]"
```

:::
::::

This installs the `aigverse-mcp-server` command-line entry point along with [FastMCP](https://gofastmcp.com/),
[httpx](https://www.python-httpx.org/), [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/), and
[markdownify](https://github.com/matthewwithanm/python-markdownify) as additional dependencies.

## Client Configuration

Configure your MCP-compatible client to start the server over `stdio`.

::::{tab-set}

:::{tab-item} Claude Desktop

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "aigverse": {
      "command": "aigverse-mcp-server"
    }
  }
}
```

:::

:::{tab-item} Cursor

In Cursor Settings → MCP, add a new server with:

- **Name:** `aigverse`
- **Type:** `command`
- **Command:** `aigverse-mcp-server`

:::

:::{tab-item} Generic (stdio)

Any MCP client that supports the `stdio` transport can launch the server directly:

```bash
aigverse-mcp-server
```

:::
::::

```{tip}
If you installed `aigverse` inside a virtual environment or via `uv`, make sure the `aigverse-mcp-server` script is
on your `PATH`, or use the full path to the script in the client configuration. With `uv`, you can also use
`uvx --from "aigverse[mcp]" aigverse-mcp-server` to run the server without a persistent install.
```

## Available Tools and Resources

The server exposes the following capabilities:

### Resource

| URI                | Description                                                                                                           |
| ------------------ | --------------------------------------------------------------------------------------------------------------------- |
| `aigverse://pages` | JSON listing of all available documentation pages (guide pages and API submodule pages) with slugs, titles, and URLs. |

### Tools

| Name                   | Description                                                                                                                                                                                                                                  |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `get_documentation`    | Fetch a full documentation page by its slug (e.g., `"installation"`, `"aigs"`, `"algorithms"`, or `"api/aigverse/networks"` for API pages) and return it as Markdown.                                                                        |
| `lookup_api_symbol`    | Look up the documentation for a single API symbol (class, function, constant) by name. Accepts short names like `"Aig"` or fully qualified names like `"aigverse.networks.Aig"`. Returns only the matching section, keeping context compact. |
| `search_documentation` | Search the documentation by keyword using the ReadTheDocs search API. Returns matching page titles, URLs, and highlighted snippets.                                                                                                          |

## How It Works

The server fetches documentation pages live from [aigverse.readthedocs.io](https://aigverse.readthedocs.io/en/latest/)
at request time, so the content is always in sync with the latest published documentation. For each request, the
server:

1. Fetches the HTML page from ReadTheDocs
2. Extracts the main article content using Beautiful Soup (stripping navigation, sidebars, and other page chrome)
3. Converts the cleaned HTML to Markdown for token-efficient LLM consumption

The `lookup_api_symbol` tool goes a step further: it locates the specific HTML fragment for the requested symbol and
returns only that section, rather than the entire (often very long) API page.

## Usage Tips

- Start with `search_documentation` when you don't know the exact page or symbol name.
- Use `lookup_api_symbol` for quick, focused API lookups — it returns far less text than fetching an entire API page.
- Use `get_documentation` when you need the full context of a guide or tutorial page.
- The `aigverse://pages` resource gives a complete index of everything that's available.
