# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

_ALPHABET = "abcdefghijklmnopqrstuvwxyz"
_N = len(_ALPHABET)


def _ord_to_int(s: str, n: int) -> int:
    """Interpret s as a base-26 integer of exactly n digits (missing chars treated as 'a'=0)."""
    result = 0
    for i in range(n):
        c = _ALPHABET.index(s[i]) if i < len(s) else 0
        result = result * _N + c
    return result


def _int_to_ord(x: int, n: int) -> str:
    """Convert a base-26 integer back to a canonical order string (no trailing 'a')."""
    digits = []
    for _ in range(n):
        digits.append(x % _N)
        x //= _N
    digits.reverse()
    while digits and digits[-1] == 0:
        digits.pop()
    return ''.join(_ALPHABET[d] for d in digits)


def order_midpoint(lo: str, hi: str | None) -> str:
    """Return a canonical order string strictly between lo and hi.

    lo is the lower bound ("" means before everything).
    hi is the upper bound, or None if there is no upper bound.
    Each halving grows the string by at most one character, so precision never exhausts.
    """
    if hi is None:
        return (lo or "") + "n"
    n = max(len(lo), len(hi)) + 1
    lo_int = _ord_to_int(lo, n)
    hi_int = _ord_to_int(hi, n)
    if hi_int <= lo_int:
        raise ValueError(f"order_midpoint called with lo >= hi: {lo!r} >= {hi!r}")
    return _int_to_ord((lo_int + hi_int) // 2, n)
