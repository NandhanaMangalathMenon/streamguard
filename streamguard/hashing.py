
"""Stable hashing utilities for StreamGuard."""

import hashlib


def hash_item(item: str, seed: int = 0) -> int:
    """Return a deterministic, non-negative hash for a string item."""
    if not isinstance(item, str):
        raise TypeError("item must be a string")

    if not isinstance(seed, int):
        raise TypeError("seed must be an integer")

    payload = f"{seed}:{item}".encode("utf-8")
    digest = hashlib.blake2b(payload, digest_size=8).digest()

    return int.from_bytes(digest, byteorder="big")


def hash_index(item: str, width: int, seed: int = 0) -> int:
    """Map an item to a valid array index from 0 to width - 1."""
    if not isinstance(width, int) or isinstance(width, bool) or width <= 0:
        raise ValueError("width must be a positive integer")

    return hash_item(item, seed) % width

