from fastapi import APIRouter

from app.schemas.requests import GeocodeRequest, NearbyRequest
from app.schemas.responses import GeocodeResponse, NearbyResponse, NearbyLocationSchema
from app.services.geocoding import GeocodingService
from app.services.nearby import NearbyService

router = APIRouter()


@router.post("/geocode", response_model=GeocodeResponse)
async def geocode(body: GeocodeRequest) -> GeocodeResponse:
    svc = GeocodingService()
    result = await svc.geocode(body.address)
    return GeocodeResponse(
        lat=result.lat,
        lon=result.lon,
        display_name=result.display_name,
        short_name=result.short_name,
        available=result.available,
        error=result.error,
    )


@router.post("/nearby", response_model=NearbyResponse)
async def nearby(body: NearbyRequest) -> NearbyResponse:
    svc = NearbyService()
    result = await svc.get_nearby(
        lat=body.lat,
        lon=body.lon,
        eumetsat_score=body.eumetsat_score,
        copernicus_score=body.copernicus_score,
        eumetsat_available=body.eumetsat_available,
        copernicus_available=body.copernicus_available,
    )
    return NearbyResponse(
        locations=[
            NearbyLocationSchema(
                lat=loc.lat,
                lon=loc.lon,
                display_name=loc.display_name,
                short_name=loc.short_name,
                overall_score=loc.overall_score,
                google_score=loc.google_score,
                google_available=loc.google_available,
                error=loc.error,
            )
            for loc in result.locations
        ]
    )
