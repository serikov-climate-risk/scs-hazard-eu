"""Read DWD daily weather phenomena (thunderstorm, hail) of all stations from the downloaded zip files."""
import io
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


def read_zip(path):
    z = zipfile.ZipFile(path)
    prod = [n for n in z.namelist() if n.startswith("produkt")][0]
    df = pd.read_csv(io.BytesIO(z.read(prod)), sep=";", skipinitialspace=True, na_values=["-999", "-999.0"])
    df.columns = [c.strip() for c in df.columns]
    df = df.drop(columns=[c for c in df.columns if c == "eor"], errors="ignore")
    df["date"] = pd.to_datetime(df["MESS_DATUM"].astype(str), format="%Y%m%d")
    geo = [n for n in z.namelist() if "Geographie" in n][0]
    g = pd.read_csv(io.BytesIO(z.read(geo)), sep=";", skipinitialspace=True, encoding="latin1")
    g.columns = [c.strip() for c in g.columns]
    g = g.sort_values("bis_datum").iloc[-1]
    return df[["STATIONS_ID", "date", "GEWITTER", "HAGEL"]], (int(g["Stations_id"]), float(g["Geogr.Breite"]), float(g["Geogr.Laenge"]))


def load_all(folder, start="1991-01-01", end="2025-12-31"):
    """Long table of station-days (thunder, hail as 0/1, NaN if missing) and a station table with coordinates."""
    frames, geos = {}, {}
    for f in sorted(Path(folder).glob("wetter_tageswerte_*.zip")):
        df, geo = read_zip(f)
        df = df[(df.date >= start) & (df.date <= end)]
        if df.empty:
            continue
        frames.setdefault(geo[0], []).append(df)
        geos[geo[0]] = geo
    # a station can appear in a historical and a recent file: concatenate and drop duplicate days
    out = []
    for sid, lst in frames.items():
        d = pd.concat(lst).drop_duplicates("date", keep="last")
        out.append(d)
    long = pd.concat(out, ignore_index=True)
    st = pd.DataFrame(geos.values(), columns=["STATIONS_ID", "lat", "lon"]).set_index("STATIONS_ID")
    return long, st


def stable_stations(long, start="1991-01-01", end="2025-12-31", min_cover=0.9):
    """Stations with data on at least min_cover of all days of the period (the network changed a lot: stations that stop or start
    would create a trend in any count)."""
    n = (pd.Timestamp(end) - pd.Timestamp(start)).days + 1
    cov = long.dropna(subset=["GEWITTER"]).groupby("STATIONS_ID").date.nunique() / n
    return cov[cov >= min_cover].index.tolist()


def daily_index(long, stations, flag):
    """Share of the given stations reporting the phenomenon on each day (stations with missing data left out that day)."""
    d = long[long.STATIONS_ID.isin(stations)].dropna(subset=[flag])
    g = d.groupby("date")[flag]
    return (g.mean()).rename(flag), g.count().rename("n_active")
