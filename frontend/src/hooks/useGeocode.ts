import { useMutation } from "@tanstack/react-query";
import type { GeocodeResponse } from "@/types";

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

const MOCK_GEOCODE_DB: Record<string, GeocodeResponse> = {
  munich:    { lat: 48.1351, lon: 11.5820, display_name: "München, Bayern, Deutschland",           short_name: "Munich, DE",    available: true },
  münchen:   { lat: 48.1351, lon: 11.5820, display_name: "München, Bayern, Deutschland",           short_name: "Munich, DE",    available: true },
  berlin:    { lat: 52.5200, lon: 13.4050, display_name: "Berlin, Deutschland",                    short_name: "Berlin, DE",    available: true },
  hamburg:   { lat: 53.5511, lon:  9.9937, display_name: "Hamburg, Deutschland",                   short_name: "Hamburg, DE",   available: true },
  frankfurt: { lat: 50.1109, lon:  8.6821, display_name: "Frankfurt am Main, Hessen, Deutschland", short_name: "Frankfurt, DE", available: true },
};

async function geocodeAddress(address: string): Promise<GeocodeResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 600));
    const key = address.trim().toLowerCase().split(/[,\s]/)[0];
    return MOCK_GEOCODE_DB[key] ?? MOCK_GEOCODE_DB.frankfurt;
  }

  const resp = await fetch("/api/geocode", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ address }),
  });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body?.detail ?? `HTTP ${resp.status}`);
  }
  const data: GeocodeResponse = await resp.json();
  if (!data.available) throw new Error(data.error ?? "Location not found");
  return data;
}

export function useGeocode() {
  return useMutation({
    mutationFn: (address: string) => geocodeAddress(address),
  });
}
