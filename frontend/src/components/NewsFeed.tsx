import { useState } from "react";
import { useMarketIntel } from "@/hooks/useMarketIntel";

type Sentiment = "bullish" | "bearish" | "neutral";

const SENTIMENT_STYLES: Record<Sentiment, string> = {
  bullish: "text-term-green border-term-green",
  bearish: "text-term-red border-term-red",
  neutral: "text-term-muted border-term-border",
};

const SENTIMENT_LABEL: Record<Sentiment, string> = {
  bullish: "BUY",
  bearish: "SELL",
  neutral: "NEUT",
};

export default function NewsFeed() {
  const [expanded, setExpanded] = useState<number | null>(null);
  const { data, isLoading, isError } = useMarketIntel();

  const news = data?.news ?? [];

  return (
    <div className="bg-term-panel border border-term-border rounded p-3 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-mono text-term-muted tracking-widest">SOLAR MARKET NEWS</span>
        <span className="text-[10px] font-mono text-term-dim">
          {isLoading ? "LOADING…" : `${news.length} ITEMS · GROQ`}
        </span>
      </div>

      {isLoading && (
        <div className="text-[10px] font-mono text-term-dim animate-pulse py-2">
          ▶ Fetching and filtering live news…
        </div>
      )}

      {(isError || data?.available === false) && (
        <div className="text-[10px] font-mono text-term-red py-1">
          {data?.error ?? "News unavailable — check GROQ_API_KEY"}
        </div>
      )}

      {news.length > 0 && (
        <div className="space-y-1">
          {news.map((item, i) => {
            const sentiment = item.sentiment as Sentiment;
            return (
              <div
                key={i}
                className="border-b border-term-border pb-2 cursor-pointer"
                onClick={() => setExpanded(expanded === i ? null : i)}
              >
                <div className="flex items-start gap-2">
                  <span className={`shrink-0 text-[9px] font-mono border px-1 py-0.5 rounded mt-0.5 ${SENTIMENT_STYLES[sentiment] ?? SENTIMENT_STYLES.neutral}`}>
                    {SENTIMENT_LABEL[sentiment] ?? "NEUT"}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-[11px] text-term-text leading-snug">{item.title}</p>
                    {item.url && (
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[9px] font-mono text-term-dim hover:text-term-amber"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {new URL(item.url).hostname.replace("www.", "")}
                      </a>
                    )}
                  </div>
                </div>
                {expanded === i && item.summary && (
                  <p className="text-[10px] text-term-muted leading-relaxed mt-1 pl-8">
                    {item.summary}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
