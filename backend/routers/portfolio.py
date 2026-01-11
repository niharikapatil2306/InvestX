from fastapi import APIRouter, HTTPException

from models.schemas import PortfolioOptimizeRequest, PortfolioOptimizeResponse
from services.optimizer import optimize_portfolio

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.post("/optimize")
async def optimize(request: PortfolioOptimizeRequest) -> dict:
    """
    Optimize portfolio allocation.

    Request body:
        stocks: List of stock symbols
        target: Optimization target (max_sharpe, min_vol, target_return)
        target_return: Required if target is target_return
        max_weight: Maximum weight per asset (default 1.0)
        min_weight: Minimum weight per asset (default 0.0)

    Returns:
        optimal_portfolio: Optimized weights and metrics
        efficient_frontier: Points along the efficient frontier
        individual_stocks: Risk-return metrics for each stock
    """
    if len(request.stocks) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 stocks required for optimization"
        )

    if len(request.stocks) > 30:
        raise HTTPException(
            status_code=400,
            detail="Maximum 30 stocks allowed for optimization"
        )

    try:
        result = optimize_portfolio(
            symbols=request.stocks,
            target=request.target,
            target_return=request.target_return,
            min_weight=request.min_weight,
            max_weight=request.max_weight
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.post("/equal-weight")
async def equal_weight(request: dict) -> dict:
    """
    Create an equal-weighted portfolio.

    Request body:
        stocks: List of stock symbols

    Returns:
        weights: Equal weights for each stock
        metrics: Portfolio metrics
    """
    stocks = request.get('stocks', [])

    if len(stocks) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 stocks required"
        )

    # Create equal weights
    weight = 1.0 / len(stocks)
    weights = {s: round(weight, 4) for s in stocks}

    try:
        # Calculate metrics for equal weight portfolio
        from services.risk_engine import RiskEngine
        from services.data_loader import data_loader
        from config import TRADING_DAYS
        import numpy as np

        engine = RiskEngine(weights)
        metrics = engine.get_all_metrics()

        # Calculate expected return from the returns data
        returns_matrix = data_loader.get_returns_matrix(stocks)
        if not returns_matrix.empty:
            weights_array = np.array([weights[s] for s in stocks if s in returns_matrix.columns])
            mean_returns = returns_matrix.mean() * TRADING_DAYS
            expected_return = float(np.dot(weights_array, mean_returns[[s for s in stocks if s in returns_matrix.columns]]))
        else:
            expected_return = 0.0

        return {
            'weights': weights,
            'expected_return': round(expected_return, 4),
            'volatility': metrics['volatility'],
            'sharpe_ratio': metrics['sharpe_ratio']
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
