# Count-Min Sketch: Implementation Trade-offs 

## 1. What Was Implemented

The file `streamguard/count_min_sketch.py` implements a Count-Min Sketch using the `CountMinSketch` class.

The implementation supports the following operations:

* `update()` — updates the frequency estimate of an item.
* `estimate()` — estimates the frequency of an item.
* `update_many()` — processes multiple items.
* `merge()` — combines compatible sketch tables.
* `clear()` — resets the sketch.
* `memory_bytes()` — reports the memory occupied by the counter table.
* `error_bound()` — provides the theoretical additive error bound and confidence parameter.
* `from_error_bounds(epsilon, delta)` — creates a sketch using desired error and confidence parameters.

### Data Structure

The sketch uses a two-dimensional NumPy array of shape `depth × width`, with each counter stored as a 64-bit integer (`int64`).

For each item, multiple hash mappings identify one counter per row. The estimated frequency is the minimum of the selected counters.

### Estimation Properties

A standard Count-Min Sketch does not underestimate item frequencies, assuming counters do not overflow and updates use non-negative counts.

Hash collisions can cause overestimation.

For the standard Count-Min Sketch, the usual theoretical guarantee is:

`estimate(item) <= true_frequency(item) + epsilon × N`

with probability at least `1 - delta`, where `N` is the total number of items processed.

The conventional parameter choices are approximately:

* `width = ceil(e / epsilon)`
* `depth = ceil(ln(1 / delta))`

These guarantees rely on the required hashing assumptions and apply to the standard Count-Min Sketch. They should not be interpreted as an unconditional guarantee for every custom hashing implementation.

## 2. Width vs. Depth

Width and depth determine the sketch's memory requirements and estimation accuracy.

| Parameter   | Controls                                 | Effect of increasing it                                                   | Cost                              |
| ----------- | ---------------------------------------- | ------------------------------------------------------------------------- | --------------------------------- |
| Width (`w`) | Expected additive error                  | Generally reduces collision-related overestimation                        | More memory                       |
| Depth (`d`) | Probability of exceeding the error bound | Reduces the failure probability exponentially under the usual assumptions | More memory and update/query work |

### Increasing Width

A wider table distributes items across more counters, reducing the likelihood that unrelated items collide in the same counter.

Increasing width generally improves estimation accuracy, although the actual improvement depends on the input stream and hashing behavior.

### Increasing Depth

A deeper table uses additional hash mappings. Taking the minimum across more rows can improve estimates and reduce the probability of a large error.

However, every additional row increases the number of counters and the work required for updates and queries.

### Practical Decision

Increasing width is often useful when the main problem is frequent collisions. Increasing depth is useful when a lower theoretical failure probability is required.

The best configuration depends on the available memory, stream characteristics, and desired accuracy.

The experiment `experiments/error_vs_width_depth.py` evaluates different width and depth combinations to study these trade-offs.

## 3. Memory Efficiency

The sketch's counter-table memory is:

`Memory = width × depth × bytes_per_counter`

With eight bytes per `int64` counter:

`Memory = width × depth × 8 bytes`

For example, a sketch with width 2,000 and depth 5 requires:

`2,000 × 5 × 8 = 80,000 bytes`

This is the counter table's memory usage, not the complete memory footprint of the Python object. Hash parameters and other metadata require additional memory.

### Comparison with an Exact Counter

An exact counter, such as Python's `collections.Counter`, stores distinct item keys and their corresponding frequencies.

Its memory consumption generally grows with the number of distinct items.

In contrast, the Count-Min Sketch's counter-table size remains fixed for a given width and depth, regardless of the number of distinct items.

However, a sketch is not always smaller than an exact counter. For streams containing relatively few distinct items, the exact counter may use less memory.

The dashboard's Memory tab compares the estimated memory usage of both approaches for different stream configurations.

### Why `int64` Was Chosen

Using `int64` provides a larger counter range than `int32`, reducing the risk of integer overflow when processing high-frequency items.

The trade-off is increased counter-table memory compared with a 32-bit representation.

## 4. Standard vs. Conservative Updates

### Standard Update

For each incoming item, the standard update method increments the corresponding counter in every row.

**Advantages:**

* Simple and straightforward implementation.
* Provides the conventional Count-Min Sketch error guarantee under the required assumptions.
* Supports additive merging of compatible counter tables.

**Disadvantages:**

* Collisions can inflate multiple counters.
* Estimation errors depend on the stream and sketch configuration.

### Conservative Update

Conservative updating first obtains the current estimate of an item. It then raises the selected counters only as far as necessary to reach the current estimate plus the incoming count.

For a unit update, this means incrementing only the selected counters that equal the current minimum estimate.

**Advantages:**

* Can reduce collision-related overestimation.
* Can improve estimation accuracy for certain workloads.

**Disadvantages:**

* Requires additional reads and conditional updates.
* Performance depends on the input and implementation.
* Results can depend on stream order.

### Comparison

| Property                                                       | Standard Update                                           | Conservative Update                                                                                         |
| -------------------------------------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Can overestimate                                               | Yes                                                       | Yes                                                                                                         |
| Underestimation with non-negative updates and no overflow      | No                                                        | No                                                                                                          |
| Update behavior                                                | Increments every selected counter                         | Raises selected counters to the required level                                                              |
| Update cost                                                    | Generally simpler                                         | Requires additional comparisons                                                                             |
| Stream-order dependence                                        | Final table is order-independent for the same item counts | Generally order-dependent                                                                                   |
| Additive merge preserves the usual standard-CMS interpretation | Yes, for compatible standard sketches                     | Not necessarily; the standard guarantee cannot automatically be transferred to a merged conservative sketch |

Conservative updating may improve accuracy, but it does not guarantee lower error for every item or workload.

The experiment `experiments/conservative_vs_standard.py` compares both approaches using the same ordered input stream.

Measured error and throughput values should be added only after the experiment has been executed and its output files checked.

## 5. Hashing Choice

The implementation uses stable item hashing and row-specific mappings to select counters.

Its default hashing approach uses a BLAKE2b digest to convert an item into an integer, followed by row-specific arithmetic mappings.

This approach has several advantages:

* It avoids relying on Python's process-randomized string `hash()` for reproducible item hashing.
* It allows deterministic results when the same seed and configuration are used.
* It provides a hashing interface that can be adapted to the team's hashing module.

The class also supports an optional `hash_fn(item, row, width)` callback for alternative hashing implementations.

### Important Consideration

Reproducible hashing alone does not establish the pairwise-independence assumptions required by the conventional Count-Min Sketch proof.

The theoretical guarantee depends on the properties of the complete hashing construction, not simply on using a stable digest.

The hashing implementation should therefore be evaluated against the assumptions required by the intended guarantee.

## 6. Known Limitations

The Count-Min Sketch has several limitations:

* **Overestimation:** Hash collisions can cause estimated frequencies to exceed actual frequencies.
* **No direct enumeration:** The sketch cannot independently list every observed item because it does not store all item keys.
* **No native deletion support:** Decrementing counters can invalidate the usual guarantees.
* **No built-in sliding window:** Time-based monitoring requires additional structures or a strategy for periodically resetting or rotating sketches.
* **Memory-accuracy trade-off:** A smaller sketch may save memory but produce larger estimation errors.
* **Hashing dependence:** Poorly chosen hashing can increase collisions and undermine expected accuracy.
* **Conservative-update trade-offs:** Conservative updates can improve accuracy for some streams but require additional processing and have different order and merging properties.

A separate candidate-tracking structure, such as a heap, can be used when identifying frequent items or computing top-K results is required.

## 7. Experimental Evaluation

Two experiments are included to evaluate the implementation.

### Error vs. Width and Depth

File: `experiments/error_vs_width_depth.py`

This experiment varies width and depth and records metrics such as:

* Mean overestimation.
* Maximum overestimation.
* Counter-table memory usage.
* Percentage of observed distinct items within the calculated additive error bound.

The results help illustrate how sketch configuration affects estimation accuracy and memory usage.

### Standard vs. Conservative Update

File: `experiments/conservative_vs_standard.py`

This experiment compares standard and conservative updates across different widths and traffic-skew settings.

It records metrics such as:

* Mean overestimation.
* Maximum overestimation.
* Percentage of observed distinct items estimated exactly.
* Update throughput.
* Counter-table memory usage.

Both update strategies should receive the same ordered stream when their performance is compared.

Actual numerical conclusions should be based on the generated CSV files rather than assumed in advance.

## 8. Design Decisions

The implementation uses a fixed-size counter table to provide predictable table memory consumption.

Width and depth are configurable to let users balance memory usage against estimation accuracy.

The standard update method provides a baseline implementation with conventional theoretical guarantees under the required hashing assumptions.

The conservative update method provides an alternative that may reduce overestimation for particular workloads.

Stable hashing, reproducible experiment seeds, and configurable sketch dimensions support repeatable comparisons.

The dashboard and experiment scripts help evaluate these decisions using different stream sizes, distinct-item counts, and frequency distributions.

## 9. Conclusion

Count-Min Sketch offers a practical compromise between memory usage and frequency-estimation accuracy for large data streams.

Its main limitation is overestimation caused by hash collisions. Width, depth, hashing strategy, and update method all influence its behavior.

Comparing the sketch against an exact counter and evaluating standard versus conservative updates helps identify configurations suitable for different workloads.

The final configuration should be selected using measured memory usage, estimation errors, and throughput, together with the application's accuracy requirements.
