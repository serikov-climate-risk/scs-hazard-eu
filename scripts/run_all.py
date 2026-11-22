"""Severe convective storm hazard for Germany from DWD station observations, compared with winter windstorms."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from scs import dwd, hazard  # noqa: E402

SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "z_data" / "z11" / "dwd"
WIND = Path.home() / "de-windstorm-risk" / "results"
RES = ROOT / "results"
RES.mkdir(exist_ok=True)
START, END = "1991-01-01", "2011-12-31"   # DWD observer-based phenomena records effectively end in 2011 (network automated)
YEARS = 21

long, st = dwd.load_all(SRC, START, END)
stable = dwd.stable_stations(long, START, END, 0.85)
out = {"stations_all": int(long.STATIONS_ID.nunique()), "stations_stable": len(stable), "period": [START, END]}
tg, ng = dwd.daily_index(long, stable, "GEWITTER")
hg, nh = dwd.daily_index(long, stable, "HAGEL")
d = pd.concat([tg.rename("thunder"), hg.rename("hail"), ng.rename("n_active")], axis=1)
d.to_csv(RES / "daily_index.csv")
out["median_active_stations"] = float(ng.median())
# station level: thunderstorm and hail days per year, by region of the country (north/south split at 51 N)
sd = long[long.STATIONS_ID.isin(stable)].dropna(subset=["GEWITTER"])
per = sd.groupby("STATIONS_ID").agg(thunder_days=("GEWITTER", "sum"), hail_days=("HAGEL", "sum"), n=("GEWITTER", "count"))
per["thunder_per_yr"] = per.thunder_days / per.n * 365.25
per["hail_per_yr"] = per.hail_days / per.n * 365.25
per = per.join(st)
per.round(3).to_csv(RES / "station_rates.csv")
out["thunder_days_per_year"] = {"mean": float(per.thunder_per_yr.mean()), "p10": float(per.thunder_per_yr.quantile(0.1)), "p90": float(per.thunder_per_yr.quantile(0.9))}
out["hail_days_per_year"] = {"mean": float(per.hail_per_yr.mean()), "p10": float(per.hail_per_yr.quantile(0.1)), "p90": float(per.hail_per_yr.quantile(0.9))}
out["south_over_north_thunder"] = float(per[per.lat < 51].thunder_per_yr.mean() / per[per.lat >= 51].thunder_per_yr.mean())
mon = d.groupby(d.index.month)[["thunder", "hail"]].mean()
mon.to_csv(RES / "monthly_share.csv")
out["peak_month_thunder"] = int(mon.thunder.idxmax())
out["season_share_thunder_JJA"] = float(mon.thunder.loc[[6, 7, 8]].sum() / mon.thunder.sum())

# frequency and exceedance, warm season
res = {}
for name, s in (("thunder", d.thunder), ("hail", d.hail)):
    w = hazard.warm_season(s.dropna())
    thr = float(w.quantile(0.99))
    cnt = hazard.annual_counts(w, thr)
    res[name] = {"p99_threshold": thr, "days_above_per_year": float(cnt.mean()), "dispersion": hazard.dispersion(cnt),
                 "gpd": hazard.gpd_return_levels(w, YEARS, q=0.95), "max_day": str(w.idxmax().date()), "max_share": float(w.max()),
                 "trend_days_above_per_decade": float(np.polyfit(cnt.index.values, cnt.values, 1)[0] * 10)}
out["convective"] = res

# comparison with winter windstorms (de-windstorm-risk): breadth of the worst day or event of each year, as a share of stations.
# Thresholds differ (a station reports a thunderstorm; for the storm the gust exceeds the station's own 98th percentile), so the
# comparison is of footprint breadth, not of loss.
try:
    ev = pd.read_csv(WIND / "events.csv")
    wshare = (ev.stations_above_v98 / 156.0)[ev.season <= 2011].groupby(ev.season[ev.season <= 2011]).max()
    tshare = hazard.warm_season(d.thunder.dropna()).groupby(lambda t: t.year).max()
    hshare = hazard.warm_season(d.hail.dropna()).groupby(lambda t: t.year).max()
    out["annual_max_breadth"] = {name: {"median": float(x.median()), "p90": float(x.quantile(0.9)), "max": float(x.max()), "years": int(len(x))}
                                 for name, x in (("windstorm_stations_above_v98", wshare), ("thunderstorm_stations_reporting", tshare), ("hail_stations_reporting", hshare))}
except FileNotFoundError:
    out["annual_max_breadth"] = "de-windstorm-risk results not found"
(RES / "summary.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
print(json.dumps(out, indent=2, default=float))
