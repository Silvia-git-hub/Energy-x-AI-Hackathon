from typing import Optional
from pydantic import BaseModel, Field


class SubScoreData(BaseModel):
    score: float
    available: bool
    error: Optional[str] = None
    metrics: dict


class EvaluateResponse(BaseModel):
    lat: float
    lon: float
    overall_score: float
    sub_scores: dict[str, SubScoreData]
    weights_used: dict[str, float]
    chart_data: dict
    data_warning: Optional[str] = None


class HourlyPoint(BaseModel):
    timestamp: str
    p_kw: float
    p_kw_baseline: float
    ghi_w_m2: float


class DailyTotal(BaseModel):
    date: str
    kwh: float
    kwh_baseline: float


class ForecastResponse(BaseModel):
    system_kwp: float
    skill_score: float
    mae_kw: float
    hourly: list[HourlyPoint]
    daily: list[DailyTotal]
    signal: str = "HOLD"
    signal_score: float = 0.0
    signal_reasons: list[str] = []
    available: bool = True
    error: Optional[str] = None


class GeocodeResponse(BaseModel):
    lat: float
    lon: float
    display_name: str
    short_name: str
    available: bool = True
    error: Optional[str] = None


class NearbyLocationSchema(BaseModel):
    lat: float
    lon: float
    display_name: str
    short_name: str
    overall_score: float
    google_score: float
    google_available: bool
    error: Optional[str] = None


class NearbyResponse(BaseModel):
    locations: list[NearbyLocationSchema]


class EpexPrice(BaseModel):
    hour: str
    price_eur_mwh: float


class GridMetrics(BaseModel):
    solar_mwh:       Optional[float] = None
    wind_mwh:        Optional[float] = None
    load_mwh:        Optional[float] = None
    solar_share_pct: Optional[float] = None
    wind_share_pct:  Optional[float] = None


class MarketDataResponse(BaseModel):
    epex_current_price: Optional[float]   = None
    epex_day_high:      Optional[float]   = None
    epex_day_low:       Optional[float]   = None
    epex_prices:        list[EpexPrice]   = Field(default_factory=list)
    grid:               GridMetrics       = Field(default_factory=GridMetrics)
    updated_at:         str               = ""
    available:          bool              = True
    error:              Optional[str]     = None


class NewsItemSchema(BaseModel):
    title:     str
    summary:   str
    sentiment: str   # bullish | bearish | neutral
    url:       str


class PredictionMarketSchema(BaseModel):
    question:    str
    probability: float
    url:         str


class MarketIntelResponse(BaseModel):
    news:       list[NewsItemSchema]          = Field(default_factory=list)
    markets:    list[PredictionMarketSchema]  = Field(default_factory=list)
    updated_at: str                           = ""
    available:  bool                          = True
    error:      Optional[str]                 = None
