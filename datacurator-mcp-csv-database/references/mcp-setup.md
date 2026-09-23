# MCP setup for datacurator

## Install

```bash
pip install mcp-csv-database==0.1.7
```

Requires Python 3.10+.

## Hermes

Register the server in your Hermes MCP configuration (path depends on install). Example:

```json
{
  "mcpServers": {
    "csv-database": {
      "command": "mcp-csv-database"
    }
  }
}
```

**Do not** pass the data root as the only startup path if CSVs live in subfolders (Senckenberg layout). The agent loads each collection with `load_csv_folder("<collection-folder>")`.

Install the skill:

```bash
ln -s /path/to/hermes-skills/datacurator-mcp-csv-database ~/.hermes/skills/datacurator
```

Set `csv_source_folder_global_path` in `config.json` (absolute or relative to the skill directory).

## Cursor

Add the same `mcpServers` entry to `.cursor/mcp.json` (project or user level).

## Verify

1. MCP server appears in the client tool list.
2. `cd` to the skill directory; run `python3 scripts/discover_collections.py`.
3. Activate in chat: `Hi datacurator`.
4. Agent calls `load_csv_folder` on a collection folder, then `list_loaded_tables`.
