import numpy as np
import pandas as pd
from typing import Optional

from config import TRADING_DAYS, RISK_FREE_RATE
from services.data_loader import data_loader


class RiskEngine:
    """Calculate risk metrics for portfolios."""

    def __init__(self, weights: dict[str, float]):
        """
        Initialize with portfolio weights.

        Args:
            weights: Dictionary mapping symbols to weights (should sum to 1)
        """
        self.weights = weights
        self.symbols = list(weights.keys())

        # Get returns matrix
        self.returns_matrix = data_loader.get_returns_matrix(self.symbols)

        if self.returns_matrix.empty:
            raise ValueError("No return data available for the given symbols")

        # Align symbols with available data
        available_symbols = [s for s in self.symbols if s in self.returns_matrix.columns]
        if not available_symbols:
            raise ValueError("None of the symbols have return data")

        self.symbols = available_symbols
        self.weights = {s: weights[s] for s in available_symbols}

        # Normalize weights to sum to 1
        total_weight = sum(self.weights.values())
        if total_weight > 0:
            self.weights = {s: w / total_weight for s, w in self.weights.items()}

        # Calculate portfolio returns
        weights_array = np.array([self.weights[s] for s in self.symbols])
        self.portfolio_returns = self.returns_matrix[self.symbols].dot(weights_array)

    def calculate_volatility(self) -> float:
        """Calculate annualized portfolio volatility."""
        return float(self.portfolio_returns.std() * np.sqrt(TRADING_DAYS))

    def calculate_var(self, confidence: float = 0.95) -> float:
        """
        Calculate Value at Risk using historical simulation.

        Args:
            confidence: Confidence level (0.95 for 95% VaR)

        Returns:
            VaR as a positive percentage loss
        """
        percentile = (1 - confidence) * 100
        var = np.percentile(self.portfolio_returns, percentile)
        # Annualize (approximate)
        return float(-var * np.sqrt(TRADING_DAYS))

    def calculate_cvar(self, confidence: float = 0.95) -> float:
        """
        Calculate Conditional VaR (Expected Shortfall).

        Args:
            confidence: Confidence level

        Returns:
            CVaR as a positive percentage loss
        """
        percentile = (1 - confidence) * 100
        var_threshold = np.percentile(self.portfolio_returns, percentile)
        cvar = self.portfolio_returns[self.portfolio_returns <= var_threshold].mean()
        # Annualize (approximate)
        return float(-cvar * np.sqrt(TRADING_DAYS))

    def calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from cumulative returns."""
        cumulative = (1 + self.portfolio_returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdowns = (cumulative - rolling_max) / rolling_max
        return float(drawdowns.min())

    def calculate_sharpe_ratio(self) -> float:
        """Calculate annualized Sharpe ratio."""
        annual_return = self.portfolio_returns.mean() * TRADING_DAYS
        annual_vol = self.calculate_volatility()
        if annual_vol == 0:
            return 0.0
        return float((annual_return - RISK_FREE_RATE) / annual_vol)

    def calculate_sortino_ratio(self) -> float:
        """Calculate Sortino ratio (uses downside deviation)."""
        annual_return = self.portfolio_returns.mean() * TRADING_DAYS

        # Downside deviation (only negative returns)
        negative_returns = self.portfolio_returns[self.portfolio_returns < 0]
        if len(negative_returns) == 0:
            return float('inf')

        downside_std = negative_returns.std() * np.sqrt(TRADING_DAYS)
        if downside_std == 0:
            return float('inf')

        return float((annual_return - RISK_FREE_RATE) / downside_std)

    def calculate_beta(self, market_symbol: str = "BP") -> Optional[float]:
        """
        Calculate portfolio beta against a market proxy.

        Uses BP as a proxy for UK market (large, liquid stock).
        """
        market_returns = data_loader.get_returns(market_symbol)
        if market_returns is None:
            return None

        # Align dates
        aligned = pd.DataFrame({
            'portfolio': self.portfolio_returns,
            'market': market_returns
        }).dropna()

        if len(aligned) < 20:
            return None

        cov = aligned['portfolio'].cov(aligned['market'])
        var = aligned['market'].var()

        if var == 0:
            return None

        return float(cov / var)

    def get_all_metrics(self) -> dict:
        """Calculate all risk metrics."""
        return {
            'volatility': round(self.calculate_volatility(), 4),
            'var_95': round(self.calculate_var(0.95), 4),
            'var_99': round(self.calculate_var(0.99), 4),
            'cvar_95': round(self.calculate_cvar(0.95), 4),
            'max_drawdown': round(self.calculate_max_drawdown(), 4),
            'sharpe_ratio': round(self.calculate_sharpe_ratio(), 4),
            'sortino_ratio': round(min(self.calculate_sortino_ratio(), 10), 4)  # Cap at 10
        }


def calculate_correlation_matrix(symbols: list[str]) -> dict:
    """
    Calculate correlation matrix for a list of symbols.

    Returns:
        Dictionary with 'symbols' list and 'matrix' as 2D list
    """
    returns_matrix = data_loader.get_returns_matrix(symbols)

    if returns_matrix.empty:
        return {'symbols': [], 'matrix': []}

    correlation = returns_matrix.corr()

    return {
        'symbols': list(correlation.columns),
        'matrix': correlation.values.tolist()
    }


def analyze_portfolio_risk(weights: dict[str, float]) -> dict:
    """
    Analyze risk metrics for a portfolio.

    Args:
        weights: Dictionary mapping symbols to weights

    Returns:
        Dictionary with all risk metrics
    """
    engine = RiskEngine(weights)
    return engine.get_all_metrics()
