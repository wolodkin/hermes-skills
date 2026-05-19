---
name: siyuan-daily-note
description: Create or append to a daily note in the user's SiYuan knowledge base.
version: 3.0.0
author: Alexander Wolodkin & Cursor
category: productivity
prerequisites:
  env_vars:
    - SIYUAN_TOKEN
    - SIYUAN_URL
  commands:
    - python3
---

# SiYuan Daily Note Skill

This skill appends a line of text to **today's** daily note in SiYuan. Multiple triggers on the same UTC day reuse the same document and add blocks — no duplicate day files.

## Conventions

- Notebook: **Daily Notes** (override via state file `notebook_name` or memory `siyuan.daily_notebook`)
- Path: `/daily note/YYYY/MM/YYYY-MM-DD.sy` (UTC, zero-padded month/day)
- Tag after each entry: `#HermInE#` — SiYuan inline tag syntax (override via state file `daily_tag` or memory `siyuan.daily_tag`). Do not use `(#…)`; parentheses are not valid in tags and SiYuan will not index them.
- Extension attribute: `custom-dailynote-<YYYYMMDD>` = `<YYYYMMDD>` (set via `setBlockAttrs`, SiYuan native format)
- Never delete or overwrite existing blocks; only append

## Trigger Detection (case-insensitive)

The skill activates when the message starts with one of these prefixes, followed by `:` or `,`:

| Prefix | Example |
|--------|---------|
| `Day` / `day` | `Day: Review finished` |
| `Daily` / `daily` | `Daily, Sent status update` |
| `Dailynote` / `dailynote` | `Dailynote: …` |
| `daily note` | `daily note, Meeting notes` |

Extract the text after the delimiter, trim whitespace — that is the line to append.

## Required Environment Variables

| Variable | Description |
|----------|-------------|
| `SIYUAN_TOKEN` | API token (SiYuan → Settings → About) |
| `SIYUAN_URL` | Base URL without trailing slash |

Set in `~/.hermes/.env` (or your environment when running the script standalone).

## Step-by-Step Procedure

1. **Parse the user message** — extract `TEXT_TO_ADD` using the trigger rules above.

2. **Run the bundled script only** (do not improvise curl/API calls):

   ```bash
   python3 scripts/append_daily_note.py "TEXT_TO_ADD"
   ```

   Run from the skill directory. Under Hermes Agent, use the installed skill path, e.g.  
   `python3 ~/.hermes/skills/siyuan-daily-note/scripts/append_daily_note.py "TEXT_TO_ADD"`.

3. **Check the result**
   - Exit code `0`: stdout is JSON, e.g. `{"ok": true, "doc_id": "…", "path": "/daily note/…", "ymd": "20260518", "attr": "custom-dailynote-20260518"}`
   - Confirm to the user that the entry was appended and include `doc_id` if helpful.
   - Non-zero exit: read stderr, report the error.

4. **Optional — mirror doc ID in Hermes memory**
   - After success, set `siyuan.daily_note_doc_id_<YYYYMMDD>` to the returned `doc_id`.
   - At skill start, delete stale keys `siyuan.daily_note_doc_id_*` whose date is not today (see `references/cleanup-stale-ids.md`).

## State File (primary cache)

The script persists today's document ID in:

`~/.hermes/state/siyuan-daily-note.json`

```json
{
  "notebook_name": "Daily Notes",
  "daily_tag": "#HermInE#",
  "doc_ids": { "20260518": "20260518120000-abc1234" }
}
```

Only the current `ymd` entry is kept.

## What the Script Does (reference)

1. Load env from `~/.hermes/.env`
2. Read cached `doc_id` for today; verify with `/api/filetree/getHPathByID` (not `getDocByID` — often 404)
3. If missing: SQL lookup by attribute `custom-dailynote-<YMD>` = `<YMD>`
4. Else SQL lookup by `hpath` `/daily note/YYYY/MM/YYYY-MM-DD` (oldest `type=d` match)
5. If still missing: `createDocWithMd` with empty `markdown`
6. `setBlockAttrs` with `custom-dailynote-<YMD>` = `<YMD>` if not already set (repairs legacy docs)
7. `appendBlock` with user text + tag; retry lookup on append failure
8. Save `doc_id` to state file

## Do NOT

- Call `createDocWithMd` with user text on every invocation (creates duplicates)
- Rely on `listDocsByPath` alone to find the day document (unreliable for parent folders)
- Write one-off Python in the sandbox instead of the bundled script

## Result

The user's line is appended as a new block in `/daily note/<YEAR>/<MONTH>/<YYYY-MM-DD>.sy`. Repeated calls the same UTC day use the same `doc_id`.

## Pitfalls

- **Path must not include the notebook name** — use `/daily note/...`, not `/Daily Notes/daily note/...`
- **UTC date** — near local midnight, "today" may differ from your timezone
- **Missing env vars** — script exits with an error; fix `~/.hermes/.env`
- **Orphan duplicates from older create-only runs** — merge or delete manually in SiYuan once

## Related References

- `scripts/append_daily_note.py` — canonical implementation
- `references/python-append-example.md` — usage notes for the script
- `references/extension-attribute.md` — `custom-dailynote-<YYYYMMDD>` attribute
- `references/cleanup-stale-ids.md` — Hermes memory cleanup
- `references/lesson-learned-document-reuse.md` — why append + state cache
- `references/flat-vs-hierarchical-note.md` — one document per UTC day
- `templates/daily-note-example.md` — example multi-entry document

## Notes for Future Maintenance

- Notebook rename: update `notebook_name` in the state file or memory `siyuan.daily_notebook`
- Tag change: update `daily_tag` in the state file or memory `siyuan.daily_tag`
- Test on a disposable SiYuan instance before production changes

---

*End of skill.*
