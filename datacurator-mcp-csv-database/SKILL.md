---
name: datacurator
description: Activate with "Hi datacurator" to curate Senckenberg CSVs read-only via mcp-csv-database MCP only; exit with "Ciao". Discovery and prompt via bundled scripts.
version: 1.0.0
author: Alexander Wolodkin & Cursor
category: data
prerequisites:
  commands:
    - python3
---

# datacurator Skill

Curate and answer questions about Senckenberg collection CSVs using **only** the [mcp-csv-database](https://pypi.org/project/mcp-csv-database/) MCP server. Each subfolder under `csv_source_folder_global_path` is one collection (one stem-matched `.csv` + `.txt`). Collection name = folder name; SQLite **table name** = CSV file stem (e.g. `annotated_02`).

Repo folder: `datacurator-mcp-csv-database/`. Install as `~/.hermes/skills/datacurator`.

## Session lifecycle

### Activate (case-insensitive)

Message starts with `hi` and contains the word **`datacurator`** (not `datacurator-python-pandas`).

Examples: `Hi datacurator`, `hi datacurator`

**On activate — before replying:**

1. ```bash
   python3 scripts/discover_collections.py
   python3 scripts/build_prompt.py
   ```
   Under Hermes: `python3 ~/.hermes/skills/datacurator/scripts/build_prompt.py`

2. Delegate **entire stdout** of `build_prompt.py` as the **system prompt** for this session.

3. Set memory: `datacurator.session_active` = `true`

4. **MCP (mandatory):** For each collection you will use, call `load_csv_folder("<folder>")` with `folder` from discovery. Then `list_loaded_tables` and tell the user which `table_name` values are loaded.

5. Reply as curator (collections, languages, MCP-based workflow).

While `datacurator.session_active` is true, **all** data answers use MCP tools only.

### Deactivate

Message is exactly `ciao` / `Ciao` (trimmed).

- `datacurator.session_active` = `false`
- Restore default Hermes prompt
- Do not run curator scripts unless user sends `Hi datacurator` again

### Refresh

`Hi datacurator` again: optional `build_prompt.py --refresh`; stay in curator mode.

## Configuration

Edit [`config.json`](config.json):

| Key | Description |
|-----|-------------|
| `csv_source_folder_global_path` | Root with one subfolder per collection |
| `prompt_template` | System prompt template |
| `prompt.max_total_chars` | ~2 MB cap for full prompt |
| `prompt.description_max_chars` | Optional per-collection `.txt` cap in prompt |
| `mcp.server_name` | MCP server id in client config (default `csv-database`) |
| `query.default_limit` / `query.max_limit` | Guidance for `execute_sql_query` limit (not enforced by scripts) |

MCP server must be registered separately — see [`references/mcp-setup.md`](references/mcp-setup.md).

## Bundled scripts (metadata only — no CSV reads)

| Script | Purpose |
|--------|---------|
| `discover_collections.py` | Manifest + `~/.hermes/state/datacurator.json` |
| `build_prompt.py` | System prompt stdout |
| `suggest_search_terms.py` | Multilingual SQL LIKE helper |

## Per-question workflow (MCP only)

1. Collection + **`table_name`** from prompt (not folder name).
2. `load_csv_folder` if table not in `list_loaded_tables`.
3. `suggest_search_terms.py` when building multi-language LIKE queries.
4. `execute_sql_query` with explicit `limit`; summarize — do not dump huge result sets.
5. `get_data_summary` / `analyze_missing_data` for profiling.
6. Up to 3 search attempts; then say you do not know.

## Do NOT

- Use datacurator-python-pandas scripts or pandas for CSV data in this mode
- `export_table_to_csv` (or any write) under `csv_source_folder_global_path`
- Treat prompt descriptions as row-level evidence without MCP queries
- Imply a 100-row tool result is the full matching set when many rows may exist

## References

- [`references/mcp-setup.md`](references/mcp-setup.md)
- [`references/mcp-tools-readonly.md`](references/mcp-tools-readonly.md)
- [`references/sql-query-language.md`](references/sql-query-language.md)
- [`references/multilingual-search.md`](references/multilingual-search.md)
- [`references/large-collections.md`](references/large-collections.md)

## vs datacurator-python-pandas

| | datacurator (this skill) | datacurator-python-pandas |
|--|--------------------------|---------------------------|
| Data access | MCP only | Bundled Python scripts |
| Activate | `Hi datacurator` | `Hi datacurator-python-pandas` |
