"""Frequency and exceedance statistics of a daily hazard index (share of stations with thunderstorm or hail)."""
import numpy as np
import pandas as pd
from scipy import stats


def warm_season(s, months=(4, 5, 6, 7, 8, 9)):
    return s[s.index.month.isin(months)]


def annual_counts(s, thr):
    """Number of days per year above thr (days with data only)."""
    return (s > thr).groupby(s.index.year).sum()


def dispersion(counts):
    """Variance to mean ratio of annual counts and the negative-binomial size parameter by moments (Poisson has ratio 1)."""
    m, v = counts.mean(), counts.var(ddof=1)
    k = m * m / (v - m) if v > m else np.inf
    return {"mean": float(m), "var_over_mean": float(v / m), "nb_size": float(k)}


def gpd_return_levels(s, years, q=0.95, periods=(2, 5, 10, 20, 50, 100)):
    """Peaks over a threshold (the q quantile of the daily series), declustered by keeping the maximum within 3 days; GPD fit.
    Returns rate per year, shape, scale and return levels of the daily index."""
    x = s.dropna()
    u = float(x.quantile(q))
    ex = x[x > u]
    keep, last = [], None
    for t, v in ex.items():       # decluster: within 3 days keep the larger value
        if last is not None and (t - last[0]).days <= 3:
            if v > last[1]:
                keep[-1] = (t, v)
                last = (t, v)
            continue
        keep.append((t, v))
        last = (t, v)
    peaks = np.array([v for _, v in keep])
    rate = len(peaks) / years
    c, loc, sc = stats.genpareto.fit(peaks - u, floc=0)
    out = {"threshold": u, "peaks": int(len(peaks)), "rate_per_year": float(rate), "shape": float(c), "scale": float(sc)}
    for T in periods:
        p = 1.0 / (rate * T)
        out[f"rl_{T}"] = float(u + stats.genpareto.isf(p, c, loc=0, scale=sc)) if p < 1 else float(u)
    return out


def empirical_rp(s, years, levels):
    """Empirical annual exceedance rate of daily index levels (events per year)."""
    return {float(l): float((s > l).sum() / years) for l in levels}
