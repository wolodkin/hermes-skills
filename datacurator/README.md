# datacurator (Hermes Skill)

Read-only exploration and Q&A over Senckenberg collection CSVs. One folder per collection (CSV + TXT description).

## Activate and exit

| User says | Effect |
|-----------|--------|
| `Hi datacurator` / `hi datacurator` (starts with `hi`, contains `datacurator`) | Enter **curator mode**: run `build_prompt.py`, delegate full stdout as **system prompt** to the chat model, then converse as curator |
| Any message while curator mode is active | Stay in curator mode; use scripts for data questions |
| `Ciao` / `ciao` (only) | **Exit** curator mode; restore default Hermes model/system prompt |

Why delegate? The enriched prompt (descriptions, profiles, sample rows) needs a stable system context; keeping it on the session model avoids squeezing that into every Hermes turn.

See [SKILL.md](SKILL.md) for the full procedure and memory key `datacurator.session_active`.

## Quick start

```bash
cd datacurator
pip install -r requirements.txt
# Edit config.json — set csv_source_folder_global_path
python3 scripts/discover_collections.py
python3 scripts/build_prompt.py | head -60
python3 scripts/query_collection.py \
  --collection "Algae and Protists" \
  --where "Taxon.str.contains('Azadinium', case=False, na=False)" \
  --limit 5
```

## Layout

| Path | Purpose |
|------|---------|
| [SKILL.md](SKILL.md) | Hermes agent procedure |
| [config.json](config.json) | User-editable paths and limits |
| [prompt_template.txt](prompt_template.txt) | Base system prompt; `{{COLLECTIONS_BLOCK}}` filled by `build_prompt.py` |
| [scripts/](scripts/) | Discovery, profile, sample, query, prompt build |
| [references/](references/) | Query syntax and profile field docs |

## Data layout

```
csv_source_folder_global_path/
  Algae and Protists/
    *.csv
    *.txt   # collection description for the prompt
```

## Hermes install

Copy or link this folder to `~/.hermes/skills/datacurator/`. See [SKILL.md](SKILL.md) for the full workflow.

## License

See repository [LICENSE](../LICENSE).
