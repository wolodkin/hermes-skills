# datacurator (Hermes Skill, MCP)

Read-only Q&A over Senckenberg collection CSVs via [mcp-csv-database](https://pypi.org/project/mcp-csv-database/). One folder per collection; `.csv` and `.txt` share the same basename (e.g. `annotated_02.csv` / `annotated_02.txt`).

**Git folder:** `datacurator-mcp-csv-database/`  
**Skill name / activate:** `datacurator` — say `Hi datacurator`  
**Hermes install:** `~/.hermes/skills/datacurator` (symlink to this directory)

## Prerequisites

```bash
pip install mcp-csv-database
```

Register MCP server `csv-database` — see [references/mcp-setup.md](references/mcp-setup.md).

## Quick start

```bash
cd datacurator-mcp-csv-database
# Edit config.json — csv_source_folder_global_path (default: ./csv_source_folder_global_path)
python3 scripts/discover_collections.py
python3 scripts/build_prompt.py | head -80
python3 scripts/suggest_search_terms.py --term "Deutschland" --lang de --table annotated_02
```

In Hermes/Cursor with MCP enabled: `Hi datacurator` → agent loads collections via MCP and answers with SQL.

Exit: `Ciao`

## Data layout

```
csv_source_folder_global_path/
  Algae and Protists/
    annotated_02.csv
    annotated_02.txt    # collection spec → system prompt
```

MCP: `load_csv_folder("/…/Algae and Protists")` → table `annotated_02` (not the folder name).

## Layout

| Path | Purpose |
|------|---------|
| [SKILL.md](SKILL.md) | Agent procedure |
| [config.json](config.json) | Paths and limits |
| [prompt_template.txt](prompt_template.txt) | Base system prompt |
| [scripts/](scripts/) | Discovery, prompt build, search helper |
| [references/](references/) | MCP setup, SQL, multilingual search |

## Pandas skill

For CLI/pandas-based curation use [datacurator-python-pandas](../datacurator-python-pandas/) (`Hi datacurator-python-pandas`).

## License

See repository [LICENSE](../LICENSE).
