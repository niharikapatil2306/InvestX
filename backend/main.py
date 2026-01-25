from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import yfinance as yf
from scipy import stats
from pathlib import Path
from functools import lru_cache
from datetime import datetime, timedelta

app = FastAPI(title="InvestX API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent.parent

def load_stocks():
    """Load all stock data from CSV files"""
    stocks = []
    for cap, filename in [('large', 'large_cap.csv'), ('mid', 'mid_cap.csv'), ('small', 'small_cap.csv')]:
        filepath = BASE_DIR / filename
        if filepath.exists():
            df = pd.read_csv(filepath, sep=';')
            for _, row in df.iterrows():
                stocks.append({
                    'symbol': row['Symbol'],
                    'name': row['Company_Name'],
                    'market_cap': row['Market_Cap'],
                    'price': row['Price'],
                    'change': row['Change_%'],
                    'sector': row['Sector'],
                    'cap_category': cap
                })
    return stocks

STOCKS = load_stocks()

# Cache for historical data (expires after 1 hour conceptually, but lru_cache doesn't have TTL)
@lru_cache(maxsize=100)
def fetch_historical_data(symbol: str, period: str = "1y") -> dict:
    """Fetch historical data from yfinance"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        if hist.empty:
            return None
        return {
            'dates': hist.index.strftime('%Y-%m-%d').tolist(),
            'prices': hist['Close'].tolist(),
            'volumes': hist['Volume'].tolist() if 'Volume' in hist else []
        }
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None


def calculate_returns(prices: list) -> np.ndarray:
    """Calculate daily returns from prices: r_t = P_t / P_{t-1} - 1"""
    prices = np.array(prices)
    returns = prices[1:] / prices[:-1] - 1
    return returns


def calculate_portfolio_returns(symbols: list, weights: list, period: str = "1y") -> dict:
    """
    Calculate portfolio returns from individual stock returns.
    R_t = sum(w_i * r_{t,i})
    """
    all_prices = {}
    valid_symbols = []
    valid_weights = []
    common_dates = None

    # Fetch data and track which symbols succeeded
    for i, symbol in enumerate(symbols):
        data = fetch_historical_data(symbol, period)
        if data is None:
            print(f"Skipping {symbol} - no data available")
            continue

        df = pd.DataFrame({
            'date': pd.to_datetime(data['dates']),
            'price': data['prices']
        }).set_index('date')

        all_prices[symbol] = df['price']
        valid_symbols.append(symbol)
        valid_weights.append(weights[i])

        if common_dates is None:
            common_dates = set(df.index)
        else:
            common_dates = common_dates.intersection(set(df.index))

    if not valid_symbols:
        return None

    if not common_dates or len(common_dates) < 20:
        return None

    common_dates = sorted(list(common_dates))

    # Align all price series to common dates
    aligned_prices = pd.DataFrame(index=common_dates)
    for symbol in valid_symbols:
        aligned_prices[symbol] = all_prices[symbol].reindex(common_dates)

    # Drop any rows with NaN
    aligned_prices = aligned_prices.dropna()

    if aligned_prices.empty or len(aligned_prices) < 20:
        return None

    # Calculate daily returns for each stock
    returns_df = aligned_prices.pct_change().dropna()

    # Calculate portfolio returns using only valid weights
    valid_weights = np.array(valid_weights)
    valid_weights = valid_weights / valid_weights.sum()  # Normalize weights

    portfolio_returns = (returns_df * valid_weights).sum(axis=1)

    return {
        'dates': returns_df.index.strftime('%Y-%m-%d').tolist(),
        'portfolio_returns': portfolio_returns.tolist(),
        'individual_returns': {col: returns_df[col].tolist() for col in returns_df.columns},
        'prices': {col: aligned_prices[col].tolist() for col in aligned_prices.columns},
        'price_dates': aligned_prices.index.strftime('%Y-%m-%d').tolist(),
        'valid_symbols': valid_symbols,
        'valid_weights': valid_weights.tolist()
    }


class AnalysisRequest(BaseModel):
    symbols: list[str]
    weights: list[float] = None  # If None, equal weights
    portfolio_value: float = 10000  # Default portfolio value
    analyses: list[str]


@app.get("/")
def root():
    return {"message": "InvestX API", "version": "2.0.0"}


@app.get("/api/stocks")
def get_stocks(cap: str = None, sector: str = None):
    """Get all stocks with optional filtering"""
    result = STOCKS
    if cap:
        result = [s for s in result if s['cap_category'] == cap]
    if sector:
        result = [s for s in result if sector.lower() in s['sector'].lower()]
    return {"stocks": result, "count": len(result)}


@app.get("/api/stocks/{symbol}")
def get_stock(symbol: str):
    """Get single stock details"""
    for stock in STOCKS:
        if stock['symbol'].upper() == symbol.upper():
            return stock
    raise HTTPException(status_code=404, detail="Stock not found")


@app.post("/api/analysis/run")
def run_analysis(request: AnalysisRequest):
    """
    Run portfolio analysis with real historical data from yfinance.

    Analyses available:
    - expected_return: Expected return and volatility (daily → weekly)
    - historical_var: Historical VaR and Expected Shortfall
    - parametric_var: Parametric VaR assuming normality
    - monte_carlo: Monte Carlo simulation for next-week profit distribution
    - stress_tests: Stress testing scenarios
    - volatility_forecast: Volatility analysis
    """
    symbols = request.symbols
    n = len(symbols)

    if n < 1:
        raise HTTPException(status_code=400, detail="Need at least 1 stock")

    # Default to equal weights if not provided
    weights = request.weights if request.weights else [1.0 / n] * n
    if len(weights) != n:
        raise HTTPException(status_code=400, detail="Weights must match number of symbols")

    portfolio_value = request.portfolio_value

    # Fetch and calculate portfolio returns
    portfolio_data = calculate_portfolio_returns(symbols, weights, "1y")

    if portfolio_data is None:
        raise HTTPException(status_code=400, detail="Could not fetch historical data for selected stocks. Some stocks may be delisted or have no recent data.")

    # Use valid symbols and weights (stocks that had data)
    valid_symbols = portfolio_data.get('valid_symbols', symbols)
    valid_weights = portfolio_data.get('valid_weights', weights)
    n = len(valid_symbols)

    daily_returns = np.array(portfolio_data['portfolio_returns'])

    # Build warning message if some stocks were skipped
    skipped = [s for s in symbols if s not in valid_symbols]
    warning = f"Note: {', '.join(skipped)} had no data and were excluded." if skipped else None

    results = {
        'symbols': valid_symbols,
        'weights': dict(zip(valid_symbols, valid_weights)),
        'portfolio_value': portfolio_value,
        'price_history': {
            'dates': portfolio_data['price_dates'],
            'prices': portfolio_data['prices']
        }
    }

    if warning:
        results['warning'] = warning

    # 1. Expected Return and Volatility
    if 'expected_return' in request.analyses:
        mu_daily = np.mean(daily_returns)
        sigma_daily = np.std(daily_returns, ddof=1)

        # Convert to weekly (5 trading days)
        mu_weekly = 5 * mu_daily
        sigma_weekly = sigma_daily * np.sqrt(5)

        # Annualized
        mu_annual = 252 * mu_daily
        sigma_annual = sigma_daily * np.sqrt(252)

        expected_weekly_profit = mu_weekly * portfolio_value

        results['expected_return'] = {
            'daily': {
                'mean_return': mu_daily,
                'volatility': sigma_daily
            },
            'weekly': {
                'mean_return': mu_weekly,
                'volatility': sigma_weekly,
                'expected_profit': expected_weekly_profit
            },
            'annual': {
                'mean_return': mu_annual,
                'volatility': sigma_annual,
                'expected_profit': mu_annual * portfolio_value
            },
            'return_distribution': {
                'returns': daily_returns.tolist(),
                'dates': portfolio_data['dates']
            }
        }

    # 2. Historical VaR and Expected Shortfall
    if 'historical_var' in request.analyses:
        # Calculate 5-day (weekly) rolling returns
        weekly_returns = []
        for i in range(len(daily_returns) - 4):
            # Compound 5 daily returns
            week_return = np.prod(1 + daily_returns[i:i+5]) - 1
            weekly_returns.append(week_return)

        weekly_returns = np.array(weekly_returns)

        # Sort ascending for percentile calculation
        sorted_returns = np.sort(weekly_returns)

        # 95% VaR (5th percentile)
        var_95 = np.percentile(weekly_returns, 5)
        var_99 = np.percentile(weekly_returns, 1)

        # Expected Shortfall (average of returns <= VaR)
        es_95 = weekly_returns[weekly_returns <= var_95].mean() if len(weekly_returns[weekly_returns <= var_95]) > 0 else var_95
        es_99 = weekly_returns[weekly_returns <= var_99].mean() if len(weekly_returns[weekly_returns <= var_99]) > 0 else var_99

        results['historical_var'] = {
            'var_95': {
                'return': var_95,
                'loss': -var_95 * portfolio_value
            },
            'var_99': {
                'return': var_99,
                'loss': -var_99 * portfolio_value
            },
            'expected_shortfall_95': {
                'return': es_95,
                'loss': -es_95 * portfolio_value
            },
            'expected_shortfall_99': {
                'return': es_99,
                'loss': -es_99 * portfolio_value
            },
            'weekly_returns_distribution': {
                'returns': weekly_returns.tolist(),
                'histogram': np.histogram(weekly_returns, bins=30)[0].tolist(),
                'bin_edges': np.histogram(weekly_returns, bins=30)[1].tolist()
            }
        }

    # 3. Parametric VaR (Normal Distribution)
    if 'parametric_var' in request.analyses:
        mu_weekly = 5 * np.mean(daily_returns)
        sigma_weekly = np.std(daily_returns, ddof=1) * np.sqrt(5)

        # z-scores for confidence levels
        z_95 = stats.norm.ppf(0.05)  # -1.645
        z_99 = stats.norm.ppf(0.01)  # -2.326

        # Parametric VaR
        var_95_param = mu_weekly + z_95 * sigma_weekly
        var_99_param = mu_weekly + z_99 * sigma_weekly

        results['parametric_var'] = {
            'var_95': {
                'return': var_95_param,
                'loss': -var_95_param * portfolio_value,
                'z_score': z_95
            },
            'var_99': {
                'return': var_99_param,
                'loss': -var_99_param * portfolio_value,
                'z_score': z_99
            },
            'parameters': {
                'weekly_mean': mu_weekly,
                'weekly_std': sigma_weekly
            }
        }

    # 4. Monte Carlo Simulation
    if 'monte_carlo' in request.analyses:
        n_simulations = 10000
        n_days = 5  # One week

        mu_daily = np.mean(daily_returns)
        sigma_daily = np.std(daily_returns, ddof=1)

        # If multiple stocks, use covariance matrix
        if n > 1:
            individual_returns = np.array([portfolio_data['individual_returns'][s] for s in valid_symbols if s in portfolio_data['individual_returns']])
            if individual_returns.shape[0] == n:
                cov_matrix = np.cov(individual_returns)
                mean_returns = np.mean(individual_returns, axis=1)

                # Simulate multivariate normal returns
                simulated_portfolio_returns = []
                for _ in range(n_simulations):
                    total_return = 0
                    for day in range(n_days):
                        daily_sim = np.random.multivariate_normal(mean_returns, cov_matrix)
                        portfolio_daily = np.dot(valid_weights, daily_sim)
                        total_return = (1 + total_return) * (1 + portfolio_daily) - 1
                    simulated_portfolio_returns.append(total_return)
            else:
                # Fallback to univariate
                simulated_portfolio_returns = []
                for _ in range(n_simulations):
                    daily_sims = np.random.normal(mu_daily, sigma_daily, n_days)
                    week_return = np.prod(1 + daily_sims) - 1
                    simulated_portfolio_returns.append(week_return)
        else:
            simulated_portfolio_returns = []
            for _ in range(n_simulations):
                daily_sims = np.random.normal(mu_daily, sigma_daily, n_days)
                week_return = np.prod(1 + daily_sims) - 1
                simulated_portfolio_returns.append(week_return)

        simulated_portfolio_returns = np.array(simulated_portfolio_returns)
        simulated_profits = simulated_portfolio_returns * portfolio_value

        # Calculate percentiles
        percentiles = {
            '5th': np.percentile(simulated_profits, 5),
            '25th': np.percentile(simulated_profits, 25),
            '50th': np.percentile(simulated_profits, 50),
            '75th': np.percentile(simulated_profits, 75),
            '95th': np.percentile(simulated_profits, 95)
        }

        # Sample paths for visualization (simulate 100 paths over 5 days)
        sample_paths = []
        for _ in range(100):
            path = [portfolio_value]
            value = portfolio_value
            for day in range(n_days):
                daily_return = np.random.normal(mu_daily, sigma_daily)
                value = value * (1 + daily_return)
                path.append(value)
            sample_paths.append(path)

        results['monte_carlo'] = {
            'n_simulations': n_simulations,
            'n_days': n_days,
            'statistics': {
                'mean': np.mean(simulated_profits),
                'median': np.median(simulated_profits),
                'std': np.std(simulated_profits),
                'min': np.min(simulated_profits),
                'max': np.max(simulated_profits)
            },
            'percentiles': percentiles,
            'distribution': {
                'profits': simulated_profits.tolist()[:1000],  # Limit for transfer
                'histogram': np.histogram(simulated_profits, bins=50)[0].tolist(),
                'bin_edges': np.histogram(simulated_profits, bins=50)[1].tolist()
            },
            'sample_paths': sample_paths[:20]  # 20 sample paths for chart
        }

    # 5. Stress Tests
    if 'stress_tests' in request.analyses:
        # Calculate portfolio beta using market proxy (if available)
        # For simplicity, use historical worst cases
        sorted_daily = np.sort(daily_returns)

        results['stress_tests'] = {
            'scenarios': {
                'market_crash_20pct': {
                    'portfolio_loss': -0.20 * portfolio_value,
                    'description': '20% market decline'
                },
                'flash_crash': {
                    'portfolio_loss': sorted_daily[0] * portfolio_value,
                    'description': f'Worst historical day: {sorted_daily[0]*100:.2f}%'
                },
                'bad_week': {
                    'portfolio_loss': np.percentile(daily_returns, 1) * 5 * portfolio_value,
                    'description': 'Sustained 1st percentile daily returns for a week'
                },
                'volatility_spike': {
                    'new_var_95': np.percentile(daily_returns, 5) * 2 * portfolio_value,
                    'description': 'Volatility doubles'
                }
            },
            'historical_drawdowns': {
                'max_drawdown': calculate_max_drawdown(daily_returns),
                'worst_days': sorted_daily[:5].tolist()
            }
        }

    # 6. Volatility Forecast
    if 'volatility_forecast' in request.analyses:
        # Simple EWMA volatility
        lambda_param = 0.94
        variance = [daily_returns[0]**2]
        for r in daily_returns[1:]:
            var = lambda_param * variance[-1] + (1 - lambda_param) * r**2
            variance.append(var)

        ewma_volatility = np.sqrt(np.array(variance))

        # Rolling 20-day volatility
        rolling_vol = pd.Series(daily_returns).rolling(20).std().dropna().tolist()

        results['volatility_forecast'] = {
            'current_daily_vol': np.std(daily_returns[-20:], ddof=1),
            'current_annual_vol': np.std(daily_returns[-20:], ddof=1) * np.sqrt(252),
            'ewma_volatility': ewma_volatility[-20:].tolist(),
            'rolling_20d_volatility': rolling_vol[-60:] if len(rolling_vol) > 60 else rolling_vol,
            'volatility_trend': 'increasing' if ewma_volatility[-1] > ewma_volatility[-20] else 'decreasing'
        }

    return results


def calculate_max_drawdown(returns: np.ndarray) -> float:
    """Calculate maximum drawdown from returns"""
    cumulative = np.cumprod(1 + returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - running_max) / running_max
    return float(np.min(drawdown))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
