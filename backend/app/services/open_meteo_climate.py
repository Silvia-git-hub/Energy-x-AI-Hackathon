import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


@dataclass
class ClimateResult:
    avg_cloud_cover_pct: float = 50.0
    sample_days: int = 0
    available: bool = True
    error: Optional[str] = None


class OpenMeteoClimateService:
    async def get_cloud_cover(self, lat: float, lon: float) -> ClimateResult:
        try:
            # Historical archive has ~5-day delay; use last 90 days
            end = date.today() - timedelta(days=5)
            start = end - timedelta(days=89)

            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(
                    ARCHIVE_URL,
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "start_date": start.isoformat(),
                        "end_date": end.isoformat(),
                        "hourly": "cloud_cover",
                        "timezone": "UTC",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            values = [v for v in data["hourly"]["cloud_cover"] if v is not None]
            avg = sum(values) / len(values) if values else 50.0

            return ClimateResult(
                avg_cloud_cover_pct=round(avg, 1),
                sample_days=len(values) // 24,
            )

        except httpx.HTTPStatusError as exc:
            msg = f"Open-Meteo HTTP {exc.response.status_code}"
            logger.warning("Climate service error: %s", msg)
            return ClimateResult(available=False, error=msg)
        except Exception as exc:
            logger.warning("Climate service failed: %s", exc)
            return ClimateResult(available=False, error=str(exc))
