from pydantic import BaseModel
from typing import Optional


class StockInfo(BaseModel):
    symbol: str
    name: str
    sector: str
    market_cap: str
    market_cap_category: str  # large, mid, small
    price: Optional[float] = None
    change_pct: Optional[float] = None
    analyst_rating: Optional[str] = None


class StockMetrics(BaseModel):
    symbol: str
    expected_return: float
    volatility: float
    sharpe_ratio: float
    beta: Optional[float] = None
    max_drawdown: float


class PortfolioOptimizeRequest(BaseModel):
    stocks: list[str]
    target: str = "max_sharpe"  # max_sharpe, min_vol, target_return
    target_return: Optional[float] = None
    max_weight: float = 1.0
    min_weight: float = 0.0


class PortfolioWeights(BaseModel):
    weights: dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float


class EfficientFrontierPoint(BaseModel):
    volatility: float
    expected_return: float
    sharpe_ratio: float
    weights: dict[str, float]


class PortfolioOptimizeResponse(BaseModel):
    optimal_portfolio: PortfolioWeights
    efficient_frontier: list[EfficientFrontierPoint]
    individual_stocks: list[dict]


class RiskAnalyzeRequest(BaseModel):
    weights: dict[str, float]


class RiskMetrics(BaseModel):
    volatility: float
    var_95: float
    var_99: float
    cvar_95: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float


class CorrelationMatrix(BaseModel):
    symbols: list[str]
    matrix: list[list[float]]
