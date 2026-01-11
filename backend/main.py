from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import stocks, portfolio, risk
from services.data_loader import data_loader


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    print("Loading stock data...")
    data_loader.load_all()
    stocks_count = len(data_loader.get_all_stocks())
    print(f"Loaded {stocks_count} stocks")
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    title="InvestX API",
    description="Portfolio Optimization and Risk Analysis API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stocks.router)
app.include_router(portfolio.router)
app.include_router(risk.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "name": "InvestX API",
        "version": "1.0.0"
    }


@app.get("/api/health")
async def health():
    """Health check with data status."""
    stocks = data_loader.get_all_stocks()
    return {
        "status": "healthy",
        "stocks_loaded": len(stocks),
        "categories": {
            "large": len([s for s in stocks if s.get('market_cap_category') == 'large']),
            "mid": len([s for s in stocks if s.get('market_cap_category') == 'mid']),
            "small": len([s for s in stocks if s.get('market_cap_category') == 'small'])
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
