import { useMutation } from "@tanstack/react-query";
import type { NearbyResponse } from "@/types";

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

interface NearbyParams {
  lat: number;
  lon: number;
  eumetsat_score: number;
  copernicus_score: number;
  eumetsat_available: boolean;
  copernicus_available: boolean;
}

const MOCK_CITIES: Record<string, {
  lat: number; lon: number; label: string;
  districts: { name: string; score: number; dlat: number; dlon: number }[];
}> = {
  munich: {
    lat: 48.1351, lon: 11.5820, label: "Munich",
    districts: [
      { name: "Bogenhausen",   score: 79, dlat:  0.020, dlon:  0.035 },
      { name: "Schwabing",     score: 76, dlat:  0.025, dlon:  0.005 },
      { name: "Maxvorstadt",   score: 74, dlat:  0.010, dlon: -0.005 },
      { name: "Haidhausen",    score: 71, dlat:  0.005, dlon:  0.020 },
      { name: "Neuhausen",     score: 68, dlat:  0.008, dlon: -0.025 },
      { name: "Sendling",      score: 65, dlat: -0.012, dlon: -0.010 },
      { name: "Giesing",       score: 62, dlat: -0.015, dlon:  0.018 },
      { name: "Pasing",        score: 58, dlat: -0.005, dlon: -0.055 },
    ],
  },
  berlin: {
    lat: 52.5200, lon: 13.4050, label: "Berlin",
    districts: [
      { name: "Prenzlauer Berg",  score: 72, dlat:  0.022, dlon:  0.008 },
      { name: "Mitte",            score: 70, dlat:  0.003, dlon: -0.005 },
      { name: "Friedrichshain",   score: 68, dlat:  0.000, dlon:  0.030 },
      { name: "Kreuzberg",        score: 65, dlat: -0.010, dlon:  0.010 },
      { name: "Schöneberg",       score: 63, dlat: -0.018, dlon: -0.012 },
      { name: "Charlottenburg",   score: 60, dlat:  0.010, dlon: -0.035 },
      { name: "Neukölln",         score: 56, dlat: -0.025, dlon:  0.015 },
      { name: "Spandau",          score: 52, dlat:  0.012, dlon: -0.075 },
    ],
  },
  hamburg: {
    lat: 53.5511, lon: 9.9937, label: "Hamburg",
    districts: [
      { name: "Blankenese",     score: 66, dlat:  0.005, dlon: -0.075 },
      { name: "Altona",         score: 63, dlat: -0.002, dlon: -0.022 },
      { name: "Eimsbüttel",     score: 61, dlat:  0.012, dlon: -0.010 },
      { name: "Eppendorf",      score: 59, dlat:  0.022, dlon:  0.002 },
      { name: "Barmbek",        score: 57, dlat:  0.018, dlon:  0.025 },
      { name: "Wandsbek",       score: 55, dlat:  0.008, dlon:  0.048 },
      { name: "Harburg",        score: 52, dlat: -0.030, dlon:  0.010 },
      { name: "Bergedorf",      score: 48, dlat: -0.010, dlon:  0.080 },
    ],
  },
  frankfurt: {
    lat: 50.1109, lon: 8.6821, label: "Frankfurt am Main",
    districts: [
      { name: "Sachsenhausen", score: 74, dlat: -0.010, dlon:  0.005 },
      { name: "Bornheim",      score: 68, dlat:  0.010, dlon:  0.015 },
      { name: "Nordend",       score: 65, dlat:  0.015, dlon:  0.000 },
      { name: "Westend",       score: 63, dlat:  0.005, dlon: -0.015 },
      { name: "Bockenheim",    score: 59, dlat:  0.005, dlon: -0.025 },
      { name: "Gallus",        score: 55, dlat: -0.005, dlon: -0.020 },
      { name: "Rödelheim",     score: 52, dlat:  0.012, dlon: -0.040 },
      { name: "Griesheim",     score: 48, dlat: -0.008, dlon: -0.030 },
    ],
  },
};

function detectCity(lat: number, lon: number) {
  let best = MOCK_CITIES.frankfurt;
  let bestDist = Infinity;
  for (const city of Object.values(MOCK_CITIES)) {
    const d = Math.hypot(lat - city.lat, lon - city.lon);
    if (d < bestDist) { bestDist = d; best = city; }
  }
  return best;
}

function makeMockNearby(lat: number, lon: number): NearbyResponse {
  const city = detectCity(lat, lon);
  return {
    locations: city.districts.map((d) => ({
      lat: city.lat + d.dlat,
      lon: city.lon + d.dlon,
      display_name: `${d.name}, ${city.label}, DE`,
      short_name: d.name,
      overall_score: d.score,
      google_score: d.score + 4,
      google_available: true,
      error: null,
    })),
  };
}

async function fetchNearby(params: NearbyParams): Promise<NearbyResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 1400));
    return makeMockNearby(params.lat, params.lon);
  }

  const resp = await fetch("/api/nearby", {
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

export function useNearby() {
  return useMutation({
    mutationFn: (params: NearbyParams) => fetchNearby(params),
  });
}
