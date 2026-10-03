"""
Downloads BTS On-Time Performance monthly files (2025-2026), keeps only DFW departures,
and writes one condensed CSV: dfw_departures.csv

Usage:  python download_dfw_bts.py
Needs:  pip install pandas requests
Months BTS has not published yet are skipped automatically.
"""
import io, zipfile, time, requests, pandas as pd

YEARS = [ 2025, 2026]
KEEP = ["Year","Month","DayofMonth","DayOfWeek","FlightDate","Reporting_Airline","Origin","Dest",
        "CRSDepTime","CRSElapsedTime","Distance","DepDelay","DepDel15","Cancelled","Diverted"]

URL = ("https://transtats.bts.gov/PREZIP/"
       "On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{y}_{m}.zip")

dfw_df = []
for y in YEARS:
    for m in range(1, 13):
        url = URL.format(y=y, m=m)
        try:
            r = requests.get(url, timeout=300, headers={"User-Agent": "Mozilla/5.0"})
        except requests.RequestException as e:
            print(f"{y}-{m:02d}: network error ({e}); skipping"); continue
        if r.status_code != 200:
            print(f"{y}-{m:02d}: not available (HTTP {r.status_code}); skipping"); continue
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
            with z.open(name) as f:
                df = pd.read_csv(f, usecols=lambda c: c in KEEP, low_memory=False)
        # reset dataframe to only flights originating from DFW
        df = df[df["Origin"] == "DFW"]
        print(f"{y}-{m:02d}: {len(df):,} DFW departures")
        dfw_df.append(df)
        time.sleep(1)

if not dfw_df:
    raise SystemExit("Nothing downloaded. Use manual download instead.")
out = pd.concat(dfw_df, ignore_index=True)
out.to_csv("dfw_departures.csv", index=False)
print(f"\nSaved dfw_departures.csv with {len(out):,} rows "
      f"({out.FlightDate.min()} to {out.FlightDate.max()})")
