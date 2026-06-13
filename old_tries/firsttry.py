import ee
import pandas as pd
from datetime import datetime, timedelta

# =====================================================
# CONFIGURATION
# =====================================================

PROJECT_ID = "firsttryhackathon"

LAT = 48.137154
LON = 11.576124

START_DATE = "2014-01-01"
END_DATE   = "2024-01-01"

STEP_DAYS = 10

# =====================================================
# INITIALIZE EARTH ENGINE
# =====================================================

ee.Initialize(project=PROJECT_ID)

point = ee.Geometry.Point([LON, LAT])

# =====================================================
# DATASETS
# =====================================================

era5 = (
    ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
    .filterDate(START_DATE, END_DATE)
)

# Daily accumulated solar radiation
radiation_collection = era5.select(
    "surface_solar_radiation_downwards_sum"
)

# =====================================================
# GENERATE DATES
# =====================================================

start = datetime.strptime(START_DATE, "%Y-%m-%d")
end = datetime.strptime(END_DATE, "%Y-%m-%d")

dates = []

current = start

while current < end:
    dates.append(current)
    current += timedelta(days=STEP_DAYS)

# =====================================================
# DOWNLOAD DATA
# =====================================================

records = []

for date in dates:

    date_str = date.strftime("%Y-%m-%d")

    print(f"Processing {date_str}")

    image = (
        radiation_collection
        .filterDate(
            date_str,
            (date + timedelta(days=1)).strftime("%Y-%m-%d")
        )
        .first()
    )

    if image is None:
        continue

    try:

        result = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=10000,
            maxPixels=1e9
        ).getInfo()

        radiation = result.get(
            "surface_solar_radiation_downwards_sum"
        )

        records.append({
            "date": date_str,
            "irradiance": radiation
        })

    except Exception as e:

        print(
            f"Failed for {date_str}: {e}"
        )

# =====================================================
# CREATE DATAFRAME
# =====================================================

df = pd.DataFrame(records)

# =====================================================
# LOCAL STATISTICS
# =====================================================

irradiance_mean = df["irradiance"].mean()

print("\n==========================")
print("RESULTS")
print("==========================")
print(f"Samples: {len(df)}")
print(f"Mean Irradiance: {irradiance_mean}")
print("==========================\n")

# Save raw data
df.to_csv(
    "irradiance_10day_samples.csv",
    index=False
)

print(
    "Saved to irradiance_10day_samples.csv"
)
