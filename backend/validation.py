"""
Data quality checks run on every price series before it is stored.

Hard failures raise DataValidationError so bad data never reaches the
risk models. Softer issues are returned as warnings and logged.
"""
from dataclasses import dataclass, field
from datetime import date

import holidays
import pandas as pd

REQUIRED_COLUMNS = ['Close', 'Volume']
MIN_ROWS = 200              # 365 calendar days is ~252 LSE trading days
MAX_STALENESS_DAYS = 7      # latest price must be recent
MAX_MISSING_PCT = 0.05      # fail if more than 5% of trading days are missing
MAX_DAILY_MOVE = 0.5        # a 50%+ daily move is flagged for review


class DataValidationError(Exception):
    pass


@dataclass
class ValidationResult:
    symbol: str
    data: pd.DataFrame          # index: trading date, columns: close, volume
    missing_days: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


def lse_trading_days(start, end) -> pd.DatetimeIndex:
    """Weekdays between start and end, minus England & Wales bank holidays (LSE closures)"""
    days = pd.bdate_range(start, end)
    bank_holidays = holidays.UK(subdiv='ENG', years=range(days[0].year, days[-1].year + 1))
    return days[~days.isin(pd.to_datetime(list(bank_holidays.keys())))]


def validate_prices(symbol: str, raw: pd.DataFrame, today: date = None) -> ValidationResult:
    today = today or date.today()
    warnings = []

    # 1. Schema: the source must return the columns and types we expect
    if raw is None or raw.empty:
        raise DataValidationError(f"{symbol}: source returned no rows (delisted or wrong ticker?)")
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in raw.columns]
    if missing_cols:
        raise DataValidationError(f"{symbol}: missing expected columns {missing_cols}, got {list(raw.columns)}")
    if not isinstance(raw.index, pd.DatetimeIndex):
        raise DataValidationError(f"{symbol}: expected a date index, got {type(raw.index).__name__}")

    df = raw[REQUIRED_COLUMNS].copy()
    df.columns = ['close', 'volume']
    index = df.index.tz_localize(None) if df.index.tz is not None else df.index
    df.index = index.normalize()
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)

    # 2. Values: prices must be present and positive
    n_null = int(df['close'].isna().sum())
    if n_null:
        warnings.append(f"dropped {n_null} rows with no closing price")
        df = df.dropna(subset=['close'])
    if (df['close'] <= 0).any():
        raise DataValidationError(f"{symbol}: found zero or negative prices")

    # 3. Uniqueness: one row per trading date
    n_dupes = int(df.index.duplicated().sum())
    if n_dupes:
        warnings.append(f"dropped {n_dupes} duplicate dates")
        df = df[~df.index.duplicated(keep='last')]
    df = df.sort_index()

    # 4. Calendar: drop rows on non-trading days, then find genuinely missing trading days
    calendar = lse_trading_days(df.index[0], df.index[-1])
    off_calendar = df.index.difference(calendar)
    if len(off_calendar):
        warnings.append(f"dropped {len(off_calendar)} rows on non-trading days")
        df = df[df.index.isin(calendar)]

    if len(df) < MIN_ROWS:
        raise DataValidationError(f"{symbol}: only {len(df)} trading days, need at least {MIN_ROWS}")

    staleness = (pd.Timestamp(today) - df.index[-1]).days
    if staleness > MAX_STALENESS_DAYS:
        raise DataValidationError(f"{symbol}: latest price is {staleness} days old ({df.index[-1].date()}), stock may be suspended")

    # Missing days are not forward-filled: filling would invent zero-return days and understate volatility
    missing = calendar.difference(df.index)
    if len(missing) / len(calendar) > MAX_MISSING_PCT:
        raise DataValidationError(f"{symbol}: {len(missing)} of {len(calendar)} trading days missing")
    if len(missing):
        warnings.append(f"{len(missing)} trading days missing (left as gaps, not filled)")

    # 5. Sanity: flag extreme moves (often a pence/pounds unit error at the source)
    big_moves = df['close'].pct_change().abs() > MAX_DAILY_MOVE
    if big_moves.any():
        days = ', '.join(d.strftime('%Y-%m-%d') for d in df.index[big_moves])
        warnings.append(f"daily move over {MAX_DAILY_MOVE:.0%} on {days}, check for unit errors")

    return ValidationResult(symbol=symbol, data=df, missing_days=list(missing), warnings=warnings)
