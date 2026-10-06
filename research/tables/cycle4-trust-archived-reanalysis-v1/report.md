# Cycle 4 trust calibration outcome

**Status:** Frozen calibration executed; no post-result selector tuning.
**Evidence:** `C:/Users/Adish/HelloCode/CC_CP/results/cycle4-trust/calibration-20261005-v1`. **Decision:** D. **Final:** NOT RUN: no qualified calibration candidate.

Question: does divergence/horizon add prospective information beyond the epsilon gate in authored J1?
Method: 1,200 seed x full-cell runs, eight repeated anchors each; global frozen quantiles; all 60 cells required. Development was feature validation only. Seed-bootstrap intervals are in the machine summaries. Undefined precision stays in denominators and fails qualification.

| Candidate | d (queue-vehicle ticks) | h | Pass cells /60 | Coverage | Precision | Abstention | Qualified |
|---|---:|---:|---:|---:|---:|---:|---|
| baseline | None | None | 29 | 0.4274 | 0.959054350475262 | 0.5726 | False |
| divergence-q0.25 | 6.0 | None | 5 | 0.0923 | 0.989841986455982 | 0.9077 | False |
| divergence-horizon-q0.25-h2 | 6.0 | 2 | 5 | 0.0798 | 0.9921671018276762 | 0.9202 | False |
| divergence-horizon-q0.25-h6 | 6.0 | 6 | 5 | 0.0921 | 0.9898190045248869 | 0.9079 | False |
| divergence-horizon-q0.25-h20 | 6.0 | 20 | 5 | 0.0923 | 0.989841986455982 | 0.9077 | False |
| divergence-q0.5 | 27.53565787126474 | None | 13 | 0.1759 | 0.9840142095914742 | 0.8241 | False |
| divergence-horizon-q0.5-h2 | 27.53565787126474 | 2 | 11 | 0.1247 | 0.9949874686716792 | 0.8753 | False |
| divergence-horizon-q0.5-h6 | 27.53565787126474 | 6 | 13 | 0.1663 | 0.9855889724310777 | 0.8337 | False |
| divergence-horizon-q0.5-h20 | 27.53565787126474 | 20 | 13 | 0.1759 | 0.9840142095914742 | 0.8241 | False |
| divergence-q0.75 | 104.69210862021271 | None | 23 | 0.3183 | 0.9882198952879581 | 0.6817 | False |
| divergence-horizon-q0.75-h2 | 104.69210862021271 | 2 | 11 | 0.1247 | 0.9949874686716792 | 0.8753 | False |
| divergence-horizon-q0.75-h6 | 104.69210862021271 | 6 | 21 | 0.2626 | 0.9908766362554542 | 0.7374 | False |
| divergence-horizon-q0.75-h20 | 104.69210862021271 | 20 | 23 | 0.3183 | 0.9882198952879581 | 0.6817 | False |
| divergence-q1 | 1135.089625124064 | None | 29 | 0.4274 | 0.959054350475262 | 0.5726 | False |
| divergence-horizon-q1-h2 | 1135.089625124064 | 2 | 11 | 0.1247 | 0.9949874686716792 | 0.8753 | False |
| divergence-horizon-q1-h6 | 1135.089625124064 | 6 | 21 | 0.2626 | 0.9908766362554542 | 0.7374 | False |
| divergence-horizon-q1-h20 | 1135.089625124064 | 20 | 29 | 0.4274 | 0.959054350475262 | 0.5726 | False |

Findings: see all candidate cells/runs, global per-seed distributions and predefined negative controls beside this report. No conditional positive category substitutes for all-cell failure.

Limitations: authored source-isolated software reference; shared J1 specification and seeded PRNG. Same-window epsilon exists after production execution, so this is offline common-window evidence selection with fresh seeds, not demonstrated real decision-time availability. Calibration results cannot establish prospective final replication. No causal or physical validity and no learning permission.

Next action: preserve D when none qualifies; keep final seeds ungenerated. Future mechanism changes require a new protocol and new splits.
