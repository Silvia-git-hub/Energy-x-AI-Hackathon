import { useState, useRef, useEffect } from "react";
import { useChat } from "@/hooks/useChat";
import type { ChatMessage, EvaluateResponse, ForecastResponse, MarketDataResponse } from "@/types";

interface Props {
  locationContext: EvaluateResponse | Record<string, unknown>;
  forecast?: ForecastResponse | null;
  marketData?: MarketDataResponse;
}

function buildTradingContext(
  loc: EvaluateResponse | Record<string, unknown>,
  forecast?: ForecastResponse | null,
  market?: MarketDataResponse,
): Record<string, unknown> {
  const e = loc as EvaluateResponse;
  const forecast7dKwh = forecast?.daily?.reduce((s, d) => s + d.kwh, 0) ?? null;
  return {
    // Signal panel
    signal:          forecast?.signal ?? null,
    solar_index:     e.overall_score ?? null,
    forecast_7d_kwh: forecast7dKwh != null ? Math.round(forecast7dKwh) : null,
    system_kwp:      forecast?.system_kwp ?? null,
    skill_pct:       forecast?.skill_score != null ? Math.round(forecast.skill_score * 100) : null,
    // Sub-scores panel
    google_solar_score: e.sub_scores?.google_solar?.score ?? null,
    pvgis_score:        e.sub_scores?.pvgis?.score ?? null,
    cloud_cover_score:  e.sub_scores?.climate?.score ?? null,
    // EPEX market panel
    epex_eur_mwh:       market?.epex_current_price ?? null,
    epex_day_high:      market?.epex_day_high ?? null,
    epex_day_low:       market?.epex_day_low ?? null,
    // Grid ticker
    solar_grid_share_pct: market?.grid?.solar_share_pct ?? null,
    wind_grid_share_pct:  market?.grid?.wind_share_pct ?? null,
  };
}

function Message({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  return (
    <div className={`font-mono text-[11px] leading-relaxed ${isUser ? "text-term-amber" : "text-term-text"}`}>
      <span className="text-term-dim mr-1">{isUser ? ">" : "$"}</span>
      {msg.content}
      {msg.streaming && <span className="inline-block w-1.5 h-3 bg-term-amber ml-0.5 animate-pulse" />}
    </div>
  );
}

export default function ChatPanel({ locationContext, forecast, marketData }: Props) {
  const [input, setInput] = useState("");
  const tradingContext = buildTradingContext(locationContext, forecast, marketData);
  const { messages, isStreaming, sendMessage } = useChat(tradingContext);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || isStreaming) return;
    setInput("");
    sendMessage(text);
  };

  return (
    <div className="bg-term-panel border border-term-border rounded flex flex-col" style={{ height: 320 }}>
      <div className="px-3 py-2 border-b border-term-border shrink-0 flex items-center justify-between">
        <span className="text-[10px] font-mono text-term-muted tracking-widest">AI ANALYST · CLAUDE</span>
        {isStreaming && <span className="text-[9px] font-mono text-term-amber animate-pulse">STREAMING…</span>}
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2">
        {messages.length === 0 && (
          <p className="text-[10px] font-mono text-term-dim">
            $ Analyse a location to enable context-aware trading insights…
          </p>
        )}
        {messages.map((msg) => <Message key={msg.id} msg={msg} />)}
        <div ref={bottomRef} />
      </div>

      <div className="px-3 py-2 border-t border-term-border shrink-0 flex gap-1">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
          disabled={isStreaming}
          placeholder="Ask the analyst…"
          className="flex-1 bg-term-bg border border-term-border rounded px-2 py-1.5 text-[11px] font-mono text-term-text placeholder-term-dim focus:outline-none focus:border-term-amber disabled:opacity-50"
        />
        <button
          onClick={handleSend}
          disabled={isStreaming || !input.trim()}
          className="px-3 py-1.5 text-[11px] font-mono border border-term-amber text-term-amber hover:bg-term-amber hover:text-black disabled:opacity-40 transition-colors rounded"
        >
          SEND
        </button>
      </div>
    </div>
  );
}
