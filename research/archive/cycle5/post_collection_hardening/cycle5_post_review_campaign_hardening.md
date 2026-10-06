# Cycle 5 post-review campaign cleanup hardening

**Status:** Implemented and locally tested after the main measurements. Independent reviewer R9 was MODERATE. The immutable main source archive predates these changes; none of its performance results are upgraded or replaced.

**Question:** Can an orchestration failure leave pressure helpers running or an outer campaign waiting indefinitely?

**Evidence:** `results/cycle5-post-review/campaign-cleanup-20261006T143957Z/manifest.json` and `unittest.log`; eight targeted mocked regressions passed. Current methods: `experiments/cycle5_async.py`; tests: `tests/test_cycle5_campaign_cleanup.py`.

**Method and changes:** Pressure helper readiness now occurs inside its cleanup `try/finally`. Cleanup attempts a cooperative stop and a 10 second join, then terminate and a 2 second join, then kill and a final 2 second join. Failure to write the stop file still triggers bounded cleanup. Failure to reap propagates instead of permitting another condition to run.

The outer coordinator has a campaign watchdog of `300 + 2 * configured duration_epochs` seconds: 700 seconds for the registered 200 epoch pilot and 6,300 seconds for its 3,000 epoch long run. This generous execution control is not a production deadline, evidence eligibility extension, deployment target, or pass criterion. The original 300 ms evidence deadline is unchanged. On expiry, Windows terminates only the launched coordinator's owned process tree; POSIX uses its newly created process group. The launcher reaps the direct child with bounded waits and aborts the campaign. Unconfirmed tree cleanup fails closed and is reported as an orchestration exception, rather than silently continuing pressure exposure.

**Findings:** Tests cover helper death before ready, ready timeout, unavailable stop storage, terminate-to-kill escalation, unconfirmed reaping, successful bounded launcher wait, hanging launcher tree cleanup, and tree cleanup failure. These regressions test control flow using mocks, not OS proof of descendant termination. The first local test attempt exposed a Windows test portability issue (`os.killpg` is absent); the mock was corrected before the recorded eight-test pass.

**Limitations:** This does not provide crash-durable process ownership across host reboot, hostile-process containment, or a reliable way to prove an uncooperative descendant was terminated when the OS termination command itself fails. The campaign aborts in that case. Pressure stop-file writes and OS calls remain subject to host scheduling. The archived measured runner had neither the corrected readiness cleanup nor this outer watchdog. Main runs all completed, but that observation does not retroactively close R9 for the archived variant.

**Open questions and next actions:** Include these regressions in the post-review full suite and independent re-review. Future performance collection requires a fresh source identity and protocol freeze; it must not reuse or overwrite the Cycle 5 main series.

## Second correction after independent re-review

**Status:** Implemented and locally tested current variant; the original eight-test validation remains immutable. The independent re-review correctly found that the first correction's parent launcher could continue after a nonzero exit if a pressure `final.json` existed. That application marker did not establish process cleanup certainty.

The current child records `run_succeeded` and `cleanup_confirmed` separately in an atomically replaced `ownership/<run_id>/cleanup.json`. Confirmation requires a normal runtime return and, when a pressure helper exists, actual helper reaping. Runtime exceptions are conservatively treated as uncertain ownership. Missing or malformed confirmation, false confirmation, or any nonzero child exit stops the whole campaign and marks every later scheduled condition `NOT_ATTEMPTED`. The pressure application marker has no authority to permit continuation. This conservatively aborts ordinary failed conditions too; it does not silently classify a failed prefix as a full run.

Cleanup permission errors no longer interrupt attempts on the remaining owned cleanup steps: terminate, kill and bounded reaping are attempted. The launcher separately attempts tree termination and direct-child reaping, records a failed control disposition, and stops if ownership remains uncertain. OS permission failure is preserved as uncertainty, never converted to cleanup proof.

**Evidence:** `results/cycle5-post-review/campaign-cleanup-v2-20261006T144939Z/manifest.json` and `unittest.log`: 13 tests passed in 2.838 seconds. The new tests include a real child process that writes false ownership plus an application final marker and exits nonzero; the actual launcher boundary records the next condition as unattempted. A disposable real Windows parent/descendant pair is launched by the tested watchdog and the descendant's exit is checked with Windows process-handle signaling. Only those explicitly created process identities are terminated. Mocked tests additionally cover cleanup permission errors and missing nonpressure cleanup confirmation. This is tested cooperative Windows cleanup behavior, not hostile descendant containment or universal OS cleanup reliability.

No main experiment was rerun. Source identities, deadlines, conclusions, and all historical archives remain separate. These corrections require inclusion in the fresh current-tree full gate and independent re-review before any future campaign.
