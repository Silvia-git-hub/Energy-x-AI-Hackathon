import type { SubScoreData } from "@/types";

const SOURCE_LABELS: Record<string, string> = {
  google_solar: "GOOGLE SOLAR",
  pvgis:        "PVGIS · EU JRC",
  climate:      "CLOUD COVER",
};

const SOURCE_DESC: Record<string, string> = {
  google_solar: "Micro-shading · Roof metrics",
  pvgis:        "Solar irradiance · Long-term avg",
  climate:      "90-day cloud cover · Open-Meteo",
};

interface Props {
  sourceKey: string;
  data: SubScoreData;
  weight: number;
}

function scoreColor(score: number) {
  if (score >= 75) return "text-term-green";
  if (score >= 50) return "text-term-amber";
  if (score >= 25) return "text-term-yellow";
  return "text-term-red";
}

export default function SubScoreCard({ sourceKey, data, weight }: Props) {
  return (
    <div className="bg-term-panel border border-term-border rounded p-2 space-y-1.5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[10px] font-mono text-term-amber tracking-wider">
            {SOURCE_LABELS[sourceKey] ?? sourceKey.toUpperCase()}
          </p>
          <p className="text-[9px] font-mono text-term-dim">{SOURCE_DESC[sourceKey] ?? ""}</p>
        </div>
        <div className="flex flex-col items-end gap-0.5">
          <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${
            data.available
              ? "border-term-green text-term-green"
              : "border-term-red text-term-red"
          }`}>
            {data.available ? "LIVE" : "N/A"}
          </span>
          <span className="text-[9px] font-mono text-term-dim">{Math.round(weight * 100)}% WT</span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className={`text-xl font-mono font-bold ${scoreColor(data.score)}`}>
          {data.score.toFixed(1)}
        </span>
        <div className="flex-1 h-1.5 bg-term-border rounded-full overflow-hidden">
          <div
            className="h-full rounded-full"
            style={{ width: `${data.score}%`, background: data.score >= 75 ? "#00c853" : data.score >= 50 ? "#f57c00" : "#ffd600" }}
          />
        </div>
      </div>

      {data.available && Object.keys(data.metrics).length > 0 && (
        <div className="space-y-0.5 pt-1 border-t border-term-border">
          {Object.entries(data.metrics)
            .filter(([, v]) => v !== null && typeof v !== "object")
            .slice(0, 3)
            .map(([k, v]) => (
              <div key={k} className="flex justify-between text-[10px] font-mono">
                <span className="text-term-dim truncate mr-1">{k.replace(/_/g, " ")}</span>
                <span className="text-term-text shrink-0">
                  {typeof v === "number" ? v.toLocaleString(undefined, { maximumFractionDigits: 1 }) : String(v)}
                </span>
              </div>
            ))}
        </div>
      )}

      {!data.available && data.error && (
        <p className="text-[10px] font-mono text-term-red break-words pt-1 border-t border-term-border">{data.error}</p>
      )}
    </div>
  );
}
