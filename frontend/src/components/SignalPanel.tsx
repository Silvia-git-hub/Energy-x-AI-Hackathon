import type { ForecastResponse } from "@/types";

type Signal = "STRONG BUY" | "BUY" | "HOLD" | "SELL" | "STRONG SELL";

const SIGNAL_STYLES: Record<Signal, { border: string; text: string; dim: string }> = {
  "STRONG BUY":  { border: "border-term-green",  text: "text-term-green",  dim: "text-green-700" },
  "BUY":         { border: "border-term-green",  text: "text-term-green",  dim: "text-green-700" },
  "HOLD":        { border: "border-term-yellow", text: "text-term-yellow", dim: "text-yellow-700" },
  "SELL":        { border: "border-term-red",    text: "text-term-red",    dim: "text-red-700" },
  "STRONG SELL": { border: "border-term-red",    text: "text-term-red",    dim: "text-red-700" },
};

const DEFAULT_STYLE = SIGNAL_STYLES["HOLD"];

interface Props {
  score: number;
  forecast: ForecastResponse | null;
}

export default function SignalPanel({ score, forecast }: Props) {
  const signal = (forecast?.signal ?? "HOLD") as Signal;
  const s = SIGNAL_STYLES[signal] ?? DEFAULT_STYLE;
  const total7d = forecast?.daily.reduce((acc, d) => acc + d.kwh, 0) ?? null;

  return (
    <div className={`border ${s.border} rounded p-3 bg-term-panel space-y-2`}>
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-mono text-term-muted tracking-widest">SIGNAL</span>
        <span className="text-[10px] font-mono text-term-dim">7D OUTLOOK</span>
      </div>

      <div className={`text-2xl font-mono font-bold tracking-wide ${s.text}`}>{signal}</div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-1 pt-1 border-t border-term-border">
        <Metric label="Solar Index"  value={`${score.toFixed(1)} / 100`} />
        <Metric label="7d Est."      value={total7d != null ? `${total7d.toFixed(0)} kWh` : "—"} />
        <Metric label="Sys. Size"    value={forecast ? `${forecast.system_kwp} kWp` : "—"} />
        <Metric label="Skill"        value={forecast ? `${(forecast.skill_score * 100).toFixed(0)}%` : "—"} />
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-[10px] font-mono">
      <span className="text-term-dim">{label}</span>
      <span className="text-term-text">{value}</span>
    </div>
  );
}

export type { Signal };
