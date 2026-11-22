# Severe convective storms in Germany from station observations: frequency, extent and a comparison with winter windstorms

Hazard study without vulnerability. How often do thunderstorms and hail affect many places on the same day in Germany, how is the hazard distributed over the year, and how does the breadth of the worst day of a year compare with that of the worst winter windstorm? (The European Severe Weather Database needs a registration; the substitute is the DWD station record, which is open.)

**Data.** DWD Climate Data Center, daily weather phenomena (thunderstorm, hail), 739 stations; the observer-based record effectively ends in 2011 (only a handful of stations report afterwards), so the study period is **1991 to 2011 (21 years)** and uses the **233 stations with data on at least 85% of the days**. Winter windstorm breadth comes from the sibling project `de-windstorm-risk` (861 events at 156 stations, 1991-2025; seasons up to 2011 used here).

## Results (`results/summary.json`)
- **Frequency per station.** 20 thunderstorm days a year on average (10th to 90th percentile of stations 12 to 28), 1.2 hail days (0.5 to 2.0); the south (below 51 N) has 1.09 times the thunderstorm days of the north. 64% of thunderstorm days fall in June to August, the peak month is July (monthly mean share of stations reporting: 16% in July, 14% in June, 12% in August, 1.2% or less from November to February; `monthly_share.csv`).
- **Extent.** The widest day was 22 July 1995 with 84% of the 233 stations reporting a thunderstorm; the widest hail day 31 May 2001 with 12% of stations. A typical year's widest thunderstorm day reaches 71% of stations (90th percentile of years 81%); the widest hail day of a year reaches 8% (90th percentile 9%). The index is a share of stations, so it is bounded: a generalised Pareto fit above the 95th percentile of warm-season days gives a negative shape (-0.5 thunderstorm, -0.2 hail) and return levels that flatten at 0.84 (1-in-100 years) for thunderstorm and 0.12 for hail. They are a statement about breadth, not about loss.
- **Frequency model.** Days above the warm-season 99th percentile (index above 0.64 for thunderstorms, 0.06 for hail) occur 1.9 times a year; their annual counts are not overdispersed (variance to mean 0.82 and 0.81, so a Poisson count is consistent with the data in these 21 years) and show a trend of -0.6 (thunderstorm) and -0.3 (hail) days per decade that was not tested for significance.
- **Against winter windstorms.** The worst windstorm of a winter lifts the gust above the station's own 98th percentile at a median of 87% of stations (90th percentile of winters 96%), against a median of 71% of stations reporting a thunderstorm on the worst convective day of a year. The thresholds differ (a reported thunderstorm is a weaker condition than a 98th-percentile gust), so this compares breadth of footprints, not damage; hail, the damaging convective peril, reaches at most 12% of stations on one day.

## What this does not show
No vulnerability, exposure or loss; observer-based flags, not radar or hail size (small hail counts); the network shrank from 560 to 375 stations during 1991 to 2011 and only stations with 85% coverage are used, which keeps the index comparable but does not remove changes in observer practice; no trend statement beyond 21 years. The environment-based part of the plan (ERA5 CAPE and shear calibrated to these days) is **not done yet**: the data source was rate limited on the day of the run. Wildfires and tropical cyclones are not covered.

## Run
```
python scripts/run_all.py     # reads the DWD zip files from z_data/z11/dwd (downloaded by scripts/download_dwd.py)
pytest
```
