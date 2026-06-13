import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface Props {
  hours: number;
}

const REFERENCE_LOCATIONS = [
  { city: "Nairobi",  hours: 2800 },
  { city: "Madrid",   hours: 2700 },
  { city: "Rome",     hours: 2600 },
  { city: "Munich",   hours: 1740 },
  { city: "Berlin",   hours: 1625 },
];

export default function SunshineBar({ hours }: Props) {
  const data = [
    { name: "This Location", hours: Math.round(hours) },
    ...REFERENCE_LOCATIONS.map((l) => ({ name: l.city, hours: l.hours })),
  ];

  return (
    <div className="rounded-xl bg-gray-900 border border-gray-800 p-5">
      <h3 className="text-sm font-semibold text-gray-200 mb-4">
        Annual Sunshine Hours — Comparison
      </h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} />
          <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} domain={[0, 3000]} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "1px solid #374151",
              borderRadius: "8px",
              color: "#f3f4f6",
            }}
            formatter={(value: number) => [`${value} h`, "Sunshine hours"]}
          />
          <ReferenceLine y={2000} stroke="#22c55e" strokeDasharray="4 4" label={{ value: "High solar", fill: "#22c55e", fontSize: 10 }} />
          <Bar dataKey="hours" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={entry.name}
                fill={index === 0 ? "#f59e0b" : "#4b5563"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
