import ee
import pandas as pd

# =====================================================
# CONFIGURATION
# =====================================================
PROJECT_ID = "firsttryhackathon"
LAT, LON = 48.137154, 11.576124
START_DATE = "2016-01-01"
END_DATE   = "2026-01-01"
STEP_DAYS  = 10

# Initialize Earth Engine
ee.Initialize(project=PROJECT_ID)
point = ee.Geometry.Point([LON, LAT])

# =====================================================
# OPTIMIZED EARTH ENGINE PIPELINE
# =====================================================

# 1. Load the ImageCollection once
era5 = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR").select("surface_solar_radiation_downwards_sum", "temperature_2m")
# for cloudiness
merra2 = ee.ImageCollection("NASA/GSFC/MERRA/rad/2").select("CLDTOT")
# other stuff
merraae2 = ee.ImageCollection("NASA/GSFC/MERRA/aer/2").select("DUCMASS", "TOTEXTTAU", "TOTSCATAU")

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
    image2 = merra2.filterDate(date, date.advance(1, 'day')).first()
    image3 = merraae2.filterDate(date, date.advance(1, 'day')).first()
    
    # Reduce region for the point
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=10000,
        maxPixels=1e9
    )
    stats2 = image2.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=10000,
        maxPixels=1e9
    )
    stats3 = image3.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=10000,
        maxPixels=1e9
    )
    
    # Return a Feature with properties for easy parsing later
    return ee.Feature(None, {
        'date': date.format('YYYY-MM-DD'),
        'irradiance': stats.get('surface_solar_radiation_downwards_sum'),
        'temperature': stats.get('temperature_2m'),
        'cloudiness': stats2.get('CLDTOT'),
        'Dust_column_mass_density': stats3.get('DUCMASS'),
        'aerosol_extinction': stats3.get('TOTEXTTAU'),
        'aerosol_scattering': stats3.get('TOTSCATAU')
    })

# Run the server-side loop
server_sequence = day_offsets.map(extract_radiation)

# 4. Bring the data to the client with ONE SINGLE network request
print("Fetching all data from Earth Engine at once...")
extracted_features = ee.FeatureCollection(server_sequence).getInfo()['features']

# =====================================================
# PROCESS RESULTS LOCAL-SIDE
# =====================================================
records = [f['properties'] for f in extracted_features if f['properties']['irradiance'] is not None and f['properties']['temperature'] is not None and f['properties']['cloudiness'] is not None and f['properties']['Dust_column_mass_density'] is not None and f['properties']['aerosol_extinction'] is not None and f['properties']['aerosol_scattering'] is not None]

df = pd.DataFrame(records)
irradiance_mean = df["irradiance"].mean()
temperature_mean = df["temperature"].mean()
cloudiness_mean = df["cloudiness"].mean()
dust_column_mass_density_mean = df["Dust_column_mass_density"].mean()
aerosol_extinction_mean = df["aerosol_extinction"].mean()
aerosol_scattering_mean = df["aerosol_scattering"].mean()
print("\n==========================")
print("RESULTS")
print("==========================")
print(f"Samples: {len(df)}")
print(f"Mean Irradiance: {irradiance_mean}")
print("==========================\n")
print(f"Mean Temperature: {temperature_mean}")
print("==========================\n")
print(f"Mean Cloudiness: {cloudiness_mean}")
print("==========================\n")
print(f"Mean Dust Column Mass Density: {dust_column_mass_density_mean}")
print("==========================\n")
print(f"Mean Aerosol Extinction: {aerosol_extinction_mean}")
print("==========================\n")
print(f"Mean Aerosol Scattering: {aerosol_scattering_mean}")
print("==========================\n")


df.to_csv("irradiance_10day_samples.csv", index=False)
print("Saved to irradiance_10day_samples.csv")
