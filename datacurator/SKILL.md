---
name: datacurator
description: Activate with "Hi datacurator" to run as collection curator with enriched system prompt; exit with "Ciao". Discover, profile, sample, and query Senckenberg CSVs read-only via bundled scripts.
version: 1.0.0
author: Alexander Wolodkin & Cursor
category: data
prerequisites:
  commands:
    - python3
---

# datacurator Skill

Curate and answer questions about Senckenberg collection CSVs. Each subfolder under `csv_source_folder_global_path` is one collection (one `.csv` + one `.txt` description). Collection name = folder name.

## Session lifecycle (activate / deactivate)

datacurator runs in a **delegated mode**: a dedicated model context with the full curator system prompt (rich collection context). Normal Hermes resumes after exit.

### Activate (case-insensitive)

The skill **enters delegated mode** when the user message matches:

- Starts with `hi` (optional trailing space), **and**
- Contains the word `datacurator` (substring match is enough)

Examples: `Hi datacurator`, `hi datacurator`, `Hi  datacurator`

**On activate — do this before replying:**

1. Run discovery and build the enriched system prompt:

   ```bash
   python3 scripts/discover_collections.py
   python3 scripts/build_prompt.py
   ```

   Under Hermes, use the installed skill path, e.g.  
   `python3 ~/.hermes/skills/datacurator/scripts/build_prompt.py`

2. **Delegate to the curator model:** apply the **entire stdout** of `build_prompt.py` as the **system prompt** for the current chat session (replace or overlay the default Hermes system prompt for this thread). This keeps collection descriptions, profiles, and sample rows in context without re-loading them every turn.

3. Set Hermes memory: `datacurator.session_active` = `true` (and optionally store `datacurator.activated_at` ISO timestamp).

4. Reply as the data curator: follow the “First task” in the built prompt (introduce yourself, list collections, languages you can use).

While `datacurator.session_active` is true, **all user messages** in this session are handled in **curator mode** (same system prompt, use bundled scripts for data questions). Do not revert to the default Hermes persona mid-session unless the user deactivates.

### Deactivate (case-insensitive)

The skill **exits delegated mode** when the user message is exactly:

- `ciao` or `Ciao` (trim whitespace; no other text required)

**On deactivate:**

1. Set `datacurator.session_active` = `false`.
2. **Restore the original Hermes session:** drop the curator system prompt overlay and return to the default Hermes model/system prompt for this thread.
3. Confirm briefly that datacurator mode ended and Hermes continues as usual.
4. Do **not** run collection scripts unless the user starts a new session with `Hi datacurator` again.

### If already active

- `Hi datacurator` again: optional refresh (`build_prompt.py --refresh`); stay in curator mode.
- Unrelated messages while active: stay in curator mode; answer as curator using scripts.

## Configuration

Edit [`config.json`](config.json):

| Key | Description |
|-----|-------------|
| `csv_source_folder_global_path` | Absolute path to the data root folder |
| `prompt_template` | Path to system prompt template (relative to skill dir) |

Install dependencies once:

```bash
pip install -r requirements.txt
```

## Required scripts only

Run from the skill directory. Under Hermes:

```bash
python3 ~/.hermes/skills/datacurator/scripts/<script>.py ...
```

Never improvise pandas or shell CSV reads in the sandbox.

## Curator session setup (after activate)

Runs as part of **Activate** above, not on every unrelated Hermes message:

1. `discover_collections.py` — refresh manifest + state
2. `build_prompt.py` — stdout becomes the delegated **system prompt**
3. Re-run with `--refresh` after data or config changes, or when the user asks to reload collections

## Per-question workflow

1. Parse the user's search concept in their language.
2. Expand to **English and Latin/scientific** variants (never query a single translation only).  
   Helper: `python3 scripts/suggest_search_terms.py --term "…" --lang de`
3. Run `query_collection.py` with an OR `str.contains` pattern across relevant columns (`Taxon`, `Substrat`, `Habitat`, `Bemerkung`, …).
4. Summarize JSON results — do not paste full CSVs or hundreds of rows.
5. Up to 3 attempts: broaden EN/LA stems or columns, then narrow if too noisy; if still empty, say so.

See [`references/multilingual-search.md`](references/multilingual-search.md).

## Phase scripts

| Phase | Script |
|-------|--------|
| 1 Discovery | `discover_collections.py` |
| 2 Profiling | `profile_collection.py --collection "NAME"` |
| 3 Sampling | `sample_collection.py --collection "NAME" [--n 8]` |
| 4 Query | `query_collection.py --collection "NAME" ...` |

State file: `~/.hermes/state/datacurator.json`

## Large CSVs and context budget

**CSV on disk** can be 100+ MB. **System prompt** (including collection metadata) is capped at **~2 MB** (`prompt.max_total_chars` in `config.json`, default 2 097 152). Nemotron 1M context is not used to hold raw tables.

| Layer | Behavior |
|-------|----------|
| System prompt | `build_prompt.py` — max ~2 MB total; ~8k chars per collection (defaults) |
| Profiling | Sampled mode when CSV ≥ **2 MB** on disk (`large_file_threshold_mb`) |
| Queries | Full file read in script only — `--count-only`, tight `--where`, low `--limit` |

See [`references/large-collections.md`](references/large-collections.md).

## Do NOT

- Modify files under `csv_source_folder_global_path`
- Dump entire CSV contents into chat (even with 1M context)
- Answer about collections not listed in discovery output
- Use hypothetical data when queries return nothing
- Treat `sample_rows` in the prompt as complete evidence

## References

- [`references/query-language.md`](references/query-language.md)
- [`references/profiling-fields.md`](references/profiling-fields.md)
- [`references/large-collections.md`](references/large-collections.md)
- [`references/multilingual-search.md`](references/multilingual-search.md)
- [`scripts/`](scripts/) — canonical implementation
