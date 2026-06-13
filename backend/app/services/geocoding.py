import logging
import math
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
HEADERS = {"User-Agent": "SolarViewr/1.0 (hackathon-demo)"}


@dataclass
class GeocodeResult:
    lat: float
    lon: float
    display_name: str
    short_name: str
    available: bool = True
    error: Optional[str] = None


class GeocodingService:
    async def geocode(self, address: str) -> GeocodeResult:
        try:
            async with httpx.AsyncClient(timeout=10.0, headers=HEADERS) as client:
                resp = await client.get(
                    f"{NOMINATIM_BASE}/search",
                    params={"q": address, "format": "json", "limit": 1, "addressdetails": 1},
                )
                resp.raise_for_status()
                results = resp.json()

            if not results:
                return GeocodeResult(lat=0, lon=0, display_name="", short_name="",
                                     available=False, error=f"No results found for '{address}'")

            r = results[0]
            lat, lon = float(r["lat"]), float(r["lon"])
            display = r.get("display_name", "")
            short = _short_name(r.get("address", {}), display)
            return GeocodeResult(lat=lat, lon=lon, display_name=display, short_name=short)

        except Exception as exc:
            logger.warning("Geocode failed for '%s': %s", address, exc)
            return GeocodeResult(lat=0, lon=0, display_name="", short_name="",
                                 available=False, error=str(exc))

    async def reverse_geocode(self, lat: float, lon: float) -> GeocodeResult:
        try:
            async with httpx.AsyncClient(timeout=10.0, headers=HEADERS) as client:
                resp = await client.get(
                    f"{NOMINATIM_BASE}/reverse",
                    params={"lat": lat, "lon": lon, "format": "json", "addressdetails": 1},
                )
                resp.raise_for_status()
                r = resp.json()

            display = r.get("display_name", f"{lat:.4f}, {lon:.4f}")
            short = _short_name(r.get("address", {}), display)
            return GeocodeResult(lat=lat, lon=lon, display_name=display, short_name=short)

        except Exception as exc:
            logger.warning("Reverse geocode failed (%s, %s): %s", lat, lon, exc)
            return GeocodeResult(lat=lat, lon=lon,
                                 display_name=f"{lat:.4f}, {lon:.4f}",
                                 short_name=f"{lat:.4f}, {lon:.4f}",
                                 available=False, error=str(exc))


def _short_name(addr: dict, fallback: str) -> str:
    """Extract a concise human-readable label from a Nominatim address dict."""
    for key in ("neighbourhood", "suburb", "quarter", "city_district",
                "borough", "town", "village", "city", "county"):
        if key in addr:
            country = addr.get("country_code", "").upper()
            return f"{addr[key]}, {country}" if country else addr[key]
    # Fall back to first two comma-separated parts of display_name
    parts = fallback.split(",")
    return ", ".join(p.strip() for p in parts[:2])


def nearby_coords(lat: float, lon: float, radius_km: float = 1.5, n: int = 8) -> list[tuple[float, float]]:
    """Return n evenly-spaced points around lat/lon at approximately radius_km."""
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * math.cos(math.radians(lat)))
    points = []
    for i in range(n):
        angle = 2 * math.pi * i / n
        points.append((
            round(lat + dlat * math.sin(angle), 6),
            round(lon + dlon * math.cos(angle), 6),
        ))
    return points
