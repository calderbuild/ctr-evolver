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
    """Annualized volatility from a series of returns.

    If raw prices given, compute log returns first:
      log_return = ln(p2/p1)
    Then: vol = std(returns) * sqrt(periods_per_year)
    """
    n = len(returns)
    if n < 2:
        return 0.0
    mean_r = sum(returns) / n
    variance = sum((r - mean_r) ** 2 for r in returns) / (n - 1)
    vol = math.sqrt(variance) * math.sqrt(periods_per_year)
    return round(vol * 100, decimals)  # as percentage


def hp_filter(values, lam=100, decimals=2):
    """Hodrick-Prescott filter. Returns trend component.

    Uses matrix method: minimize sum((y-t)^2) + lambda*sum((t[i+1]-2*t[i]+t[i-1])^2)
    """
    n = len(values)
    if n < 3:
        return values

    # Build penalty matrix K (second difference)
    # Solve: (I + lambda * K'K) * trend = y
    # Using iterative approach for simplicity (no numpy dependency)
    trend = list(values)  # start with y as initial guess

    for _ in range(100):  # iterate to convergence
        new_trend = list(trend)
        for i in range(n):
            numerator = values[i]
            denominator = 1.0

            if i >= 2:
                numerator += lam * (trend[i - 2] - 2 * trend[i - 1])
                denominator += lam
            if i >= 1 and i <= n - 2:
                numerator += lam * (-2 * trend[i - 1] + -2 * trend[i + 1])
                denominator += 4 * lam
            if i <= n - 3:
                numerator += lam * (trend[i + 2] - 2 * trend[i + 1])
                denominator += lam

            # Simplified: direct solve for this element
            if denominator > 0:
                new_trend[i] = numerator / denominator

        # Check convergence
        diff = sum((new_trend[j] - trend[j]) ** 2 for j in range(n))
        trend = new_trend
        if diff < 1e-10:
            break

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
