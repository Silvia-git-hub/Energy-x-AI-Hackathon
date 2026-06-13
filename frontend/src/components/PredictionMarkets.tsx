import { useMarketIntel } from "@/hooks/useMarketIntel";

function pctColor(p: number) {
  if (p >= 70) return "text-term-green";
  if (p >= 45) return "text-term-yellow";
  return "text-term-red";
}

function pctBarColor(p: number) {
  if (p >= 70) return "#00c853";
  if (p >= 45) return "#ffd600";
  return "#ff1744";
}

export default function PredictionMarkets() {
  const { data, isLoading, isError } = useMarketIntel();
  const markets = data?.markets ?? [];
  const yesPct = (p: number) => Math.round(p * 100);

  return (
    <div className="bg-term-panel border border-term-border rounded p-3 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-mono text-term-muted tracking-widest">PREDICTION MARKETS</span>
        <span className="text-[10px] font-mono text-term-amber">MANIFOLD</span>
      </div>

      {isLoading && (
        <div className="text-[10px] font-mono text-term-dim animate-pulse py-1">
          ▶ Fetching markets…
        </div>
      )}

      {(isError || data?.available === false) && (
        <div className="text-[10px] font-mono text-term-red py-1">
          {data?.error ?? "Markets unavailable — check GROQ_API_KEY"}
        </div>
      )}

      {markets.length > 0 && (
        <div className="space-y-3">
          {markets.map((m, i) => {
            const pct = yesPct(m.probability);
            return (
              <div key={i} className="space-y-1">
                <div className="flex items-start justify-between gap-2">
                  <a
                    href={m.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[11px] text-term-text leading-snug flex-1 hover:text-term-amber"
                  >
                    {m.question}
                  </a>
                  <span className={`text-sm font-mono font-bold shrink-0 ${pctColor(pct)}`}>
                    {pct}%
                  </span>
                </div>

                <div className="h-1.5 bg-term-border rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{ width: `${pct}%`, background: pctBarColor(pct) }}
                  />
                </div>

                <div className="flex justify-between text-[9px] font-mono text-term-dim">
                  <span>YES {pct}% · NO {100 - pct}%</span>
                  <span>MANIFOLD MARKETS</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {!isLoading && !isError && markets.length === 0 && data?.available && (
        <div className="text-[10px] font-mono text-term-dim py-1">No relevant markets found</div>
      )}
    </div>
  );
}
