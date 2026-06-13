import { useState } from "react";
import { Toaster } from "sonner";
import LocationInput from "@/components/LocationInput";
import ScoreGauge from "@/components/ScoreGauge";
import SubScorePanel from "@/components/SubScorePanel";
import ForecastChart from "@/components/ForecastChart";
import NearbyTable from "@/components/NearbyTable";
import ChatPanel from "@/components/ChatPanel";
import TickerBar from "@/components/TickerBar";
import SignalPanel from "@/components/SignalPanel";
import MarketPricePanel from "@/components/MarketPricePanel";
import NewsFeed from "@/components/NewsFeed";
import PredictionMarkets from "@/components/PredictionMarkets";
import { useEvaluate } from "@/hooks/useEvaluate";
import { useForecast } from "@/hooks/useForecast";
import { useNearby } from "@/hooks/useNearby";
import { useMarketData } from "@/hooks/useMarketData";
import { isInSMARDRegion } from "@/utils/smardRegion";
import RegionSuggestions from "@/components/RegionSuggestions";
import SunLogo from "@/components/SunLogo";
import type { EvaluateResponse, ForecastResponse, NearbyResponse } from "@/types";

export default function App() {
  const [result, setResult]   = useState<EvaluateResponse | null>(null);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [nearby, setNearby]   = useState<NearbyResponse | null>(null);
  const [currentLat, setCurrentLat] = useState(50.1109); // Frankfurt default
  const [currentLon, setCurrentLon] = useState(8.6821);
  const [currentCity, setCurrentCity] = useState<string | null>(null);

  const evaluate    = useEvaluate();
  const forecastMut = useForecast();
  const nearbyMut   = useNearby();
  const { data: marketData } = useMarketData();

  const runAnalysis = (lat: number, lon: number, cityName?: string) => {
    setCurrentLat(lat);
    setCurrentLon(lon);
    if (cityName) setCurrentCity(cityName);
    setForecast(null);
    setNearby(null);
    evaluate.mutate({ lat, lon }, {
      onSuccess: (data) => {
        setResult(data);
        const gMetrics = data.sub_scores.google_solar?.metrics ?? {};
        const pvgisScore = data.sub_scores.pvgis?.score ?? 50;
        const climateScore = data.sub_scores.climate?.score ?? 50;

        forecastMut.mutate(
          {
            lat, lon,
            panel_count: (gMetrics.panel_count as number) ?? 10,
            panel_capacity_watts: (gMetrics["panel capacity W"] as number) ?? 400,
            solar_index: data.overall_score,
            epex_price: marketData?.epex_current_price,
            solar_share_pct: marketData?.grid?.solar_share_pct,
          },
          { onSuccess: setForecast }
        );

        if (isInSMARDRegion(lat, lon)) {
          nearbyMut.mutate(
            {
              lat, lon,
              eumetsat_score: pvgisScore,
              copernicus_score: climateScore,
              eumetsat_available: data.sub_scores.pvgis?.available ?? false,
              copernicus_available: data.sub_scores.climate?.available ?? false,
            },
            { onSuccess: setNearby }
          );
        }
      },
    });
  };

  const signal = forecast?.signal;
  const inRegion = isInSMARDRegion(currentLat, currentLon);
  const now = new Date();
  const timeStr = now.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  const dateStr = now.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }).toUpperCase();

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-term-bg text-term-text">
      <Toaster richColors position="top-right" />

      {/* Header */}
      <header className="shrink-0 px-4 py-2 border-b border-term-border flex items-center justify-between bg-term-panel">
        <div className="flex items-center gap-2.5">
          <SunLogo size={22} />
          <span className="text-term-amber font-mono font-bold text-sm tracking-widest">SOLARBITRAGE</span>
          <span className="text-[10px] font-mono text-term-dim border-l border-term-border pl-3">
            DE · AT · SOLAR ENERGY ARBITRAGE
          </span>
        </div>
        <div className="flex items-center gap-4 text-[10px] font-mono text-term-dim">
          {result && (
            <>
              {currentCity && (
                <span className="text-term-amber font-bold tracking-wide">
                  {currentCity.toUpperCase()}
                </span>
              )}
              <span className={currentCity ? "text-term-dim" : "text-term-amber"}>
                {currentLat.toFixed(4)}°N {currentLon.toFixed(4)}°E
              </span>
              <span className={`text-[9px] px-2 py-0.5 rounded border font-mono ${
                inRegion ? "border-term-green text-term-green" : "border-term-yellow text-term-yellow"
              }`}>
                {inRegion ? "DE/AT ✓" : "OUT OF REGION"}
              </span>
            </>
          )}
          <span>{dateStr}</span>
          <span className="text-term-text tabular-nums">{timeStr}</span>
          <span className={`px-2 py-0.5 rounded border text-[9px] ${
            evaluate.isPending
              ? "border-term-yellow text-term-yellow animate-pulse"
              : result
              ? "border-term-green text-term-green"
              : "border-term-border text-term-dim"
          }`}>
            {evaluate.isPending ? "SCANNING" : result ? "LIVE" : "IDLE"}
          </span>
        </div>
      </header>

      {/* Ticker */}
      <TickerBar solarScore={result?.overall_score} signal={signal} marketData={marketData} />

      {/* 3-column body */}
      <div className="flex-1 grid overflow-hidden min-h-0" style={{ gridTemplateColumns: "260px 1fr 300px" }}>

        {/* ── LEFT: location + score ── */}
        <aside className="border-r border-term-border overflow-y-auto p-2 space-y-2">
          <LocationInput
            onAnalyse={(lat, lon, city) => runAnalysis(lat, lon, city)}
            isLoading={evaluate.isPending}
            error={evaluate.isError ? String(evaluate.error) : null}
          />

          {result?.data_warning && (
            <div className="border border-term-red text-term-red text-[10px] font-mono rounded p-2">
              ⚠ {result.data_warning}
            </div>
          )}

          {result && (
            <>
              <SignalPanel score={result.overall_score} forecast={forecast} />
              <ScoreGauge score={result.overall_score} label="Solar Index" size={130} />
              <SubScorePanel subScores={result.sub_scores} weightsUsed={result.weights_used} />
            </>
          )}

          {!result && !evaluate.isPending && (
            <div className="border border-term-border rounded p-3 text-[10px] font-mono text-term-dim space-y-1">
              <p className="text-term-muted">AWAITING LOCATION INPUT</p>
              <p>Enter coordinates or search an address to begin market analysis.</p>
            </div>
          )}
        </aside>

        {/* ── CENTER: forecast + nearby ── */}
        <main className="overflow-y-auto p-2 space-y-2">
          {!result && !evaluate.isPending && (
            <div className="h-full flex items-center justify-center">
              <div className="text-center space-y-3">
                <div className="text-4xl font-mono text-term-amber opacity-30">◈</div>
                <p className="text-[11px] font-mono text-term-dim">
                  SOLARBITRAGE · ENTER LOCATION TO BEGIN
                </p>
                <div className="text-[10px] font-mono text-term-border space-y-1">
                  <p>EPEX SPOT · DL FORECAST ENGINE · GOOGLE SOLAR API</p>
                  <p>EUMETSAT SARAH-3 · COPERNICUS SENTINEL · CLAUDE AI</p>
                </div>
              </div>
            </div>
          )}

          {evaluate.isPending && (
            <div className="border border-term-border rounded p-4 text-[11px] font-mono text-term-amber animate-pulse">
              ▶ Fetching solar data… Google Solar · EUMETSAT · Copernicus
            </div>
          )}

          {forecastMut.isPending && (
            <div className="border border-term-border rounded p-3 text-[10px] font-mono text-term-dim animate-pulse">
              ▶ Running 7-day deep learning forecast…
            </div>
          )}

          {forecast?.available && (
            <ForecastChart
              hourly={forecast.hourly}
              systemKwp={forecast.system_kwp}
              skillScore={forecast.skill_score}
            />
          )}

          {forecast && !forecast.available && (
            <div className="border border-term-red rounded p-3 text-[10px] font-mono text-term-red">
              FORECAST UNAVAILABLE · {forecast.error}
            </div>
          )}

          {result && !inRegion && (
            <RegionSuggestions
              lat={currentLat}
              lon={currentLon}
              onSelect={(lat, lon) => runAnalysis(lat, lon)}
            />
          )}

          {inRegion && nearbyMut.isPending && (
            <div className="border border-term-border rounded p-3 text-[10px] font-mono text-term-dim animate-pulse">
              ▶ Scanning nearby locations…
            </div>
          )}

          {inRegion && nearby && nearby.locations.length > 0 && (
            <NearbyTable
              locations={nearby.locations}
              mainScore={result?.overall_score ?? 50}
              forecast={forecast}
              onSelect={(lat, lon) => runAnalysis(lat, lon)}
              isLoading={nearbyMut.isPending}
            />
          )}
        </main>

        {/* ── RIGHT: market + news + chat ── */}
        <aside className="border-l border-term-border overflow-y-auto p-2 space-y-2">
          <MarketPricePanel marketData={marketData} />
          <NewsFeed />
          <PredictionMarkets />
          <ChatPanel locationContext={result ?? {}} forecast={forecast} marketData={marketData} />
        </aside>
      </div>
    </div>
  );
}
