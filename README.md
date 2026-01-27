# InvestX

A portfolio analysis web application that helps investors understand risk and expected returns using real market data from Yahoo Finance.

## Features

- **Stock Selection**: Browse and select from 60+ UK stocks across large, mid, and small cap categories
- **Portfolio Builder**: Assign share quantities to build your portfolio with real-time value calculations
- **Real-Time Data**: Fetches historical price data from Yahoo Finance for accurate analysis

### Analysis Types

- **Expected Return & Volatility**: Daily, weekly, and annualized return expectations with risk metrics
- **Historical VaR**: Value at Risk and Expected Shortfall based on actual historical returns
- **Parametric VaR**: Normal distribution-based risk estimates at 95% and 99% confidence levels
- **Monte Carlo Simulation**: 10,000 simulated portfolio outcomes for next-week profit distribution
- **Stress Tests**: Market crash, flash crash, and prolonged downturn scenario analysis
- **Volatility Forecast**: EWMA volatility tracking and trend analysis

### Story-Driven Dashboard

Results are presented in plain English with explanations of what each metric means for your investment decisions.

## Tech Stack

**Backend**: FastAPI, Python, NumPy, Pandas, SciPy, yfinance

**Frontend**: React, Vite, Recharts

## Installation

### Backend

```bash
cd backend
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Running the App

### Start Backend

```bash
cd backend
python main.py
```

The API will be available at http://localhost:8000

### Start Frontend

```bash
cd frontend
npm run dev
```

The app will be available at http://localhost:5173

## API Endpoints

- `GET /api/stocks` - List all stocks with optional filtering by cap category or sector
- `GET /api/stocks/{symbol}` - Get single stock details
- `POST /api/analysis/run` - Run portfolio analysis

### Analysis Request Body

```json
{
  "symbols": ["AZN", "SHEL", "BP"],
  "weights": [0.4, 0.35, 0.25],
  "portfolio_value": 10000,
  "analyses": ["expected_return", "historical_var", "monte_carlo", "stress_tests", "volatility_forecast"]
}
```

## Usage

1. **Select Stocks**: Browse the stock list, filter by market cap, and select up to 10 stocks
2. **Assign Quantities**: Set the number of shares for each stock using +/- controls or type directly
3. **Choose Analysis**: Select which analyses to run (Expected Return, VaR, Monte Carlo, etc.)
4. **View Results**: See your portfolio story with clear explanations of risk and return metrics

## Risk Metrics Explained

- **VaR (Value at Risk)**: The maximum loss expected in 19 out of 20 weeks (95% confidence)
- **Expected Shortfall**: The average loss when things go worse than VaR
- **Volatility**: How much your portfolio value fluctuates day-to-day
- **Maximum Drawdown**: The largest peak-to-trough decline in portfolio value

## Running Analysis Tests

Generate statistics and KPIs for your resume:

```bash
# First, make sure backend is running in one terminal
cd backend
python main.py

# In another terminal, run the test script
cd backend
python run_analysis_tests.py
```

This will output:
- Data coverage statistics
- API performance metrics
- Sample portfolio analysis with real numbers
- Resume-ready KPIs

## Project KPIs

- Analyzed 60+ UK equities across 10+ market sectors
- Processed 250+ trading days of historical data per stock
- Implemented 6 quantitative risk models (VaR, ES, Monte Carlo, etc.)
- Executed 10,000 Monte Carlo simulations per portfolio analysis
- Achieved sub-3 second API response times
- Built real-time data pipeline with Yahoo Finance integration

## License

MIT
