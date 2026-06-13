const DE_AT_CITIES: { name: string; lat: number; lon: number; country: string }[] = [
  { name: "Berlin",      lat: 52.5200, lon: 13.4050, country: "DE" },
  { name: "Hamburg",     lat: 53.5753, lon:  9.9929, country: "DE" },
  { name: "Munich",      lat: 48.1372, lon: 11.5761, country: "DE" },
  { name: "Cologne",     lat: 50.9333, lon:  6.9500, country: "DE" },
  { name: "Frankfurt",   lat: 50.1109, lon:  8.6821, country: "DE" },
  { name: "Stuttgart",   lat: 48.7758, lon:  9.1829, country: "DE" },
  { name: "Dusseldorf",  lat: 51.2217, lon:  6.7762, country: "DE" },
  { name: "Leipzig",     lat: 51.3397, lon: 12.3731, country: "DE" },
  { name: "Dortmund",    lat: 51.5136, lon:  7.4653, country: "DE" },
  { name: "Bremen",      lat: 53.0793, lon:  8.8017, country: "DE" },
  { name: "Dresden",     lat: 51.0504, lon: 13.7373, country: "DE" },
  { name: "Hanover",     lat: 52.3759, lon:  9.7320, country: "DE" },
  { name: "Nuremberg",   lat: 49.4521, lon: 11.0767, country: "DE" },
  { name: "Vienna",      lat: 48.2082, lon: 16.3738, country: "AT" },
  { name: "Graz",        lat: 47.0707, lon: 15.4395, country: "AT" },
  { name: "Linz",        lat: 48.3064, lon: 14.2858, country: "AT" },
  { name: "Salzburg",    lat: 47.8095, lon: 13.0550, country: "AT" },
  { name: "Innsbruck",   lat: 47.2692, lon: 11.4041, country: "AT" },
];

function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

interface Props {
  lat: number;
  lon: number;
  onSelect: (lat: number, lon: number) => void;
}

export default function RegionSuggestions({ lat, lon, onSelect }: Props) {
  const sorted = DE_AT_CITIES
    .map((c) => ({ ...c, distKm: haversineKm(lat, lon, c.lat, c.lon) }))
    .sort((a, b) => a.distKm - b.distKm)
    .slice(0, 5);

  return (
    <div className="bg-term-panel border border-term-border rounded p-3 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-mono text-term-muted tracking-widest">NEAREST SMARD LOCATIONS</span>
        <span className="text-[10px] font-mono text-term-dim">DE · AT COVERAGE</span>
      </div>
      <p className="text-[10px] font-mono text-term-dim">
        This location is outside the SMARD data region. Closest covered cities:
      </p>
      <div className="space-y-1">
        {sorted.map((c) => (
          <button
            key={c.name}
            onClick={() => onSelect(c.lat, c.lon)}
            className="w-full flex items-center justify-between px-3 py-2 border border-term-border hover:border-term-amber hover:bg-[#141414] transition-colors rounded text-left"
          >
            <div className="flex items-center gap-2">
              <span className="text-[9px] font-mono text-term-dim border border-term-border px-1 rounded">{c.country}</span>
              <span className="text-[11px] font-mono text-term-text">{c.name}</span>
            </div>
            <span className="text-[10px] font-mono text-term-muted">{Math.round(c.distKm).toLocaleString()} km →</span>
          </button>
        ))}
      </div>
    </div>
  );
}
