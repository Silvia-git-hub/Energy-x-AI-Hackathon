from fastapi import APIRouter
from app.services.market_intel import MarketIntelService
from app.schemas.responses import MarketIntelResponse, NewsItemSchema, PredictionMarketSchema

router = APIRouter()


@router.get("/market-intel", response_model=MarketIntelResponse)
async def market_intel() -> MarketIntelResponse:
    svc = MarketIntelService()
    result = await svc.get_intel()
    return MarketIntelResponse(
        news=[
            NewsItemSchema(
                title=n.title,
                summary=n.summary,
                sentiment=n.sentiment,
                url=n.url,
            )
            for n in result.news
        ],
        markets=[
            PredictionMarketSchema(
                question=m.question,
                probability=m.probability,
                url=m.url,
            )
            for m in result.markets
        ],
        updated_at=result.updated_at,
        available=result.available,
        error=result.error,
    )
