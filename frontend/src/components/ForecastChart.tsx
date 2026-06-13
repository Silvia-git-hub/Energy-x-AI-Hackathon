import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { HourlyPoint } from "@/types";

interface Props {
  hourly: HourlyPoint[];
  systemKwp: number;
  skillScore: number;
}

function fmt(ts: string) {
  const d = new Date(ts);
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, "0")}h`;
}

function skillLabel(s: number) {
  if (s > 0.1)  return { text: `+${(s * 100).toFixed(0)}% vs persistence`, color: "text-term-green" };
  if (s > 0)    return { text: `+${(s * 100).toFixed(1)}% vs persistence`, color: "text-term-green" };
  if (s === 0)  return { text: "On par with persistence", color: "text-term-muted" };
  return { text: `${(s * 100).toFixed(1)}% vs persistence`, color: "text-term-red" };
}

export default function ForecastChart({ hourly, systemKwp, skillScore }: Props) {
  const data = hourly
    .filter((_, i) => i % 2 === 0)
    .map((h) => ({
      time: fmt(h.timestamp),
      "Forecast": h.p_kw,
      "Baseline": h.p_kw_baseline,
    }));

  const skill = skillLabel(skillScore);

  return (
    <div className="bg-term-panel border border-term-border rounded p-3">
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-[10px] font-mono text-term-muted tracking-widest">7-DAY GENERATION FORECAST</p>
          <p className="text-[9px] font-mono text-term-dim mt-0.5">{systemKwp} kWp · DL model vs persistence baseline</p>
        </div>
        <span className={`text-[10px] font-mono px-2 py-1 border border-term-border rounded ${skill.color}`}>
          {skill.text}
        </span>
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="fGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#f57c00" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#f57c00" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="bGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#444" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#444" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="2 4" stroke="#1c1c1c" />
          <XAxis dataKey="time" tick={{ fill: "#444", fontSize: 9 }} interval={11} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: "#444", fontSize: 9 }} unit="kW" axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{ background: "#0e0e0e", border: "1px solid #1c1c1c", fontSize: 11, color: "#ccc", borderRadius: 2 }}
          />
          <Legend wrapperStyle={{ fontSize: 10, color: "#555" }} />
          <Area type="monotone" dataKey="Baseline" stroke="#333" strokeWidth={1} strokeDasharray="3 3" fill="url(#bGrad)" dot={false} />
          <Area type="monotone" dataKey="Forecast" stroke="#f57c00" strokeWidth={1.5} fill="url(#fGrad)" dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
