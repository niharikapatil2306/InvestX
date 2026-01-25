import numpy as np
from scipy.optimize import minimize

def calculate_portfolio_return(weights: np.ndarray, returns: np.ndarray) -> float:
    """
    Expected Portfolio Return = Sum(wi * ri)
    where wi = weight of asset i, ri = expected return of asset i
    """
    return np.sum(weights * returns)

def calculate_portfolio_volatility(weights: np.ndarray, cov_matrix: np.ndarray) -> float:
    """
    Portfolio Volatility (Std Dev) = sqrt(w^T * Cov * w)
    where w = weight vector, Cov = covariance matrix
    """
    return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

def calculate_sharpe_ratio(portfolio_return: float, portfolio_volatility: float, risk_free_rate: float = 0.04) -> float:
    """
    Sharpe Ratio = (Rp - Rf) / Sigma_p
    where Rp = portfolio return, Rf = risk-free rate, Sigma_p = portfolio volatility
    """
    if portfolio_volatility == 0:
        return 0
    return (portfolio_return - risk_free_rate) / portfolio_volatility

def negative_sharpe(weights: np.ndarray, returns: np.ndarray, cov_matrix: np.ndarray, risk_free_rate: float) -> float:
    """Negative Sharpe for minimization"""
    p_ret = calculate_portfolio_return(weights, returns)
    p_vol = calculate_portfolio_volatility(weights, cov_matrix)
    return -calculate_sharpe_ratio(p_ret, p_vol, risk_free_rate)

def optimize_max_sharpe(returns: np.ndarray, cov_matrix: np.ndarray, risk_free_rate: float = 0.04) -> dict:
    """Optimize portfolio for maximum Sharpe Ratio"""
    n_assets = len(returns)
    init_weights = np.ones(n_assets) / n_assets
    bounds = tuple((0, 1) for _ in range(n_assets))
    constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}

    result = minimize(
        negative_sharpe,
        init_weights,
        args=(returns, cov_matrix, risk_free_rate),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    opt_weights = result.x
    opt_return = calculate_portfolio_return(opt_weights, returns)
    opt_volatility = calculate_portfolio_volatility(opt_weights, cov_matrix)
    opt_sharpe = calculate_sharpe_ratio(opt_return, opt_volatility, risk_free_rate)

    return {
        'weights': opt_weights.tolist(),
        'expected_return': float(opt_return),
        'volatility': float(opt_volatility),
        'sharpe_ratio': float(opt_sharpe)
    }

def optimize_min_volatility(returns: np.ndarray, cov_matrix: np.ndarray) -> dict:
    """Optimize portfolio for minimum volatility"""
    n_assets = len(returns)
    init_weights = np.ones(n_assets) / n_assets
    bounds = tuple((0, 1) for _ in range(n_assets))
    constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}

    result = minimize(
        lambda w: calculate_portfolio_volatility(w, cov_matrix),
        init_weights,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    opt_weights = result.x
    opt_return = calculate_portfolio_return(opt_weights, returns)
    opt_volatility = calculate_portfolio_volatility(opt_weights, cov_matrix)
    opt_sharpe = calculate_sharpe_ratio(opt_return, opt_volatility)

    return {
        'weights': opt_weights.tolist(),
        'expected_return': float(opt_return),
        'volatility': float(opt_volatility),
        'sharpe_ratio': float(opt_sharpe)
    }

def generate_efficient_frontier(returns: np.ndarray, cov_matrix: np.ndarray, n_points: int = 50) -> list:
    """Generate efficient frontier points"""
    min_vol_port = optimize_min_volatility(returns, cov_matrix)
    max_sharpe_port = optimize_max_sharpe(returns, cov_matrix)

    min_ret = min_vol_port['expected_return']
    max_ret = max(returns) * 0.95

    target_returns = np.linspace(min_ret, max_ret, n_points)
    frontier = []

    n_assets = len(returns)

    for target in target_returns:
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},
            {'type': 'eq', 'fun': lambda w, t=target: calculate_portfolio_return(w, returns) - t}
        ]
        bounds = tuple((0, 1) for _ in range(n_assets))
        init_weights = np.ones(n_assets) / n_assets

        result = minimize(
            lambda w: calculate_portfolio_volatility(w, cov_matrix),
            init_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        if result.success:
            vol = calculate_portfolio_volatility(result.x, cov_matrix)
            frontier.append({
                'return': float(target),
                'volatility': float(vol),
                'sharpe': float(calculate_sharpe_ratio(target, vol))
            })

    return frontier
