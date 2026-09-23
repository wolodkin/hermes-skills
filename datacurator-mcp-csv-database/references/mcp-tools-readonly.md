# MCP tools — read-only on source files

Policy: **never write or export into** `csv_source_folder_global_path` (collection `.csv` / `.txt` on disk). MCP uses a temporary SQLite copy.

## Allowed (typical curator workflow)

| Tool | Use |
|------|-----|
| `load_csv_folder` | Load one collection folder (one `*.csv` per folder) |
| `list_loaded_tables` | Confirm queryable tables |
| `get_database_schema` / `get_table_info` | Schema and samples |
| `get_data_summary` | Overview |
| `analyze_missing_data` / `find_duplicates` | Quality |
| `get_column_stats` | Column statistics |
| `execute_sql_query` | Queries on loaded tables; set `limit` per call |
| `get_query_plan` | Explain query |
| `create_index` | Temp DB performance only |
| `clear_database` | Reload after source CSV changed (temp data only) |

## Forbidden or restricted

| Tool / action | Reason |
|---------------|--------|
| `export_table_to_csv` → path under data root | Would write files next to source CSVs |
| `backup_database` → path under data root | Same |
| Editing `.csv` / `.txt` on disk | Out of scope; use MCP on copies |
| Shell / pandas / custom scripts reading CSV for answers | Use MCP only in curator mode |

## execute_sql_query

- Not limited to `SELECT` on the temp database, but curator answers should use `SELECT` / aggregates for user questions.
- `limit` on the tool caps **rows returned in that tool result** (MCP default 100). It is not the number of “relevant” rows in the collection.
- Quote SQLite column names with double quotes when they contain spaces or dots.
