import asyncio

from fastapi import APIRouter

from app.config import settings
from app.schemas.requests import EvaluateLocationRequest
from app.schemas.responses import EvaluateResponse, SubScoreData
from app.services.google_solar import GoogleSolarService
from app.services.pvgis import PvgisService
from app.services.open_meteo_climate import OpenMeteoClimateService
from app.services.scoring import compute_overall_score

router = APIRouter()


@router.post("/evaluate-location", response_model=EvaluateResponse)
async def evaluate_location(body: EvaluateLocationRequest) -> EvaluateResponse:
    google_svc  = GoogleSolarService(api_key=settings.google_solar_api_key)
    pvgis_svc   = PvgisService()
    climate_svc = OpenMeteoClimateService()

    google_result, pvgis_result, climate_result = await asyncio.gather(
        google_svc.get_building_insights(body.lat, body.lon),
        pvgis_svc.get_irradiance(body.lat, body.lon),
        climate_svc.get_cloud_cover(body.lat, body.lon),
    )

    score = compute_overall_score(google_result, pvgis_result, climate_result)

    return EvaluateResponse(
        lat=body.lat,
        lon=body.lon,
        overall_score=score.overall,
        sub_scores={
            "google_solar": SubScoreData(
                score=score.google_solar.score,
                available=score.google_solar.available,
                error=score.google_solar.error,
                metrics=score.google_solar.raw_metrics,
            ),
            "pvgis": SubScoreData(
                score=score.pvgis.score,
                available=score.pvgis.available,
                error=score.pvgis.error,
                metrics=score.pvgis.raw_metrics,
            ),
            "climate": SubScoreData(
                score=score.climate.score,
                available=score.climate.available,
                error=score.climate.error,
                metrics=score.climate.raw_metrics,
            ),
        },
        weights_used=score.weights_used,
        chart_data=score.chart_data,
        data_warning=score.data_warning,
    )
