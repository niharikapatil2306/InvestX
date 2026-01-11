from fastapi import APIRouter, HTTPException
from typing import Optional

from services.data_loader import data_loader
from models.schemas import StockInfo, StockMetrics

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("")
async def get_all_stocks(
    category: Optional[str] = None,
    sector: Optional[str] = None
) -> list[dict]:
    """
    Get all available stocks.

    Query params:
        category: Filter by market cap category (large, mid, small)
        sector: Filter by sector
    """
    stocks = data_loader.get_all_stocks()

    if category:
        stocks = [s for s in stocks if s.get('market_cap_category') == category]

    if sector:
        stocks = [s for s in stocks if sector.lower() in s.get('sector', '').lower()]

    return stocks


@router.get("/sectors")
async def get_sectors() -> list[str]:
    """Get list of unique sectors."""
    stocks = data_loader.get_all_stocks()
    sectors = set(s.get('sector', 'Unknown') for s in stocks)
    return sorted(list(sectors))


@router.get("/{symbol}")
async def get_stock(symbol: str) -> dict:
    """Get detailed info for a specific stock."""
    info = data_loader.get_stock_info(symbol)
    if not info:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    # Add detailed company info if available
    detailed = data_loader.get_detailed_info(symbol)
    if detailed:
        info['industry'] = detailed.get('industry')
        info['website'] = detailed.get('website')
        info['description'] = detailed.get('longBusinessSummary')
        info['employees'] = detailed.get('fullTimeEmployees')

    return info


@router.get("/{symbol}/metrics")
async def get_stock_metrics(symbol: str) -> dict:
    """Get financial metrics for a stock."""
    metrics = data_loader.get_stock_metrics(symbol)
    if not metrics:
        raise HTTPException(status_code=404, detail=f"No metrics available for {symbol}")

    return metrics


@router.get("/{symbol}/history")
async def get_stock_history(
    symbol: str,
    period: Optional[str] = "1y"
) -> dict:
    """
    Get historical price data.

    Query params:
        period: Time period (1m, 3m, 6m, 1y, 2y, 5y)
    """
    hist = data_loader.get_historical_data(symbol)
    if hist is None:
        raise HTTPException(status_code=404, detail=f"No historical data for {symbol}")

    # Filter by period
    period_days = {
        '1m': 30,
        '3m': 90,
        '6m': 180,
        '1y': 365,
        '2y': 730,
        '5y': 1825
    }
    days = period_days.get(period, 365)

    hist = hist.tail(days)

    # Convert to list of dicts for JSON serialization
    records = []
    for date, row in hist.iterrows():
        records.append({
            'date': date.strftime('%Y-%m-%d'),
            'open': round(row['Open'], 2),
            'high': round(row['High'], 2),
            'low': round(row['Low'], 2),
            'close': round(row['Close'], 2),
            'volume': int(row['Volume'])
        })

    return {
        'symbol': symbol,
        'period': period,
        'data': records
    }
