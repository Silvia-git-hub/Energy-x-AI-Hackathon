# Solarbitrage — Solar Energy Arbitrage Terminal

A real-time solar energy trading dashboard for the German and Austrian EPEX spot market. It combines live solar irradiance data, grid metrics, and AI-powered market intelligence to generate buy/sell/hold signals for solar energy arbitrage.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend                     │
│   LocationInput → ScoreGauge → ForecastChart        │
│   SignalPanel · MarketPricePanel · ChatPanel         │
│   NewsFeed · PredictionMarkets · NearbyTable         │
└───────────────────┬─────────────────────────────────┘
                    │ HTTP / SSE (Vite proxy → :8000)
┌───────────────────▼─────────────────────────────────┐
│                 FastAPI Backend                      │
│                                                      │
│  /api/evaluate-location  → scoring engine            │
│  /api/forecast           → DL forecast + signal     │
│  /api/market-data        → EPEX prices + grid share │
│  /api/market-intel       → Groq news agent           │
│  /api/chat               → Ollama streaming chat     │
│  /api/geocoding          → city name → lat/lon       │
│  /api/nearby             → nearby location scores    │
└─────────────────────────────────────────────────────┘
```

### Signal Algorithm

The trade signal (STRONG BUY → STRONG SELL) is computed from four weighted components:

| Component | Weight | Source |
|---|---|---|
| EPEX spot price vs 60 €/MWh neutral | 45% | SMARD / ENTSO-E |
| 7-day generation vs persistence baseline | 35% | DL forecast model |
| Forecast trend | 10% | DL forecast model |
| Site solar quality index | 10% | Google Solar + PVGIS + cloud cover |

A saturation penalty is applied when solar grid share exceeds 20% (negative price risk).

### Solar Index Scoring

Three data sources are fused into a 0–100 site quality score:

| Sub-score | Weight | Source |
|---|---|---|
| Google Solar | 50% | Google Solar API — sunshine hours + panel config |
| PVGIS | 30% | EU JRC PVGIS — long-term irradiance (Wh/m²/day) |
| Cloud Cover | 20% | Open-Meteo — 90-day historical cloud cover |

---

## APIs Used

| API | Purpose | Auth |
|---|---|---|
| **Google Solar API** | Building-level solar potential, panel count, sunshine hours | API key |
| **PVGIS (EU JRC)** | Long-term monthly solar irradiance for DACH region | None (free) |
| **Open-Meteo Archive** | 90-day historical cloud cover percentage | None (free) |
| **SMARD (Bundesnetzagentur)** | EPEX day-ahead spot prices, solar/wind grid share | None (free) |
| **Nominatim (OpenStreetMap)** | City name → latitude/longitude geocoding | None (free) |
| **Manifold Markets** | Prediction market probabilities for energy questions | None (free) |
| **PV Magazine RSS** | Solar industry news feed | None (free) |
| **Renewables Now RSS** | Renewable energy news feed | None (free) |
| **Groq API** | LLM filtering of news + markets for trading relevance (llama-3.3-70b) | API key |
| **Ollama (local)** | Streaming chat assistant for dashboard Q&A (llama3.2:1b) | Local |

---

## Stack

**Backend:** Python · FastAPI · httpx · Pydantic  
**Frontend:** React 18 · TypeScript · Vite · Tailwind CSS · TanStack Query · Recharts  
**AI:** Ollama (local inference) · Groq cloud (market intel agent)

---

## Setup

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in API keys
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Requires Ollama running locally with `llama3.2:1b` pulled:

```bash
ollama pull llama3.2:1b
ollama serve
```

### Environment Variables

```
GOOGLE_SOLAR_API_KEY=
GROQ_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
```
