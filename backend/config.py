from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
LARGE_CAP_DIR = DATA_DIR / "large_cap"
MID_CAP_DIR = DATA_DIR / "mid_cap"
SMALL_CAP_DIR = DATA_DIR / "small_cap"

# Stock list CSVs
LARGE_CAP_CSV = PROJECT_ROOT / "large_cap.csv"
MID_CAP_CSV = PROJECT_ROOT / "mid_cap.csv"
SMALL_CAP_CSV = PROJECT_ROOT / "small_cap.csv"

# Risk-free rate (UK gilt yield approximation)
RISK_FREE_RATE = 0.04  # 4% annual

# Trading days per year
TRADING_DAYS = 252
