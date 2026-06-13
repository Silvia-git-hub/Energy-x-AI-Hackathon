import asyncio
import json
import logging
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

TTL = 30 * 60
_cache: Optional[dict] = None
_cache_ts: float = 0.0

RSS_FEEDS = [
    "https://www.pv-magazine.com/feed/",
    "https://renewablesnow.com/feed/",
]

MANIFOLD_URL = "https://api.manifold.markets/v0/search-markets"
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"

GROQ_SYSTEM = (
    "You are a solar energy market intelligence analyst for the German and Austrian EPEX spot market. "
    "You return only valid JSON — no markdown, no explanation."
)

GROQ_USER = """Filter the raw news headlines and prediction markets below for relevance to solar energy trading in Germany/Austria.

Return this exact JSON structure:
{{
  "news": [
    {{"title": "...", "summary": "1-2 sentence trading impact summary", "sentiment": "bullish|bearish|neutral", "url": "..."}}
  ],
  "markets": [
    {{"question": "...", "probability": 0.65, "url": "..."}}
  ]
}}

Rules:
- max 4 news items, max 3 prediction markets
- only include items relevant to: solar PV, EPEX/electricity prices, German/Austrian grid, renewable policy, storage
- sentiment = bullish|bearish|neutral from a solar trader perspective
- empty array if nothing relevant

NEWS:
{news_block}

PREDICTION MARKETS:
{markets_block}
"""


@dataclass
class NewsItem:
    title: str
    summary: str
    sentiment: str
    url: str


@dataclass
class PredictionMarketItem:
    question: str
    probability: float
    url: str


@dataclass
class MarketIntelResult:
    news: list[NewsItem]           = field(default_factory=list)
    markets: list[PredictionMarketItem] = field(default_factory=list)
    updated_at: str                = ""
    available: bool                = True
    error: Optional[str]           = None


def _parse_rss(xml_text: str, max_items: int = 10) -> list[dict]:
    try:
        root = ET.fromstring(xml_text)
        items = []
        for el in root.findall(".//item")[:max_items]:
            title = (el.findtext("title") or "").strip()
            link  = (el.findtext("link")  or "").strip()
            if title:
                items.append({"title": title, "url": link})
        return items
    except Exception as exc:
        logger.debug("RSS parse error: %s", exc)
        return []


async def _fetch_rss(client: httpx.AsyncClient, url: str) -> list[dict]:
    try:
        r = await client.get(url, timeout=10.0, follow_redirects=True)
        r.raise_for_status()
        return _parse_rss(r.text)
    except Exception as exc:
        logger.warning("RSS fetch failed %s: %s", url, exc)
        return []


async def _fetch_manifold(client: httpx.AsyncClient) -> list[dict]:
    try:
        queries = ["solar energy germany", "electricity price europe"]
        results = await asyncio.gather(*[
            client.get(MANIFOLD_URL, params={"term": q, "sort": "liquidity", "limit": 6}, timeout=10.0)
            for q in queries
        ], return_exceptions=True)

        seen, markets = set(), []
        for r in results:
            if isinstance(r, Exception) or not hasattr(r, "json"):
                continue
            for m in r.json():
                mid = m.get("id", "")
                if mid in seen or m.get("isResolved"):
                    continue
                seen.add(mid)
                prob = m.get("probability") or m.get("p", None)
                markets.append({
                    "question":    m.get("question", ""),
                    "probability": round(float(prob), 2) if prob is not None else 0.5,
                    "url":         m.get("url", "https://manifold.markets"),
                })
        return markets[:8]
    except Exception as exc:
        logger.warning("Manifold fetch failed: %s", exc)
        return []


async def _call_groq(news: list[dict], markets: list[dict]) -> MarketIntelResult:
    if not settings.groq_api_key:
        return MarketIntelResult(available=False, error="GROQ_API_KEY not configured")

    news_block    = "\n".join(f"- {i['title']} ({i['url']})" for i in news)    or "none"
    markets_block = "\n".join(
        f"- [{m['probability']*100:.0f}%] {m['question']} ({m['url']})" for m in markets
    ) or "none"

    payload = {
        "model":           "llama-3.3-70b-versatile",
        "temperature":     0.1,
        "max_tokens":      800,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": GROQ_SYSTEM},
            {"role": "user",   "content": GROQ_USER.format(
                news_block=news_block, markets_block=markets_block
            )},
        ],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json=payload,
        )
        r.raise_for_status()

    raw = r.json()["choices"][0]["message"]["content"]
    data = json.loads(raw)

    news_items = [
        NewsItem(
            title=n.get("title", ""),
            summary=n.get("summary", ""),
            sentiment=n.get("sentiment", "neutral").lower(),
            url=n.get("url", ""),
        )
        for n in data.get("news", [])
    ]
    market_items = [
        PredictionMarketItem(
            question=m.get("question", ""),
            probability=float(m.get("probability", 0.5)),
            url=m.get("url", ""),
        )
        for m in data.get("markets", [])
    ]

    return MarketIntelResult(
        news=news_items,
        markets=market_items,
        updated_at=datetime.now(timezone.utc).isoformat(),
    )


class MarketIntelService:
    async def get_intel(self) -> MarketIntelResult:
        global _cache, _cache_ts
        if _cache and time.time() - _cache_ts < TTL:
            return MarketIntelResult(
                news=[NewsItem(**n) for n in _cache["news"]],
                markets=[PredictionMarketItem(**m) for m in _cache["markets"]],
                updated_at=_cache["updated_at"],
                available=_cache["available"],
                error=_cache["error"],
            )

        try:
            async with httpx.AsyncClient(headers={"User-Agent": "Solarbitrage/1.0"}) as client:
                rss_results, manifold = await asyncio.gather(
                    asyncio.gather(*[_fetch_rss(client, url) for url in RSS_FEEDS]),
                    _fetch_manifold(client),
                )

            all_news = [item for feed in rss_results for item in feed]
            result = await _call_groq(all_news, manifold)

        except httpx.HTTPStatusError as exc:
            logger.error("Groq API error: %s", exc)
            result = MarketIntelResult(available=False, error=f"Groq HTTP {exc.response.status_code}")
        except Exception as exc:
            logger.error("Market intel failed: %s", exc)
            result = MarketIntelResult(available=False, error=str(exc))

        if result.available:
            _cache = {
                "news":       [n.__dict__ for n in result.news],
                "markets":    [m.__dict__ for m in result.markets],
                "updated_at": result.updated_at,
                "available":  True,
                "error":      None,
            }
            _cache_ts = time.time()

        return result
