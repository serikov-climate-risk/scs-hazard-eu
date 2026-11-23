"""CAPE proxy for thunderstorm days: calibration on DWD observer days 1991-2011 and model-based frequency 1991-2025.

    python scripts/run_env.py     # needs z_data/openmeteo_cape_de (hourly CAPE, daily maxima) and the DWD zip files
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from scs import dwd, env  # noqa: E402

DWD = Path.home() / "z_data" / "z11" / "dwd"
CAPE = Path.home() / "z_data" / "openmeteo_cape_de"
RES = ROOT / "results"
long, st = dwd.load_all(DWD, "1991-01-01", "2011-12-31")
stable = dwd.stable_stations(long, "1991-01-01", "2011-12-31", 0.85)
st = st.loc[stable]
long = long[long.STATIONS_ID.isin(stable)]
rows, series = [], {}
for f in sorted(CAPE.glob("cape_*.parquet")):
    _, la, lo = f.stem.split("_")
    la, lo = float(la), float(lo)
    cape = pd.read_parquet(f)["cape_max"]
    flag = env.point_flag(long, st, la, lo)
    df = pd.concat([flag, cape], axis=1).dropna(subset=["cape_max"])
    df = df[df.index <= "2011-12-31"]
    r = env.evaluate(df)
    model = env.fit_full(df)
    days = env.expected_days(model, cape)
    obs = flag[flag.index.month.isin(env.WARM)].groupby(flag[flag.index.month.isin(env.WARM)].index.year).sum()
    r.update({"lat": la, "lon": lo, "model_days_1991_2011": float(days[days.index <= 2011].mean()), "model_days_2012_2025": float(days[days.index >= 2012].mean()),
              "observed_days_1991_2011_incl_missing_as_zero": float(obs.mean())})
    rows.append(r)
    series[f"{la}_{lo}"] = days
res = pd.DataFrame(rows)
res.to_csv(RES / "env_proxy_by_point.csv", index=False)
yr = pd.DataFrame(series)
yr.to_csv(RES / "env_proxy_model_days_by_year.csv")
out = {"points": int(len(res)), "median_auc_cape": float(res.auc_cape.median()), "median_auc_month_climatology": float(res.auc_month_climatology.median()),
       "median_brier_skill": float(res.brier_skill_vs_climatology.median()),
       "mean_model_days_1991_2011": float(res.model_days_1991_2011.mean()), "mean_model_days_2012_2025": float(res.model_days_2012_2025.mean()),
       "ratio_2012_2025_over_1991_2011": float(res.model_days_2012_2025.mean() / res.model_days_1991_2011.mean())}
(RES / "env_proxy_summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))
