# Cycle 5 deterministic systems tables

Source: `results\cycle5-async\local-20261006-v1\analysis.json`; independent unit: seed/run. Three seeds/cell. Full distributions and paired effects are retained in JSON.

| Mode | Condition | Cadence median ms | Complete fraction median [min,max] | Partial fraction | Expired | Dropped |
|---|---|---:|---|---:|---:|---:|
| k0 | normal | 40.398 | unavailable | unavailable | 0 | 0 |
| k0 | cpu | 40.462 | unavailable | unavailable | 0 | 0 |
| k0 | memory | 40.353 | unavailable | unavailable | 0 | 0 |
| k0 | storage | 40.345 | unavailable | unavailable | 0 | 0 |
| cold1 | normal | 40.509 | 0.000 [0.000,0.000] | 0.000 | 732 | 348 |
| cold1 | moderate | 40.463 | 0.000 [0.000,0.000] | 0.000 | 704 | 376 |
| cold1 | severe | 40.393 | 0.000 [0.000,0.000] | 0.000 | 579 | 501 |
| cold1 | cpu | 40.350 | 0.000 [0.000,0.000] | 0.000 | 731 | 349 |
| cold1 | memory | 40.355 | 0.000 [0.000,0.000] | 0.000 | 596 | 484 |
| cold1 | storage | 40.397 | 0.000 [0.000,0.000] | 0.000 | 724 | 356 |
| cold2 | normal | 40.505 | 0.000 [0.000,0.000] | 0.000 | 863 | 757 |
| cold2 | moderate | 40.421 | 0.000 [0.000,0.000] | 0.000 | 565 | 1055 |
| cold2 | severe | 40.345 | 0.000 [0.000,0.000] | 0.000 | 829 | 791 |
| cold2 | cpu | 40.516 | 0.000 [0.000,0.000] | 0.000 | 604 | 1016 |
| cold2 | memory | 40.335 | 0.000 [0.000,0.000] | 0.000 | 616 | 1004 |
| cold2 | storage | 40.392 | 0.000 [0.000,0.000] | 0.000 | 876 | 744 |
| warm1 | normal | 40.395 | 1.000 [1.000,1.000] | 0.000 | 0 | 0 |
| warm1 | moderate | 40.391 | 0.000 [0.000,0.211] | 0.000 | 683 | 300 |
| warm1 | severe | 40.387 | 0.000 [0.000,0.000] | 0.000 | 557 | 523 |
| warm1 | cpu | 40.475 | 1.000 [0.722,1.000] | 0.000 | 89 | 0 |
| warm1 | memory | 40.373 | 1.000 [1.000,1.000] | 0.000 | 0 | 0 |
| warm1 | storage | 40.326 | 1.000 [0.950,1.000] | 0.000 | 7 | 8 |
| warm2 | normal | 40.389 | 0.994 [0.989,0.994] | 0.000 | 0 | 12 |
| warm2 | moderate | 40.337 | 0.000 [0.000,0.117] | 0.000 | 885 | 634 |
| warm2 | severe | 40.358 | 0.000 [0.000,0.000] | 0.000 | 574 | 1046 |
| warm2 | cpu | 40.422 | 0.989 [0.989,0.994] | 0.000 | 0 | 15 |
| warm2 | memory | 40.365 | 0.956 [0.956,0.994] | 0.000 | 20 | 30 |
| warm2 | storage | 40.381 | 0.950 [0.606,0.983] | 0.006 | 171 | 24 |

10,000 consecutive epochs at >=90% completeness not evaluated by this 200-epoch factorial / 3000-epoch longest pilot

linear-interpolated per-run p50/p95/p99; 180 measured epochs gives <2 observations in p99 tail; tail descriptive

Total CPU efficiency unavailable (null): observed coordinator + accepted/late worker CPU excludes killed/expired workers without output; Windows CPU quantization. Components retained separately.
