"""Download DWD daily weather phenomena (thunderstorm, hail, ...) for all stations: historical and recent, 1949-2026."""
import re
import time
from pathlib import Path

import requests

B = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/weather_phenomena/"
out = Path(__file__).parent / "dwd"
out.mkdir(exist_ok=True)
for sub in ("historical", "recent"):
    html = requests.get(B + sub + "/", timeout=120).text
    for f in sorted(set(re.findall(r'href="(wetter_tageswerte_[^"]+\.zip)"', html))):
        p = out / f
        if p.exists() and p.stat().st_size > 0:
            continue
        for k in range(5):
            try:
                r = requests.get(B + sub + "/" + f, timeout=120)
                r.raise_for_status()
                p.write_bytes(r.content)
                break
            except Exception:
                time.sleep(5)
requests.get(B + "wetter_tageswerte_Beschreibung_Stationen.txt", timeout=60)
(out / "stations.txt").write_bytes(requests.get(B + "wetter_tageswerte_Beschreibung_Stationen.txt", timeout=60).content)
print("done", len(list(out.glob("*.zip"))))
