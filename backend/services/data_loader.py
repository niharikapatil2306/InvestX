import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional


from config import (
    LARGE_CAP_DIR, MID_CAP_DIR, SMALL_CAP_DIR,
    LARGE_CAP_CSV, MID_CAP_CSV, SMALL_CAP_CSV, TRADING_DAYS
)


class DataLoader:
    """Loads and caches stock data from CSV files."""

    def __init__(self):
        self._stock_list: dict = {}
        self._historical_data: dict[str, pd.DataFrame] = {}
        self._returns_data: dict[str, pd.Series] = {}
        self._info_data: dict[str, dict] = {}
        self._loaded = False

    def load_all(self) -> None:
        """Load all stock data into memory."""
        if self._loaded:
            return

        # Load stock lists from CSVs
        self._load_stock_lists()

        # Load historical data for each stock
        self._load_historical_data()

        self._loaded = True

    def _load_stock_lists(self) -> None:
        """Load stock info from the main CSV files."""
        for csv_path, category in [
            (LARGE_CAP_CSV, "large"),
            (MID_CAP_CSV, "mid"),
            (SMALL_CAP_CSV, "small")
        ]:
            if not csv_path.exists():
                print(f"CSV file not found: {csv_path}")
                continue

            df = pd.read_csv(csv_path, sep=';')
            for _, row in df.iterrows():
                symbol = row['Symbol']
                self._stock_list[symbol] = {
                    'symbol': symbol,
                    'name': row['Company_Name'],
                    'market_cap': row['Market_Cap'],
                    'market_cap_category': category,
                    'price': self._parse_price(row['Price']),
                    'change_pct': self._parse_change(row['Change_%']),
                    'sector': row['Sector'],
                    # 'analyst_rating': row.get('Analyst_Rating', None)
                }

    def _parse_price(self, price_str: str) -> Optional[float]:
        """Parse price string like '10,336 GBX' to float."""
        try:
            price = str(price_str).replace(' GBX', '').strip()
            return float(price)
        except (ValueError, AttributeError):
            return None

    def _parse_change(self, change_str: str) -> Optional[float]:
        """Parse change string like '+1.29%' to float."""
        try:
            change = str(change_str).replace('%', '').replace('+', '')
            return float(change)
        except (ValueError, AttributeError):
            return None

    def _load_historical_data(self) -> None:
        """Load historical price data for all stocks."""
        for data_dir, category in [
            (LARGE_CAP_DIR, "large"),
            (MID_CAP_DIR, "mid"),
            (SMALL_CAP_DIR, "small")
        ]:
            if not data_dir.exists():
                continue

            for stock_dir in data_dir.iterdir():
                if not stock_dir.is_dir():
                    continue

                folder_symbol = stock_dir.name
                hist_file = stock_dir / f"{folder_symbol}_historical.csv"

                if hist_file.exists():
                    try:
                        df = pd.read_csv(hist_file, index_col=0, parse_dates=True)
                        if 'Close' in df.columns and len(df) > 0:
                            # Clean the data
                            df = df.sort_index()
                            df = df[~df.index.duplicated(keep='first')]

                            # Try to match with CSV symbol (strip .L suffix)
                            base_symbol = folder_symbol.replace('.L', '')

                            # Use base_symbol if it exists in stock list, otherwise use folder_symbol
                            if base_symbol in self._stock_list:
                                # Update existing stock entry with folder symbol reference
                                stock_info = self._stock_list[base_symbol]
                                # Store historical data under folder_symbol for consistency
                                self._historical_data[folder_symbol] = df
                                self._returns_data[folder_symbol] = df['Close'].pct_change().dropna()
                                # Also store under base_symbol for lookup
                                self._historical_data[base_symbol] = df
                                self._returns_data[base_symbol] = df['Close'].pct_change().dropna()
                                # Update stock info to use folder_symbol
                                self._stock_list[base_symbol]['symbol'] = folder_symbol
                                # Also add entry for folder_symbol pointing to same data
                                self._stock_list[folder_symbol] = self._stock_list[base_symbol].copy()
                            else:
                                # No match in CSV, create new entry
                                self._historical_data[folder_symbol] = df
                                self._returns_data[folder_symbol] = df['Close'].pct_change().dropna()

                                if folder_symbol not in self._stock_list:
                                    self._stock_list[folder_symbol] = {
                                        'symbol': folder_symbol,
                                        'name': folder_symbol,
                                        'market_cap': 'N/A',
                                        'market_cap_category': category,
                                        'price': df['Close'].iloc[-1] if len(df) > 0 else None,
                                        'change_pct': None,
                                        'sector': 'Unknown',
                                        'analyst_rating': None
                                    }
                    except Exception as e:
                        print(f"Error loading {folder_symbol}: {e}")

                # Load info data
                info_file = stock_dir / f"{folder_symbol}_info.csv"
                if info_file.exists():
                    try:
                        info_df = pd.read_csv(info_file)
                        self._info_data[folder_symbol] = dict(zip(info_df['Metric'], info_df['Value']))
                    except Exception:
                        pass

    def get_all_stocks(self) -> list[dict]:
        """Get list of all stocks with basic info."""
        self.load_all()
        return list(self._stock_list.values())

    # def get_stock_info(self, symbol: str) -> Optional[dict]:
    #     """Get info for a specific stock."""
    #     self.load_all()
    #     return self._stock_list.get(symbol)

    def get_historical_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get historical price data for a stock."""
        self.load_all()
        return self._historical_data.get(symbol)

    def get_returns(self, symbol: str) -> Optional[pd.Series]:
        """Get daily returns for a stock."""
        self.load_all()
        return self._returns_data.get(symbol)

    def get_returns_matrix(self, symbols: list[str]) -> pd.DataFrame:
        """Get aligned returns matrix for multiple stocks."""
        self.load_all()

        returns_dict = {}
        for symbol in symbols:
            if symbol in self._returns_data:
                returns_dict[symbol] = self._returns_data[symbol]

        if not returns_dict:
            return pd.DataFrame()

        # Combine into DataFrame and align dates
        returns_df = pd.DataFrame(returns_dict)
        returns_df = returns_df.dropna()

        return returns_df

    def get_stock_metrics(self, symbol: str) -> Optional[dict]:
        """Calculate basic metrics for a stock."""
        self.load_all()

        returns = self._returns_data.get(symbol)
        if returns is None or len(returns) < 20:
            return None

        # Annualized metrics
        expected_return = returns.mean() * TRADING_DAYS
        volatility = returns.std() * np.sqrt(TRADING_DAYS)

        # Sharpe ratio (assuming 4% risk-free rate)
        risk_free_rate = 0.04
        sharpe = (expected_return - risk_free_rate) / volatility if volatility > 0 else 0

        # Max drawdown
        hist = self._historical_data.get(symbol)
        if hist is not None and 'Close' in hist.columns:
            prices = hist['Close']
            rolling_max = prices.expanding().max()
            drawdowns = (prices - rolling_max) / rolling_max
            max_drawdown = drawdowns.min()
        else:
            max_drawdown = 0

        return {
            'symbol': symbol,
            'expected_return': round(expected_return, 4),
            'volatility': round(volatility, 4),
            'sharpe_ratio': round(sharpe, 4),
            'max_drawdown': round(max_drawdown, 4)
        }

    # def get_detailed_info(self, symbol: str) -> Optional[dict]:
    #     """Get detailed company info."""
    #     self.load_all()
    #     return self._info_data.get(symbol)


# Singleton instance
data_loader = DataLoader()
