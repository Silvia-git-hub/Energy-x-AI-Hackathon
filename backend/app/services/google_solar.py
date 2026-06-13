import logging
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

BUILDING_INSIGHTS_URL = "https://solar.googleapis.com/v1/buildingInsights:findClosest"


@dataclass
class GoogleSolarResult:
    max_sunshine_hours_per_year: float = 0.0
    carbon_offset_factor_kg_per_kwh: float = 0.0
    estimated_annual_dc_kwh: float = 0.0
    panel_count: int = 0
    panel_capacity_watts: float = 0.0
    raw_panel_configs: list = field(default_factory=list)
    available: bool = True
    error: Optional[str] = None


class GoogleSolarService:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def get_building_insights(self, lat: float, lon: float) -> GoogleSolarResult:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    BUILDING_INSIGHTS_URL,
                    params={
                        "location.latitude": lat,
                        "location.longitude": lon,
                        "requiredQuality": "LOW",
                        "key": self._api_key,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            solar = data.get("solarPotential", {})
            sunshine_hours = float(solar.get("maxSunshineHoursPerYear", 0))
            carbon_offset = float(solar.get("carbonOffsetFactorKgPerMwh", 0)) / 1000.0
            panel_configs = solar.get("solarPanelConfigs", [])
            panel_capacity_w = float(solar.get("panelCapacityWatts", 400))

            best_config = max(panel_configs, key=lambda c: c.get("panelsCount", 0), default={})
            panel_count = int(best_config.get("panelsCount", 0))

            estimated_dc_kwh = panel_count * (panel_capacity_w / 1000.0) * sunshine_hours

            return GoogleSolarResult(
                max_sunshine_hours_per_year=sunshine_hours,
                carbon_offset_factor_kg_per_kwh=carbon_offset,
                estimated_annual_dc_kwh=estimated_dc_kwh,
                panel_count=panel_count,
                panel_capacity_watts=panel_capacity_w,
                raw_panel_configs=panel_configs[:5],
            )

        except httpx.HTTPStatusError as exc:
            msg = f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"
            logger.warning("Google Solar API error: %s", msg)
            return GoogleSolarResult(available=False, error=msg)
        except Exception as exc:
            logger.warning("Google Solar service failed: %s", exc)
            return GoogleSolarResult(available=False, error=str(exc))
