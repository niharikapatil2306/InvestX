# InvestX

A web application for investment portfolio optimization with real-time predictions and risk-adjusted suggestions.

## Features

- **Stock Selection**: Browse and select from 60+ UK stocks (large, mid, small cap)
- **Portfolio Optimization**: Mean-variance optimization using Markowitz theory
  - Maximum Sharpe Ratio optimization
  - Minimum Volatility portfolio
  - Target Return optimization
- **Efficient Frontier**: Interactive visualization of risk-return tradeoffs
- **Risk Analysis**:
  - Volatility (annualized standard deviation)
  - Value at Risk (VaR) at 95% and 99% confidence
  - Conditional VaR (Expected Shortfall)
  - Maximum Drawdown
  - Sharpe and Sortino Ratios
- **Correlation Matrix**: Visualize stock correlations for diversification

## Tech Stack

**Backend**: FastAPI, Python, NumPy, Pandas, SciPy
**Frontend**: React, Vite, Tailwind CSS, Recharts

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
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

### Start Frontend

```bash
cd frontend
npm run dev
```

The app will be available at http://localhost:5173

## API Endpoints

- `GET /api/stocks` - List all stocks
- `GET /api/stocks/{symbol}` - Get stock details
- `GET /api/stocks/{symbol}/metrics` - Get stock metrics
- `POST /api/portfolio/optimize` - Optimize portfolio
- `POST /api/risk/analyze` - Analyze portfolio risk
- `GET /api/risk/correlation?symbols=A,B,C` - Get correlation matrix

## Usage

1. Select stocks from the stock list (filter by market cap or search)
2. Choose optimization target (Max Sharpe, Min Volatility, or Target Return)
3. Set weight constraints if needed
4. Click "Optimize Portfolio"
5. View results: optimal weights, efficient frontier, risk metrics, correlations

## License

MIT
