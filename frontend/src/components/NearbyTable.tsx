import type { NearbyLocation, ForecastResponse } from "@/types";

interface Props {
  locations: NearbyLocation[];
  mainScore: number;
  forecast: ForecastResponse | null;
  onSelect: (lat: number, lon: number, name: string) => void;
  isLoading: boolean;
}

function signal(score: number): { label: string; color: string } {
  if (score >= 70) return { label: "BUY",  color: "text-term-green" };
  if (score >= 45) return { label: "HOLD", color: "text-term-yellow" };
  return             { label: "SELL", color: "text-term-red" };
}

function avgDailyKwh(forecast: ForecastResponse | null): number {
  if (!forecast || forecast.daily.length === 0) return 0;
  return forecast.daily.reduce((s, d) => s + d.kwh, 0) / forecast.daily.length;
}

export default function NearbyTable({ locations, mainScore, forecast, onSelect, isLoading }: Props) {
  const baseKwh = avgDailyKwh(forecast);

  return (
    <div className="bg-term-panel border border-term-border rounded">
      <div className="px-3 py-2 border-b border-term-border flex items-center justify-between">
        <span className="text-[10px] font-mono text-term-muted tracking-widest">NEARBY LOCATIONS · 1.5 KM RING</span>
        {isLoading && <span className="text-[10px] font-mono text-term-amber animate-pulse">SCANNING…</span>}
      </div>

      <table className="w-full text-[11px] font-mono">
        <thead>
          <tr className="border-b border-term-border text-term-dim text-[10px]">
            <th className="px-3 py-1.5 text-left font-normal">#</th>
            <th className="px-2 py-1.5 text-left font-normal">LOCATION</th>
            <th className="px-2 py-1.5 text-right font-normal">SCORE</th>
            <th className="px-2 py-1.5 text-right font-normal">SIG</th>
            <th className="px-2 py-1.5 text-right font-normal">EST KWH/D</th>
            <th className="px-2 py-1.5 text-right font-normal">Δ REF</th>
            <th className="px-2 py-1.5 text-center font-normal"></th>
          </tr>
        </thead>
        <tbody>
          {locations.map((loc, i) => {
            const sig = signal(loc.overall_score);
            const delta = loc.overall_score - mainScore;
            const estKwh = baseKwh > 0 ? (baseKwh * loc.overall_score / Math.max(mainScore, 1)).toFixed(1) : "—";
            return (
              <tr
                key={`${loc.lat}-${loc.lon}`}
                className="border-b border-term-border hover:bg-[#141414] transition-colors"
              >
                <td className="px-3 py-1.5 text-term-dim">{i + 1}</td>
                <td className="px-2 py-1.5 text-term-text max-w-[120px] truncate">{loc.short_name}</td>
                <td className="px-2 py-1.5 text-right text-term-amber font-bold">{loc.overall_score.toFixed(1)}</td>
                <td className={`px-2 py-1.5 text-right font-bold ${sig.color}`}>{sig.label}</td>
                <td className="px-2 py-1.5 text-right text-term-text">{estKwh}</td>
                <td className={`px-2 py-1.5 text-right ${delta > 0 ? "text-term-green" : delta < 0 ? "text-term-red" : "text-term-dim"}`}>
                  {delta > 0 ? "+" : ""}{delta.toFixed(1)}
                </td>
                <td className="px-2 py-1.5 text-center">
                  <button
                    onClick={() => onSelect(loc.lat, loc.lon, loc.short_name)}
                    className="text-[10px] px-2 py-0.5 border border-term-amber text-term-amber hover:bg-term-amber hover:text-black transition-colors rounded"
                  >
                    RUN
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
