import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

def generate_synthetic_returns(n_stocks: int, n_days: int = 252, seed: int = 42) -> np.ndarray:
    """Generate synthetic daily returns for demonstration"""
    np.random.seed(seed)
    base_returns = np.random.normal(0.0005, 0.02, (n_days, n_stocks))
    market_factor = np.random.normal(0, 0.01, n_days).reshape(-1, 1)
    betas = np.random.uniform(0.5, 1.5, n_stocks)
    returns = base_returns + market_factor * betas
    return returns

def create_features(returns: np.ndarray, lookback: int = 20) -> tuple:
    """
    Create ML features from return series:
    - Rolling mean (momentum)
    - Rolling std (volatility)
    - Rolling Sharpe
    - Lag returns
    """
    n_days, n_stocks = returns.shape
    features_list = []
    targets = []

    for i in range(lookback, n_days - 5):
        window = returns[i-lookback:i]

        features = []
        for stock in range(n_stocks):
            stock_window = window[:, stock]
            roll_mean = np.mean(stock_window)
            roll_std = np.std(stock_window)
            roll_sharpe = roll_mean / roll_std if roll_std > 0 else 0
            lag_1 = returns[i-1, stock]
            lag_5 = np.mean(returns[i-5:i, stock])

            features.extend([roll_mean, roll_std, roll_sharpe, lag_1, lag_5])

        features_list.append(features)
        future_ret = np.mean(returns[i:i+5], axis=0)
        targets.append(future_ret)

    return np.array(features_list), np.array(targets)

def predict_returns_linear(returns: np.ndarray, n_future: int = 5) -> dict:
    """
    Linear Regression for return prediction
    Model: R_t+1 = alpha + beta * Features_t + epsilon
    """
    X, y = create_features(returns)

    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = LinearRegression()
    model.fit(X_train_scaled, y_train)

    predictions = model.predict(X_test_scaled)

    mse = float(np.mean((predictions - y_test) ** 2))
    r2 = float(model.score(X_test_scaled, y_test))

    latest_features = scaler.transform(X[-1:])
    next_pred = model.predict(latest_features)[0]

    return {
        'model': 'Linear Regression',
        'predictions': next_pred.tolist(),
        'mse': mse,
        'r2_score': r2,
        'feature_importance': None
    }

def predict_returns_ridge(returns: np.ndarray, alpha: float = 1.0) -> dict:
    """
    Ridge Regression (L2 regularization)
    Minimizes: ||y - Xw||^2 + alpha * ||w||^2
    Helps prevent overfitting
    """
    X, y = create_features(returns)

    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = Ridge(alpha=alpha)
    model.fit(X_train_scaled, y_train)

    predictions = model.predict(X_test_scaled)

    mse = float(np.mean((predictions - y_test) ** 2))
    r2 = float(model.score(X_test_scaled, y_test))

    latest_features = scaler.transform(X[-1:])
    next_pred = model.predict(latest_features)[0]

    return {
        'model': 'Ridge Regression',
        'predictions': next_pred.tolist(),
        'mse': mse,
        'r2_score': r2,
        'alpha': alpha
    }

def predict_returns_rf(returns: np.ndarray, n_estimators: int = 100) -> dict:
    """
    Random Forest for return prediction
    Ensemble of decision trees with bootstrap aggregating
    """
    X, y = create_features(returns)

    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestRegressor(n_estimators=n_estimators, random_state=42, n_jobs=-1)
    model.fit(X_train_scaled, y_train)

    predictions = model.predict(X_test_scaled)

    mse = float(np.mean((predictions - y_test) ** 2))
    r2 = float(model.score(X_test_scaled, y_test))

    latest_features = scaler.transform(X[-1:])
    next_pred = model.predict(latest_features)[0]

    return {
        'model': 'Random Forest',
        'predictions': next_pred.tolist(),
        'mse': mse,
        'r2_score': r2,
        'n_estimators': n_estimators,
        'feature_importance': model.feature_importances_.tolist()
    }

def monte_carlo_simulation(mean_returns: np.ndarray, cov_matrix: np.ndarray,
                           initial_value: float = 10000, n_days: int = 252,
                           n_simulations: int = 1000) -> dict:
    """
    Monte Carlo Simulation for portfolio value
    Simulates future paths using: dS = mu*dt + sigma*dW
    where dW is Wiener process (random walk)
    """
    np.random.seed(42)
    n_assets = len(mean_returns)

    portfolio_values = np.zeros((n_simulations, n_days))
    portfolio_values[:, 0] = initial_value

    L = np.linalg.cholesky(cov_matrix)

    for sim in range(n_simulations):
        for day in range(1, n_days):
            Z = np.random.normal(0, 1, n_assets)
            correlated_returns = mean_returns + L @ Z
            daily_return = np.mean(correlated_returns)
            portfolio_values[sim, day] = portfolio_values[sim, day-1] * (1 + daily_return)

    final_values = portfolio_values[:, -1]

    return {
        'mean_final_value': float(np.mean(final_values)),
        'std_final_value': float(np.std(final_values)),
        'var_95': float(np.percentile(final_values, 5)),
        'var_99': float(np.percentile(final_values, 1)),
        'best_case': float(np.percentile(final_values, 95)),
        'worst_case': float(np.percentile(final_values, 5)),
        'percentiles': {
            '5th': float(np.percentile(final_values, 5)),
            '25th': float(np.percentile(final_values, 25)),
            '50th': float(np.percentile(final_values, 50)),
            '75th': float(np.percentile(final_values, 75)),
            '95th': float(np.percentile(final_values, 95))
        },
        'sample_paths': portfolio_values[:10].tolist()
    }
