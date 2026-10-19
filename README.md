# InvestX

A portfolio analysis web application that helps investors understand risk and expected returns using real market data from Yahoo Finance.

## Features

- **Stock Selection**: Browse and select from 60+ UK stocks across large, mid, and small cap categories
- **Portfolio Builder**: Assign share quantities to build your portfolio with real-time value calculations
- **Data Pipeline**: Daily job fetches 365 days of prices from Yahoo Finance, validates them and stores them in SQLite

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

**Backend**: FastAPI, Python, NumPy, Pandas, SciPy, yfinance, SQLite

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

## Data Pipeline

`backend/pipeline.py` runs fetch -> validate -> store for every stock in the three CSV lists:

1. **Fetch** 365 calendar days (~252 LSE trading days) per ticker from Yahoo Finance, retrying failed requests up to 3 times
2. **Validate** with `backend/validation.py`:
   - expected columns and types are present (a source format change fails loudly instead of feeding bad data to the models)
   - prices are present and positive, one row per date
   - dates are checked against the LSE calendar (weekdays minus England & Wales bank holidays); rows on non-trading days are dropped, and genuinely missing trading days are logged but **not** forward-filled, since filling would invent zero-return days and understate volatility
   - at least 200 trading days, no more than 5% of trading days missing, latest price no more than 7 days old
   - daily moves over 50% are flagged as possible pence/pounds unit errors
3. **Store** in `data/investx.db` (SQLite). Prices are keyed on (symbol, date) and written with an upsert, so rerunning the pipeline never creates duplicates
4. **Convert** each stock's latest price to pounds (most LSE stocks quote in pence; a few quote in USD or EUR and use the live exchange rate), which the frontend uses to value the portfolio
5. **Record** each ticker's status and each run's outcome (`success`, `partial`, `failed`) in the database and in `logs/pipeline.log`

All tickers use their London listing (`.L` suffix). Without it, Yahoo resolves some symbols to different US companies (for example `BA` is Boeing, not BAE Systems).

Tickers that fail validation stay in the stock list but are greyed out in the UI, with the failure reason shown on hover.

### Running and scheduling

```bash
cd backend
python pipeline.py              # all stocks
python pipeline.py BA.L AZN.L   # specific tickers
```

The API also starts a pipeline run in the background on startup if the last run is more than 20 hours old. To schedule a daily run on Windows (weekdays at 18:00, after the LSE closes):

```powershell
powershell -ExecutionPolicy Bypass -File backend/schedule_pipeline.ps1
```

The script exits with code 1 when more than 20% of tickers fail, so Task Scheduler records the run as failed. `GET /api/pipeline/status` shows the last run and any failing tickers.

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

- `GET /api/stocks` - List all stocks with their data status, with optional filtering by cap category or sector
- `GET /api/stocks/{symbol}` - Get single stock details
- `GET /api/pipeline/status` - Last pipeline run and tickers that failed validation
- `POST /api/analysis/run` - Run portfolio analysis

### Analysis Request Body

```json
{
  "symbols": ["AZN.L", "SHEL.L", "BP.L"],
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

## Tests

### Unit tests (offline)

```bash
cd backend
python -m pytest tests
```

13 tests covering the LSE calendar, every validation rule (empty responses, format changes, negative prices, stale data, missing days, duplicates, extreme moves) and that rerunning the pipeline does not duplicate rows.

### End-to-end analysis report

```bash
# With the backend running in another terminal
cd backend
python run_analysis_tests.py
```

Calls the live API with several real portfolios and prints data coverage, average and slowest response times, every risk metric, and a comparison of the historical, parametric and Monte Carlo VaR.

## Project KPIs

- 61 UK equities tracked (54 currently pass validation; 7 delisted or acquired stocks are flagged and excluded)
- ~252 trading days (365 calendar days) of validated price history per stock
- Risk models: historical, parametric and Monte Carlo VaR, Expected Shortfall (CVaR), stress tests, maximum drawdown, EWMA volatility
- 10,000 correlated Monte Carlo simulations per portfolio analysis
- Sub-second API responses (~0.1s for a 6-stock portfolio with all analyses)

## License

MIT
