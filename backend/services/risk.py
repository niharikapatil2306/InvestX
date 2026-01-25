import numpy as np
from scipy import stats

def calculate_var_historical(returns: np.ndarray, confidence: float = 0.95) -> float:
    """
    Historical Value at Risk (VaR)
    VaR = Percentile(returns, 1 - confidence)
    Returns the maximum expected loss at given confidence level
    """
    return float(np.percentile(returns, (1 - confidence) * 100))

def calculate_var_parametric(mean: float, std: float, confidence: float = 0.95) -> float:
    """
    Parametric VaR (Variance-Covariance Method)
    VaR = mu - z * sigma
    where mu = mean return, z = z-score for confidence, sigma = std dev
    Assumes returns are normally distributed
    """
    z_score = stats.norm.ppf(1 - confidence)
    return float(mean + z_score * std)

def calculate_cvar(returns: np.ndarray, confidence: float = 0.95) -> float:
    """
    Conditional VaR (Expected Shortfall / CVaR)
    CVaR = E[R | R <= VaR]
    Average of all returns below VaR threshold
    More conservative risk measure than VaR
    """
    var = calculate_var_historical(returns, confidence)
    return float(np.mean(returns[returns <= var]))

def calculate_max_drawdown(prices: np.ndarray) -> float:
    """
    Maximum Drawdown = max((Peak - Trough) / Peak)
    Measures the largest peak-to-trough decline
    """
    peak = np.maximum.accumulate(prices)
    drawdown = (peak - prices) / peak
    return float(np.max(drawdown))

def calculate_sortino_ratio(returns: np.ndarray, risk_free_rate: float = 0.04, target: float = 0) -> float:
    """
    Sortino Ratio = (Rp - Rf) / Downside_Deviation
    where Downside_Deviation = sqrt(mean(min(R - target, 0)^2))
    Only penalizes downside volatility, unlike Sharpe
    """
    excess_return = np.mean(returns) - risk_free_rate / 252
    downside_returns = returns[returns < target]
    if len(downside_returns) == 0:
        return float('inf')
    downside_std = np.sqrt(np.mean(downside_returns ** 2))
    if downside_std == 0:
        return float('inf')
    return float(excess_return / downside_std * np.sqrt(252))

def calculate_calmar_ratio(returns: np.ndarray, prices: np.ndarray) -> float:
    """
    Calmar Ratio = Annualized Return / Max Drawdown
    Measures return relative to maximum drawdown risk
    """
    ann_return = np.mean(returns) * 252
    max_dd = calculate_max_drawdown(prices)
    if max_dd == 0:
        return float('inf')
    return float(ann_return / max_dd)

def calculate_beta(asset_returns: np.ndarray, market_returns: np.ndarray) -> float:
    """
    Beta = Cov(Ra, Rm) / Var(Rm)
    Measures systematic risk relative to market
    Beta > 1: more volatile than market
    Beta < 1: less volatile than market
    """
    covariance = np.cov(asset_returns, market_returns)[0, 1]
    market_variance = np.var(market_returns)
    if market_variance == 0:
        return 1.0
    return float(covariance / market_variance)

def calculate_alpha(asset_returns: np.ndarray, market_returns: np.ndarray, risk_free_rate: float = 0.04) -> float:
    """
    Jensen's Alpha = Ra - [Rf + Beta * (Rm - Rf)]
    Measures excess return over CAPM prediction
    Positive alpha = outperforming risk-adjusted benchmark
    """
    beta = calculate_beta(asset_returns, market_returns)
    rf_daily = risk_free_rate / 252
    expected_return = rf_daily + beta * (np.mean(market_returns) - rf_daily)
    actual_return = np.mean(asset_returns)
    return float((actual_return - expected_return) * 252)

def calculate_information_ratio(asset_returns: np.ndarray, benchmark_returns: np.ndarray) -> float:
    """
    Information Ratio = (Ra - Rb) / Tracking_Error
    where Tracking_Error = Std(Ra - Rb)
    Measures active return per unit of active risk
    """
    active_returns = asset_returns - benchmark_returns
    tracking_error = np.std(active_returns)
    if tracking_error == 0:
        return 0.0
    return float(np.mean(active_returns) / tracking_error * np.sqrt(252))

def full_risk_analysis(returns: np.ndarray, prices: np.ndarray, risk_free_rate: float = 0.04) -> dict:
    """Complete risk analysis"""
    ann_return = float(np.mean(returns) * 252)
    ann_volatility = float(np.std(returns) * np.sqrt(252))

    return {
        'annualized_return': ann_return,
        'annualized_volatility': ann_volatility,
        'sharpe_ratio': float((ann_return - risk_free_rate) / ann_volatility) if ann_volatility > 0 else 0,
        'sortino_ratio': calculate_sortino_ratio(returns, risk_free_rate),
        'var_95': calculate_var_historical(returns, 0.95),
        'var_99': calculate_var_historical(returns, 0.99),
        'cvar_95': calculate_cvar(returns, 0.95),
        'max_drawdown': calculate_max_drawdown(prices),
        'calmar_ratio': calculate_calmar_ratio(returns, prices)
    }
