# Cycle 4 deterministic local async tables

**Status:** Derived from one preregistered immutable series.

Source: `results\cycle4-async\local-20261005-v1\analysis.json`. Units: ms and fractions; five paired seed-runs per primary group, three in the microstudy.

Within-run medians are reduced before seed medians. Interval is production start-to-start; K excludes mirrors. Ten measured epochs make p95/p99 descriptive only.

| Track | Mode | Condition | Median cadence ms | Paired change vs normal ms [range] | Complete fraction | Partial fraction | Expired | Dropped |
|---|---|---|---:|---|---:|---:|---:|---:|
| primary | k0 | normal | 40.368 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 0 | 0 |
| primary | k0 | moderate | 40.362 | -0.030 [-0.083, 0.078] | 0.000 | 0.000 | 0 | 0 |
| primary | k0 | severe | 40.409 | -0.007 [-0.110, 0.138] | 0.000 | 0.000 | 0 | 0 |
| primary | k0 | timeout | 40.328 | -0.059 [-0.172, 0.190] | 0.000 | 0.000 | 0 | 0 |
| primary | k0 | crash | 40.340 | -0.029 [-0.120, 0.191] | 0.000 | 0.000 | 0 | 0 |
| primary | k0 | saturation | 40.409 | 0.056 [-0.230, 0.180] | 0.000 | 0.000 | 0 | 0 |
| primary | sync1 | normal | 147.027 | 0.000 [0.000, 0.000] | 1.000 | 0.000 | 0 | 0 |
| primary | sync1 | moderate | 188.156 | 44.817 [17.827, 46.225] | 1.000 | 0.000 | 0 | 0 |
| primary | sync1 | severe | 266.100 | 119.463 [102.336, 125.219] | 1.000 | 0.000 | 0 | 0 |
| primary | sync1 | timeout | 139.414 | -6.358 [-16.822, -1.946] | 0.900 | 0.100 | 0 | 0 |
| primary | sync1 | crash | 142.845 | -4.182 [-14.803, 20.385] | 0.900 | 0.100 | 0 | 0 |
| primary | sync1 | saturation | 270.316 | 121.713 [108.105, 123.383] | 1.000 | 0.000 | 0 | 0 |
| primary | sync2 | normal | 163.376 | 0.000 [0.000, 0.000] | 1.000 | 0.000 | 0 | 0 |
| primary | sync2 | moderate | 200.104 | 43.011 [23.272, 68.135] | 1.000 | 0.000 | 0 | 0 |
| primary | sync2 | severe | 280.209 | 112.554 [107.971, 133.243] | 1.000 | 0.000 | 0 | 0 |
| primary | sync2 | timeout | 156.661 | -12.314 [-21.848, 18.654] | 0.900 | 0.100 | 0 | 0 |
| primary | sync2 | crash | 161.578 | 2.901 [-22.096, 10.669] | 0.900 | 0.100 | 0 | 0 |
| primary | sync2 | saturation | 286.027 | 119.656 [103.752, 137.621] | 1.000 | 0.000 | 0 | 0 |
| primary | async1 | normal | 40.436 | 0.000 [0.000, 0.000] | 0.100 | 0.000 | 61 | 30 |
| primary | async1 | moderate | 40.461 | 0.025 [-0.074, 0.088] | 0.000 | 0.000 | 66 | 34 |
| primary | async1 | severe | 40.471 | 0.058 [-0.182, 0.174] | 0.000 | 0.000 | 50 | 50 |
| primary | async1 | timeout | 40.440 | -0.008 [-0.140, 0.210] | 0.100 | 0.000 | 62 | 30 |
| primary | async1 | crash | 40.504 | 0.090 [-0.093, 0.227] | 0.100 | 0.000 | 62 | 30 |
| primary | async1 | saturation | 40.341 | -0.113 [-0.217, 0.040] | 0.100 | 0.000 | 0 | 90 |
| primary | async2 | normal | 40.498 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 60 | 90 |
| primary | async2 | moderate | 40.465 | 0.001 [-0.079, 0.098] | 0.000 | 0.000 | 60 | 90 |
| primary | async2 | severe | 40.369 | -0.129 [-0.195, 0.211] | 0.000 | 0.000 | 60 | 90 |
| primary | async2 | timeout | 40.496 | 0.041 [-0.198, 0.118] | 0.000 | 0.000 | 63 | 87 |
| primary | async2 | crash | 40.516 | 0.024 [-0.066, 0.240] | 0.000 | 0.000 | 60 | 90 |
| primary | async2 | saturation | 40.440 | -0.015 [-0.096, 0.230] | 0.000 | 0.000 | 9 | 135 |
| micro | async2 | normal | 40.342 | 0.000 [0.000, 0.000] | 0.000 | 0.000 | 33 | 54 |
| micro | async2 | cpu | 40.418 | 0.079 [0.013, 0.082] | 0.000 | 0.000 | 36 | 54 |
| micro | async2 | memory | 40.400 | 0.021 [0.016, 0.058] | 0.000 | 0.000 | 34 | 54 |
| micro | async2 | occupancy | 40.366 | -0.001 [-0.027, 0.027] | 0.100 | 0.000 | 3 | 81 |

K0 complete comparison fraction is zero by definition because no shadow evidence is planned, not a production failure.

All five/three paired effects are preserved in `analysis.json`; no timing equivalence threshold is inferred.

Sync branch completion is worker dispatch roundtrip; async is commit-to-coordinator acceptance, including queueing/poll delay. Sync comparison completion is branch creation + barrier + comparison duration; async is commit-to-finalization. Origins differ and absolute cross-mode completion comparisons are descriptive.

| Mode | Condition | Decision ms | Run p95 interval ms (median across seeds) | Comparison ms | Branch ms | Coordinator CPU ms | Worker CPU ms | Serialized bytes | Max active | Max queued |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| k0 | normal | 0.419 | 40.519 | 0.076 | unavailable | 0.000 | unavailable | 0 | 0 | 0 |
| k0 | moderate | 0.401 | 40.583 | 0.066 | unavailable | 0.000 | unavailable | 0 | 0 | 0 |
| k0 | severe | 0.413 | 40.715 | 0.067 | unavailable | 0.000 | unavailable | 0 | 0 | 0 |
| k0 | timeout | 0.352 | 40.604 | 0.068 | unavailable | 0.000 | unavailable | 0 | 0 | 0 |
| k0 | crash | 0.366 | 40.604 | 0.064 | unavailable | 0.000 | unavailable | 0 | 0 | 0 |
| k0 | saturation | 0.425 | 40.552 | 0.072 | unavailable | 0.000 | unavailable | 0 | 0 | 0 |
| sync1 | normal | 0.261 | 165.330 | 143.418 | 142.158 | 7.812 | 0.000 | 141058 | 0 | 0 |
| sync1 | moderate | 0.265 | 205.128 | 183.008 | 181.164 | 7.812 | 0.000 | 141662 | 0 | 0 |
| sync1 | severe | 0.264 | 287.931 | 260.954 | 258.506 | 15.625 | 0.000 | 141085 | 0 | 0 |
| sync1 | timeout | 0.265 | 409.218 | 135.968 | 134.661 | 7.812 | 0.000 | 134361 | 0 | 0 |
| sync1 | crash | 0.272 | 166.112 | 138.319 | 137.236 | 15.625 | 0.000 | 133760 | 0 | 0 |
| sync1 | saturation | 0.254 | 278.662 | 262.845 | 261.407 | 15.625 | 0.000 | 142258 | 0 | 0 |
| sync2 | normal | 0.270 | 187.966 | 159.201 | 157.073 | 15.625 | 0.000 | 211569 | 0 | 0 |
| sync2 | moderate | 0.270 | 220.055 | 195.275 | 192.265 | 15.625 | 0.000 | 212483 | 0 | 0 |
| sync2 | severe | 0.269 | 296.883 | 271.519 | 269.575 | 15.625 | 0.000 | 211602 | 0 | 0 |
| sync2 | timeout | 0.270 | 426.020 | 152.503 | 150.620 | 15.625 | 0.000 | 205032 | 0 | 0 |
| sync2 | crash | 0.268 | 178.762 | 154.564 | 152.402 | 15.625 | 0.000 | 204113 | 0 | 0 |
| sync2 | saturation | 0.272 | 312.830 | 281.362 | 279.370 | 15.625 | 0.000 | 213366 | 0 | 0 |
| async1 | normal | 0.400 | 40.555 | 300.821 | 378.794 | 0.000 | 0.000 | 70646 | 12 | 9 |
| async1 | moderate | 0.410 | 40.738 | 301.020 | 389.033 | 0.000 | 0.000 | 49688 | 12 | 9 |
| async1 | severe | 0.475 | 40.573 | 281.949 | 512.219 | 0.000 | 0.000 | 28256 | 12 | 9 |
| async1 | timeout | 0.454 | 40.627 | 301.088 | 402.733 | 0.000 | 0.000 | 63753 | 12 | 9 |
| async1 | crash | 0.419 | 40.625 | 300.864 | 412.314 | 0.000 | 0.000 | 63527 | 12 | 9 |
| async1 | saturation | 0.379 | 40.501 | 166.026 | 281.767 | 0.000 | 0.000 | 14248 | 2 | 2 |
| async2 | normal | 0.423 | 40.601 | 269.239 | 424.552 | 0.000 | 0.000 | 42439 | 12 | 9 |
| async2 | moderate | 0.497 | 40.603 | 272.841 | 447.920 | 0.000 | 0.000 | 42622 | 12 | 9 |
| async2 | severe | 0.393 | 40.565 | 272.675 | 519.084 | 0.000 | 0.000 | 21205 | 12 | 9 |
| async2 | timeout | 0.518 | 40.602 | 277.671 | 405.613 | 0.000 | 0.000 | 42490 | 12 | 9 |
| async2 | crash | 0.447 | 40.666 | 274.514 | 417.633 | 0.000 | 0.000 | 42303 | 12 | 9 |
| async2 | saturation | 0.427 | 40.584 | 190.154 | 308.542 | 0.000 | 0.000 | 21370 | 3 | 0 |
| async2 | normal | 0.389 | 40.621 | 273.647 | 401.940 | 0.000 | 0.000 | 42197 | 12 | 9 |
| async2 | cpu | 0.507 | 40.701 | 273.964 | 482.124 | 0.000 | 62.500 | 41967 | 12 | 9 |
| async2 | memory | 0.476 | 40.575 | 273.913 | 464.192 | 0.000 | 0.000 | 42215 | 12 | 9 |
| async2 | occupancy | 0.403 | 40.550 | 193.327 | 296.056 | 0.000 | 0.000 | 21243 | 3 | 0 |

CPU zeros can reflect Windows process-time quantization; they do not show zero cost. Worker RSS is unavailable on this host; tracemalloc measures Python allocation, not process RSS. PID counts under-report timed-out/crashed workers.

Production decision excludes evidence bookkeeping; cadence includes coordinator storage, comparison, polling and host scheduling. Local results do not establish resource non-interference, real-time safety, K3s containment or durable distributed restart.
