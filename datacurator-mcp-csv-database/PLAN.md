---
name: datacurator Skill (MCP)
overview: Hermes skill datacurator — MCP-only CSV curation, activate Hi datacurator, repo folder datacurator-mcp-csv-database.
todos:
  - id: scaffold
    content: config, scripts, .gitignore, requirements
    status: completed
  - id: adapt-annotated-txt
    content: annotated_02.txt MCP/SQL + EN summary
    status: completed
  - id: skill-docs
    content: SKILL.md, README.md, references, prompt_template
    status: completed
isProject: false
---

# datacurator — Implementation plan (MCP)

**Skill ID:** `datacurator`  
**Repo folder:** `datacurator-mcp-csv-database/`  
**Activate:** `Hi datacurator` · **Exit:** `Ciao`

## Architecture

- Discovery / prompt: Python scripts (filesystem `.txt` only).
- All CSV row data: **mcp-csv-database** MCP tools on temp SQLite.
- Per collection: `load_csv_folder("<collection-folder>")` → table name = CSV stem.

## Configuration

See [config.json](config.json). Data root defaults to `./csv_source_folder_global_path` relative to skill dir.

## Read-only policy

No writes/exports under `csv_source_folder_global_path`. MCP temp DB operations allowed.

## Query limits

`execute_sql_query` `limit` caps rows per tool call (MCP default 100). `query.max_limit` in config is agent guidance only.

## Test

```bash
cd datacurator-mcp-csv-database
python3 scripts/discover_collections.py
python3 scripts/build_prompt.py | head -60
python3 scripts/suggest_search_terms.py --term "Deutschland" --lang de
```

Manual: MCP `load_csv_folder` → `list_loaded_tables` → `get_data_summary('annotated_02')`.
