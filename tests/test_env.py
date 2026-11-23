import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scs import env  # noqa: E402


def test_calibration_recovers_cape_signal():
    rng = np.random.default_rng(0)
    idx = pd.date_range("1991-01-01", "2010-12-31")
    cape = pd.Series(rng.gamma(0.6, 400, len(idx)), index=idx)
    p = 1 / (1 + np.exp(-(1.2 * np.log1p(cape) - 7.5)))
    thunder = pd.Series((rng.random(len(idx)) < p).astype(float), index=idx)
    r = env.evaluate(pd.DataFrame({"thunder": thunder, "cape_max": cape}))
    assert r["auc_cape"] > 0.8 and r["brier_skill_vs_climatology"] > 0


def test_point_flag_needs_enough_stations():
    long = pd.DataFrame({"STATIONS_ID": [1, 2, 3, 1, 2], "date": pd.to_datetime(["2000-06-01"] * 3 + ["2000-06-02"] * 2), "GEWITTER": [0, 1, 0, 0, 0]})
    st = pd.DataFrame({"lat": [50, 50.1, 50.2], "lon": [8, 8, 8]}, index=[1, 2, 3])
    f = env.point_flag(long, st, 50.1, 8.0)
    assert f["2000-06-01"] == 1.0 and np.isnan(f["2000-06-02"])
