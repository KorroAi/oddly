"""User configuration & position tracking for Oddly."""
import json
import os
from dataclasses import dataclass, field, fields
from datetime import datetime
from pathlib import Path

CONFIG_DIR = Path(__file__).parent / ".config"
CONFIG_FILE = CONFIG_DIR / "user.json"
PORTFOLIO_DIR = Path(__file__).parent / ".portfolio"
POSITIONS_FILE = PORTFOLIO_DIR / "positions.json"
HISTORY_FILE = PORTFOLIO_DIR / "history.jsonl"


@dataclass
class UserConfig:
    capital: float = 500.0
    max_per_position_pct: float = 100.0  # odd-lot: one position at a time is ok
    max_positions: int = 2
    min_tender_premium: float = 5.0
    notifications: bool = True
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "capital": self.capital,
            "max_per_position_pct": self.max_per_position_pct,
            "max_positions": self.max_positions,
            "min_tender_premium": self.min_tender_premium,
            "notifications": self.notifications,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Position:
    symbol: str
    entry_price: float
    entry_date: str
    shares: int
    tender_price: float
    tender_deadline: str
    premium_pct: float
    expected_profit: float
    status: str = "active"  # active, tendered, completed, expired
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "entry_price": self.entry_price,
            "entry_date": self.entry_date,
            "shares": self.shares,
            "tender_price": self.tender_price,
            "tender_deadline": self.tender_deadline,
            "premium_pct": self.premium_pct,
            "expected_profit": self.expected_profit,
            "status": self.status,
            "notes": self.notes,
        }


def _known_fields(cls) -> set[str]:
    return {f.name for f in fields(cls)}


def _atomic_write(path: Path, content: str) -> None:
    """Write to temp file, then rename — prevents corruption on crash."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content)
    os.replace(tmp, path)  # atomic on same filesystem


def load_config() -> UserConfig:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            valid_keys = _known_fields(UserConfig)
            filtered = {k: v for k, v in data.items() if k in valid_keys}
            return UserConfig(**filtered)
        except (json.JSONDecodeError, TypeError):
            pass
    return UserConfig()


def save_config(cfg: UserConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg.updated_at = datetime.now().isoformat()
    if not cfg.created_at:
        cfg.created_at = datetime.now().isoformat()
    _atomic_write(CONFIG_FILE, json.dumps(cfg.to_dict(), indent=2))


def load_positions() -> list[Position]:
    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)
    if POSITIONS_FILE.exists():
        try:
            data = json.loads(POSITIONS_FILE.read_text())
            valid_keys = _known_fields(Position)
            return [Position(**{k: v for k, v in p.items() if k in valid_keys}) for p in data]
        except (json.JSONDecodeError, TypeError):
            pass
    return []


def save_positions(positions: list[Position]) -> None:
    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)
    _atomic_write(POSITIONS_FILE, json.dumps([p.to_dict() for p in positions], indent=2))


def log_trade(position: Position, exit_price: float, pnl_pct: float,
              exit_date: str, reason: str) -> None:
    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        **position.to_dict(),
        "exit_price": exit_price,
        "pnl_pct": round(pnl_pct, 2),
        "exit_date": exit_date,
        "exit_reason": reason,
        "closed_at": datetime.now().isoformat(),
    }
    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def load_history() -> list[dict]:
    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)
    if not HISTORY_FILE.exists():
        return []
    trades = []
    with open(HISTORY_FILE) as f:
        for line in f:
            if line.strip():
                trades.append(json.loads(line))
    return trades
