# SiYuan Daily Note (Hermes Skill)

**Works with [siyuan-plugin-calendar](https://github.com/gradypark86/siyuan-plugin-calendar).** This skill creates and appends to daily notes in SiYuan using the same document layout and block attributes that the calendar plugin expects. Each day’s document gets the native attribute `custom-dailynote-<YYYYMMDD>` = `<YYYYMMDD>` (via `setBlockAttrs`), so calendar-driven navigation and agent-driven entries stay aligned.

A [Hermes](https://github.com/) agent skill that appends a line of text to **today’s** daily note in your SiYuan knowledge base. Multiple invocations on the same UTC day reuse one document and add blocks—no duplicate day files.

## Features

- **Append-only** — never deletes or overwrites existing blocks
- **One document per UTC day** at `/daily note/YYYY/MM/YYYY-MM-DD.sy`
- **Calendar-compatible attributes** — sets `custom-dailynote-<YYYYMMDD>` on the document (SiYuan’s built-in daily-note format)
- **Smart resolution** — cache, attribute SQL lookup, then path fallback before creating a new doc
- **Configurable** notebook name and trailing tag via state file or Hermes memory

## Prerequisites

| Requirement | Description |
|-------------|-------------|
| [SiYuan](https://github.com/siyuan-note/siyuan) | Running instance with API enabled |
| [siyuan-plugin-calendar](https://github.com/gradypark86/siyuan-plugin-calendar) | Recommended for calendar UI and periodic notes; uses the same daily-note paths and attributes |
| Hermes Agent | To use this folder as an installed skill (optional for script-only use) |
| `python3` | 3.8+, stdlib only |
| `SIYUAN_TOKEN` | API token (SiYuan → Settings → About) |
| `SIYUAN_URL` | Base URL without trailing slash |

Store credentials in `~/.hermes/.env`:

```env
SIYUAN_TOKEN=your-token-here
SIYUAN_URL=http://127.0.0.1:6806
```

## Usage with Hermes

The skill activates when your message starts with one of these prefixes (case-insensitive), followed by `:` or `,`:

| Prefix | Example |
|--------|---------|
| `Day` / `day` | `Day: Review finished` |
| `Daily` / `daily` | `Daily, Sent status update` |
| `Dailynote` / `dailynote` | `Dailynote: Standup notes` |
| `daily note` | `daily note, Meeting notes` |

The text after the delimiter is appended as one paragraph with an inline tag (default label `HermInE`). The script uses SiYuan DOM textmarks because `appendBlock` with markdown does not register `#tag#` as a real tag.

Install the skill in your Hermes skills directory and ensure `SIYUAN_TOKEN` and `SIYUAN_URL` are set. See [SKILL.md](SKILL.md) for the full agent procedure.

## Standalone script

You can run the bundled script without the agent:

```bash
python3 scripts/append_daily_note.py "Your note text here"
```

On success, stdout is JSON, for example:

```json
{
  "ok": true,
  "doc_id": "20260518120000-abc1234",
  "path": "/daily note/2026/05/2026-05-18.sy",
  "ymd": "20260518",
  "attr": "custom-dailynote-20260518"
}
```

## Integration with siyuan-plugin-calendar

The [calendar plugin](https://github.com/gradypark86/siyuan-plugin-calendar) creates daily notes from the calendar UI and supports weekly, monthly, and yearly periodic notes. This skill targets the **daily** workflow:

| Aspect | Behavior |
|--------|----------|
| **Path** | `/daily note/YYYY/MM/YYYY-MM-DD.sy` under notebook **Daily Notes** (overridable) |
| **Attribute** | `custom-dailynote-<YYYYMMDD>` = `<YYYYMMDD>` on the document block |
| **Why** | Matches SiYuan’s native daily-note attribute (since v2.11.1). Notes created by the agent are findable the same way as notes created from the calendar. |
| **Repair** | If an older note is missing the attribute, the script sets it on the next append |

`createDocWithMd` alone does not reliably persist these attrs on every deployment; the script always calls `POST /api/attr/setBlockAttrs` after resolve or create. See [references/extension-attribute.md](references/extension-attribute.md) for details.

Configure the calendar plugin’s daily-note notebook and path to match this skill (default notebook **Daily Notes**, path under `daily note/`). Then calendar clicks and agent triggers land on the same documents.

## Conventions

- **Notebook:** `Daily Notes` (override in `~/.hermes/state/siyuan-daily-note.json` → `notebook_name`, or Hermes memory `siyuan.daily_notebook`)
- **Tag:** `HermInE` (override via `daily_tag`; `#HermInE#` in config is normalized to the label)
- **Date:** UTC for “today” (near local midnight, the active day may differ from your timezone)
- **Path:** Do not include the notebook name in API paths—use `/daily note/...`, not `/Daily Notes/daily note/...`

## State file

Document IDs are cached at:

`~/.hermes/state/siyuan-daily-note.json`

```json
{
  "notebook_name": "Daily Notes",
  "daily_tag": "HermInE",
  "doc_ids": { "20260518": "20260518120000-abc1234" }
}
```

Only the current UTC day’s entry is kept.

## Repository layout

| Path | Purpose |
|------|---------|
| [SKILL.md](SKILL.md) | Hermes skill definition and step-by-step procedure |
| [scripts/append_daily_note.py](scripts/append_daily_note.py) | Canonical implementation |
| [references/](references/) | Attributes, cleanup, pitfalls, examples |
| [templates/daily-note-example.md](templates/daily-note-example.md) | Example multi-entry document |

## Pitfalls

- **Duplicate day files** — do not call `createDocWithMd` with user text on every run; always use the bundled script
- **Orphan docs** — legacy runs may have left extras; merge or delete manually in SiYuan once
- **Missing env** — script exits with an error if `SIYUAN_TOKEN` or `SIYUAN_URL` is unset

## License

See repository license file if present. Skill metadata: see [SKILL.md](SKILL.md) front matter.

## Author

Alexander Wolodkin