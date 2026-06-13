import logging
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

PVGIS_URL = "https://re.jrc.ec.europa.eu/api/v5_2/MRcalc"
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


@dataclass
class PvgisResult:
    # H(h): monthly mean of daily sum of global irradiation [Wh/m²/day]
    annual_mean_hh_wh_per_day: float = 0.0
    monthly_hh: list[float] = field(default_factory=list)
    month_labels: list[str] = field(default_factory=lambda: MONTH_LABELS.copy())
    available: bool = True
    error: Optional[str] = None


class PvgisService:
    async def get_irradiance(self, lat: float, lon: float) -> PvgisResult:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(
                    PVGIS_URL,
                    params={"lat": lat, "lon": lon, "outputformat": "json"},
                )
                resp.raise_for_status()
                data = resp.json()

            monthly = data["outputs"]["monthly"]["fixed"]
            hh_values = [float(m["H(h)"]) for m in monthly]
            annual_mean = sum(hh_values) / len(hh_values)

            return PvgisResult(
                annual_mean_hh_wh_per_day=round(annual_mean, 1),
                monthly_hh=[round(v, 1) for v in hh_values],
            )

        except httpx.HTTPStatusError as exc:
            msg = f"PVGIS HTTP {exc.response.status_code}"
            logger.warning("PVGIS error: %s", msg)
            return PvgisResult(available=False, error=msg)
        except Exception as exc:
            logger.warning("PVGIS service failed: %s", exc)
            return PvgisResult(available=False, error=str(exc))
