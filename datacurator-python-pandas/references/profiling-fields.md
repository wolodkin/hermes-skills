# Profiling output fields

`profile_collection.py` writes a JSON profile per collection to `~/.hermes/state/datacurator-python-pandas.json` under `profiles.<collection_name>`.

| Field | Meaning |
|-------|---------|
| `row_count` | Number of data rows |
| `column_count` | Number of columns |
| `columns[]` | Per column: `name`, `dtype`, `null_count`, `null_pct`, `non_null_count`, `n_unique`, optional `max_str_len` |
| `numeric_summary` | min/max/mean for columns that parse as numeric |
| `categorical_top_values` | Top values for low-cardinality columns |
| `duplicate_rows` | Fully duplicate row count |
| `empty_columns` | 100% null or empty |
| `high_null_columns` | Above threshold from config (default 90%) |
| `json_like_columns` | Many cells contain `{...}` structured text |
| `memory_bytes` | Approximate in-memory size |

`profile_summary` in the built prompt is a one-line human summary derived from these fields.
