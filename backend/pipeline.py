"""
InvestX data pipeline: fetch -> validate -> upsert into SQLite.

    python pipeline.py            # ingest every stock in the CSV lists
    python pipeline.py BA.L AZN.L # ingest specific tickers

Runs daily via Windows Task Scheduler (see schedule_pipeline.ps1), and the API
also triggers it on startup when data is more than a day old.
Exits with code 1 when the run fails, so the scheduler records the failure.
"""
import logging
import sqlite3
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

from validation import DataValidationError, validate_prices

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / 'data' / 'investx.db'
LOG_PATH = BASE_DIR / 'logs' / 'pipeline.log'
STOCK_FILES = ['large_cap.csv', 'mid_cap.csv', 'small_cap.csv']

LOOKBACK_DAYS = 365
MAX_RETRIES = 3
MAX_FAILURE_RATE = 0.2      # run is marked failed if more than 20% of tickers fail
STALE_AFTER_HOURS = 20

log = logging.getLogger('pipeline')

SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    symbol TEXT NOT NULL,
    date   TEXT NOT NULL,
    close  REAL NOT NULL,
    volume REAL,
    PRIMARY KEY (symbol, date)
);
CREATE TABLE IF NOT EXISTS ticker_status (
    symbol       TEXT PRIMARY KEY,
    status       TEXT NOT NULL,
    message      TEXT,
    rows         INTEGER,
    last_date    TEXT,
    missing_days INTEGER,
    currency     TEXT,
    latest_price_gbp REAL,
    checked_at   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at     TEXT NOT NULL,
    finished_at    TEXT,
    status         TEXT,
    n_ok           INTEGER,
    n_failed       INTEGER,
    failed_symbols TEXT
);
"""


class SourceError(Exception):
    pass


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute('PRAGMA journal_mode=WAL')  # lets the API read while the pipeline writes
    conn.executescript(SCHEMA)
    # Add columns introduced after a database was first created
    existing = {row[1] for row in conn.execute('PRAGMA table_info(ticker_status)')}
    for column, col_type in [('currency', 'TEXT'), ('latest_price_gbp', 'REAL')]:
        if column not in existing:
            conn.execute(f'ALTER TABLE ticker_status ADD COLUMN {column} {col_type}')
    return conn


def setup_logging():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
        handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()]
    )


def load_symbols() -> list:
    symbols = []
    for filename in STOCK_FILES:
        filepath = BASE_DIR / filename
        if filepath.exists():
            symbols.extend(pd.read_csv(filepath, sep=';')['Symbol'].tolist())
    return symbols


def fetch(symbol: str) -> tuple:
    """Download the last LOOKBACK_DAYS calendar days, retrying transient API failures.
    Returns (prices, currency) where currency is Yahoo's quote currency, e.g. 'GBp' for pence"""
    start = date.today() - timedelta(days=LOOKBACK_DAYS)
    end = date.today() + timedelta(days=1)  # yfinance end date is exclusive
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start, end=end)
            currency = ticker.history_metadata.get('currency') if not hist.empty else None
            return hist, currency
        except Exception as e:
            log.warning(f"{symbol}: fetch attempt {attempt}/{MAX_RETRIES} failed: {e}")
            time.sleep(2 ** attempt)
    raise SourceError(f"{symbol}: source API failed after {MAX_RETRIES} attempts")


def to_gbp(price: float, currency: str) -> float:
    """Convert a quoted price to pounds. LSE stocks mostly quote in pence ('GBp'), a few in USD or EUR"""
    if currency == 'GBp':
        return price / 100
    if currency == 'GBP':
        return price
    if not currency:
        return None
    try:
        rate = yf.Ticker(f'{currency}GBP=X').history(period='5d')['Close'].iloc[-1]
        return float(price * rate)
    except Exception as e:
        log.warning(f"could not fetch {currency}/GBP exchange rate: {e}")
        return None


def set_status(conn, symbol, status, message, result=None, currency=None, latest_price_gbp=None):
    conn.execute(
        """INSERT INTO ticker_status (symbol, status, message, rows, last_date, missing_days,
                                      currency, latest_price_gbp, checked_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(symbol) DO UPDATE SET status=excluded.status, message=excluded.message,
               rows=excluded.rows, last_date=excluded.last_date, missing_days=excluded.missing_days,
               currency=excluded.currency, latest_price_gbp=excluded.latest_price_gbp,
               checked_at=excluded.checked_at""",
        (symbol, status, message,
         len(result.data) if result else None,
         result.data.index[-1].strftime('%Y-%m-%d') if result else None,
         len(result.missing_days) if result else None,
         currency, latest_price_gbp,
         datetime.now().isoformat(timespec='seconds'))
    )


def upsert_prices(conn, symbol: str, df: pd.DataFrame):
    """One row per (symbol, date): reruns update existing rows instead of duplicating them"""
    rows = [(symbol, d.strftime('%Y-%m-%d'), float(c), float(v))
            for d, c, v in zip(df.index, df['close'], df['volume'])]
    conn.executemany(
        """INSERT INTO prices (symbol, date, close, volume) VALUES (?, ?, ?, ?)
           ON CONFLICT(symbol, date) DO UPDATE SET close=excluded.close, volume=excluded.volume""",
        rows
    )


def ingest_symbol(conn, symbol: str) -> bool:
    try:
        raw, currency = fetch(symbol)
        result = validate_prices(symbol, raw)
    except (SourceError, DataValidationError) as e:
        log.error(str(e))
        with conn:
            set_status(conn, symbol, 'failed', str(e))
        return False

    for warning in result.warnings:
        log.warning(f"{symbol}: {warning}")
    latest_price_gbp = to_gbp(float(result.data['close'].iloc[-1]), currency)
    with conn:  # prices and status are committed together or not at all
        upsert_prices(conn, symbol, result.data)
        set_status(conn, symbol, 'ok', '; '.join(result.warnings) or None, result,
                   currency, latest_price_gbp)
    log.info(f"{symbol}: stored {len(result.data)} trading days up to {result.data.index[-1].date()}")
    return True


def run(symbols: list = None) -> bool:
    started_at = datetime.now().isoformat(timespec='seconds')
    symbols = symbols or load_symbols()
    conn = connect()
    log.info(f"Pipeline run started: {len(symbols)} tickers, {LOOKBACK_DAYS}-day lookback")

    failed = []
    for i, symbol in enumerate(symbols, 1):
        log.info(f"[{i}/{len(symbols)}] {symbol}")
        if not ingest_symbol(conn, symbol):
            failed.append(symbol)
        time.sleep(0.5)  # stay under Yahoo's rate limits

    failure_rate = len(failed) / len(symbols)
    if not failed:
        status = 'success'
    elif failure_rate <= MAX_FAILURE_RATE:
        status = 'partial'
    else:
        status = 'failed'

    with conn:
        conn.execute(
            """INSERT INTO pipeline_runs (started_at, finished_at, status, n_ok, n_failed, failed_symbols)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (started_at, datetime.now().isoformat(timespec='seconds'), status,
             len(symbols) - len(failed), len(failed), ','.join(failed))
        )
    conn.close()

    level = logging.ERROR if status == 'failed' else logging.INFO
    log.log(level, f"Pipeline run {status}: {len(symbols) - len(failed)} ok, {len(failed)} failed {failed}")
    return status != 'failed'


def read_prices(symbol: str) -> pd.DataFrame:
    """Closing prices for the lookback window, oldest first (empty if none stored)"""
    start = (date.today() - timedelta(days=LOOKBACK_DAYS)).isoformat()
    conn = connect()
    df = pd.read_sql_query(
        'SELECT date, close, volume FROM prices WHERE symbol = ? AND date >= ? ORDER BY date',
        conn, params=(symbol, start)
    )
    conn.close()
    return df


def ticker_statuses() -> dict:
    conn = connect()
    rows = conn.execute(
        'SELECT symbol, status, message, last_date, latest_price_gbp FROM ticker_status'
    ).fetchall()
    conn.close()
    return {s: {'status': st, 'message': m, 'last_date': d, 'latest_price_gbp': p}
            for s, st, m, d, p in rows}


def last_run() -> dict:
    conn = connect()
    row = conn.execute(
        """SELECT started_at, finished_at, status, n_ok, n_failed, failed_symbols
           FROM pipeline_runs ORDER BY id DESC LIMIT 1"""
    ).fetchone()
    conn.close()
    if row is None:
        return None
    keys = ['started_at', 'finished_at', 'status', 'n_ok', 'n_failed', 'failed_symbols']
    run_info = dict(zip(keys, row))
    run_info['failed_symbols'] = [s for s in (run_info['failed_symbols'] or '').split(',') if s]
    return run_info


def is_stale() -> bool:
    run_info = last_run()
    if run_info is None or run_info['status'] == 'failed':
        return True
    finished = datetime.fromisoformat(run_info['finished_at'])
    return datetime.now() - finished > timedelta(hours=STALE_AFTER_HOURS)


if __name__ == '__main__':
    setup_logging()
    sys.exit(0 if run(sys.argv[1:] or None) else 1)
