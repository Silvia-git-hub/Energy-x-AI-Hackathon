from typing import Optional
from pydantic import BaseModel, Field


class EvaluateLocationRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    location_context: dict = Field(default_factory=dict)


class ForecastRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    panel_count: int = Field(default=10, ge=1, le=10_000)
    panel_capacity_watts: float = Field(default=400.0, ge=1.0, le=1_000.0)
    surface_tilt: Optional[float] = Field(default=None, ge=0, le=90)
    surface_azimuth: float = Field(default=180.0, ge=0, le=360)
    solar_index: float = Field(default=50.0, ge=0.0, le=100.0)
    epex_price: Optional[float] = Field(default=None)        # €/MWh current EPEX DA price
    solar_share_pct: Optional[float] = Field(default=None)  # % of grid load from solar


class GeocodeRequest(BaseModel):
    address: str = Field(..., min_length=2, max_length=500)


class NearbyRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    eumetsat_score: float = Field(default=50.0, ge=0, le=100)
    copernicus_score: float = Field(default=50.0, ge=0, le=100)
    eumetsat_available: bool = True
    copernicus_available: bool = True
