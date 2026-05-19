# Hierarchical Daily Note Storage (v3)

As of skill v3, daily notes use **one document per UTC day** at:

```
/daily note/YYYY/MM/YYYY-MM-DD.sy
```

Multiple entries on the same day are appended via `appendBlock` to the same document ID (cached in `~/.hermes/state/siyuan-daily-note.json`).

## No flat-document fallback

Earlier drafts supported a single flat document named `daily note` at the notebook root. That fallback was removed to match the user's path convention and avoid ambiguity.

## Why duplicates happened (v2)

The create-only skill called `createDocWithMd` with user text on every trigger instead of appending. Combined with unreliable `listDocsByPath` on parent folders, each invocation could create a new document. v3 fixes this with the bundled script, state cache, idempotent empty create, and `appendBlock`.
