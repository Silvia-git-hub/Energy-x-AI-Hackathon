export interface SubScoreData {
  score: number;
  available: boolean;
  error: string | null;
  metrics: Record<string, unknown>;
}

export interface ChartData {
  sunshine_hours_annual: number | null;
  monthly_irradiance: number[] | null;
  monthly_labels: string[];
  seasonal_irradiance: Record<string, number> | null;
  avg_cloud_cover_pct: number | null;
}

export interface EvaluateResponse {
  lat: number;
  lon: number;
  overall_score: number;
  sub_scores: Record<string, SubScoreData>;
  weights_used: Record<string, number>;
  chart_data: ChartData;
  data_warning?: string | null;
}

export interface GeocodeResponse {
  lat: number;
  lon: number;
  display_name: string;
  short_name: string;
  available: boolean;
  error?: string | null;
}

export interface NearbyLocation {
  lat: number;
  lon: number;
  display_name: string;
  short_name: string;
  overall_score: number;
  google_score: number;
  google_available: boolean;
  error?: string | null;
}

export interface NearbyResponse {
  locations: NearbyLocation[];
}

export interface HourlyPoint {
  timestamp: string;
  p_kw: number;
  p_kw_baseline: number;
  ghi_w_m2: number;
}

export interface DailyTotal {
  date: string;
  kwh: number;
  kwh_baseline: number;
}

export interface ForecastResponse {
  system_kwp: number;
  skill_score: number;
  mae_kw: number;
  hourly: HourlyPoint[];
  daily: DailyTotal[];
  signal: string;
  signal_score: number;
  signal_reasons: string[];
  available: boolean;
  error?: string | null;
}

export interface EpexPrice {
  hour: string;
  price_eur_mwh: number;
}

export interface GridMetrics {
  solar_mwh:       number | null;
  wind_mwh:        number | null;
  load_mwh:        number | null;
  solar_share_pct: number | null;
  wind_share_pct:  number | null;
}

export interface MarketDataResponse {
  epex_current_price: number | null;
  epex_day_high:      number | null;
  epex_day_low:       number | null;
  epex_prices:        EpexPrice[];
  grid:               GridMetrics;
  updated_at:         string;
  available:          boolean;
  error?:             string | null;
}

export interface NewsItem {
  title:     string;
  summary:   string;
  sentiment: "bullish" | "bearish" | "neutral";
  url:       string;
}

export interface PredictionMarket {
  question:    string;
  probability: number;
  url:         string;
}

export interface MarketIntelResponse {
  news:       NewsItem[];
  markets:    PredictionMarket[];
  updated_at: string;
  available:  boolean;
  error?:     string | null;
}

export type SSEChunk =
  | { type: "text"; content: string }
  | { type: "done" }
  | { type: "error"; content: string };

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
}
