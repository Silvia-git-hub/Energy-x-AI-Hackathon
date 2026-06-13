import { useQuery } from "@tanstack/react-query";
import type { MarketDataResponse } from "@/types";
import { MOCK_MARKET_DATA } from "@/mock/data";

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";
const REFETCH_MS = 15 * 60 * 1000; // 15 min — matches backend TTL

async function fetchMarketData(): Promise<MarketDataResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 400));
    return MOCK_MARKET_DATA;
  }
  const resp = await fetch("/api/market-data");
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body?.detail ?? `HTTP ${resp.status}`);
  }
  return resp.json();
}

export function useMarketData() {
  return useQuery({
    queryKey: ["market-data"],
    queryFn: fetchMarketData,
    staleTime: REFETCH_MS,
    refetchInterval: REFETCH_MS,
    refetchOnWindowFocus: false,
  });
}
