from fastapi import APIRouter

from app.schemas.responses import MarketDataResponse, EpexPrice, GridMetrics
from app.services.market_data import MarketDataService

router = APIRouter()


@router.get("/market-data", response_model=MarketDataResponse)
async def market_data() -> MarketDataResponse:
    svc    = MarketDataService()
    result = await svc.get_market_data()
    return MarketDataResponse(
        epex_current_price=result.epex_current_price,
        epex_day_high=result.epex_day_high,
        epex_day_low=result.epex_day_low,
        epex_prices=[
            EpexPrice(hour=p.hour, price_eur_mwh=p.price_eur_mwh)
            for p in result.epex_prices
        ],
        grid=GridMetrics(
            solar_mwh=result.grid.solar_mwh,
            wind_mwh=result.grid.wind_mwh,
            load_mwh=result.grid.load_mwh,
            solar_share_pct=result.grid.solar_share_pct,
            wind_share_pct=result.grid.wind_share_pct,
        ),
        updated_at=result.updated_at,
        available=result.available,
        error=result.error,
    )
