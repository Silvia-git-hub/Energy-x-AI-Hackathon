import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional

from app.config import settings
from app.services.geocoding import GeocodingService, nearby_coords
from app.services.google_solar import GoogleSolarService
from app.services.scoring import _normalize_google, _clamp
from app.services.google_solar import GoogleSolarResult

logger = logging.getLogger(__name__)

# For nearby points we reuse the macro scores (Copernicus cloud cover and
# EUMETSAT irradiance barely change over 1-2 km) and only re-run Google Solar,
# which captures roof-level micro-shading differences between buildings.
GOOGLE_W = 0.50
EUMETSAT_W = 0.30
COPERNICUS_W = 0.20


@dataclass
class NearbyLocation:
    lat: float
    lon: float
    display_name: str
    short_name: str
    overall_score: float
    google_score: float
    google_available: bool
    error: Optional[str] = None


@dataclass
class NearbyResult:
    locations: list[NearbyLocation] = field(default_factory=list)
    available: bool = True
    error: Optional[str] = None


class NearbyService:
    def __init__(self) -> None:
        self._geo = GeocodingService()
        self._solar = GoogleSolarService(api_key=settings.google_solar_api_key)

    async def get_nearby(
        self,
        lat: float,
        lon: float,
        eumetsat_score: float,
        copernicus_score: float,
        eumetsat_available: bool = True,
        copernicus_available: bool = True,
    ) -> NearbyResult:
        coords = nearby_coords(lat, lon, radius_km=1.5, n=8)

        # Fetch Google Solar + reverse geocode for all points concurrently
        tasks = [
            self._score_point(
                pt_lat, pt_lon,
                eumetsat_score, copernicus_score,
                eumetsat_available, copernicus_available,
            )
            for pt_lat, pt_lon in coords
        ]
        locations = await asyncio.gather(*tasks, return_exceptions=False)

        # Sort by score descending
        locations.sort(key=lambda loc: loc.overall_score, reverse=True)
        return NearbyResult(locations=list(locations))

    async def _score_point(
        self,
        lat: float,
        lon: float,
        eumetsat_score: float,
        copernicus_score: float,
        eumetsat_available: bool,
        copernicus_available: bool,
    ) -> NearbyLocation:
        # Run Google Solar + reverse geocode concurrently for this point
        google_task = self._solar.get_building_insights(lat, lon)
        geo_task = self._geo.reverse_geocode(lat, lon)
        google_result, geo_result = await asyncio.gather(google_task, geo_task)

        google_score = _clamp(_normalize_google(google_result)) if google_result.available else 0.0

        # Effective weights: redistribute if macro sources unavailable
        available_weights = {
            "google": GOOGLE_W,
            **({"eumetsat": EUMETSAT_W} if eumetsat_available else {}),
            **({"copernicus": COPERNICUS_W} if copernicus_available else {}),
        }
        total = sum(available_weights.values())
        eff = {k: v / total for k, v in available_weights.items()}

        overall = (
            eff.get("google", 0) * google_score
            + eff.get("eumetsat", 0) * eumetsat_score
            + eff.get("copernicus", 0) * copernicus_score
        )

        return NearbyLocation(
            lat=lat,
            lon=lon,
            display_name=geo_result.display_name,
            short_name=geo_result.short_name,
            overall_score=round(overall, 1),
            google_score=round(google_score, 1),
            google_available=google_result.available,
            error=google_result.error if not google_result.available else None,
        )
