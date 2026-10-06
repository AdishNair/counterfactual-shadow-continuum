# CSC information timing audit

**Status:** Implemented-source architectural analysis, 2026-10-06. No new trust
selector, learner, prospective trust experiment, or domain was implemented.

## Question

When can each CSC quantity be known relative to the decision and the H-tick
window it evaluates? Can the current-window evidence be used to justify that
same window's initial action?

## Evidence and method

Trace `csc/async_runner.py`, `csc/runner.py`, `csc/contracts.py`,
`csc/branches.py`, `csc/compare.py`, `csc/pending.py`, and
`experiments/replay.py`. Classify availability from dependencies, rather than
from variable names or the order of serialized records. Read alongside
`research/evidence/cycle4/CYCLE4_EXECUTIVE_SUMMARY.md`, `research/evidence/cycle4/cycle4_trust_analysis.md`,
and `research/evidence/cycle4/domain_adapter_readiness.md`. This audit uses repository source
only and performs no statistical inference.

## Findings

| Quantity | Earliest availability | Required information / limitation |
|---|---|---|
| Decision-relevant live state | PRE-DECISION | Authoritative `snapshot_state()` before selecting this epoch's action; it includes a watermark and recent past arrivals, not realised future outcomes. |
| Captured immutable anchor | AT DECISION | Capture completes before action selection/actuation and records experiment, epoch, canonical state, seed and input watermark. Availability requires successful capture; a failed capture cannot be replaced by a later snapshot. |
| Production action and branch identities | AT DECISION | The scheduler selects from current state and configured policy, then binds the anchor/window. The current production scheduler does not consume epsilon, divergence or regret. |
| Actual exogenous event stream | DURING WINDOW | A physical online event is available when observed. This local harness generates/assigns the complete seeded window before simulating its ticks, so its earlier local availability is an experimental convenience, not an online observability claim. |
| Production trajectory prefix | DURING WINDOW | Each `world.step` creates one more realised tick. A complete-window metric requires the final tick. |
| Previous epsilon | PRE-DECISION, conditional | Only an earlier completed mirror comparison delivered before this decision is usable. Async completion may lag several windows; record originating epoch, completion time and age. The existing comparator EWMA is updated at comparison finalization, not at capture, and is not a decision input. |
| Current mirror epsilon | POST-WINDOW | `abs(u_mirror - u_real)` requires both full-window utilities plus identity/input comparability. Its availability can be later than production-window completion because worker execution, delivery or ordered finalization still waits. Missing current mirror must remain distinguished from an estimated historical value. |
| Current trajectory divergence | POST-WINDOW for its full-window value | Full production/mirror traces are required. Prefix distances can exist during a window but are different statistics; no such online prefix selector is implemented. |
| Current alternative utility | POST-WINDOW | A complete alternative trace and domain utility are required. In the local seeded simulator an alternative can finish earlier in wall time than production; it still uses the future H-tick input contract and cannot establish online decision-time information. |
| Historical calibration | PRE-DECISION, conditional | A frozen version can be used if trained/calibrated only on earlier, appropriately separated evidence, with its version and data cutoff declared. Historical Cycle 4 calibration is not a new evaluation split or prospective current-window guarantee. |
| Current signed/raw regret | POST-WINDOW | Depends on realised production utility and comparable alternative utility. These are estimated alternatives, not observed factual counterfactuals. Async incomplete alternative sets receive unavailable regret. |
| Current discounted regret | POST-WINDOW | Requires the above and mirror-derived epsilon or explicitly labeled historical estimate. A historical epsilon source does not make the current outcome comparison pre-decision. |
| Current outcome comparison/CFR | POST-WINDOW | Requires production outcome and accepted results, or deadline/retention finalization with explicit missingness. Ordered comparison can wait behind an earlier incomplete epoch. |

The category POST-WINDOW is a semantic information boundary, not a guarantee
that every quantity is available immediately when production finishes. Wall-clock
comparison availability is the latest dependency completion plus transport,
validation, storage and finalization. Branch completion and complete comparable
epoch evidence are therefore different events.

`OutcomeComparisonEngine` updates `epsilon_ewma` when a mirror is accepted;
without a current mirror it emits a prior estimate labeled `ESTIMATED`, or
`UNAVAILABLE`. That fallback must never be reported as current measured epsilon.
The async ledger additionally removes regret/best-action outputs when the
expected comparison is incomplete. A later result cannot retroactively become
an input to an already chosen production action.

## Limitations and open questions

This analysis describes the authored software experiment, whose simulated ticks
are not a physical time stream. It does not establish trustworthy online
uncertainty, a safe age limit for historical epsilon, or validity of any prefix
distance. A future trust design must decide what information is observable
before action, its data cutoff and maximum evidence age, and whether its
objective concerns model error, alternative-action ranking or policy benefit.

## Next actions

Preserve Decision D and learning BLOCKED. Before a separate Cycle 6 trust study,
pre-register a causal information contract, log signal source epoch/availability
time, freeze calibration before fresh evaluation, and test unavailable/stale
signal behavior. No Cycle 4 selector retuning or final held-out seed generation
is authorized by this audit.
