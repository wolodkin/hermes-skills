# Large collections and query limits

## Two layers

| Layer | Typical size | In chat / system prompt? |
|-------|----------------|---------------------------|
| CSV on disk | MB to 100+ MB | Never inlined |
| Built system prompt | Up to ~2 MB (`prompt.max_total_chars`) | Collection `.txt` descriptions only |
| MCP `execute_sql_query` result | Capped by tool `limit` (default 100) | Summarized by agent |

## What `limit` means

Each `execute_sql_query(..., limit=N)` returns at most **N rows** in that tool output. If 20 000 rows match Germany filters, the database still has 20 000 matches — the agent only *sees* N unless it runs another query (OFFSET, aggregate, or higher limit).

`query.max_limit` in `config.json` is a **recommended ceiling** for N per call, not a second quota.

## Good practices (no mandatory COUNT-first)

- Prefer **aggregates** (`GROUP BY`, `COUNT(*)` when the user asks for counts).
- Show **small samples** and label them as samples when matches are large.
- Ask the user to **narrow** (region, taxon, date) if they need a full list.
- Use `get_data_summary` / `analyze_missing_data` instead of scanning all rows in chat.
- Never paste huge tool JSON verbatim into the reply.

## Many collections

Load collections on demand with `load_csv_folder`. Use `list_loaded_tables` before SQL.

## Reload after CSV changes on disk

`clear_database` (temp SQLite only), then `load_csv_folder` again for that collection folder.
