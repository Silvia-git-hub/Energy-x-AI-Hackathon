import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

AWATTAR_URL   = "https://api.awattar.de/v1/marketdata"
SMARD_BASE    = "https://www.smard.de/app/chart_data"
SMARD_REGION  = "DE"
SMARD_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Solarbitrage/1.0)",
    "Accept":     "application/json",
    "Referer":    "https://www.smard.de/",
}

SMARD_SOLAR         = 4068
SMARD_WIND_ONSHORE  = 4066
SMARD_WIND_OFFSHORE = 4067
SMARD_LOAD          = 410

TTL_SECONDS = 900  # 15 min — matches SMARD publish cadence

@dataclass
class EpexPrice:
    hour: str            # "HH:00" UTC
    price_eur_mwh: float

@dataclass
class GridMetrics:
    solar_mwh:       Optional[float] = None
    wind_mwh:        Optional[float] = None
    load_mwh:        Optional[float] = None
    solar_share_pct: Optional[float] = None
    wind_share_pct:  Optional[float] = None

@dataclass
class MarketDataResult:
    epex_current_price: Optional[float]  = None
    epex_day_high:      Optional[float]  = None
    epex_day_low:       Optional[float]  = None
    epex_prices:        list[EpexPrice]  = field(default_factory=list)
    grid:               GridMetrics      = field(default_factory=GridMetrics)
    updated_at:         str              = ""
    available:          bool             = True
    error:              Optional[str]    = None


_cache:    Optional[MarketDataResult] = None
_cache_ts: float = 0.0


class MarketDataService:
    async def get_market_data(self) -> MarketDataResult:
        global _cache, _cache_ts
        if _cache is not None and (time.monotonic() - _cache_ts) < TTL_SECONDS:
            return _cache
        try:
            result    = await self._fetch_all()
            _cache    = result
            _cache_ts = time.monotonic()
            return result
        except Exception as exc:
            logger.warning("Market data fetch failed: %s", exc)
            if _cache is not None:
                return _cache
            return MarketDataResult(
                available=False,
                error=str(exc),
                updated_at=datetime.now(timezone.utc).isoformat(),
            )

    async def _fetch_all(self) -> MarketDataResult:
        epex, solar, wind_on, wind_off, load = await asyncio.gather(
            self._fetch_awattar(),
            self._fetch_smard_latest(SMARD_SOLAR),
            self._fetch_smard_latest(SMARD_WIND_ONSHORE),
            self._fetch_smard_latest(SMARD_WIND_OFFSHORE),
            self._fetch_smard_latest(SMARD_LOAD),
            return_exceptions=True,
        )

        prices: list[EpexPrice] = epex if isinstance(epex, list) else []
        now_h         = datetime.now(timezone.utc).strftime("%H:00")
        current_price = next((p.price_eur_mwh for p in prices if p.hour == now_h), None)
        day_high      = max((p.price_eur_mwh for p in prices), default=None)
        day_low       = min((p.price_eur_mwh for p in prices), default=None)

        def _f(v) -> Optional[float]:
            return float(v) if isinstance(v, (int, float)) else None

        solar_mwh    = _f(solar)
        wind_on_mwh  = _f(wind_on)
        wind_off_mwh = _f(wind_off)
        load_mwh     = _f(load)

        if wind_on_mwh is not None and wind_off_mwh is not None:
            wind_mwh = wind_on_mwh + wind_off_mwh
        else:
            wind_mwh = wind_on_mwh or wind_off_mwh

        solar_share = round(solar_mwh / load_mwh * 100, 1) if solar_mwh and load_mwh else None
        wind_share  = round(wind_mwh  / load_mwh * 100, 1) if wind_mwh  and load_mwh else None

        return MarketDataResult(
            epex_current_price=round(current_price, 2) if current_price is not None else None,
            epex_day_high=round(day_high, 2) if day_high is not None else None,
            epex_day_low=round(day_low,  2) if day_low  is not None else None,
            epex_prices=prices,
            grid=GridMetrics(
                solar_mwh=round(solar_mwh, 1) if solar_mwh is not None else None,
                wind_mwh=round(wind_mwh,   1) if wind_mwh  is not None else None,
                load_mwh=round(load_mwh,   1) if load_mwh  is not None else None,
                solar_share_pct=solar_share,
                wind_share_pct=wind_share,
            ),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

    async def _fetch_awattar(self) -> list[EpexPrice]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(AWATTAR_URL)
            resp.raise_for_status()
        prices = []
        for entry in resp.json().get("data", []):
            ts = datetime.fromtimestamp(entry["start_timestamp"] / 1000, tz=timezone.utc)
            prices.append(EpexPrice(
                hour=ts.strftime("%H:00"),
                price_eur_mwh=round(float(entry["marketprice"]), 2),
            ))
        return prices

    async def _fetch_smard_latest(self, filter_id: int) -> Optional[float]:
        base = f"{SMARD_BASE}/{filter_id}/{SMARD_REGION}"
        async with httpx.AsyncClient(timeout=10.0, headers=SMARD_HEADERS) as client:
            idx = await client.get(f"{base}/index_quarterhour.json")
            idx.raise_for_status()
            timestamps = idx.json().get("timestamps", [])
            if not timestamps:
                return None
            bucket = timestamps[-1]
            data = await client.get(
                f"{base}/{filter_id}_{SMARD_REGION}_quarterhour_{bucket}.json"
            )
            data.raise_for_status()
        for _ts, val in reversed(data.json().get("series", [])):
            if val is not None:
                return float(val)
        return None
