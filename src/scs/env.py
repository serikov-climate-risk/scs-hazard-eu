"""Environment proxy for thunderstorm days: daily maximum CAPE from ERA5 (Open-Meteo archive) calibrated on DWD observer days.

Per grid point: a day is a thunderstorm day if at least one stable DWD station within RADIUS_KM reports thunder (at least three of
them with data that day). The model is a logistic regression of that flag on log(1 + daily maximum CAPE) in the warm season (May to
September), fitted on odd years and tested on even years (and the reverse), compared with the seasonal climatology. Wind shear is not
used (no pressure-level wind in the download). Applied to the years after the observer record ends it gives a model-based
thunderstorm-day frequency, not an observation.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

RADIUS_KM = 75.0
WARM = (5, 6, 7, 8, 9)


def haversine_km(lat1, lon1, lat2, lon2):
    p = np.pi / 180
    a = np.sin((lat2 - lat1) * p / 2) ** 2 + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * np.arcsin(np.sqrt(a))


def point_flag(long: pd.DataFrame, stations: pd.DataFrame, lat: float, lon: float, radius=RADIUS_KM, min_active=3) -> pd.Series:
    """1 if at least one station within the radius reports thunder, 0 if none does, NaN with fewer than min_active stations with data."""
    d = haversine_km(lat, lon, stations.lat.to_numpy(), stations.lon.to_numpy())
    near = stations.index[d <= radius]
    x = long[long.STATIONS_ID.isin(near)].dropna(subset=["GEWITTER"])
    g = x.groupby("date").GEWITTER
    flag = (g.max() > 0).astype(float)
    flag[g.count() < min_active] = np.nan
    return flag.rename("thunder")


def features(cape_max: pd.Series) -> np.ndarray:
    return np.log1p(cape_max.clip(lower=0).to_numpy(float)).reshape(-1, 1)


def evaluate(df: pd.DataFrame) -> dict:
    """df: index date, columns thunder (0/1), cape_max. Warm season only. Fit on odd years / test on even years and the reverse."""
    d = df[df.index.month.isin(WARM)].dropna(subset=["thunder", "cape_max"])
    out = {"n_days": int(len(d)), "thunder_share": float(d.thunder.mean())}
    pooled = {"y": [], "p": [], "clim": []}
    for test_parity in (0, 1):
        te = d[d.index.year % 2 == test_parity]
        tr = d[d.index.year % 2 != test_parity]
        if te.thunder.nunique() < 2 or tr.thunder.nunique() < 2:
            continue
        m = LogisticRegression(C=10.0).fit(features(tr.cape_max), tr.thunder)
        pooled["y"].append(te.thunder.to_numpy())
        pooled["p"].append(m.predict_proba(features(te.cape_max))[:, 1])
        # climatology: share by month in the training years
        mon = tr.groupby(tr.index.month).thunder.mean()
        pooled["clim"].append(te.index.month.map(mon).to_numpy(float))
    if not pooled["y"]:
        return out
    y, p, c = (np.concatenate(pooled[k]) for k in ("y", "p", "clim"))
    out.update({"auc_cape": float(roc_auc_score(y, p)), "auc_month_climatology": float(roc_auc_score(y, c)),
                "brier_cape": float(brier_score_loss(y, p)), "brier_month_climatology": float(brier_score_loss(y, c)),
                "brier_skill_vs_climatology": float(1 - brier_score_loss(y, p) / brier_score_loss(y, c))})
    return out


def fit_full(df: pd.DataFrame) -> LogisticRegression:
    d = df[df.index.month.isin(WARM)].dropna(subset=["thunder", "cape_max"])
    return LogisticRegression(C=10.0).fit(features(d.cape_max), d.thunder)


def expected_days(model: LogisticRegression, cape_max: pd.Series) -> pd.Series:
    """Expected number of warm-season thunderstorm days per year from the CAPE series (sum of daily probabilities)."""
    c = cape_max[cape_max.index.month.isin(WARM)].dropna()
    p = pd.Series(model.predict_proba(features(c))[:, 1], index=c.index)
    return p.groupby(p.index.year).sum()
