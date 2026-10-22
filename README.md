# StreamGuard

Real-time network traffic analytics using a **Count-Min Sketch** to estimate
source-IP frequencies, detect heavy hitters and flag floods with low memory.
A Streamlit dashboard compares approximate and exact counts for accuracy,
speed and memory.

## Why
Exact counting (a hash map) needs memory proportional to the number of distinct
sources. A Count-Min Sketch uses a fixed table, never underestimates, and keeps
error within epsilon*N with probability at least 1 - delta.

## Setup
```
pip install -r requirements.txt
```

## Run
| What | Command |
|---|---|
| Dashboard | `streamlit run dashboard/app.py` |
| CLI demo | `python cli.py` |
| Tests | `pytest -v` |
| Experiments | `python experiments/error_vs_width_depth.py` |

## Structure
| Path | Purpose |
|---|---|
| `streamguard/` | Sketch, hashing, top-k, exact counter, generator, metrics |
| `dashboard/` | Streamlit app and tabs |
| `tests/` | pytest suites |
| `experiments/` | Error vs width/depth, conservative update, memory, top-k |
| `data/` | Sample traffic input |
| `results/` | Saved graphs |
| `docs/` | Justification, complexity proofs, trade-offs, viva Q&A |

## Complexity
| Operation | Time |
|---|---|
| Update / Query | O(d) = O(ln(1/delta)) |
| Merge | O(w*d) |
| Top-k update | O(d + log k) |
| Space | O((1/epsilon) ln(1/delta)), independent of stream size |

## Team
| Member | Area |
|---|---|
| M1 | Count-Min Sketch core, memory tab, experiments |
| M2 | Hashing, top-k, CLI |
| M3 | Traffic generator, exact counter, metrics, tests |
| M4 | Repo, dashboard, anomaly tab, edge-case tests, docs |
