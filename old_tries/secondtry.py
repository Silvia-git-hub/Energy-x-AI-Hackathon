import ee
import pandas as pd

# =====================================================
# CONFIGURATION
# =====================================================
PROJECT_ID = "firsttryhackathon"
LAT, LON = 48.137154, 11.576124
START_DATE = "2014-01-01"
END_DATE   = "2024-01-01"
STEP_DAYS  = 10

# Initialize Earth Engine
ee.Initialize(project=PROJECT_ID)
point = ee.Geometry.Point([LON, LAT])

# =====================================================
# OPTIMIZED EARTH ENGINE PIPELINE
# =====================================================

# 1. Load the ImageCollection once
era5 = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR") \
         .select("surface_solar_radiation_downwards_sum")

# 2. Generate dates entirely on the server side
start_ee = ee.Date(START_DATE)
end_ee = ee.Date(END_DATE)
diff_days = end_ee.difference(start_ee, 'days')

# Create a list of day offsets (0, 10, 20, 30...)
day_offsets = ee.List.sequence(0, diff_days.subtract(1), STEP_DAYS)

# 3. Map over the offsets to extract data completely in the cloud
def extract_radiation(day_offset):
    date = start_ee.advance(ee.Number(day_offset), 'days')
    
    # Filter for that specific single day
    image = era5.filterDate(date, date.advance(1, 'day')).first()
    
    # Reduce region for the point
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=10000,
        maxPixels=1e9
    )
    
    # Return a Feature with properties for easy parsing later
    return ee.Feature(None, {
        'date': date.format('YYYY-MM-DD'),
        'irradiance': stats.get('surface_solar_radiation_downwards_sum')
    })

# Run the server-side loop
server_sequence = day_offsets.map(extract_radiation)

# 4. Bring the data to the client with ONE SINGLE network request
print("Fetching all data from Earth Engine at once...")
extracted_features = ee.FeatureCollection(server_sequence).getInfo()['features']

# =====================================================
# PROCESS RESULTS LOCAL-SIDE
# =====================================================
records = [f['properties'] for f in extracted_features if f['properties']['irradiance'] is not None]

df = pd.DataFrame(records)
irradiance_mean = df["irradiance"].mean()

print("\n==========================")
print("RESULTS")
print("==========================")
print(f"Samples: {len(df)}")
print(f"Mean Irradiance: {irradiance_mean}")
print("==========================\n")

df.to_csv("irradiance_10day_samples.csv", index=False)
print("Saved to irradiance_10day_samples.csv")
