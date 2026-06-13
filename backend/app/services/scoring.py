from dataclasses import dataclass, field
from typing import Optional

from app.services.google_solar import GoogleSolarResult
from app.services.pvgis import PvgisResult
from app.services.open_meteo_climate import ClimateResult

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

NOMINAL_WEIGHTS = {
    "google_solar": 0.50,
    "pvgis":        0.30,
    "climate":      0.20,
}


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _normalize_google(result: GoogleSolarResult) -> float:
    sunshine_score = _clamp((result.max_sunshine_hours_per_year - 800) / (2800 - 800) * 100)
    energy_score = _clamp(result.estimated_annual_dc_kwh / 30_000 * 100)
    return 0.7 * sunshine_score + 0.3 * energy_score


def _normalize_pvgis(result: PvgisResult) -> float:
    # H(h) annual mean [Wh/m²/day]; calibrated for Central Europe
    # 2000 Wh/m²/day ≈ score 0 (poor northern EU), 4000 ≈ score 100 (Alpine/Med)
    return _clamp((result.annual_mean_hh_wh_per_day - 2000) / (4000 - 2000) * 100)


def _normalize_climate(result: ClimateResult) -> float:
    return _clamp(100.0 - result.avg_cloud_cover_pct)


@dataclass
class SubScore:
    score: float
    raw_metrics: dict
    available: bool
    error: Optional[str] = None


@dataclass
class SolarScore:
    overall: float
    google_solar: SubScore
    pvgis: SubScore
    climate: SubScore
    weights_used: dict[str, float]
    chart_data: dict
    data_warning: Optional[str] = None


def compute_overall_score(
    google: GoogleSolarResult,
    pvgis: PvgisResult,
    climate: ClimateResult,
) -> SolarScore:
    google_score = SubScore(
        score=round(_normalize_google(google), 1) if google.available else 0.0,
        available=google.available,
        error=google.error,
        raw_metrics={
            "sunshine hrs / yr": int(google.max_sunshine_hours_per_year),
            "annual yield kWh": round(google.estimated_annual_dc_kwh, 1),
            "panel count": google.panel_count,
            "panel capacity W": int(google.panel_capacity_watts),
        } if google.available else {},
    )

    pvgis_score = SubScore(
        score=round(_normalize_pvgis(pvgis), 1) if pvgis.available else 0.0,
        available=pvgis.available,
        error=pvgis.error,
        raw_metrics={
            "annual mean Wh/m²/day": pvgis.annual_mean_hh_wh_per_day,
        } if pvgis.available else {},
    )

    climate_score = SubScore(
        score=round(_normalize_climate(climate), 1) if climate.available else 0.0,
        available=climate.available,
        error=climate.error,
        raw_metrics={
            "avg cloud cover %": climate.avg_cloud_cover_pct,
            "sample days": climate.sample_days,
        } if climate.available else {},
    )

    available_sources = {
        k: v for k, v in {
            "google_solar": google.available,
            "pvgis":        pvgis.available,
            "climate":      climate.available,
        }.items() if v
    }

    if not available_sources:
        return SolarScore(
            overall=0.0,
            google_solar=google_score,
            pvgis=pvgis_score,
            climate=climate_score,
            weights_used={k: 0.0 for k in NOMINAL_WEIGHTS},
            chart_data=_build_chart_data(google, pvgis, climate),
            data_warning="No data sources available — score cannot be calculated.",
        )

    total_nominal = sum(NOMINAL_WEIGHTS[src] for src in available_sources)
    effective_weights = {
        src: (NOMINAL_WEIGHTS[src] / total_nominal if src in available_sources else 0.0)
        for src in NOMINAL_WEIGHTS
    }

    score_map = {
        "google_solar": google_score.score,
        "pvgis":        pvgis_score.score,
        "climate":      climate_score.score,
    }
    overall = sum(effective_weights[src] * score_map[src] for src in available_sources)

    return SolarScore(
        overall=round(overall, 1),
        google_solar=google_score,
        pvgis=pvgis_score,
        climate=climate_score,
        weights_used={k: round(v, 4) for k, v in effective_weights.items()},
        chart_data=_build_chart_data(google, pvgis, climate),
    )


def _build_chart_data(
    google: GoogleSolarResult,
    pvgis: PvgisResult,
    climate: ClimateResult,
) -> dict:
    # Convert PVGIS H(h) [Wh/m²/day] → average W/m² for chart display
    monthly_irradiance = (
        [round(h / 24.0, 1) for h in pvgis.monthly_hh]
        if pvgis.available else None
    )
    return {
        "sunshine_hours_annual": google.max_sunshine_hours_per_year if google.available else None,
        "monthly_irradiance": monthly_irradiance,
        "monthly_labels": pvgis.month_labels if pvgis.available else MONTH_LABELS,
        "seasonal_irradiance": None,
        "avg_cloud_cover_pct": climate.avg_cloud_cover_pct if climate.available else None,
    }
