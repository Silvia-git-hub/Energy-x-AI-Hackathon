import type { MarketDataResponse } from "@/types";

interface Item {
  label: string;
  value: string;
  unit?: string;
  dir?: "up" | "down" | "flat";
}

function dirIcon(dir?: "up" | "down" | "flat") {
  if (dir === "up")   return <span className="text-term-green">▲</span>;
  if (dir === "down") return <span className="text-term-red">▼</span>;
  return <span className="text-term-muted">–</span>;
}

function fmt(v: number | null | undefined, decimals = 2): string {
  return v != null ? v.toFixed(decimals) : "—";
}

interface Props {
  solarScore?:  number;
  signal?:      string;
  marketData?:  MarketDataResponse;
}

export default function TickerBar({ solarScore, signal, marketData }: Props) {
  const md = marketData;

  const epexPrice   = md?.epex_current_price;
  const epexHigh    = md?.epex_day_high;
  const epexLow     = md?.epex_day_low;
  const solarMwh    = md?.grid.solar_mwh;
  const windMwh     = md?.grid.wind_mwh;
  const loadMwh     = md?.grid.load_mwh;
  const solarShare  = md?.grid.solar_share_pct;
  const windShare   = md?.grid.wind_share_pct;

  const items: Item[] = [
    {
      label: "EPEX DA",
      value: fmt(epexPrice),
      unit: "€/MWh",
      dir: epexPrice != null
        ? epexPrice > 80 ? "up" : epexPrice < 50 ? "down" : "flat"
        : "flat",
    },
    epexHigh != null && epexLow != null
      ? { label: "DA H/L", value: `${epexHigh.toFixed(0)} / ${epexLow.toFixed(0)}`, unit: "€/MWh", dir: "flat" }
      : { label: "DA H/L", value: "— / —", unit: "€/MWh", dir: "flat" },
    {
      label: "DE SOLAR",
      value: solarMwh != null ? (solarMwh / 1000).toFixed(2) : "—",
      unit: "GWh",
      dir: solarShare != null ? (solarShare > 20 ? "up" : solarShare < 5 ? "down" : "flat") : "flat",
    },
    {
      label: "DE WIND",
      value: windMwh != null ? (windMwh / 1000).toFixed(2) : "—",
      unit: "GWh",
      dir: windShare != null ? (windShare > 30 ? "up" : "flat") : "flat",
    },
    {
      label: "DE LOAD",
      value: loadMwh != null ? (loadMwh / 1000).toFixed(1) : "—",
      unit: "GW",
      dir: "flat",
    },
    {
      label: "SOLAR SHARE",
      value: fmt(solarShare, 1),
      unit: "%",
      dir: solarShare != null ? (solarShare > 20 ? "up" : solarShare < 5 ? "down" : "flat") : "flat",
    },
    {
      label: "WIND SHARE",
      value: fmt(windShare, 1),
      unit: "%",
      dir: windShare != null ? (windShare > 30 ? "up" : "flat") : "flat",
    },
    { label: "FEED-IN TARIFF", value: "8.20", unit: "ct/kWh", dir: "flat" },
  ];

  if (solarScore !== undefined)
    items.push({ label: "SOLAR IDX", value: solarScore.toFixed(1), unit: "/100", dir: solarScore >= 60 ? "up" : "down" });
  if (signal)
    items.push({
      label: "SIGNAL",
      value: signal,
      dir: signal === "BUY" || signal === "STRONG BUY" ? "up"
         : signal === "SELL" || signal === "STRONG SELL" ? "down"
         : "flat",
    });

  const doubled = [...items, ...items];

  return (
    <div className="shrink-0 bg-term-panel border-b border-term-border h-7 flex items-center overflow-hidden">
      <div className="shrink-0 px-3 h-full flex items-center border-r border-term-border text-term-amber text-[10px] font-mono font-bold tracking-widest">
        {md ? "LIVE" : "—"}
      </div>
      <div className="flex-1 overflow-hidden">
        <div className="flex animate-ticker">
          {doubled.map((item, i) => (
            <span key={i} className="inline-flex items-center gap-1 px-3 text-[11px] font-mono whitespace-nowrap">
              <span className="text-term-muted">{item.label}</span>
              {dirIcon(item.dir)}
              <span className={
                item.dir === "up"   ? "text-term-green" :
                item.dir === "down" ? "text-term-red"   : "text-term-text"
              }>
                {item.value}
              </span>
              {item.unit && <span className="text-term-dim text-[10px]">{item.unit}</span>}
              <span className="text-term-border pl-2">│</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
