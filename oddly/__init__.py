"""Oddly — AI-powered odd-lot tender arbitrage scanner."""
from .sec_filings import scan_opportunities, get_recent_tenders, get_recent_spinoffs, enrich_opportunity, Opportunity
from .config import (
    load_config, save_config, UserConfig,
    load_positions, save_positions, log_trade, load_history, Position,
)
from .backtest import run_cef_backtest, print_report

__version__ = "1.0.0"
