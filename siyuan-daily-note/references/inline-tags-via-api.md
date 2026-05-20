# Inline Tags via appendBlock

## Problem

SiYuan shows inline tags in the editor as styled marks (not plain text). Typing `#HermInE#` in the UI creates a **textmark tag** stored in the `spans` table (`type = textmark tag`, `content = HermInE`).

Using `/api/block/appendBlock` with `dataType: "markdown"` and body `text\n#HermInE#` (or inline `#HermInE#`) stores literal characters. The tag panel does not list them.

## Solution

Use `dataType: "dom"` and a paragraph with separate spans:

```html
<motion.div class="p" data-type="NodeParagraph">
  <span data-type="text">Your entry text (</span>
  <span data-type="tag" data-info="">HermInE</span>
  <span data-type="text">)</span>
</motion.div>
```

Renders as `Your entry text (HermInE)` — parentheses are plain text spans; `HermInE` is a real inline tag.

The tag **label** is `HermInE` (no `#` wrappers). The bundled script escapes user text with `html.escape`.

## Configuration

`daily_tag` in `~/.hermes/state/siyuan-daily-note.json` may be:

| Value | Normalized label |
|-------|------------------|
| `HermInE` | `HermInE` |
| `#HermInE#` | `HermInE` |
| `(#HermInE)` | `HermInE` |

## Verification

After append, SQL:

```sql
SELECT content, type FROM spans WHERE block_id = '<new-block-id>';
```

Expect a row with `type = textmark tag` and `content = HermInE`.

Or check the tag panel (`Alt+4`) for label `HermInE`.

## Note on manual editing

In the UI, tags still display with `#` delimiters when editing. API-created tags use the same underlying textmark; appearance matches native tags.
