import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { MarketDataResponse } from "@/types";

interface Props {
  marketData?: MarketDataResponse;
}

const CURRENT_HOUR = new Date().getHours();

function priceColor(price: number, high: number, low: number): string {
  if (price >= high * 0.9) return "#ff1744";
  if (price <= low  * 1.1) return "#00c853";
  return "#333333";
}

export default function MarketPricePanel({ marketData }: Props) {
  const md = marketData;
  const prices = md?.epex_prices ?? [];

  const currentPrice = md?.epex_current_price;
  const dayHigh      = md?.epex_day_high;
  const dayLow       = md?.epex_day_low;

  const data = prices.map((p, i) => ({
    h:       p.hour,
    price:   p.price_eur_mwh,
    current: i === CURRENT_HOUR,
  }));

  const solarShare = md?.grid.solar_share_pct;
  const windShare  = md?.grid.wind_share_pct;
  const renewShare = solarShare != null && windShare != null
    ? (solarShare + windShare).toFixed(1)
    : "—";

  const stats = [
    { label: "FEED-IN TARIFF", value: "8.20 ct/kWh" },
    { label: "MARKET PREMIUM", value: "4.15 ct/kWh" },
    { label: "SOLAR SHARE",    value: solarShare != null ? `${solarShare.toFixed(1)} %` : "—" },
    { label: "WIND SHARE",     value: windShare  != null ? `${windShare.toFixed(1)} %`  : "—" },
  ];

  return (
    <div className="bg-term-panel border border-term-border rounded p-3 space-y-3">
      <div className="flex items-baseline justify-between">
        <span className="text-[10px] font-mono text-term-muted tracking-widest">EPEX SPOT · DAY-AHEAD</span>
        <span className="text-[10px] font-mono text-term-dim">
          {md?.updated_at ? new Date(md.updated_at).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" }) + " UTC" : "DE-LU"}
        </span>
      </div>

      <div className="flex items-end gap-3">
        <span className="text-3xl font-mono font-bold text-term-amber">
          {currentPrice != null ? currentPrice.toFixed(2) : "—"}
        </span>
        <span className="text-sm font-mono text-term-muted mb-1">€/MWh</span>
        {dayHigh != null && dayLow != null && (
          <span className="text-xs font-mono text-term-green mb-1 ml-auto">
            H {dayHigh} · L {dayLow}
          </span>
        )}
      </div>

      {data.length > 0 ? (
        <ResponsiveContainer width="100%" height={72}>
          <BarChart data={data} margin={{ top: 0, right: 0, left: -30, bottom: 0 }}>
            <XAxis
              dataKey="h"
              tick={{ fill: "#444", fontSize: 8 }}
              interval={5}
              axisLine={false}
              tickLine={false}
            />
            <YAxis hide domain={["auto", "auto"]} />
            <Tooltip
              contentStyle={{ background: "#111", border: "1px solid #1c1c1c", fontSize: 10, color: "#ccc" }}
              formatter={(v: number) => [`${v.toFixed(2)} €/MWh`, "Price"]}
              labelFormatter={(l) => `Hour ${l}`}
            />
            <Bar dataKey="price" radius={[1, 1, 0, 0]}>
              {data.map((entry, i) => (
                <Cell
                  key={i}
                  fill={
                    entry.current
                      ? "#f57c00"
                      : dayHigh != null && dayLow != null
                      ? priceColor(entry.price, dayHigh, dayLow)
                      : "#333333"
                  }
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <div className="h-[72px] flex items-center justify-center text-[10px] font-mono text-term-dim">
          {md?.available === false ? "EPEX DATA UNAVAILABLE" : "LOADING…"}
        </div>
      )}

      <div className="grid grid-cols-2 gap-x-4 gap-y-1 pt-1 border-t border-term-border">
        {stats.map((s) => (
          <div key={s.label} className="flex justify-between text-[10px] font-mono">
            <span className="text-term-dim">{s.label}</span>
            <span className="text-term-text">{s.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
