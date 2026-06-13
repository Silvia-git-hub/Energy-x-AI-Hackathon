from fastapi import APIRouter

from app.schemas.requests import ForecastRequest
from app.schemas.responses import ForecastResponse, HourlyPoint, DailyTotal
from app.services.forecast import ForecastService

router = APIRouter()


@router.post("/forecast", response_model=ForecastResponse)
async def forecast(body: ForecastRequest) -> ForecastResponse:
    svc = ForecastService()
    result = await svc.get_forecast(
        lat=body.lat,
        lon=body.lon,
        panel_count=body.panel_count,
        panel_capacity_watts=body.panel_capacity_watts,
        surface_tilt=body.surface_tilt,
        surface_azimuth=body.surface_azimuth,
        solar_index=body.solar_index,
        epex_price=body.epex_price,
        solar_share_pct=body.solar_share_pct,
    )

    if not result.available:
        return ForecastResponse(
            system_kwp=0.0,
            skill_score=0.0,
            mae_kw=0.0,
            hourly=[],
            daily=[],
            signal="HOLD",
            signal_score=0.0,
            signal_reasons=[],
            available=False,
            error=result.error,
        )

    return ForecastResponse(
        system_kwp=result.system_kwp,
        skill_score=result.skill_score,
        mae_kw=result.mae_kw,
        hourly=[
            HourlyPoint(
                timestamp=h.timestamp,
                p_kw=h.p_kw,
                p_kw_baseline=h.p_kw_baseline,
                ghi_w_m2=h.ghi_w_m2,
            )
            for h in result.hourly
        ],
        daily=[
            DailyTotal(date=d.date, kwh=d.kwh, kwh_baseline=d.kwh_baseline)
            for d in result.daily
        ],
        signal=result.signal,
        signal_score=result.signal_score,
        signal_reasons=result.signal_reasons,
    )
