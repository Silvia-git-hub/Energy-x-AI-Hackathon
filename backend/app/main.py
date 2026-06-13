from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.exceptions import DomainError, domain_exception_handler
from app.core.logging import setup_logging
from app.routers import evaluate, chat as chat_router, forecast as forecast_router, geocoding as geocoding_router, market_data as market_data_router, market_intel as market_intel_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Solar Viewr API",
        version="1.0.0",
        description="Solar panel suitability scoring powered by Google Solar, EUMETSAT, and Copernicus.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(DomainError, domain_exception_handler)

    app.include_router(evaluate.router, prefix="/api", tags=["evaluate"])
    app.include_router(chat_router.router, prefix="/api", tags=["chat"])
    app.include_router(forecast_router.router, prefix="/api", tags=["forecast"])
    app.include_router(geocoding_router.router, prefix="/api", tags=["geocoding"])
    app.include_router(market_data_router.router,  prefix="/api", tags=["market-data"])
    app.include_router(market_intel_router.router, prefix="/api", tags=["market-intel"])

    @app.get("/health", include_in_schema=False)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
