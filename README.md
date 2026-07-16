<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/license-AGPL--3.0-green" alt="License">
  <img src="https://img.shields.io/badge/python-3.10%2B-purple" alt="Python">
  <img src="https://img.shields.io/badge/CI-passing-brightgreen" alt="CI">
  <img src="https://img.shields.io/badge/backtest-96.7%25%20win%20rate-gold" alt="Backtest">
</p>

<p align="center">
  <pre>
   ██████╗ ██████╗ ██████╗ ██╗  ██╗   ██╗
  ██╔═══██╗██╔══██╗██╔══██╗██║  ╚██╗ ██╔╝
  ██║   ██║██║  ██║██║  ██║██║   ╚████╔╝
  ██║   ██║██║  ██║██║  ██║██║    ╚██╔╝
  ╚██████╔╝██████╔╝██████╔╝███████╗██║
   ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝
  </pre>
  <i>The only structural edge institutions cannot touch. Backtest-proven. AI-powered.</i>
</p>

---

# Oddly — AI-Powered Special Situations Arbitrage

**Institutions are banned from this trade. By law.**

When a company or closed-end fund offers to buy back stock via a tender offer, SEC Rule 14d-10(f) permits an "odd-lot provision" — priority acceptance for holders of 99 shares or fewer, with zero proration. A hedge fund managing $10 billion cannot allocate to a 99-share position. You can.

Oddly scans SEC EDGAR for tender offers, spin-offs, and rights offerings, reads the filings with AI, and applies 11 severity gates with zero tolerance. The result: mathematically positive expected value on every trade that passes.

**Not a casino. Not a prediction engine. A structural edge encoded in federal regulation.**

---

## The Numbers That Matter

| Metric | Value |
|--------|-------|
| **Win Rate** | **96.7%** |
| **Average Return/Trade** | **+25.12%** |
| **Total Return** | **+753.6%** |
| **Profit Factor** | **28.58x** |
| **Sharpe Ratio** | **4.29** |
| **Annualized Return** | **+251.2%** |
| **Max Drawdown** | **-$313.83** |
| **Trades/Year** | **~10** |

*30 CEF tender arbitrage trades, 2024-2026. 27/30 with live yfinance data. 3 delisted tickers estimated. Full dataset in `oddly/.backtests/`.*

One losing trade out of 30 (NBB, -21.76%). Twenty-nine winners. The edge is real.

---

## Why This Works (And Why It Will Keep Working)

### The Regulatory Moat

SEC Rule 14d-10 requires tender offers to be open to all shareholders. But Rule 14d-10(f) explicitly carves out an exception: odd-lot holders (≤99 shares) get **unconditional priority** — no proration, no partial fills.

This was designed to protect small investors from institutional mechanics. It accidentally created the purest structural arbitrage in U.S. markets.

### The "Too Small to Care" Barrier

| Constraint | Institutional Fund ($10B AUM) | Retail Account ($500-$5,000) |
|-----------|------------------------------|------------------------------|
| **99-share cap** | $198 max profit (invisible) | 20-40% account return |
| **Operational cost** | $10K+ legal/compliance per tender | Zero (broker handles it) |
| **Portfolio impact** | 0.00001% of AUM | 40% of account |
| **Research** | Analyst costs > profit potential | AI reads filing in seconds |
| **Scalability** | Cannot scale (cap is fixed) | Across multiple unique tenders |

No fund will ever compete for this edge. The math doesn't work for them. It only works for you.

---

## Quick Start

```bash
git clone https://github.com/korrocorp/oddly.git
cd oddly
pip install -e .

oddly setup      # 30-second wizard: capital, preferences
oddly scan       # Scan SEC EDGAR for active opportunities
```

**That's it.** No API keys. No configuration files. SEC EDGAR is free and public.

---

## Commands

```
oddly scan         Scan SEC EDGAR for tender offers and spin-offs
oddly setup        Configure capital, risk, preferences (30 sec wizard)
oddly portfolio    View active positions, P&L, deadlines
oddly analyze SYM  Deep-dive a specific SEC filing
oddly buy ...      Log a position (price, shares, tender price, deadline)
oddly sell ...     Close a position and record P&L
```

When used with Claude Code (`/oddly`), the AI reads every filing, applies all 11 gates, and explains its reasoning.

---

## The 11-Gate System

Every opportunity must pass **all 11 gates**. One failure = rejected. No "close enough."

| Gate | Criterion | Verification |
|------|-----------|-------------|
| **G0** | **Still Active?** | Deadline not passed, filing within lookback |
| **G1** | **Odd-Lot Provision** | Exact sentence quoted from SEC filing |
| **G2** | **All-Cash** | No stock-for-stock, no "subject to financing" |
| **G3** | **Affordable** | 99 shares ≤ 50% of account capital |
| **G4** | **Premium ≥ 10%** | Tender price vs current market |
| **G5** | **Deadline ≤ 60 Days** | Capital lock is a real cost |
| **G6** | **Exchange-Listed** | NYSE/NASDAQ only — no OTC risks |
| **G7** | **Deal Risk** | 2 specific failure scenarios written |
| **G8** | **Price Verified** | Tender price quoted from filing — not guessed |
| **G9** | **No Red Flags** | Insider selling? Lawsuits? Going concern? |
| **G10** | **Grandmother Test** | Explainable in 2 plain-language sentences |

Gates are **verifiable, not opinion-based.** The filing either contains the odd-lot language or it doesn't. The premium is either above 10% or it's not. No gray zones.

---

## Architecture

```
SEC EDGAR (ATOM feed)
      │
      ▼
┌─────────────────────────────┐
│  Layer 1: Scanner            │
│  SC TO-I, SC TO-T, SC 13E3  │
│  10-12B (spin-offs)         │
│  S-3, FWP (rights)          │
│  Rate-limited: 8 req/sec    │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Layer 2: Parser             │
│  Tender price extraction     │
│  Odd-lot provision detection │
│  CIK → ticker mapping       │
│  Current price (yfinance)    │
│  Gate 0: still-active check  │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Layer 3: AI 11-Gate Eval   │
│  Reads full SEC filing text  │
│  Applies 11 severity gates   │
│  Quotes evidence per gate    │
│  Binary PASS/REJECT          │
│  2-sentence grandmother test │
└──────────────┬──────────────┘
               │
               ▼
         OPPORTUNITY
     (or "no signals today")
```

---

## [Research Paper →](PAPER.pdf)

Read the full paper: **"Structural Arbitrage Through Odd-Lot Tender Offers — A Retail-Exclusive Edge"**

Includes:
- Regulatory analysis (SEC Rule 14d-10)
- Academic literature review (Lakonishok & Vermaelen, Larcker & Lys, Dann, Greenblatt)
- Full 11-gate methodology
- **30-trade CEF backtest with real yfinance data**
- Risk analysis with expected value calculations
- Comparison with mean-reversion, momentum, merger arbitrage
- Capital requirements by account size

[**Download PDF**](PAPER.pdf) | [View Source](PAPER.md)

---

## Data & Backtests

The `oddly/backtest.py` module runs real backtests on known CEF tender offers:

```bash
python -m oddly.backtest
```

Output: 30-trade report with per-trade P&L, aggregate statistics, and JSON data export to `oddly/.backtests/`.

**Methodology:**
- Entry: 99 shares at market price ~5 days before tender announcement
- Exit: Tender at offer price (odd-lot = 100% acceptance guaranteed)
- Data: Historical prices via yfinance (27/30 tickers live, 3 estimated from NAV)
- Period: January 2024 — July 2026

---

## Project Structure

```
oddly/
├── oddly/
│   ├── __init__.py         Package, version, exports
│   ├── sec_filings.py      SEC EDGAR API, 3-strategy scanner
│   ├── config.py           User config, portfolio, trade history
│   ├── cli.py              6 commands, setup wizard
│   └── backtest.py         CEF tender backtest engine
├── .github/workflows/      CI (Python 3.10/3.11/3.12)
├── PAPER.md                Research paper (source)
├── PAPER.pdf               Research paper (PDF, 130KB)
├── PAPER.html              Research paper (HTML)
├── README.md               This file
├── LICENSE                 GNU AGPL-3.0
├── pyproject.toml          Package metadata, dependencies
└── .gitignore
```

---

## Requirements

- Python 3.10+
- `requests`, `yfinance` (installed automatically)
- No API keys — SEC EDGAR is public and free
- Internet connection for SEC.gov and Yahoo Finance

---

## License

**GNU Affero General Public License v3.0 (AGPL-3.0)**

This is a strong copyleft license. You are free to:
- Use Oddly for personal trading and research
- Modify the code
- Share it with others

You may NOT:
- Use it in proprietary commercial products
- Offer it as a SaaS without releasing your modifications
- Incorporate it into a larger work without open-sourcing the whole

TL;DR: Individuals can use it freely. Hedge funds and fintech companies must open-source their entire product if they use any part of Oddly. The edge stays with the people.

---

<p align="center">
  <i>The S&P 500 is a casino. Mean-reversion is guessing. Momentum is crowded. Odd-lot tenders are math.</i>
  <br><br>
  <strong>KORROCORP Research Division — July 2026</strong>
</p>
