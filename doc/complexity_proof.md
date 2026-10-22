# Complexity and Error-Bound Analysis

Notation: w = columns, d = rows, N = total events, n = distinct sources,
k = top-k size, L = key length in characters.

Parameters: w = ceil(e / epsilon), d = ceil(ln(1 / delta)).

## Time complexity

| Operation | Time | Justification |
|---|---|---|
| Initialise | O(w*d) | Allocates and zeroes d x w counters. |
| Update | O(d) | Computes d hashes and increments one counter per row. Each hash is O(1) arithmetic, and each array access is O(1). d = ceil(ln(1/delta)) is independent of N and n. |
| Query | O(d) | Reads one counter per row and takes the minimum of d values. |
| Merge | O(w*d) | Adds two d x w tables cell by cell. |
| Top-k update | O(d + log k) | One query (O(d)) plus a heap push/pop (O(log k)). |
| Whole stream | O(N*(d + log k)) | N events, each handled in O(d + log k). |
| IP to integer | O(1) for IPv4 | Fixed-width conversion. For arbitrary strings the hash is O(L), so update is O(d*L). |

Since d = O(ln(1/delta)), update and query are O(ln(1/delta)), which is a
constant once delta is fixed.

## Space complexity

The table holds w*d counters of 4 bytes each:

    Space = O(w*d) = O((e/epsilon) * ln(1/delta)) = O((1/epsilon) * ln(1/delta))

This is independent of N and n.

Example: epsilon = 0.001, delta = 0.01 gives w = 2719, d = 5, so
2719 * 5 * 4 = 54,380 bytes (about 53 KB).

An exact hash map needs Theta(n) space, which grows with every new source.

## Error bound (proof)

**Claim.** For any item x with true count f_x, the estimate f_hat_x satisfies:
1. f_hat_x >= f_x (always).
2. f_hat_x <= f_x + epsilon*N with probability at least 1 - delta.

**Proof of 1.** In every row j, the counter at h_j(x) includes all of x's
updates, plus the updates of any items that collide with x. Counters only
increase, so each row's value is at least f_x. The estimate is the minimum
over rows, so it is also at least f_x.

**Proof of 2.**
1. In row j, define the overcount X_j = (counter at h_j(x)) - f_x. It is the
   total count of other items y that collide with x in that row.
2. For a universal hash family, P(h_j(y) = h_j(x)) <= 1/w for y != x. So:

       E[X_j] = sum over y != x of f_y * P(collision) <= N / w

3. X_j >= 0, so Markov's inequality gives:

       P(X_j > epsilon*N) <= E[X_j] / (epsilon*N) <= 1 / (epsilon*w) <= 1/e

   because w = ceil(e/epsilon) >= e/epsilon.
4. The estimate exceeds f_x + epsilon*N only if **all d rows** exceed it.
   Rows use independent hash functions, so:

       P(f_hat_x > f_x + epsilon*N) <= (1/e)^d = e^(-d) <= delta

   because d = ceil(ln(1/delta)) >= ln(1/delta).

Therefore with probability at least 1 - delta, f_x <= f_hat_x <= f_x + epsilon*N.
**QED.**

## Why the minimum?
Each row only overestimates. The row with the fewest collisions is closest to
the truth, so the minimum is the best available estimate, and it keeps the
guarantee f_hat_x >= f_x.

## Top-k correctness note
Any source with true count above the k-th largest exact count is retained in
the heap, because its estimate is never below its true count. The heap may
include an item whose estimate was inflated by collisions, which is the
source of false positives measured in the top-k experiment.
