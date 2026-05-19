# Cleanup of Stale SiYuan Daily Note IDs

## Problem
The skill caches the document ID of the current day's daily note in Hermes memory under the key `siyuan.daily_note_doc_id_<YYYYMMDD>`. Over time, if the agent runs across month boundaries or if documents are deleted externally, these cached IDs can become stale, leading to failed lookups or unnecessary API calls.

## Solution
At the start of each skill execution, perform a cleanup of any memory keys matching the pattern `siyuan.daily_note_doc_id_*` that do not correspond to today's date (YYYYMMDD). This ensures that only the valid ID for the current day remains in memory.

### Implementation (pseudo‑code)
```bash
# List all memory keys (this would be done via the Hermes memory tool)
# For each key that matches the pattern:
#   if key does not end with today's YYYYMMDD:
#       delete the key
```

## Benefits
- Prevents accumulation of obsolete document IDs.
- Reduces unnecessary API calls to validate stale IDs.
- Keeps the memory footprint small and relevant.

## Note
The actual cleanup is performed by the agent using its internal memory tool; the skill documentation describes the expected behavior so that future maintainers understand the intent.