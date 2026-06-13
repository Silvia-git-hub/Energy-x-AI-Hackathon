import { useQuery } from "@tanstack/react-query";
import type { MarketIntelResponse } from "@/types";

const TTL = 30 * 60 * 1000;

async function fetchMarketIntel(): Promise<MarketIntelResponse> {
  const resp = await fetch("/api/market-intel");
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

export function useMarketIntel() {
  return useQuery<MarketIntelResponse>({
    queryKey: ["market-intel"],
    queryFn: fetchMarketIntel,
    staleTime: TTL,
    refetchInterval: TTL,
    retry: 1,
  });
}
