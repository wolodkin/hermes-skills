# Lesson Learned: Document Reuse and Hierarchical Path Creation in SiYuan

## Problem
When using `/api/filetree/createDocWithMd` to create a daily note at a hierarchical path
(e.g., `/daily note/2026/05/2026-05-18.sy`), the SiYuan API does not automatically
create missing parent directories (`2026/05/`). Although the document is created and
accessible via its ID, subsequent calls to `/api/filetree/listDocsByPath` for the
parent folder return "no such file or directory". This caused the skill to repeatedly
create new documents instead of reusing the existing one, leading to many orphaned
document IDs that are not visible in the folder listing.

## Solution
Added a memory‑based cache that stores the document ID for the current date
(key `siyuan.daily_note_doc_id_<YYYYMMDD>`). Before attempting to locate or create
a document, the skill checks this cache and verifies the ID still exists via
`/api/filetree/getDocByID`. If valid, it reuses the same document, avoiding
unnecessary creation.

Additionally, the skill now prefers the existing flat document named "daily note"
in the notebook root (if present) before falling back to hierarchical path
creation, aligning with the user's actual SiYuan setup where a single
`daily note` document holds all daily entries.

## Verification
After the fix, multiple entries for the same date are appended to the same
document, as evidenced by increasing block counts while the document ID remains
constant.