# Experiment rules

- Treat every existing `results/` directory as immutable. New experiment output
  must use a fresh, unique directory and preserve manifest, config, source hashes,
  seed, environment, raw JSONL, summary, and failure status.
- K excludes mirrors. State K, mirror count, horizon, policy, workload profile,
  warm-up rule, seed, backend, and semantic version in every comparison.
- Pair conditions on the same workload seed. Do not treat individual epochs as
  independent replicates when the independent unit is a run/seed.
- Exclude non-comparable branches explicitly; do not impute favorable utilities
  for missing, duplicate, reordered, or faulted inputs.
- Run the relevant tests before and after semantic changes. Preserve earlier
  evidence and state when a new result is not comparable with it.
