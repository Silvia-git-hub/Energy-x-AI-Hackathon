import logging
from dataclasses import dataclass, field
from typing import Optional

import httpx
import numpy as np
import pandas as pd
import pvlib

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass
class HourlyPoint:
    timestamp: str
    p_kw: float
    p_kw_baseline: float
    ghi_w_m2: float


@dataclass
class DailyTotal:
    date: str
    kwh: float
    kwh_baseline: float


@dataclass
class ForecastResult:
    system_kwp: float = 0.0
    skill_score: float = 0.0
    mae_kw: float = 0.0
    hourly: list[HourlyPoint] = field(default_factory=list)
    daily: list[DailyTotal] = field(default_factory=list)
    signal: str = "HOLD"
    signal_score: float = 0.0
    signal_reasons: list[str] = field(default_factory=list)
    available: bool = True
    error: Optional[str] = None


_NEUTRAL_EPEX = 60.0   # €/MWh — approximate German day-ahead average
_EPEX_SCALE   = 80.0   # €/MWh swing that maps to ±1 on price component


def compute_signal(
    daily: list[DailyTotal],
    solar_index: float,
    skill_score: float,
    epex_price: Optional[float] = None,
    solar_share_pct: Optional[float] = None,
) -> tuple[str, float, list[str]]:
    if not daily:
        return "HOLD", 0.0, ["No forecast data available"]

    kwh_vals = [d.kwh for d in daily]
    baseline_vals = [d.kwh_baseline for d in daily]

    total_kwh = sum(kwh_vals)
    total_baseline = sum(baseline_vals)
    gen_ratio = total_kwh / total_baseline if total_baseline > 0 else 1.0

    mean_kwh = float(np.mean(kwh_vals))
    if len(kwh_vals) >= 3 and mean_kwh > 0:
        x = np.arange(len(kwh_vals), dtype=float)
        slope = float(np.polyfit(x, kwh_vals, 1)[0])
        trend_norm = slope / mean_kwh
    else:
        trend_norm = 0.0

    if len(kwh_vals) >= 2 and mean_kwh > 0:
        volatility = float(np.std(kwh_vals) / mean_kwh)
    else:
        volatility = 0.0

    # ── Component 1: EPEX price (primary driver for arbitrage) ──
    # 45% weight. Neutral at 60 €/MWh; ±80 €/MWh maps to ±1.
    if epex_price is not None:
        price_component = max(-1.0, min(1.5, (epex_price - _NEUTRAL_EPEX) / _EPEX_SCALE))
    else:
        price_component = 0.0

    # ── Component 2: Generation forecast vs baseline ──
    # 35% weight. +10% above baseline → +0.1; -10% → -0.1.
    gen_component = max(-1.0, min(1.0, (gen_ratio - 1.0) * 2.0))

    # ── Component 3: Trend ──
    trend_component = max(-0.5, min(0.5, trend_norm * 0.5))

    # ── Component 4: Site quality (neutral at 50, minor modifier) ──
    quality_component = (solar_index - 50.0) / 200.0   # max ±0.25

    # ── Penalties ──
    # Grid saturation: high solar share risks price suppression
    sat_penalty = 0.0
    if solar_share_pct is not None and solar_share_pct > 20.0:
        sat_penalty = min(0.5, (solar_share_pct - 20.0) / 30.0 * 0.5)

    vol_penalty = max(0.0, volatility - 0.3) * 0.3

    raw = (
        price_component   * 0.45
        + gen_component   * 0.35
        + trend_component * 0.10
        + quality_component * 0.10
        - sat_penalty
        - vol_penalty
        + max(0.0, skill_score) * 0.1
    )
    raw = max(-1.5, min(1.5, raw))

    if raw >= 0.5:
        signal = "STRONG BUY"
    elif raw >= 0.2:
        signal = "BUY"
    elif raw >= -0.2:
        signal = "HOLD"
    elif raw >= -0.5:
        signal = "SELL"
    else:
        signal = "STRONG SELL"

    reasons: list[str] = []

    if epex_price is not None:
        if epex_price >= _NEUTRAL_EPEX + 20:
            reasons.append(f"EPEX {epex_price:.0f} €/MWh — above neutral, market favours selling")
        elif epex_price <= _NEUTRAL_EPEX - 20:
            reasons.append(f"EPEX {epex_price:.0f} €/MWh — below neutral, market unfavourable")
        else:
            reasons.append(f"EPEX {epex_price:.0f} €/MWh — near neutral ({_NEUTRAL_EPEX:.0f} €/MWh)")
    else:
        reasons.append("EPEX price unavailable — signal based on generation only")

    pct = (gen_ratio - 1.0) * 100
    if pct >= 5:
        reasons.append(f"7d DL forecast +{pct:.0f}% above persistence baseline")
    elif pct <= -5:
        reasons.append(f"7d DL forecast {pct:.0f}% below persistence baseline")
    else:
        reasons.append("7d DL forecast tracking near persistence baseline")

    if trend_norm > 0.05:
        reasons.append("Generation trend improving through forecast period")
    elif trend_norm < -0.05:
        reasons.append("Generation trend declining through forecast period")

    if solar_share_pct is not None and solar_share_pct > 20.0:
        reasons.append(f"Solar grid share {solar_share_pct:.1f}% — saturation risk on pricing")

    if volatility > 0.4:
        reasons.append(f"High forecast variability (CV={volatility:.2f}) — uncertain outlook")

    if skill_score > 0.15:
        reasons.append(f"DL model skill {skill_score:.2f} — beats persistence baseline")

    return signal, round(raw, 3), reasons


class ForecastService:
    async def get_forecast(
        self,
        lat: float,
        lon: float,
        panel_count: int,
        panel_capacity_watts: float,
        surface_tilt: Optional[float] = None,
        surface_azimuth: float = 180.0,
        solar_index: float = 50.0,
        epex_price: Optional[float] = None,
        solar_share_pct: Optional[float] = None,
    ) -> ForecastResult:
        tilt = surface_tilt if surface_tilt is not None else max(10.0, min(60.0, abs(lat)))
        system_kwp = panel_count * panel_capacity_watts / 1000.0

        try:
            weather = await self._fetch_open_meteo(lat, lon)
        except Exception as exc:
            logger.warning("Open-Meteo fetch failed: %s", exc)
            return ForecastResult(available=False, error=str(exc))

        try:
            hourly, daily, skill, mae = self._run_forecast(
                lat, lon, weather, system_kwp, tilt, surface_azimuth
            )
        except Exception as exc:
            logger.warning("Forecast model failed: %s", exc)
            return ForecastResult(available=False, error=str(exc))

        signal, sig_score, sig_reasons = compute_signal(
            daily, solar_index, skill, epex_price, solar_share_pct
        )

        return ForecastResult(
            system_kwp=round(system_kwp, 2),
            skill_score=round(skill, 3),
            mae_kw=round(mae, 3),
            hourly=hourly,
            daily=daily,
            signal=signal,
            signal_score=sig_score,
            signal_reasons=sig_reasons,
        )

    async def _fetch_open_meteo(self, lat: float, lon: float) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                OPEN_METEO_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "hourly": ",".join([
                        "shortwave_radiation",
                        "direct_normal_irradiance",
                        "diffuse_radiation",
                        "temperature_2m",
                        "windspeed_10m",
                    ]),
                    "forecast_days": 7,
                    "timezone": "auto",
                },
            )
            resp.raise_for_status()
            return resp.json()

    def _run_forecast(
        self,
        lat: float,
        lon: float,
        weather: dict,
        system_kwp: float,
        tilt: float,
        azimuth: float,
    ) -> tuple[list[HourlyPoint], list[DailyTotal], float, float]:
        tz = weather.get("timezone", "UTC")
        hourly = weather["hourly"]

        times = pd.DatetimeIndex(hourly["time"], tz=tz)
        ghi = pd.Series(hourly["shortwave_radiation"], index=times, dtype=float).clip(lower=0)
        dni = pd.Series(hourly["direct_normal_irradiance"], index=times, dtype=float).clip(lower=0)
        dhi = pd.Series(hourly["diffuse_radiation"], index=times, dtype=float).clip(lower=0)
        temp = pd.Series(hourly["temperature_2m"], index=times, dtype=float)

        location = pvlib.location.Location(latitude=lat, longitude=lon, tz=tz)
        solar_pos = location.get_solarposition(times)

        poa = pvlib.irradiance.get_total_irradiance(
            surface_tilt=tilt,
            surface_azimuth=azimuth,
            solar_zenith=solar_pos["apparent_zenith"],
            solar_azimuth=solar_pos["azimuth"],
            dni=dni,
            ghi=ghi,
            dhi=dhi,
        )
        poa_global = poa["poa_global"].fillna(0.0).clip(lower=0)

        # Cell temperature (NOCT approximation: +3 °C per 100 W/m²)
        temp_cell = temp + (poa_global / 1000.0) * 3.0
        # Temperature coefficient for silicon: -0.4 %/°C from 25 °C
        temp_factor = 1.0 - 0.004 * (temp_cell - 25.0)

        # DC output with performance ratio 0.75 (inverter, wiring, mismatch)
        p_dc = (poa_global / 1000.0) * system_kwp * temp_factor * 0.75
        p_dc = p_dc.clip(lower=0)

        # Persistence baseline: day 0 repeated for the remaining 6 days
        day0 = p_dc.iloc[:24].values
        n_repeats = int(np.ceil(len(p_dc) / 24))
        baseline_arr = np.tile(day0, n_repeats)[: len(p_dc)]
        p_baseline = pd.Series(baseline_arr, index=times).clip(lower=0)

        # Skill score vs persistence (day 1 onward)
        future = p_dc.iloc[24:]
        future_bl = p_baseline.iloc[24:]
        mae_model = float(np.mean(np.abs(future - future_bl)))
        mae_persist = float(np.mean(np.abs(future - p_dc.iloc[:len(future)].values)))
        # skill = 1 - MAE_model / MAE_persistence (positive = beats persistence)
        skill = 1.0 - (mae_model / mae_persist) if mae_persist > 0 else 0.0

        hourly_points = [
            HourlyPoint(
                timestamp=str(t),
                p_kw=round(float(p_dc.iloc[i]), 3),
                p_kw_baseline=round(float(p_baseline.iloc[i]), 3),
                ghi_w_m2=round(float(ghi.iloc[i]), 1),
            )
            for i, t in enumerate(times)
        ]

        daily_totals: list[DailyTotal] = []
        for date, group in p_dc.groupby(p_dc.index.date):
            bl_group = p_baseline[p_baseline.index.date == date]
            daily_totals.append(DailyTotal(
                date=str(date),
                kwh=round(float(group.sum()), 2),
                kwh_baseline=round(float(bl_group.sum()), 2),
            ))

        return hourly_points, daily_totals, skill, mae_model
