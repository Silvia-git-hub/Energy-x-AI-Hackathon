import { useMutation } from "@tanstack/react-query";
import type { ForecastResponse } from "@/types";
import { MOCK_FORECAST_RESPONSE } from "@/mock/data";

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

interface ForecastParams {
  lat: number;
  lon: number;
  panel_count: number;
  panel_capacity_watts: number;
  surface_tilt?: number;
  solar_index?: number;
  epex_price?: number | null;
  solar_share_pct?: number | null;
}

async function fetchForecast(params: ForecastParams): Promise<ForecastResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 900));
    return MOCK_FORECAST_RESPONSE;
  }

  const resp = await fetch("/api/forecast", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body?.detail ?? `HTTP ${resp.status}`);
  }
  return resp.json();
}

export function useForecast() {
  return useMutation({
    mutationFn: (params: ForecastParams) => fetchForecast(params),
  });
}
