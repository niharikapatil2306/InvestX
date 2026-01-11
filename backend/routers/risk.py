from fastapi import APIRouter, HTTPException
from typing import Optional

from models.schemas import RiskAnalyzeRequest, RiskMetrics, CorrelationMatrix
from services.risk_engine import analyze_portfolio_risk, calculate_correlation_matrix

router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.post("/analyze")
async def analyze_risk(request: RiskAnalyzeRequest) -> dict:
    """
    Analyze risk metrics for a portfolio.

    Request body:
        weights: Dictionary mapping symbols to weights

    Returns:
        volatility: Annualized volatility
        var_95: 95% Value at Risk
        var_99: 99% Value at Risk
        cvar_95: 95% Conditional VaR (Expected Shortfall)
        max_drawdown: Maximum drawdown
        sharpe_ratio: Sharpe ratio
        sortino_ratio: Sortino ratio
    """
    if not request.weights:
        raise HTTPException(status_code=400, detail="Weights required")

    if len(request.weights) < 1:
        raise HTTPException(status_code=400, detail="At least 1 stock required")

    try:
        metrics = analyze_portfolio_risk(request.weights)
        return metrics
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {str(e)}")


@router.get("/correlation")
async def get_correlation(symbols: str) -> dict:
    """
    Get correlation matrix for selected stocks.

    Query params:
        symbols: Comma-separated list of stock symbols

    Returns:
        symbols: List of symbols
        matrix: 2D correlation matrix
    """
    symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]

    if len(symbol_list) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 symbols required for correlation"
        )

    if len(symbol_list) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maximum 20 symbols for correlation matrix"
        )

    try:
        result = calculate_correlation_matrix(symbol_list)
        if not result['symbols']:
            raise HTTPException(
                status_code=400,
                detail="No data available for the given symbols"
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Correlation calculation failed: {str(e)}")


@router.get("/var-breakdown")
async def get_var_breakdown(symbols: str, weights: Optional[str] = None) -> dict:
    """
    Get VaR breakdown by component.

    Query params:
        symbols: Comma-separated list of stock symbols
        weights: Comma-separated list of weights (optional, defaults to equal)

    Returns:
        total_var: Portfolio VaR
        components: VaR contribution by each stock
    """
    symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]

    if weights:
        weight_list = [float(w.strip()) for w in weights.split(',')]
        if len(weight_list) != len(symbol_list):
            raise HTTPException(
                status_code=400,
                detail="Number of weights must match number of symbols"
            )
        weight_dict = dict(zip(symbol_list, weight_list))
    else:
        # Equal weights
        w = 1.0 / len(symbol_list)
        weight_dict = {s: w for s in symbol_list}

    try:
        # Get total portfolio VaR
        total_metrics = analyze_portfolio_risk(weight_dict)

        # Get individual VaRs
        components = []
        for symbol in symbol_list:
            individual_metrics = analyze_portfolio_risk({symbol: 1.0})
            components.append({
                'symbol': symbol,
                'weight': weight_dict[symbol],
                'individual_var_95': individual_metrics['var_95'],
                'contribution': weight_dict[symbol] * individual_metrics['var_95']
            })

        return {
            'total_var_95': total_metrics['var_95'],
            'total_var_99': total_metrics['var_99'],
            'components': components
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VaR breakdown failed: {str(e)}")
