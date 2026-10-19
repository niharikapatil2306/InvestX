"""Offline unit tests for data validation and pipeline storage (no network needed).

Run from the backend folder:  python -m pytest tests
"""
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import pipeline
from validation import DataValidationError, lse_trading_days, validate_prices

TODAY = date(2026, 10, 16)


def make_prices(days=None, close=None):
    """A clean year of LSE trading days, shaped like a yfinance response"""
    days = days if days is not None else lse_trading_days('2025-10-17', '2026-10-16')
    close = close if close is not None else np.linspace(100, 120, len(days))
    index = pd.DatetimeIndex(days).tz_localize('Europe/London')
    return pd.DataFrame({'Open': close, 'Close': close, 'Volume': 1000}, index=index)


# Calendar

def test_calendar_excludes_weekends_and_bank_holidays():
    days = lse_trading_days('2025-12-22', '2026-01-02')
    assert pd.Timestamp('2025-12-25') not in days   # Christmas
    assert pd.Timestamp('2025-12-26') not in days   # Boxing Day
    assert pd.Timestamp('2026-01-01') not in days   # New Year's Day
    assert pd.Timestamp('2025-12-27') not in days   # Saturday
    assert pd.Timestamp('2025-12-24') in days


# Happy path

def test_clean_data_passes():
    result = validate_prices('TEST.L', make_prices(), today=TODAY)
    assert result.warnings == []
    assert result.missing_days == []
    assert list(result.data.columns) == ['close', 'volume']
    assert result.data.index.tz is None


# Hard failures

def test_empty_response_fails():
    with pytest.raises(DataValidationError, match='no rows'):
        validate_prices('DEAD.L', pd.DataFrame(), today=TODAY)


def test_format_change_fails_loudly():
    raw = make_prices().rename(columns={'Close': 'Last'})
    with pytest.raises(DataValidationError, match='missing expected columns'):
        validate_prices('TEST.L', raw, today=TODAY)


def test_negative_price_fails():
    raw = make_prices()
    raw.iloc[10, raw.columns.get_loc('Close')] = -5
    with pytest.raises(DataValidationError, match='negative'):
        validate_prices('TEST.L', raw, today=TODAY)


def test_too_little_history_fails():
    with pytest.raises(DataValidationError, match='trading days'):
        validate_prices('TEST.L', make_prices().iloc[-50:], today=TODAY)


def test_stale_data_fails():
    raw = make_prices(lse_trading_days('2025-06-01', '2026-06-01'))
    with pytest.raises(DataValidationError, match='days old'):
        validate_prices('TEST.L', raw, today=TODAY)


def test_too_many_missing_days_fails():
    days = lse_trading_days('2025-10-17', '2026-10-16')
    with pytest.raises(DataValidationError, match='missing'):
        validate_prices('TEST.L', make_prices(days.delete(range(100, 120))), today=TODAY)


# Soft issues: cleaned and reported, not fatal

def test_few_missing_days_are_flagged_not_filled():
    days = lse_trading_days('2025-10-17', '2026-10-16')
    gappy = days.delete([50, 51, 52])
    result = validate_prices('TEST.L', make_prices(gappy), today=TODAY)
    assert result.missing_days == list(days[[50, 51, 52]])
    assert len(result.data) == len(gappy)               # gaps not forward-filled
    assert any('missing' in w for w in result.warnings)


def test_weekend_rows_are_dropped():
    days = lse_trading_days('2025-10-17', '2026-10-16').append(pd.DatetimeIndex(['2026-10-10']))
    result = validate_prices('TEST.L', make_prices(days.sort_values()), today=TODAY)
    assert pd.Timestamp('2026-10-10') not in result.data.index
    assert any('non-trading' in w for w in result.warnings)


def test_duplicate_dates_are_dropped():
    raw = make_prices()
    raw = pd.concat([raw, raw.iloc[[5]]])
    result = validate_prices('TEST.L', raw, today=TODAY)
    assert not result.data.index.duplicated().any()


def test_extreme_move_is_flagged():
    raw = make_prices()
    raw.iloc[100:, raw.columns.get_loc('Close')] *= 100   # pence/pounds unit switch
    result = validate_prices('TEST.L', raw, today=TODAY)
    assert any('unit errors' in w for w in result.warnings)


# Currency

def test_pence_and_pounds_convert_to_gbp():
    assert pipeline.to_gbp(12400.0, 'GBp') == pytest.approx(124.0)
    assert pipeline.to_gbp(5.5, 'GBP') == 5.5
    assert pipeline.to_gbp(10.0, None) is None


# Storage

def test_rerun_does_not_duplicate_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, 'DB_PATH', tmp_path / 'test.db')
    data = validate_prices('TEST.L', make_prices(), today=TODAY).data
    conn = pipeline.connect()

    pipeline.upsert_prices(conn, 'TEST.L', data)
    pipeline.upsert_prices(conn, 'TEST.L', data * 1.01)   # second run with revised prices

    count, = conn.execute("SELECT COUNT(*) FROM prices WHERE symbol = 'TEST.L'").fetchone()
    latest, = conn.execute("SELECT close FROM prices WHERE symbol = 'TEST.L' ORDER BY date DESC LIMIT 1").fetchone()
    assert count == len(data)
    assert latest == pytest.approx(120 * 1.01)
