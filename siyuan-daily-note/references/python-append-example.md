# Python Implementation (Bundled Script)

The skill uses a single bundled script — do not duplicate this logic in the sandbox.

**Path:** `scripts/append_daily_note.py`

## Usage

```bash
python3 ~/.hermes/skills/siyuan/siyuan-daily-note/scripts/append_daily_note.py "Your note text here"
```

On success (exit 0), stdout is one JSON line:

```json
{"ok": true, "doc_id": "20260518120000-abc1234", "path": "/daily note/2026/05/2026-05-18.sy", "ymd": "20260518"}
```

## Dependencies

- Python 3.8+
- Stdlib only (`urllib`, `json`) — no `pip install` required
- `SIYUAN_TOKEN` and `SIYUAN_URL` in `~/.hermes/.env`

## State

Document IDs are cached in `~/.hermes/state/siyuan-daily-note.json`. See `SKILL.md` for the schema.

## API flow (summary)

1. Cached `doc_id` + `getHPathByID` validation
2. Else SQL lookup by `custom-dailynote-<YMD>` attribute
3. Else SQL lookup by `hpath`
4. Else `createDocWithMd` with empty markdown
5. `setBlockAttrs` with `custom-dailynote-<YMD>` = `<YMD>`
6. `appendBlock` with `dataType: "markdown"`

See `references/extension-attribute.md` for attribute naming.
