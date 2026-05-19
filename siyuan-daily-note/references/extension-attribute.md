# Extension Attribute Naming Scheme

SiYuan's built-in daily note workflow (since v2.11.1) uses a **custom block attribute** with this exact pattern:

```
custom-dailynote-<YYYYMMDD>
```

where `<YYYYMMDD>` is the zero-padded date (e.g. `20260518`). The attribute **value** must be the same date string (`20260518`).

This matches [siyuan-note/siyuan#9807](https://github.com/siyuan-note/siyuan/issues/9807) and what appears in the `attributes` SQL table for native daily notes.

> **Not** `dailynote-<YYYYMMDD>` without the `custom-` prefix — that name is ignored by SiYuan and will not show up in queries or extensions.

## How the skill sets the attribute

`createDocWithMd` does **not** reliably store document attrs on this deployment. The bundled script therefore calls:

```
POST /api/attr/setBlockAttrs
{
  "id": "<DOCUMENT_ID>",
  "attrs": { "custom-dailynote-20260518": "20260518" }
}
```

This runs after the day document is resolved or created, and on every append if the attribute is still missing (repairs older Hermes-created notes).

## Lookup by attribute

To find today's document without relying on path listing:

```sql
SELECT block_id FROM attributes
WHERE name = 'custom-dailynote-20260518' AND value = '20260518'
LIMIT 1
```

The script uses this as the preferred doc resolver before falling back to `hpath`.

## Verification

1. Open the daily note in SiYuan.
2. Properties panel → look for `custom-dailynote-<today>` = `<today>`.
3. Or run SQL against the `attributes` table (see above).

## Troubleshooting

* **`setBlockAttrs` returns "tree not found"** — the document ID may be orphaned (not in `blocks`). Create a fresh note via the script or merge duplicates in SiYuan.
* **Attribute missing after create** — expected if only `createDocWithMd` attrs were used; re-run the script once to repair via `setBlockAttrs`.
* **Extension still ignores the note** — confirm the name is exactly `custom-dailynote-<YYYYMMDD>` (case-sensitive, no spaces).
