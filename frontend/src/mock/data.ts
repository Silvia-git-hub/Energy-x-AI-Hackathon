import type { EvaluateResponse, ForecastResponse, MarketDataResponse } from "@/types";

const CITY_MOCK_DATA: Record<string, EvaluateResponse> = {
  munich: {
    lat: 48.1351, lon: 11.5820,
    overall_score: 73.2,
    sub_scores: {
      google_solar: { score: 81.0, available: true, error: null, metrics: { max_sunshine_hours_per_year: 1840, estimated_annual_dc_kwh: 16400, panel_count: 24, panel_capacity_watts: 400, carbon_offset_factor_kg_per_kwh: 0.38 } },
      pvgis:        { score: 75.0, available: true, error: null, metrics: { "annual mean Wh/m²/day": 3520 } },
      climate:      { score: 61.0, available: true, error: null, metrics: { "avg cloud cover %": 39.0, "sample days": 85 } },
    },
    weights_used: { google_solar: 0.5, pvgis: 0.3, climate: 0.2 },
    chart_data: { sunshine_hours_annual: 1840, monthly_irradiance: [55, 85, 140, 185, 225, 265, 295, 270, 195, 135, 70, 48], monthly_labels: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], seasonal_irradiance: { DJF: 72, MAM: 195, JJA: 335, SON: 162 }, avg_cloud_cover_pct: 39.0 },
  },
  berlin: {
    lat: 52.5200, lon: 13.4050,
    overall_score: 64.8,
    sub_scores: {
      google_solar: { score: 74.0, available: true, error: null, metrics: { max_sunshine_hours_per_year: 1710, estimated_annual_dc_kwh: 14800, panel_count: 24, panel_capacity_watts: 400, carbon_offset_factor_kg_per_kwh: 0.40 } },
      pvgis:        { score: 55.0, available: true, error: null, metrics: { "annual mean Wh/m²/day": 3100 } },
      climate:      { score: 55.0, available: true, error: null, metrics: { "avg cloud cover %": 45.0, "sample days": 85 } },
    },
    weights_used: { google_solar: 0.5, pvgis: 0.3, climate: 0.2 },
    chart_data: { sunshine_hours_annual: 1710, monthly_irradiance: [45, 75, 120, 165, 205, 235, 250, 225, 170, 110, 55, 38], monthly_labels: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], seasonal_irradiance: { DJF: 55, MAM: 178, JJA: 295, SON: 140 }, avg_cloud_cover_pct: 45.0 },
  },
  hamburg: {
    lat: 53.5511, lon: 9.9937,
    overall_score: 55.1,
    sub_scores: {
      google_solar: { score: 63.0, available: true, error: null, metrics: { max_sunshine_hours_per_year: 1590, estimated_annual_dc_kwh: 13100, panel_count: 24, panel_capacity_watts: 400, carbon_offset_factor_kg_per_kwh: 0.42 } },
      pvgis:        { score: 25.0, available: true, error: null, metrics: { "annual mean Wh/m²/day": 2500 } },
      climate:      { score: 44.0, available: true, error: null, metrics: { "avg cloud cover %": 56.0, "sample days": 85 } },
    },
    weights_used: { google_solar: 0.5, pvgis: 0.3, climate: 0.2 },
    chart_data: { sunshine_hours_annual: 1590, monthly_irradiance: [38, 65, 108, 155, 190, 215, 225, 200, 152, 98, 48, 32], monthly_labels: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], seasonal_irradiance: { DJF: 48, MAM: 158, JJA: 265, SON: 118 }, avg_cloud_cover_pct: 56.0 },
  },
  frankfurt: {
    lat: 50.1109, lon: 8.6821,
    overall_score: 61.4,
    sub_scores: {
      google_solar: { score: 72.5, available: true, error: null, metrics: { max_sunshine_hours_per_year: 1660, estimated_annual_dc_kwh: 14200, panel_count: 24, panel_capacity_watts: 400, carbon_offset_factor_kg_per_kwh: 0.41 } },
      pvgis:        { score: 55.0, available: true, error: null, metrics: { "annual mean Wh/m²/day": 3100 } },
      climate:      { score: 52.0, available: true, error: null, metrics: { "avg cloud cover %": 48.0, "sample days": 85 } },
    },
    weights_used: { google_solar: 0.5, pvgis: 0.3, climate: 0.2 },
    chart_data: { sunshine_hours_annual: 1660, monthly_irradiance: [65, 90, 130, 165, 200, 225, 235, 215, 170, 125, 75, 55], monthly_labels: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], seasonal_irradiance: { DJF: 80, MAM: 165, JJA: 225, SON: 123 }, avg_cloud_cover_pct: 48.0 },
  },
};

function detectCityMock(lat: number, lon: number): EvaluateResponse {
  const cities = Object.values(CITY_MOCK_DATA);
  return cities.reduce((best, c) =>
    Math.hypot(lat - c.lat, lon - c.lon) < Math.hypot(lat - best.lat, lon - best.lon) ? c : best
  );
}

export const MOCK_EVALUATE_RESPONSE = CITY_MOCK_DATA.frankfurt;
export function getMockEvaluate(lat: number, lon: number): EvaluateResponse {
  return detectCityMock(lat, lon);
}

function makeMockHourly(): ForecastResponse["hourly"] {
  const points = [];
  const now = new Date();
  now.setMinutes(0, 0, 0);
  // Bell-curve generation profile: peaks ~13:00
  const profile = [0,0,0,0,0,0.02,0.08,0.22,0.45,0.68,0.85,0.95,1.0,0.95,0.85,0.68,0.45,0.22,0.08,0.02,0,0,0,0];
  const systemKwp = 9.6;
  for (let day = 0; day < 7; day++) {
    const variance = 0.8 + Math.random() * 0.4;
    for (let h = 0; h < 24; h++) {
      const ts = new Date(now.getTime() + (day * 24 + h) * 3600_000);
      const gen = profile[h] * systemKwp * variance;
      const baseline = profile[h] * systemKwp * 0.9;
      points.push({
        timestamp: ts.toISOString(),
        p_kw: Math.round(gen * 100) / 100,
        p_kw_baseline: Math.round(baseline * 100) / 100,
        ghi_w_m2: Math.round(profile[h] * 850),
      });
    }
  }
  return points;
}

function makeMockDaily(): ForecastResponse["daily"] {
  const now = new Date();
  const days = [];
  for (let d = 0; d < 7; d++) {
    const date = new Date(now.getTime() + d * 86_400_000);
    const kwh = 28 + Math.random() * 10;
    days.push({
      date: date.toISOString().slice(0, 10),
      kwh: Math.round(kwh * 10) / 10,
      kwh_baseline: Math.round(28 * 10) / 10,
    });
  }
  return days;
}

export const MOCK_FORECAST_RESPONSE: ForecastResponse = {
  system_kwp: 9.6,
  skill_score: 0.12,
  mae_kw: 0.38,
  signal: "BUY",
  signal_score: 0.41,
  signal_reasons: [
    "7d forecast +8% above persistence baseline",
    "Generation trend improving through forecast period",
    "Strong solar index (61/100) underpins production",
    "Model skill 0.12 — forecast reliable vs persistence",
  ],
  available: true,
  error: null,
  hourly: makeMockHourly(),
  daily: makeMockDaily(),
};

const _mockPrices = [
  47, 45, 43, 41, 40, 44, 58, 74, 82, 78, 71, 63,
  55, 53, 57, 65, 72, 86, 91, 84, 73, 64, 57, 50,
];
export const MOCK_MARKET_DATA: MarketDataResponse = {
  epex_current_price: _mockPrices[new Date().getHours()],
  epex_day_high: 91,
  epex_day_low: 40,
  epex_prices: _mockPrices.map((p, i) => ({
    hour: `${String(i).padStart(2, "0")}:00`,
    price_eur_mwh: p,
  })),
  grid: {
    solar_mwh:       4821.5,
    wind_mwh:        9340.0,
    load_mwh:        58200.0,
    solar_share_pct: 8.3,
    wind_share_pct:  16.0,
  },
  updated_at: new Date().toISOString(),
  available: true,
  error: null,
};

export const MOCK_CHAT_RESPONSE = `Based on the assessment data for Frankfurt (50.11°N, 8.68°E), here's my analysis:

**Solar Potential: Moderate (Score 61/100)**

Frankfurt receives approximately 1,660 sunshine hours per year — below the optimal threshold of 2,000+ hours but workable for a solid ROI. EUMETSAT irradiance shows strong seasonality: peak generation in June–August (~225 W/m²) drops in winter (55–65 W/m²), typical for Central European climates.

**ROI Estimate**
With 24 panels × 400W, your system could yield ~14,200 kWh/year. At German residential rates (~€0.31/kWh), that represents **~€4,400/year in avoided grid costs**. A 9.6 kWp system costs ~€14,000–17,000 installed, giving a **payback period of 3.2–3.9 years** before considering EEG feed-in tariffs.

**Key Constraint**
The 48% average cloud cover is the main drag on your score. Battery storage can smooth seasonal variance and maximise self-consumption during summer surplus periods.`;
