"""Edge-case tests for the Count-Min Sketch. Run with: pytest -v"""
import math

import pytest

from streamguard.count_min_sketch import CountMinSketch

U32_MAX = 0xFFFFFFFF


# ---- invalid parameters.
@pytest.mark.parametrize("eps", [0, -0.1, 1, 1.5, float("nan")])
def test_invalid_epsilon_rejected(eps):
    with pytest.raises(ValueError):
        CountMinSketch(epsilon=eps, delta=0.01)


@pytest.mark.parametrize("delta", [0, -1, 1, 2, float("nan")])
def test_invalid_delta_rejected(delta):
    with pytest.raises(ValueError):
        CountMinSketch(epsilon=0.01, delta=delta)


def test_dimensions_follow_formula():
    s = CountMinSketch(epsilon=0.001, delta=0.01)
    assert s.w == math.ceil(math.e / 0.001)
    assert s.d == math.ceil(math.log(1 / 0.01))


# ---- invalid updates
@pytest.mark.parametrize("count", [0, -5])
def test_non_positive_count_rejected(count):
    s = CountMinSketch(0.01, 0.01, seed=1)
    with pytest.raises(ValueError):
        s.update("10.0.0.1", count)


# ---- unusual input must not crash
@pytest.mark.parametrize("item", ["", "not-an-ip", "999.999.999.999", "::1",
                                  "2001:db8::ff00:42:8329", "  ", 12345])
def test_odd_inputs_do_not_crash(item):
    s = CountMinSketch(0.01, 0.01, seed=1)
    s.update(item)
    assert s.query(item) >= 1


def test_unseen_item_is_non_negative_int():
    s = CountMinSketch(0.01, 0.01, seed=1)
    s.update("10.0.0.1", 10)
    est = s.query("8.8.8.8")
    assert isinstance(est, int) and est >= 0


def test_empty_sketch_returns_zero():
    assert CountMinSketch(0.01, 0.01, seed=1).query("10.0.0.1") == 0


# ---- large counts
def test_single_item_one_million_times():
    s = CountMinSketch(0.001, 0.01, seed=7)
    s.update("10.0.0.1", 1_000_000)
    assert s.query("10.0.0.1") == 1_000_000
    assert s.total == 1_000_000


def test_counter_saturates_instead_of_overflowing():
    s = CountMinSketch(0.01, 0.01, seed=7)
    s.update("10.0.0.1", U32_MAX)
    s.update("10.0.0.1", 10)  # would overflow without saturation
    assert s.query("10.0.0.1") == U32_MAX


# ---- collisions
def test_tiny_width_overestimates_but_never_underestimates():
    s = CountMinSketch(epsilon=0.9, delta=0.5, seed=3)  # w=4, d=1: forces collisions
    truth = {f"10.0.{i // 250}.{i % 250}": 1 for i in range(200)}
    for ip in truth:
        s.update(ip)
    estimates = {ip: s.query(ip) for ip in truth}
    assert all(estimates[ip] >= truth[ip] for ip in truth)          # never below
    assert sum(estimates.values()) > sum(truth.values())            # collisions seen


# ---- reproducibility and merge
def test_same_seed_gives_identical_tables():
    a, b = CountMinSketch(0.01, 0.01, seed=99), CountMinSketch(0.01, 0.01, seed=99)
    for ip in ("1.1.1.1", "2.2.2.2", "1.1.1.1"):
        a.update(ip)
        b.update(ip)
    assert (a.table == b.table).all()


def test_merge_adds_counts():
    a, b = CountMinSketch(0.01, 0.01, seed=5), CountMinSketch(0.01, 0.01, seed=5)
    a.update("1.1.1.1", 3)
    b.update("1.1.1.1", 4)
    a.merge(b)
    assert a.query("1.1.1.1") == 7 and a.total == 7


def test_merge_rejects_different_dimensions():
    with pytest.raises(ValueError):
        CountMinSketch(0.01, 0.01, seed=5).merge(CountMinSketch(0.05, 0.01, seed=5))


def test_merge_rejects_different_seeds():
    with pytest.raises(ValueError):
        CountMinSketch(0.01, 0.01, seed=1).merge(CountMinSketch(0.01, 0.01, seed=2))


# ---- conservative update
def test_conservative_error_not_worse_than_standard():
    ips = [f"10.1.{i // 250}.{i % 250}" for i in range(400)]
    truth = {ip: (i % 7) + 1 for i, ip in enumerate(ips)}
    std = CountMinSketch(0.05, 0.1, seed=11, conservative=False)
    con = CountMinSketch(0.05, 0.1, seed=11, conservative=True)
    for ip, c in truth.items():
        std.update(ip, c)
        con.update(ip, c)
    err_std = sum(std.query(ip) - c for ip, c in truth.items())
    err_con = sum(con.query(ip) - c for ip, c in truth.items())
    assert all(con.query(ip) >= c for ip, c in truth.items())  # still never below
    assert err_con <= err_std
