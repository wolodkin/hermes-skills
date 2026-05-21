# Large CSV collections and context limits

## Two separate limits

| Layer | Typical size | Goes into model context? |
|-------|----------------|---------------------------|
| **CSV on disk** | 2 MB – 100+ MB | **Never** |
| **Built system prompt** (`build_prompt.py`) | **≤ ~2 MB** (config) | **Yes** — this is the only data-layer budget |

A 1M-token window does **not** mean you should load large CSVs into the prompt. Nemotron keeps room for conversation, tool output, and reasoning.

## Defaults in `config.json`

```json
"prompt": { "max_total_chars": 2097152 },
"profiling": {
  "large_file_threshold_mb": 2,
  "prompt_max_chars_per_collection": 8000,
  "prompt_sample_cell_max_len": 80
}
```

- **`max_total_chars`**: ~2 MiB (2 097 152 characters) for template + `{{COLLECTIONS_BLOCK}}` combined.
- **`large_file_threshold_mb`**: CSV ≥ 2 MB on disk → sampled profiling (not full in-memory profile).
- If many collections exceed the 2 MB prompt cap, later collections are truncated or omitted with a note in the block.

## Profiling (`profile_collection.py`)

| File size on disk | Mode | Behavior |
|-------------------|------|----------|
| &lt; 2 MB | `full` | Load entire CSV for stats |
| ≥ 2 MB | `sampled` | Line count + stats from first `profile_sample_rows` (default 10 000) |

Sampled profiles: `large_file: true`, `stats_approximate: true`.

## Queries (`query_collection.py`)

Reads the **full** CSV file on disk (RAM-bound). Context limit does not apply to the script — only to what the model sees.

- Use `--count-only`, narrow `--where`, low `--limit`.
- Future: chunked engine (DuckDB/Polars) for 100+ MB without full RAM load.

## Agent rules

1. Never paste CSV rows into chat.
2. Never assume the 1M context can hold the dataset.
3. Treat prompt `sample_rows` as illustrations, not evidence.
4. Evidence = `query_collection.py` JSON only.
