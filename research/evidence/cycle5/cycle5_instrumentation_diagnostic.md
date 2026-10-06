# Cycle 5 instrumentation retention diagnostic

**Status:** Locally measured after all 86 main campaign runs completed. No
diagnostic overlapped measured production, and CSC source was not changed.

## Question, evidence and method

Does constructing a new Windows `Counters` ctypes type on every resource sample
retain those classes indefinitely, or create cycles reclaimed by garbage
collection? The specific persistent-Counters prediction was **not observed**:
all observed class weak references were dead after collection in both blocks.
This does not establish general memory-leak freedom or a long-run memory plateau.

Primary evidence: `results/cycle5-validation/os-metrics-cache-20261006-v3/diagnostic.json`; mechanism confirmation:
`results/cycle5-validation/os-metrics-cache-20261006-v4/diagnostic.json`. The deterministic
analyzer is `experiments/cycle5_instrumentation_analysis.py`, with verified
machine output at `research/tables/cycle5_instrumentation_diagnostic.json`.
Both archives have valid artifact/config/script identities and the unchanged
measurement-source hash `51e46e590d517cbca0089c73bad792ad3f66b544b43feefa36da2a31dbff62de`.

Each probe preloaded one call, then measured blocks of 10 and 100 self-process
samples with current/peak Python allocations, GC-visible `Counters` classes and
weak references before and after explicit collection. This is Python
3.14.7 on Windows-11-10.0.26300-SP0.

Python 3.14 documentation describes pointer-type caching through a type's
`__pointer_type__` attribute. The documentation opened during this cycle was
Python 3.14.8; the actual measured runtime was 3.14.7. See the
[official ctypes POINTER documentation](https://docs.python.org/3.14/library/ctypes.html#ctypes.POINTER).
The v4 confirmation observed this attribute through normal attribute lookup on
10 and 14 live classes, with matching pointed-to-class
backreferences, despite the attribute being absent from the classes' own
dictionaries. All those classes were subsequently collected.

## Primary findings

| Phase | Live Counters | Observed weakrefs still reachable | Python current bytes |
|---|---:|---:|---:|
| baseline | 0 | 0 | 992 |
| after_10_calls | 10 | 10 | 191500 |
| after_10_calls_gc | 0 | 0 | 7900 |
| after_110_calls | 14 | 14 | 309732 |
| after_110_calls_gc | 0 | 0 | 26078 |

Ten calls took 8.7500 ms total
(0.8750 ms/call); the next 100 calls took
76.9254 ms (0.7693 ms/call).
These are post-collection microdiagnostic timings, not reconstructed main-run
instrumentation costs. The probes do not explain a production cadence change.

Residual traced allocations increased from 992
bytes at baseline to 26078 bytes after the final
collection. Diagnostic bookkeeping, ctypes allocations and allocator behavior
remain included; zero surviving target classes does not mean zero retained
allocation. The broader memory question is decided from the main long-run
current-allocation/RSS trends in `research/evidence/cycle5/cycle5_results_analysis.md`, rather
than from this short probe. Positive main-run slopes must not be reinterpreted
as a plateau because this one mechanism was not detected.

## Preserved attempts and limitations

V1 is an unexecuted draft. V2 failed before measured blocks because Python
3.14.7 exposes `_pointer_type_cache` as a compatibility object without `len()`;
its FAILED manifest is preserved. V3 treats that legacy count as unavailable and
provides the primary GC/weak-reference result. Its initial direct-class-dictionary
attribute check was incomplete; v4 used normal attribute lookup and confirmed the
documented type-local mechanism. V4 repeats the bounded probe and is a mechanism
confirmation, not a new fundamental evidence series or a main-study retune.

Only GC-visible target classes are counted. Explicit collection distinguishes
retention from reclamation but does not represent normal collection cadence.
Both probes have 110 measured calls; neither is a long-run experiment. No
resource isolation, real-time guarantee or universal memory bound follows.

## Next actions

No CSC correction is justified by the specific retained-Counters hypothesis.
Preserve the frozen main evidence, retain unresolved memory growth where present,
and investigate allocator/instrumentation costs separately if main trends warrant
it. Any future sampler optimization needs new source identity, a correctness gate
and preregistered confirmation; it must not replace the present results.
