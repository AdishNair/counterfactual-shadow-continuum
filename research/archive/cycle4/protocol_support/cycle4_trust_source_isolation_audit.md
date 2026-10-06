# Cycle 4 source isolation audit

**Status:** Implemented and locally mutation-tested before outcome generation (2026-10-05). **Question:** are reference dynamics independent of SEM and selector code?

## Dependency closure

| Module | Direct imports | Outcome generation | Shared dependencies |
|---|---|---|---|
| `experiments/trust_reference.py` | stdlib `copy.deepcopy`, `random` | independently written dictionary transition, observation/metric/utility code | action strings, serialized records, authored J1 specification, stdlib keyed PRNG semantics |
| `experiments/trust_selector.py` | stdlib `math` | none; consumes exact feature allowlist | no oracle, no reference or SEM import |
| `experiments/cycle4_trust.py` | CSC contracts/world, isolated reference, selector validation, stdlib | orchestrates distinct authoritative, SEM, reference implementations | authoritative production path supplies realized epsilon; no reference labels supplied to selector |
| `experiments/analyze_cycle4_trust.py` | driver helpers, selector, stdlib | post-window analysis only | intentionally sees reference labels; cannot actuate |

The reference imports no CSC package, transition helper, compare utility, mismatch implementation, SEM trajectory logic or selector. Its import AST is checked against the exact set `copy, random`; a fresh subprocess import confirms no `csc` module loaded. The reference accepts plain records, deep-copies state, and leaves supplied inputs unchanged. SEM and reference share action names and serialized state/event field meanings only; their transition and metric implementations are separately written.

## Evidence and tests

`python -m unittest tests.test_cycle4_trust -v`: **15 tests passed**. These cover SEM-step mutation with reference unchanged; authoritative-production-step and CSC metric mutations with reference unchanged; isolated reference-transition and reference-metric mutations with SEM unchanged; canonical serialization/input preservation; all actions at H=2/6/20 with/without heterogeneity agreeing with authored authoritative traces; selector rejection of oracle fields; unknown/late/unsupported incident semantics; misdeclared capability visibility limit; exact gain/divergence boundaries; import firewall. Fixtures use seeds 123/999, outside all research splits. Four added final-firewall fixtures prove unqualified generation and analysis stop before outcome reads, the final analyzer never recalibrates, and coverage/FPR baseline checks fail independently.

The semantic identity test confirms both implementations interpret supplied records identically under aligned conditions. It does not make SEM software outcomes independent of the authored J1 specification. An intentional omission of incident knowledge changes SEM config only; the reference always honors supplied blocked-EW records. Selector results never enter reference simulation or authoritative transition.

## Limitations

Mutation isolation establishes implementation separation, not correctness of the shared authored specification. Both references use the same documented keyed Python PRNG to model heterogeneity. Independent source cannot prove physical dynamics. A falsely declared SEM incident capability can remain undetected through this interface; tests preserve that limitation. The retrospective same-window epsilon timing defect is documented in `research/archive/cycle4/protocol_support/cycle4_trust_preoutcome_specification.md` and the director's `research/archive/cycle4/protocol_support/cycle4_protocol_preflight.md`.

## Next action

Director review before collection, then archive all relevant source/config/report/firewall code and digest. Execute only development first. Historical series remain untouched; no final series exists before qualification.
