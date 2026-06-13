import { useMutation } from "@tanstack/react-query";
import type { EvaluateResponse } from "@/types";
import { getMockEvaluate } from "@/mock/data";

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

async function evaluateLocation(lat: number, lon: number): Promise<EvaluateResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 1200));
    return getMockEvaluate(lat, lon);
  }

  const resp = await fetch("/api/evaluate-location", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat, lon }),
  });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body?.detail ?? `HTTP ${resp.status}`);
  }
  return resp.json();
}

export function useEvaluate() {
  return useMutation({
    mutationFn: ({ lat, lon }: { lat: number; lon: number }) =>
      evaluateLocation(lat, lon),
  });
}
