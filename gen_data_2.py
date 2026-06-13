import ee
import pandas as pd
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

# =====================================================
# CONFIGURATION
# =====================================================
PROJECT_ID = "top-places-in"

_today    = datetime.now(timezone.utc)

_ERA5_LAG = timedelta(days=365)
END_DATE   = (_today - _ERA5_LAG).strftime("%Y-%m-%d")
START_DATE = (_today - _ERA5_LAG - timedelta(days=365)).strftime("%Y-%m-%d")

CITIES = {
    # Germany only — SMARD (filter 4068) is DE national total; AT cities removed
    # because Austrian solar generation is not available in SMARD.
    "Berlin":      (52.5200,  13.4050),
    "Hamburg":     (53.5753,   9.9929),
    "Munich":      (48.1372,  11.5761),
    "Cologne":     (50.9333,   6.9500),
    "Frankfurt":   (50.1109,   8.6821),
    "Stuttgart":   (48.7758,   9.1829),
    "Dusseldorf":  (51.2217,   6.7762),
    "Leipzig":     (51.3397,  12.3731),
    "Dortmund":    (51.5136,   7.4653),
    "Essen":       (51.4556,   7.0116),
    "Bremen":      (53.0793,   8.8017),
    "Dresden":     (51.0504,  13.7373),
    "Hanover":     (52.3759,   9.7320),
    "Nuremberg":   (49.4521,  11.0767),
    "Duisburg":    (51.4344,   6.7623),
}

# SMARD — quarter-hourly PV actual generation (Germany only)
# Filter 4068 = Photovoltaik Erzeugung (tatsächlich); 4070 was wrong (non-solar series)
SMARD_FILTER  = 4068
SMARD_REGION  = "DE"
SMARD_BASE    = f"https://www.smard.de/app/chart_data/{SMARD_FILTER}/{SMARD_REGION}"
SMARD_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept":     "application/json",
    "Referer":    "https://www.smard.de/",
}

# NASA POWER — hourly solar + atmospheric variables (free, no key required)
NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/hourly/point"
NASA_PARAMS    = ",".join([
    "ALLSKY_SFC_SW_DWN",   # All-sky GHI (W/m²)
    "CLRSKY_SFC_SW_DWN",   # Clear-sky GHI (W/m²) — used to compute clearness index
    "ALLSKY_SFC_SW_DNI",   # Direct Normal Irradiance (W/m²)
    "ALLSKY_SFC_SW_DIFF",  # Diffuse Horizontal Irradiance (W/m²)
    "ALLSKY_KT",           # Clearness index (0–1): ratio of actual to clear-sky GHI
    "CLOUD_AMT",           # Cloud amount (%)
    "RH2M",                # Relative humidity at 2m (%)
    "AOD_55",              # Aerosol Optical Depth at 550nm (dimensionless)
])

# =====================================================
# INIT
# =====================================================
ee.Initialize(project=PROJECT_ID)

start_ts_ms = int(datetime.strptime(START_DATE, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)
end_ts_ms   = int(datetime.strptime(END_DATE,   "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)


# =====================================================
# HELPER: month batches (avoids EE 5000-element limit)
# =====================================================
def _month_batches(start: str, end: str) -> list[tuple[str, str]]:
    batches = []
    cur = datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    fin = datetime.strptime(end,   "%Y-%m-%d").replace(tzinfo=timezone.utc)
    while cur < fin:
        nxt = cur.replace(month=cur.month % 12 + 1, day=1) if cur.month < 12 \
              else cur.replace(year=cur.year + 1, month=1, day=1)
        nxt = min(nxt, fin)
        batches.append((cur.strftime("%Y-%m-%d"), nxt.strftime("%Y-%m-%d")))
        cur = nxt
    return batches


# =====================================================
# SOURCE 1: ERA5-Land via Google Earth Engine
# Variables: GHI, net solar, temperature, dewpoint,
#            wind, pressure, precipitation, snow, albedo
# =====================================================
ERA5_BANDS = [
    "surface_solar_radiation_downwards",   # → ghi_era5
    "surface_net_solar_radiation",         # → net_solar_w_m2
    "temperature_2m",                      # → temp_c
    "dewpoint_temperature_2m",             # → dewpoint_c
    "u_component_of_wind_10m",
    "v_component_of_wind_10m",             # → wind_speed
    "surface_pressure",                    # → pressure_hpa
    "total_precipitation",                 # → precipitation_mm
    "snow_cover",                          # → snow_cover_frac
    "forecast_albedo",                     # → albedo
]

def fetch_gee_city(city: str, lat: float, lon: float) -> pd.DataFrame:
    print(f"  [{city}] ERA5-Land (monthly batches)...")
    point   = ee.Geometry.Point([lon, lat])
    batches = _month_batches(START_DATE, END_DATE)
    records = []

    def extract(image):
        stats = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=9000,
        )
        return ee.Feature(None, {band: stats.get(band) for band in ERA5_BANDS}
                          | {"timestamp": image.date().millis()})

    for b_start, b_end in batches:
        col      = (ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY")
                    .filterDate(b_start, b_end)
                    .select(ERA5_BANDS))
        features = ee.FeatureCollection(col.map(extract)).getInfo()["features"]
        records.extend(f["properties"] for f in features)
        print(f"    {b_start} → {b_end}: {len(features)} images")

    if not records:
        raise RuntimeError(
            f"ERA5-Land returned 0 images for {city} ({START_DATE}→{END_DATE}). "
            "Data may not be published yet — increase ERA5_LAG or shift dates further back."
        )

    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df.sort_values("timestamp").reset_index(drop=True)

    # ERA5-Land accumulated fields (SSRD, SSR, TP) accumulate since 00:00 UTC each day
    # and reset at the next UTC midnight.  The 00:00 UTC image carries the PREVIOUS
    # day's cumulative total as a carryover artefact — drop it, then diff within each
    # UTC calendar date to recover per-hour flux / depth.
    df = df[df["timestamp"].dt.hour != 0].copy()
    _date = df["timestamp"].dt.date

    for raw_col, out_col, scale in [
        ("surface_solar_radiation_downwards", "ghi_era5",       1 / 3600.0),  # J/m² → W/m²
        ("surface_net_solar_radiation",       "net_solar_w_m2", 1 / 3600.0),  # J/m² → W/m²
        ("total_precipitation",               "precipitation_mm", 1000.0),    # m → mm
    ]:
        diff_vals = (
            df.groupby(_date)[raw_col]
            .diff()
            .fillna(df[raw_col])  # first hour of each day: no previous → use raw value
        )
        df[out_col] = (diff_vals * scale).clip(lower=0)

    df["temp_c"]          = df["temperature_2m"] - 273.15
    df["dewpoint_c"]      = df["dewpoint_temperature_2m"] - 273.15
    df["wind_speed"]      = (df["u_component_of_wind_10m"] ** 2 + df["v_component_of_wind_10m"] ** 2) ** 0.5
    df["pressure_hpa"]    = df["surface_pressure"] / 100.0
    df["snow_cover_frac"] = df["snow_cover"] / 100.0  # ERA5-Land reports % (0-100)
    df["albedo"]          = df["forecast_albedo"]
    df["city"]            = city
    df["lat"]             = lat
    df["lon"]             = lon

    drop_cols = ["surface_solar_radiation_downwards", "surface_net_solar_radiation",
                 "temperature_2m", "dewpoint_temperature_2m",
                 "u_component_of_wind_10m", "v_component_of_wind_10m",
                 "surface_pressure", "total_precipitation",
                 "snow_cover", "forecast_albedo"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])
    return df.sort_values("timestamp").reset_index(drop=True)


# =====================================================
# SOURCE 2: NASA POWER
# Variables: clearness index, cloud amount, DNI, DHI,
#            humidity, aerosol optical depth
# Resolution: hourly (free, no API key required)
# =====================================================
def fetch_nasa_power_city(city: str, lat: float, lon: float) -> pd.DataFrame:
    print(f"  [{city}] NASA POWER...")
    params = {
        "parameters": NASA_PARAMS,
        "community":  "RE",
        "longitude":  lon,
        "latitude":   lat,
        "start":      START_DATE.replace("-", ""),
        "end":        END_DATE.replace("-", ""),
        "format":     "JSON",
    }

    for attempt in range(1, 4):
        resp = requests.get(NASA_POWER_URL, params=params, timeout=90)
        if resp.ok:
            break
        wait = attempt * 10
        print(f"  [{city}] NASA POWER HTTP {resp.status_code}, retry {attempt}/3 in {wait}s…")
        time.sleep(wait)
    else:
        raise RuntimeError(f"NASA POWER failed for {city} after 3 retries: HTTP {resp.status_code}")

    param_data = resp.json()["properties"]["parameter"]

    # NASA POWER hourly keys are flat 10-char strings: YYYYMMDDHHH
    # e.g. "2025061300" = 2025-06-13 00:00 UTC
    rows = []
    for dt_str in next(iter(param_data.values())):
        date_part = dt_str[:8]   # YYYYMMDD
        hour      = int(dt_str[8:])  # 0-23
        ts = datetime(
            int(date_part[:4]), int(date_part[4:6]), int(date_part[6:]),
            hour, tzinfo=timezone.utc,
        )
        row = {"timestamp": pd.Timestamp(ts)}
        for param, values in param_data.items():
            val = values.get(dt_str)
            row[param.lower()] = None if val in (-999.0, -999) else val
        rows.append(row)

    if not rows:
        raise RuntimeError(
            f"NASA POWER returned no usable hourly rows for {city}. "
            f"First parameter sample: {str(next(iter(param_data.values())))[:200]}"
        )

    df = pd.DataFrame(rows)
    df = df.rename(columns={
        "allsky_sfc_sw_dwn":  "ghi_nasa",
        "clrsky_sfc_sw_dwn":  "clearsky_ghi",
        "allsky_sfc_sw_dni":  "dni_w_m2",
        "allsky_sfc_sw_diff": "dhi_w_m2",
        "allsky_kt":          "clearness_index",
        "cloud_amt":          "cloud_amount_pct",
        "rh2m":               "humidity_pct",
        "aod_55":             "aerosol_optical_depth",
    })
    return df.sort_values("timestamp").reset_index(drop=True)


# =====================================================
# SOURCE 3: SMARD — quarter-hourly PV generation
# =====================================================
def fetch_smard() -> pd.DataFrame:
    print("Fetching SMARD quarter-hourly PV generation...")
    index_resp = requests.get(f"{SMARD_BASE}/index_quarterhour.json", headers=SMARD_HEADERS)
    if not index_resp.ok:
        raise RuntimeError(f"SMARD index HTTP {index_resp.status_code}: {index_resp.text[:200]}")

    # Include buckets that overlap the window; use a generous bracket so weekly
    # bucket boundaries don't clip the edges of our date range.
    _bracket = 7 * 86_400 * 1000
    buckets = [ts for ts in index_resp.json()["timestamps"]
               if start_ts_ms - _bracket <= ts <= end_ts_ms + _bracket]
    if not buckets:
        raise RuntimeError("No SMARD buckets in range.")

    records = []
    for bucket_ts in buckets:
        url  = f"{SMARD_BASE}/{SMARD_FILTER}_{SMARD_REGION}_quarterhour_{bucket_ts}.json"
        resp = requests.get(url, headers=SMARD_HEADERS)
        print(f"  bucket {bucket_ts} → HTTP {resp.status_code}, {len(resp.text)} bytes")
        if not resp.ok or not resp.text.strip():
            continue
        for ts_ms, value in resp.json()["series"]:
            if value is not None:
                records.append({
                    "timestamp":                   pd.to_datetime(ts_ms, unit="ms", utc=True),
                    "actual_solar_generation_mwh": value,
                })

    if not records:
        raise RuntimeError("SMARD returned 0 non-null records for the selected buckets.")

    return pd.DataFrame(records).sort_values("timestamp").reset_index(drop=True)


# =====================================================
# MAIN PIPELINE
# =====================================================
print("=" * 60)
print(f"Period: {START_DATE} → {END_DATE}")
print(f"Cities: {len(CITIES)}  |  Resolution: 15-min")
print("=" * 60)

# 1. Fetch and merge GEE + NASA POWER per city (parallel)
print("\n1. Fetching ERA5-Land + NASA POWER per city (parallel, 2 workers)...")

def _fetch_city(city_name: str, lat: float, lon: float) -> pd.DataFrame:
    df_gee  = fetch_gee_city(city_name, lat, lon)
    df_nasa = fetch_nasa_power_city(city_name, lat, lon)
    df_city = pd.merge(df_gee, df_nasa, on="timestamp", how="inner")
    df_city = df_city.set_index("timestamp").resample("15min").ffill().reset_index()
    print(f"  [{city_name}] done — {len(df_city):,} rows")
    return df_city

city_frames = [None] * len(CITIES)
city_items  = list(CITIES.items())

with ThreadPoolExecutor(max_workers=2) as pool:
    futures = {
        pool.submit(_fetch_city, name, lat, lon): idx
        for idx, (name, (lat, lon)) in enumerate(city_items)
    }
    for future in as_completed(futures):
        idx = futures[future]
        city_frames[idx] = future.result()  # propagates exceptions

df_all = pd.concat(city_frames, ignore_index=True)
print(f"\nAll cities combined: {len(df_all):,} rows")

# 2. Fetch SMARD quarter-hourly
print("\n2. Fetching SMARD...")
df_smard = fetch_smard()
print(f"SMARD rows: {len(df_smard):,}")

# 3. Merge with SMARD
print("\n3. Merging...")
final_df = pd.merge(df_all, df_smard, on="timestamp", how="inner")

# Calendar features (before timestamp conversion)
final_df["hour"]        = final_df["timestamp"].dt.hour
final_df["minute"]      = final_df["timestamp"].dt.minute
final_df["day_of_year"] = final_df["timestamp"].dt.dayofyear
final_df["month"]       = final_df["timestamp"].dt.month
final_df["weekday"]     = final_df["timestamp"].dt.weekday  # 0=Mon, 6=Sun

# Unix timestamp in seconds
final_df["timestamp"] = final_df["timestamp"].apply(lambda x: int(x.timestamp()))

final_df = final_df[[
    "timestamp", "city", "lat", "lon",
    "hour", "minute", "day_of_year", "month", "weekday",
    # ERA5-Land
    "ghi_era5", "net_solar_w_m2", "temp_c", "dewpoint_c",
    "wind_speed", "pressure_hpa", "precipitation_mm",
    "snow_cover_frac", "albedo",
    # NASA POWER
    "ghi_nasa", "clearsky_ghi", "dni_w_m2", "dhi_w_m2",
    "clearness_index", "cloud_amount_pct", "humidity_pct", "aerosol_optical_depth",
    # Target
    "actual_solar_generation_mwh",
]].sort_values(["timestamp", "city"]).reset_index(drop=True)

final_df.to_csv("smard_solar_dataset.csv", index=False)
print(f"\nSaved {len(final_df):,} rows × {len(final_df.columns)} columns to smard_solar_dataset.csv")
print(final_df.head(5).to_string())
print("\nColumns:", list(final_df.columns))
