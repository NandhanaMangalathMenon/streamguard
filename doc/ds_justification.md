# Data Structure Justification: Why Count-Min Sketch for StreamGuard

## Problem
Estimate how often each traffic source (IP address) appears in an unbounded
stream of network events, using a small, fixed amount of memory, and identify
the heaviest sources in real time.

Why this is hard: the IPv4 space has 2^32 addresses and IPv6 has 2^128. A
stream can contain millions of distinct sources, and it never ends.

## Requirements
1. Memory must not grow with the number of distinct sources.
2. Each event must be processed in constant time.
3. Estimates must have a provable error bound.
4. Heavy sources must never be missed because of undercounting.

## Comparison with alternatives

| Structure | Space | Update/Query | Why it falls short here |
|---|---|---|---|
| Hash map (dict) | O(n) distinct | O(1) average | Exact, but memory grows with every new IP. This is our accuracy baseline, not the solution. |
| Balanced BST | O(n) | O(log n) | Same memory growth, and slower. |
| Sorted array | O(n) | O(log n) search, O(n) insert | Memory growth plus costly inserts. |
| Bloom filter | O(m) fixed | O(k) | Answers only "seen or not". It cannot give frequencies. |
| Counting Bloom filter | O(m) fixed | O(k) | Supports counts, but has no clean (epsilon, delta) frequency guarantee, and its design targets membership and deletion. |
| Misra-Gries / Space-Saving | O(1/epsilon) | O(1) amortised | Good top-k, but it only tracks a limited set of items, so it cannot answer a point query for an arbitrary IP, and merging is harder. |
| **Count-Min Sketch** | **O((1/eps) ln(1/delta)) fixed** | **O(d) = O(ln(1/delta))** | **Fixed memory, constant-time update and query, point queries for any IP, mergeable, provable error bound.** |

## Why Count-Min Sketch fits
- **Fixed memory.** The table is d x w counters, set by epsilon and delta. It
  does not change with stream length or distinct sources.
- **One-sided error.** Collisions only add to a counter, so the estimate is
  never below the true count. A heavy hitter is never hidden.
- **Provable bound.** With probability at least 1 - delta, the estimate is at
  most the true count + epsilon * N, where N is the stream length.
- **Mergeable.** Sketches built with the same parameters and seed can be added
  cell by cell, so monitors on several routers can be combined.
- **Works with a heap.** The sketch gives frequencies and a size-k min-heap
  keeps the current top-k.

## Honest trade-offs
- The answer is approximate: it can overcount.
- Error is relative to the total stream size N, so very rare IPs can have a
  large relative error. Heavy hitters, the ones we care about, have a small one.
- It is probabilistic: the bound holds with probability 1 - delta, not always.
- It cannot list the IPs it has seen, so top-k needs the separate heap.
- Deletion is not supported in the standard form.
- An exact hash map is faster per update in Python. StreamGuard accepts this
  to gain bounded memory, and the dashboard reports it openly.
