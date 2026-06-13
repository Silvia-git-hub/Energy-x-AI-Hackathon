import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { DailyTotal } from "@/types";

interface Props {
  daily: DailyTotal[];
}

function shortDate(iso: string): string {
  const d = new Date(iso + "T12:00:00");
  return d.toLocaleDateString(undefined, { weekday: "short", month: "numeric", day: "numeric" });
}

export default function DailyForecastBar({ daily }: Props) {
  const data = daily.map((d) => ({
    day: shortDate(d.date),
    "Forecast (kWh)": d.kwh,
    "Baseline (kWh)": d.kwh_baseline,
  }));

  const totalForecast = daily.reduce((s, d) => s + d.kwh, 0);
  const totalBaseline = daily.reduce((s, d) => s + d.kwh_baseline, 0);

  return (
    <div className="rounded-xl bg-gray-900 border border-gray-800 p-5">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-200">Daily Generation Totals</h3>
          <p className="text-xs text-gray-500 mt-0.5">Forecast vs persistence baseline</p>
        </div>
        <div className="text-right">
          <p className="text-sm font-bold text-solar-400">{totalForecast.toFixed(1)} kWh</p>
          <p className="text-xs text-gray-500">7-day total</p>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="day" tick={{ fill: "#9ca3af", fontSize: 10 }} />
          <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} unit=" kWh" />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "1px solid #374151",
              borderRadius: "8px",
              color: "#f3f4f6",
              fontSize: "12px",
            }}
          />
          <Legend wrapperStyle={{ fontSize: "12px", color: "#9ca3af" }} />
          <Bar dataKey="Baseline (kWh)" fill="#4b5563" radius={[3, 3, 0, 0]} />
          <Bar dataKey="Forecast (kWh)" fill="#f59e0b" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>

      <p className="text-xs text-gray-600 mt-2">
        Baseline = day-0 generation profile repeated. DL model forecast vs naive persistence.
      </p>
    </div>
  );
}
