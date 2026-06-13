import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

DSSR_COLLECTION_ID = "EO:EUM:DAT:0863"

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


@dataclass
class EumdacResult:
    seasonal_irradiance_w_m2: dict[str, float] = field(default_factory=dict)
    annual_avg_irradiance_w_m2: float = 0.0
    monthly_irradiance: list[float] = field(default_factory=list)
    month_labels: list[str] = field(default_factory=lambda: MONTH_LABELS.copy())
    available: bool = True
    error: Optional[str] = None


class EumdacService:
    def __init__(self, consumer_key: str, consumer_secret: str) -> None:
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret

    def get_solar_irradiance_sync(self, lat: float, lon: float) -> EumdacResult:
        """Synchronous — call via asyncio.to_thread()."""
        try:
            import eumdac
            import xarray as xr
            import numpy as np
            import tempfile
            import os

            token = eumdac.AccessToken(credentials=(self._consumer_key, self._consumer_secret))
            store = eumdac.DataStore(token)
            collection = store.get_collection(DSSR_COLLECTION_ID)

            end = datetime.utcnow()
            start = end - timedelta(days=365)

            products = list(
                collection.search(
                    dtstart=start,
                    dtend=end,
                    bbox=(lon - 0.5, lat - 0.5, lon + 0.5, lat + 0.5),
                )
            )

            if not products:
                return EumdacResult(available=False, error="No EUMETSAT products found for this location.")

            monthly_sums: dict[int, list[float]] = {m: [] for m in range(1, 13)}

            with tempfile.TemporaryDirectory() as tmpdir:
                for product in products[:24]:
                    try:
                        with product.open() as fsrc:
                            fname = os.path.join(tmpdir, fsrc.name)
                            with open(fname, "wb") as fdst:
                                fdst.write(fsrc.read())

                        ds = xr.open_dataset(fname)
                        sis_var = next(
                            (v for v in ["SIS", "sis", "DSSR", "dssr", "SIS_daily"] if v in ds),
                            None,
                        )
                        if sis_var is None:
                            ds.close()
                            continue

                        da = ds[sis_var]
                        time_dim = next((d for d in da.dims if "time" in d.lower()), None)
                        if time_dim:
                            for t in da[time_dim].values:
                                month = int(str(t)[:7].split("-")[1])
                                point = da.sel({time_dim: t}).sel(
                                    lat=lat, lon=lon, method="nearest", tolerance=1.0
                                )
                                val = float(np.nanmean(point.values))
                                if not np.isnan(val):
                                    monthly_sums[month].append(val)
                        ds.close()
                    except Exception as exc:
                        logger.debug("Skipping EUMETSAT product: %s", exc)
                        continue

            monthly_means = [
                float(np.mean(monthly_sums[m])) if monthly_sums[m] else 0.0
                for m in range(1, 13)
            ]

            annual_avg = float(np.mean([v for v in monthly_means if v > 0]) or 0.0)

            def _season(months: list[int]) -> float:
                vals = [monthly_means[m - 1] for m in months if monthly_means[m - 1] > 0]
                return float(np.mean(vals)) if vals else 0.0

            seasonal = {
                "DJF": _season([12, 1, 2]),
                "MAM": _season([3, 4, 5]),
                "JJA": _season([6, 7, 8]),
                "SON": _season([9, 10, 11]),
            }

            return EumdacResult(
                seasonal_irradiance_w_m2=seasonal,
                annual_avg_irradiance_w_m2=annual_avg,
                monthly_irradiance=monthly_means,
            )

        except Exception as exc:
            logger.warning("EUMETSAT service failed: %s", exc)
            return EumdacResult(available=False, error=str(exc))
