# Example Daily Note Entry

This is an example of what a daily note document looks like after several skill invocations on the same day.

## Structure

- One SiYuan document per UTC day: `/daily note/YYYY/MM/YYYY-MM-DD.sy`
- Each trigger appends a separate block
- Each block ends with `#HermInE#` (SiYuan inline tag)
- Document attribute: `custom-dailynote-<YYYYMMDD>` = `<YYYYMMDD>` (SiYuan native; set via `setBlockAttrs`)

## Example Content

```
Deliverable A review finished
#HermInE#

Publication abstract under review, waiting for feedback
#HermInE#

Issue solved, branch merged, more coffee needed
#HermInE#
```

## Notes

- Blocks are stored as rich text in SiYuan
- Existing entries must not be edited or deleted by the skill — append only
- Orphan documents from skill v2 may exist; merge or delete those manually in SiYuan
