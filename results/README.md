# Local immutable experiment evidence

Raw result archives live here and are intentionally excluded from ordinary Git
commits. The working repository currently contains roughly 1 GiB of historical
and active evidence, including many small JSONL files.

- Never overwrite, delete, or silently regenerate an existing run.
- Every new campaign uses a unique directory and frozen source/configuration
  identity.
- Analysis writes derived outputs outside the immutable series directory.
- Numerical claims cite the exact archive and verified analysis that generated
  them.
- Transfer raw archives through the project's research-artifact channel or a
  release/object store when the team needs them; do not force-add this directory.

The canonical result index is [../RESULTS.md](../RESULTS.md).
