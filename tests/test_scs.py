import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scs import hazard  # noqa: E402


def series(n=35 * 365, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("1991-01-01", periods=n, freq="D")
    base = rng.pareto(3.0, n) * 0.02
    return pd.Series(np.clip(base, 0, 1), index=idx)


def test_annual_counts_length():
    s = series()
    assert len(hazard.annual_counts(s, 0.05)) in (35, 36)


def test_dispersion_of_poisson_is_near_one():
    rng = np.random.default_rng(1)
    c = pd.Series(rng.poisson(10, 400))
    assert abs(hazard.dispersion(c)["var_over_mean"] - 1) < 0.25


def test_dispersion_detects_clustering():
    rng = np.random.default_rng(2)
    c = pd.Series(rng.negative_binomial(2, 0.2, 400))
    assert hazard.dispersion(c)["var_over_mean"] > 2


def test_return_levels_increase():
    r = hazard.gpd_return_levels(series(), 35)
    rl = [r[f"rl_{T}"] for T in (2, 5, 10, 20, 50, 100)]
    assert all(b >= a for a, b in zip(rl, rl[1:]))
    assert r["rate_per_year"] > 0


def test_empirical_rate_monotone():
    s = series()
    e = hazard.empirical_rp(s, 35, [0.01, 0.05, 0.1])
    v = list(e.values())
    assert v[0] >= v[1] >= v[2]
