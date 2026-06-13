import type { NearbyLocation } from "@/types";

interface Props {
  locations: NearbyLocation[];
  mainScore: number;
  onSelect: (lat: number, lon: number, name: string) => void;
  isLoading: boolean;
}

function scoreColor(score: number): string {
  if (score >= 75) return "bg-green-500";
  if (score >= 50) return "bg-amber-500";
  if (score >= 25) return "bg-orange-500";
  return "bg-red-500";
}

function deltaLabel(delta: number): JSX.Element {
  if (Math.abs(delta) < 0.5) return <span className="text-gray-500 text-xs">≈</span>;
  const sign = delta > 0 ? "+" : "";
  const color = delta > 0 ? "text-green-400" : "text-red-400";
  return <span className={`text-xs font-medium ${color}`}>{sign}{delta.toFixed(1)}</span>;
}

export default function NearbyList({ locations, mainScore, onSelect, isLoading }: Props) {
  return (
    <div className="rounded-xl bg-gray-900 border border-gray-800 p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-200">Nearby Locations</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            8 points within ~1.5 km · Google Solar re-scored · macro weather shared
          </p>
        </div>
        {isLoading && (
          <span className="text-xs text-gray-500 animate-pulse">Scanning…</span>
        )}
      </div>

      <div className="space-y-2">
        {locations.map((loc, i) => {
          const delta = loc.overall_score - mainScore;
          return (
            <div
              key={`${loc.lat}-${loc.lon}`}
              className="flex items-center gap-3 rounded-lg bg-gray-800 hover:bg-gray-750 px-3 py-2.5 transition-colors"
            >
              {/* Rank */}
              <span className="text-xs text-gray-500 w-4 shrink-0 text-right">
                {i + 1}
              </span>

              {/* Score dot */}
              <div className={`w-2.5 h-2.5 rounded-full shrink-0 ${scoreColor(loc.overall_score)}`} />

              {/* Name */}
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-200 truncate">{loc.short_name}</p>
                {!loc.google_available && (
                  <p className="text-xs text-gray-600 truncate">Google Solar unavailable</p>
                )}
              </div>

              {/* Score bar */}
              <div className="w-24 shrink-0 hidden sm:block">
                <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${scoreColor(loc.overall_score)}`}
                    style={{ width: `${loc.overall_score}%` }}
                  />
                </div>
              </div>

              {/* Score number */}
              <span className="text-sm font-semibold text-gray-100 w-8 text-right shrink-0">
                {Math.round(loc.overall_score)}
              </span>

              {/* Delta */}
              <span className="w-10 text-right shrink-0">
                {deltaLabel(delta)}
              </span>

              {/* Analyse button */}
              <button
                onClick={() => onSelect(loc.lat, loc.lon, loc.short_name)}
                className="text-xs px-2 py-1 rounded bg-gray-700 hover:bg-solar-500 hover:text-gray-950 text-gray-400 transition-colors shrink-0"
                title={loc.display_name}
              >
                Analyse
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
