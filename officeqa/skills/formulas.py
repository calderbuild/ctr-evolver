#!/usr/bin/env python3
"""Treasury QA Formula Library.

Usage: python3 formulas.py <function> <args...> [--decimals N] [--periods N]

Examples:
  python3 formulas.py percent_change 100 150 2
  python3 formulas.py cagr 100 200 10 2
  python3 formulas.py geometric_mean 1.5 2.0 1.8 --decimals 3
  python3 formulas.py theil_index 100 200 300 --decimals 3
  python3 formulas.py hp_filter "100,200,150,300" 100 2
"""

import math
import sys


def percent_change(old, new, decimals=2):
    """((new - old) / old) * 100"""
    return round(((new - old) / old) * 100, decimals)


def abs_percent_change(old, new, decimals=2):
    """abs((new - old) / old) * 100"""
    return round(abs((new - old) / old) * 100, decimals)


def cagr(start_value, end_value, years, decimals=2):
    """Compound Annual Growth Rate: ((end/start)^(1/years) - 1) * 100"""
    return round(((end_value / start_value) ** (1 / years) - 1) * 100, decimals)


def geometric_mean(*values, decimals=3):
    """(v1 * v2 * ... * vn)^(1/n)"""
    product = 1.0
    for v in values:
        product *= v
    return round(product ** (1 / len(values)), decimals)


def theil_index(*values, decimals=3):
    """Theil's T index: (1/n) * sum(xi/mu * ln(xi/mu))"""
    n = len(values)
    mu = sum(values) / n
    t = sum((v / mu) * math.log(v / mu) for v in values if v > 0) / n
    return round(t, decimals)


def euclidean_norm(*values, decimals=2):
    """sqrt(sum(v^2))"""
    return round(math.sqrt(sum(v ** 2 for v in values)), decimals)


def annualized_volatility(*returns, decimals=2, periods_per_year=52):
    """Annualized volatility from a series of log returns.

    Uses realized variance estimator: RV = sum(r_i^2) * (periods/n)
    Then vol = sqrt(RV). Works correctly even with 1-2 returns.

    If raw prices given, compute log returns first:
      log_return = ln(p2/p1)
    """
    n = len(returns)
    if n == 0:
        return 0.0
    # Realized variance estimator (sum of squared returns)
    realized_var = sum(r ** 2 for r in returns) / n
    vol = math.sqrt(realized_var * periods_per_year)
    return round(vol * 100, decimals)  # as percentage


def hp_filter(values, lam=100, decimals=2):
    """Hodrick-Prescott filter. Returns trend component.

    Solves: min sum((y-t)^2) + lambda*sum((t[i+1]-2*t[i]+t[i-1])^2)
    Uses pentadiagonal direct solve (no numpy needed).
    """
    n = len(values)
    if n < 3:
        return [round(v, decimals) for v in values]

    # Build pentadiagonal system (I + lambda * K'K)
    # Main diagonal
    d = [0.0] * n
    d[0] = 1.0 + lam
    d[1] = 1.0 + 5.0 * lam
    for i in range(2, n - 2):
        d[i] = 1.0 + 6.0 * lam
    d[n - 2] = 1.0 + 5.0 * lam
    d[n - 1] = 1.0 + lam

    # Sub-diagonal (offset 1)
    dl = [0.0] * n
    dl[1] = -2.0 * lam
    for i in range(2, n - 1):
        dl[i] = -4.0 * lam
    dl[n - 1] = -2.0 * lam

    # Sub-sub-diagonal (offset 2)
    dll = [0.0] * n
    for i in range(2, n):
        dll[i] = lam

    # Forward elimination (pentadiagonal)
    y = list(values)
    for i in range(1, n):
        if d[i - 1] == 0:
            continue
        m = dl[i] / d[i - 1]
        d[i] -= m * dl[i]  # simplified: upper band mirrors lower
        y[i] -= m * y[i - 1]
        dl[i] = 0
        if i >= 2:
            m2 = dll[i] / d[i - 2] if d[i - 2] != 0 else 0
            d[i] -= m2 * dll[i]
            y[i] -= m2 * y[i - 2]
            dll[i] = 0

    # Back substitution
    trend = [0.0] * n
    trend[n - 1] = y[n - 1] / d[n - 1] if d[n - 1] != 0 else y[n - 1]
    for i in range(n - 2, -1, -1):
        trend[i] = y[i] / d[i] if d[i] != 0 else y[i]

    return [round(t, decimals) for t in trend]


def mean(*values, decimals=2):
    """Arithmetic mean."""
    return round(sum(values) / len(values), decimals)


def log_return(p1, p2, decimals=6):
    """Natural log return: ln(p2/p1)"""
    return round(math.log(p2 / p1), decimals)


def abs_difference(a, b, decimals=2):
    """Absolute difference: |a - b|"""
    return round(abs(a - b), decimals)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    func_name = args[0]
    func = globals().get(func_name)
    if not func or not callable(func):
        print(f"Unknown function: {func_name}")
        print(f"Available: percent_change, abs_percent_change, cagr, geometric_mean, "
              f"theil_index, euclidean_norm, annualized_volatility, hp_filter, mean, "
              f"log_return, abs_difference")
        sys.exit(1)

    # Parse remaining args
    positional = []
    kwargs = {}
    i = 1
    while i < len(args):
        if args[i].startswith("--"):
            key = args[i][2:]
            if i + 1 < len(args):
                kwargs[key] = float(args[i + 1])
                i += 2
            else:
                i += 1
        else:
            # Try to parse as number, or as comma-separated list
            val = args[i]
            if "," in val:
                positional.append([float(x.strip()) for x in val.split(",")])
            else:
                try:
                    positional.append(float(val))
                except ValueError:
                    positional.append(val)
            i += 1

    # Special handling for functions that take a list
    if func_name == "hp_filter" and positional:
        values = positional[0] if isinstance(positional[0], list) else positional
        lam = int(kwargs.get("lambda", positional[1] if len(positional) > 1 else 100))
        dec = int(kwargs.get("decimals", positional[2] if len(positional) > 2 else 2))
        result = hp_filter(values, lam, dec)
        print(result)
    elif func_name in ("geometric_mean", "theil_index", "euclidean_norm", "annualized_volatility", "mean"):
        dec = int(kwargs.get("decimals", 3))
        periods = int(kwargs.get("periods", 52))
        if func_name == "annualized_volatility":
            result = annualized_volatility(*positional, decimals=dec, periods_per_year=periods)
        elif func_name in ("geometric_mean", "theil_index", "euclidean_norm", "mean"):
            result = func(*positional, decimals=dec)
        print(result)
    else:
        # For standard functions: last positional is decimals (int), rest are floats
        if len(positional) >= 2 and func_name in ("percent_change", "abs_percent_change", "cagr", "log_return", "abs_difference"):
            *vals, dec = positional
            result = func(*[float(v) for v in vals], int(dec))
        else:
            result = func(*[float(x) for x in positional])
        print(result)
