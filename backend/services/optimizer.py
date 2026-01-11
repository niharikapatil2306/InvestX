import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Optional

from config import TRADING_DAYS, RISK_FREE_RATE
from services.data_loader import data_loader


class PortfolioOptimizer:
    """Portfolio optimization using Mean-Variance Optimization (Markowitz)."""

    def __init__(self, symbols: list[str]):
        self.symbols = symbols
        self.returns_matrix = data_loader.get_returns_matrix(symbols)

        if self.returns_matrix.empty:
            raise ValueError("No return data available for the given symbols")

        # Use only symbols that have data
        self.symbols = list(self.returns_matrix.columns)
        self.n_assets = len(self.symbols)

        # Calculate expected returns and covariance matrix
        self.mean_returns = self.returns_matrix.mean() * TRADING_DAYS
        self.cov_matrix = self.returns_matrix.cov() * TRADING_DAYS

    def portfolio_return(self, weights: np.ndarray) -> float:
        """Calculate expected portfolio return."""
        return np.dot(weights, self.mean_returns)

    def portfolio_volatility(self, weights: np.ndarray) -> float:
        """Calculate portfolio volatility (standard deviation)."""
        return np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))

    def portfolio_sharpe(self, weights: np.ndarray) -> float:
        """Calculate Sharpe ratio."""
        ret = self.portfolio_return(weights)
        vol = self.portfolio_volatility(weights)
        return (ret - RISK_FREE_RATE) / vol if vol > 0 else 0

    def negative_sharpe(self, weights: np.ndarray) -> float:
        """Negative Sharpe for minimization."""
        return -self.portfolio_sharpe(weights)

    def optimize_max_sharpe(
        self,
        min_weight: float = 0.0,
        max_weight: float = 1.0
    ) -> dict:
        """Find the portfolio with maximum Sharpe ratio."""
        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        bounds = tuple((min_weight, max_weight) for _ in range(self.n_assets))
        initial_weights = np.array([1 / self.n_assets] * self.n_assets)

        result = minimize(
            self.negative_sharpe,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        weights = result.x
        return self._build_portfolio_result(weights)

    def optimize_min_volatility(
        self,
        min_weight: float = 0.0,
        max_weight: float = 1.0
    ) -> dict:
        """Find the minimum volatility portfolio."""
        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        bounds = tuple((min_weight, max_weight) for _ in range(self.n_assets))
        initial_weights = np.array([1 / self.n_assets] * self.n_assets)

        result = minimize(
            self.portfolio_volatility,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        weights = result.x
        return self._build_portfolio_result(weights)

    def optimize_target_return(
        self,
        target_return: float,
        min_weight: float = 0.0,
        max_weight: float = 1.0
    ) -> dict:
        """Find minimum volatility portfolio for a target return."""
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
            {'type': 'eq', 'fun': lambda x: self.portfolio_return(x) - target_return}
        ]
        bounds = tuple((min_weight, max_weight) for _ in range(self.n_assets))
        initial_weights = np.array([1 / self.n_assets] * self.n_assets)

        result = minimize(
            self.portfolio_volatility,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        weights = result.x
        return self._build_portfolio_result(weights)

    def generate_efficient_frontier(
        self,
        n_points: int = 50,
        min_weight: float = 0.0,
        max_weight: float = 1.0
    ) -> list[dict]:
        """Generate points along the efficient frontier."""
        # Get min and max possible returns
        min_vol_portfolio = self.optimize_min_volatility(min_weight, max_weight)
        max_sharpe_portfolio = self.optimize_max_sharpe(min_weight, max_weight)

        # Find return range
        min_return = min_vol_portfolio['expected_return']
        max_return = max(self.mean_returns.max(), max_sharpe_portfolio['expected_return'])

        # Generate target returns
        target_returns = np.linspace(min_return, max_return * 0.95, n_points)

        frontier = []
        for target in target_returns:
            try:
                portfolio = self.optimize_target_return(target, min_weight, max_weight)
                if portfolio['volatility'] < 10:  # Sanity check
                    frontier.append(portfolio)
            except Exception:
                continue

        # Sort by volatility
        frontier.sort(key=lambda x: x['volatility'])

        # Remove dominated points (keep only efficient ones)
        efficient = []
        max_return_seen = float('-inf')
        for point in frontier:
            if point['expected_return'] > max_return_seen:
                efficient.append(point)
                max_return_seen = point['expected_return']

        return efficient

    def get_individual_stock_metrics(self) -> list[dict]:
        """Get risk-return metrics for individual stocks."""
        stocks = []
        for symbol in self.symbols:
            ret = self.mean_returns[symbol]
            vol = np.sqrt(self.cov_matrix.loc[symbol, symbol])
            sharpe = (ret - RISK_FREE_RATE) / vol if vol > 0 else 0

            stocks.append({
                'symbol': symbol,
                'expected_return': round(float(ret), 4),
                'volatility': round(float(vol), 4),
                'sharpe_ratio': round(float(sharpe), 4)
            })

        return stocks

    def _build_portfolio_result(self, weights: np.ndarray) -> dict:
        """Build portfolio result dictionary."""
        # Filter out near-zero weights for cleaner output
        weights_dict = {}
        for symbol, weight in zip(self.symbols, weights):
            if weight > 0.001:  # Only include if > 0.1%
                weights_dict[symbol] = round(float(weight), 4)

        return {
            'weights': weights_dict,
            'expected_return': round(float(self.portfolio_return(weights)), 4),
            'volatility': round(float(self.portfolio_volatility(weights)), 4),
            'sharpe_ratio': round(float(self.portfolio_sharpe(weights)), 4)
        }


def optimize_portfolio(
    symbols: list[str],
    target: str = "max_sharpe",
    target_return: Optional[float] = None,
    min_weight: float = 0.0,
    max_weight: float = 1.0
) -> dict:
    """
    Main optimization function.

    Args:
        symbols: List of stock symbols
        target: Optimization target ("max_sharpe", "min_vol", "target_return")
        target_return: Required if target is "target_return"
        min_weight: Minimum weight per asset
        max_weight: Maximum weight per asset

    Returns:
        Dictionary with optimal_portfolio, efficient_frontier, and individual_stocks
    """
    optimizer = PortfolioOptimizer(symbols)

    # Get optimal portfolio based on target
    if target == "max_sharpe":
        optimal = optimizer.optimize_max_sharpe(min_weight, max_weight)
    elif target == "min_vol":
        optimal = optimizer.optimize_min_volatility(min_weight, max_weight)
    elif target == "target_return" and target_return is not None:
        optimal = optimizer.optimize_target_return(target_return, min_weight, max_weight)
    else:
        optimal = optimizer.optimize_max_sharpe(min_weight, max_weight)

    # Generate efficient frontier
    frontier = optimizer.generate_efficient_frontier(30, min_weight, max_weight)

    # Get individual stock metrics
    individual = optimizer.get_individual_stock_metrics()

    return {
        'optimal_portfolio': optimal,
        'efficient_frontier': frontier,
        'individual_stocks': individual
    }
