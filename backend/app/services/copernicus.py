import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

CDSE_TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE"
    "/protocol/openid-connect/token"
)
CDSE_STAC_SEARCH = "https://catalogue.dataspace.copernicus.eu/stac/search"


@dataclass
class CopernicusResult:
    avg_cloud_cover_pct: float = 50.0
    clearness_index: float = 50.0
    scene_count: int = 0
    available: bool = True
    error: Optional[str] = None


class CopernicusSentinelService:
    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    async def _get_token(self, client: httpx.AsyncClient) -> str:
        resp = await client.post(
            CDSE_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    async def get_clearness_index(
        self, lat: float, lon: float, days_back: int = 90
    ) -> CopernicusResult:
        try:
            bbox = [lon - 0.1, lat - 0.1, lon + 0.1, lat + 0.1]
            now = datetime.now(tz=timezone.utc)
            start = (now - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
            end = now.strftime("%Y-%m-%dT%H:%M:%SZ")

            async with httpx.AsyncClient(timeout=20.0) as client:
                token = await self._get_token(client)
                resp = await client.post(
                    CDSE_STAC_SEARCH,
                    json={
                        "collections": ["SENTINEL-2"],
                        "bbox": bbox,
                        "datetime": f"{start}/{end}",
                        "limit": 50,
                    },
                    headers={"Authorization": f"Bearer {token}"},
                )
                resp.raise_for_status()
                features = resp.json().get("features", [])

            if not features:
                return CopernicusResult(
                    avg_cloud_cover_pct=50.0,
                    clearness_index=50.0,
                    scene_count=0,
                    available=True,
                    error="No Sentinel-2 scenes found for this location/period; using default cloud cover.",
                )

            cloud_covers = [
                f["properties"].get("eo:cloud_cover", 50.0)
                for f in features
                if "properties" in f
            ]
            avg_cc = sum(cloud_covers) / len(cloud_covers) if cloud_covers else 50.0

            return CopernicusResult(
                avg_cloud_cover_pct=avg_cc,
                clearness_index=avg_cc,
                scene_count=len(features),
            )

        except httpx.HTTPStatusError as exc:
            msg = f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"
            logger.warning("Copernicus API error: %s", msg)
            return CopernicusResult(available=False, error=msg)
        except Exception as exc:
            logger.warning("Copernicus service failed: %s", exc)
            return CopernicusResult(available=False, error=str(exc))
