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

## Stable vs Latest

The MCP server uses the `stable` documentation by default. That is the right choice for normal users consuming released
versions from PyPI, because it keeps agent answers aligned with the published API.

Switch to the `latest` documentation only when you are working on `aigverse` itself, testing unreleased behavior from a
source checkout, or validating documentation for changes that have not been released yet.

For AI agents, the intended usage pattern is:

- Use `version="stable"` by default.
- Use `version="latest"` when working on `main`, a feature branch, or an unreleased local build.
- Use `aigverse://pages/stable` to discover the stable guide and API pages before calling the tools.
- Use `aigverse://pages/latest` to discover the latest guide and API pages before calling the tools.

Example prompts for agent workflows:

- "Use the stable `aigverse` docs to explain how to construct an AIG."
- "I'm adding a feature to `aigverse`; use the latest docs to check the current `Aig` API."
- "Search the latest `aigverse` docs for unreleased MCP server changes."

## Client Configuration

Configure your MCP-compatible client to start the server over `stdio`.

::::{tab-set}

:::{tab-item} Claude Code

Register the server with the `claude mcp add` command (local scope by default):

```bash
claude mcp add aigverse -- aigverse-mcp-server
```

If `aigverse-mcp-server` is not on your `PATH`, use `uvx`:

```bash
claude mcp add aigverse -- uvx --from "aigverse[mcp]" aigverse-mcp-server
```

To share the configuration with your whole team, use project scope — this writes to `.mcp.json` at the project root, which you can commit to version control:

```bash
claude mcp add --scope project aigverse -- aigverse-mcp-server
```

The resulting `.mcp.json` entry looks like:

```json
{
  "mcpServers": {
    "aigverse": {
      "command": "aigverse-mcp-server"
    }
  }
}
```

Or with `uvx`:

```json
{
  "mcpServers": {
    "aigverse": {
      "command": "uvx",
      "args": ["--from", "aigverse[mcp]", "aigverse-mcp-server"]
    }
  }
}
```

:::

:::{tab-item} Claude Desktop

Add the following to your `claude_desktop_config.json`.

If `aigverse-mcp-server` is on your `PATH` (e.g. after `pip install "aigverse[mcp]"`):

```json
{
  "mcpServers": {
    "aigverse": {
      "command": "aigverse-mcp-server"
    }
  }
}
```

If you prefer to run without a persistent install, or the script is not on your `PATH`, use `uvx`
(note that `command` and `args` must be specified separately in JSON):

```json
{
  "mcpServers": {
    "aigverse": {
      "command": "uvx",
      "args": ["--from", "aigverse[mcp]", "aigverse-mcp-server"]
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

:::{tab-item} GitHub Copilot (VS Code)

Use the MCP server registration flow in VS Code and configure a `command`/`stdio` server:

1. Open Command Palette.
2. Run the MCP server add command exposed by your Copilot/VS Code installation.
3. Add server name `aigverse`.
4. Set command to:

```bash
aigverse-mcp-server
```

If your environment does not expose `aigverse-mcp-server` on `PATH`, use:

```bash
uvx --from "aigverse[mcp]" aigverse-mcp-server
```

:::

:::{tab-item} GitHub Copilot CLI

In Copilot CLI, register an MCP `stdio` server named `aigverse` and point it to:

```bash
aigverse-mcp-server
```

If needed, use the `uvx` form:

```bash
uvx --from "aigverse[mcp]" aigverse-mcp-server
```

:::

:::{tab-item} Codex CLI

In Codex CLI MCP settings, add a `stdio` server named `aigverse` with command:

```bash
aigverse-mcp-server
```

Or use:

```bash
uvx --from "aigverse[mcp]" aigverse-mcp-server
```

:::

:::{tab-item} Gemini CLI

In Gemini CLI MCP settings, add a `stdio` server named `aigverse` with command:

```bash
aigverse-mcp-server
```

Or use:

```bash
uvx --from "aigverse[mcp]" aigverse-mcp-server
```

:::

:::{tab-item} Generic (stdio)

Any MCP client that supports the `stdio` transport can launch the server directly:

```bash
aigverse-mcp-server
```

For clients that accept a JSON `command`/`args` configuration (e.g. Claude Desktop format), the `uvx` invocation
must be split into separate fields:

```json
{
  "command": "uvx",
  "args": ["--from", "aigverse[mcp]", "aigverse-mcp-server"]
}
```

:::
::::

```{tip}
If you installed `aigverse` inside a virtual environment or via `uv`, make sure the `aigverse-mcp-server` script is
on your `PATH`, or use the full path to the script in the client configuration. With `uv`, you can also use
`uvx --from "aigverse[mcp]" aigverse-mcp-server` to run the server without a persistent install. When your client
expects a JSON `command`/`args` configuration, decompose the `uvx` invocation as
`"command": "uvx", "args": ["--from", "aigverse[mcp]", "aigverse-mcp-server"]`.
```

```{note}
Exact setting names and config file locations differ across client versions. The integration contract is the same:
register a `stdio` MCP server named `aigverse` that launches the command shown above.
```

## Available Tools and Resources

The server exposes the following capabilities:

### Resource

| URI                       | Description                                                                                                        |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `aigverse://pages/stable` | JSON listing of all stable documentation pages (guide pages and API submodule pages) with slugs, titles, and URLs. |
| `aigverse://pages/latest` | JSON listing of the latest documentation pages for `aigverse` development and unreleased changes.                  |

### Tools

| Name                   | Description                                                                                                                                                                                                                                                                                                       |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `get_documentation`    | Fetch a full documentation page by slug and return it as Markdown. Accepts a `version` parameter with `"stable"` as the default and `"latest"` for unreleased or source-build workflows.                                                                                                                          |
| `lookup_api_symbol`    | Look up the documentation for a single API symbol (class, function, constant) by name. Accepts short names like `"Aig"` or fully qualified names like `"aigverse.networks.Aig"`, plus a `version` parameter that defaults to `"stable"`. Returns only the matching section, keeping context compact.              |
| `search_documentation` | Search the documentation by keyword using the ReadTheDocs search API. Accepts a `version` parameter that defaults to `"stable"`, rewrites result URLs to the requested docs version, and returns highlighted snippets. Accepts a `max_results` parameter (default `5`) to control the number of returned results. |

## How It Works

The server fetches documentation pages live from [aigverse.readthedocs.io](https://aigverse.readthedocs.io/en/stable/)
at request time. Stable documentation is the default so that normal agent usage stays aligned with released versions.
When you explicitly select `version="latest"`, the server switches to the unreleased documentation build instead. For
each request, the server:

1. Fetches the HTML page from ReadTheDocs
2. Extracts the main article content using Beautiful Soup (stripping navigation, sidebars, and other page chrome)
3. Converts the cleaned HTML to Markdown for token-efficient LLM consumption

The `lookup_api_symbol` tool goes a step further: it locates the specific HTML fragment for the requested symbol and
returns only that section, rather than the entire (often very long) API page.

## Usage Tips

- Start with `search_documentation` when you don't know the exact page or symbol name.
- Use `lookup_api_symbol` for quick, focused API lookups — it returns far less text than fetching an entire API page.
- Use `get_documentation` when you need the full context of a guide or tutorial page.
- The `aigverse://pages/stable` resource gives the stable index; use `aigverse://pages/latest` when you want the unreleased one.
- If you are using `aigverse` installed from PyPI, stay on the stable docs.
- If you are working on `aigverse` itself or validating an unreleased change, pass `version="latest"` explicitly.

```{note}
Currently, the documentation only distinguishes between `stable` (pointing to the newest release) and `latest` (pointing to the newest GitHub commit on the `main` branch) versions. In the future, we may add more granular versioning (e.g. by release number or git commit) if there is demand for it.
```
