import { useState } from "react";
import { useGeocode } from "@/hooks/useGeocode";

interface Props {
  onAnalyse: (lat: number, lon: number, cityName?: string) => void;
  isLoading: boolean;
  error: string | null;
  initialLat?: string;
  initialLon?: string;
}

export default function LocationInput({ onAnalyse, isLoading, error, initialLat = "50.1109", initialLon = "8.6821" }: Props) {
  const [address, setAddress] = useState("");
  const [resolvedName, setResolvedName] = useState<string | null>(null);
  const [lat, setLat] = useState(initialLat);
  const [lon, setLon] = useState(initialLon);
  const geocode = useGeocode();

  const handleFind = () => {
    if (!address.trim()) return;
    geocode.mutate(address.trim(), {
      onSuccess: (data) => {
        setLat(String(data.lat));
        setLon(String(data.lon));
        setResolvedName(data.short_name);
        onAnalyse(data.lat, data.lon, data.short_name);
      },
    });
  };

  const handleAnalyse = () => {
    const latN = parseFloat(lat);
    const lonN = parseFloat(lon);
    if (isNaN(latN) || isNaN(lonN)) return;
    onAnalyse(latN, lonN, resolvedName ?? undefined);
  };

  return (
    <div className="bg-term-panel border border-term-border rounded p-3 space-y-2">
      <p className="text-[10px] font-mono text-term-muted tracking-widest">LOCATION SEARCH</p>

      {/* Address */}
      <div className="flex gap-1">
        <input
          type="text"
          value={address}
          onChange={(e) => { setAddress(e.target.value); setResolvedName(null); }}
          onKeyDown={(e) => e.key === "Enter" && handleFind()}
          placeholder="Address or place name…"
          className="flex-1 bg-term-bg border border-term-border rounded px-2 py-1.5 text-[11px] font-mono text-term-text placeholder-term-dim focus:outline-none focus:border-term-amber"
        />
        <button
          onClick={handleFind}
          disabled={geocode.isPending || isLoading || !address.trim()}
          className="px-3 py-1.5 text-[11px] font-mono border border-term-border text-term-muted hover:border-term-amber hover:text-term-amber disabled:opacity-40 transition-colors rounded"
        >
          {geocode.isPending ? "…" : "GO"}
        </button>
      </div>

      {resolvedName && (
        <p className="text-[10px] font-mono text-term-green">▶ {resolvedName}</p>
      )}
      {geocode.isError && (
        <p className="text-[10px] font-mono text-term-red">{String(geocode.error)}</p>
      )}

      {/* Coordinates */}
      <div className="flex gap-1 w-full">
        <input
          type="number" step="any" value={lat}
          onChange={(e) => { setLat(e.target.value); setResolvedName(null); }}
          placeholder="Lat"
          className="flex-1 min-w-0 bg-term-bg border border-term-border rounded px-2 py-1.5 text-[11px] font-mono text-term-text placeholder-term-dim focus:outline-none focus:border-term-amber"
        />
        <input
          type="number" step="any" value={lon}
          onChange={(e) => { setLon(e.target.value); setResolvedName(null); }}
          placeholder="Lon"
          className="flex-1 min-w-0 bg-term-bg border border-term-border rounded px-2 py-1.5 text-[11px] font-mono text-term-text placeholder-term-dim focus:outline-none focus:border-term-amber"
        />
      </div>

      <button
        onClick={handleAnalyse}
        disabled={isLoading}
        className="w-full py-2 text-[11px] font-mono font-bold tracking-widest border border-term-amber text-term-amber hover:bg-term-amber hover:text-black disabled:opacity-40 transition-colors rounded"
      >
        {isLoading ? "ANALYSING…" : "▶ RUN ANALYSIS"}
      </button>

      {error && <p className="text-[10px] font-mono text-term-red">{error}</p>}
    </div>
  );
}
