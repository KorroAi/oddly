<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/license-AGPL--3.0-green" alt="License">
  <img src="https://img.shields.io/badge/python-3.10%2B-purple" alt="Python">
  <img src="https://img.shields.io/badge/backtest-96.7%25%20win%20rate-gold" alt="Backtest">
</p>

# Oddly

Odd-lot tender arbitrage. Institutions are excluded by federal regulation. Oddly finds the opportunities and an AI applies 11 gates before any trade is approved.

## Backtest Results

30 closed-end fund tender arbitrage trades, January 2024 to July 2026. Entry: 99 shares at market price. Exit: tender at offer price. 27 of 30 trades use live yfinance data. 3 use NAV-based estimates for delisted tickers.

| Metric | Value |
|--------|-------|
| Win Rate | 96.7% |
| Average Return / Trade | +25.12% |
| Total Return | +753.6% |
| Profit Factor | 28.58x |
| Sharpe Ratio | 4.29 |
| Annualized Return | +251.2% |
| Max Drawdown | -$313.83 |
| Trades Per Year | ~10 |

29 winning trades. 1 loss (NBB, -21.76%). Full dataset in `oddly/.backtests/`.

## Why It Works

SEC Rule 14d-10(f) permits tender offers to include an odd-lot provision: shareholders holding 99 or fewer shares get unconditional priority. No proration. No partial fills. Guaranteed.

A fund managing $10 billion cannot allocate to a 99-share position. The maximum profit from a $10 to $12 tender on 99 shares is $198. That is invisible at institutional scale. It is a 20% return on a $1,000 account.

This is not a prediction. It is not a model. It is federal regulation. It has existed for decades and will persist as long as the rule exists.

| Constraint | $10B Fund | $500-$5,000 Account |
|-----------|----------|---------------------|
| 99-share cap | $198 max profit | 20-40% account return |
| Operational overhead | $10K+ per tender | Zero (broker handles it) |
| Portfolio impact | 0.00001% of AUM | Up to 40% of account |
| Research burden | Analyst time exceeds profit | AI reads filing in seconds |

## Quick Start

```bash
git clone https://github.com/KorroAi/oddly.git
cd oddly
pip install -e .

oddly setup      # Configure capital and preferences (30 seconds)
oddly scan       # Scan SEC EDGAR for active opportunities
```

No API keys. No accounts. SEC EDGAR is free and public.

## Commands

```
oddly scan         Scan SEC EDGAR for tender offers and spin-offs
oddly setup        Configure capital, risk, preferences
oddly portfolio    View active positions, P&L, deadlines
oddly analyze SYM  Deep-dive a specific SEC filing
oddly buy ...      Log a position (price, shares, tender price, deadline)
oddly sell ...     Close a position and record P&L
```

Use `/oddly` in Claude Code for the full AI pipeline: scan, read filings, apply gates, present verdict.

## 11-Gate System

Every opportunity must pass every gate. One failure stops evaluation.

| Gate | Criterion | Verification |
|------|-----------|-------------|
| G0 | Still Active | Deadline not passed, filing within lookback window |
| G1 | Odd-Lot Provision | Exact sentence quoted from SEC filing |
| G2 | All-Cash | No stock-for-stock, no financing conditions |
| G3 | Affordable | 99 shares costs no more than 50% of account |
| G4 | Premium >= 10% | Tender price vs current market price |
| G5 | Deadline <= 60 Days | Capital lock duration is a real cost |
| G6 | Exchange-Listed | NYSE or NASDAQ only. No OTC. |
| G7 | Deal Risk | 2 specific, concrete failure scenarios written |
| G8 | Price Verified | Tender price confirmed by quoting the filing |
| G9 | No Red Flags | Insider selling, litigation, going concern warnings |
| G10 | Grandmother Test | Explainable in 2 plain sentences |

Gates are verifiable. Binary. The filing either contains the odd-lot language or it does not. The premium is either above 10% or it is not.

## How It Works

```
SEC EDGAR (ATOM feed)
      |
      v
Layer 1: Scanner
  SC TO-I, SC TO-T, SC 13E3 (tender offers)
  10-12B (spin-offs)
  Rate-limited: 8 requests / second
      |
      v
Layer 2: Parser
  Extract: tender price, odd-lot provision, deadline, conditions
  Map CIK to ticker symbol
  Fetch current price (yfinance)
  Gate 0: is this still active?
      |
      v
Layer 3: AI 11-Gate Evaluation
  Read the full SEC filing
  Apply all 11 gates
  Quote evidence from the filing for each gate
  Binary PASS or REJECT with explanation
      |
      v
  OPPORTUNITY  (or "no signals today")
```

## Research Paper

[**Structural Arbitrage Through Odd-Lot Tender Offers: A Retail-Exclusive Edge** (PDF)](PAPER.pdf)

Covers the regulatory foundation (SEC Rule 14d-10), academic literature (Lakonishok & Vermaelen 1990; Larcker & Lys 1987; Dann 1981; Greenblatt 1997), the full 11-gate methodology, 30-trade backtest results, risk analysis with expected value calculations, and capital requirements by account size.

[Download PDF](PAPER.pdf) | [View source](PAPER.md)

## Backtest

```bash
python -m oddly.backtest
```

Produces a 30-trade report with per-trade P&L, aggregate statistics, and JSON data export.

## Project Structure

```
oddly/
  oddly/
    __init__.py       Package, version, public API
    sec_filings.py    SEC EDGAR client, 3-strategy scanner
    config.py         User config, portfolio tracker, trade history
    cli.py            6 commands, setup wizard
    backtest.py       CEF tender backtest engine
  .github/workflows/  CI (Python 3.10, 3.11, 3.12)
  PAPER.md            Research paper (source)
  PAPER.pdf           Research paper (PDF)
  README.md
  LICENSE             GNU AGPL-3.0
  pyproject.toml
```

## Requirements

Python 3.10+. `requests` and `yfinance` are installed automatically. No API keys needed. Internet connection required for SEC.gov and Yahoo Finance.

## License

GNU Affero General Public License v3.0 (AGPL-3.0).

You may use Oddly for personal trading and research. You may modify it. You may share it. You may not use it in proprietary commercial products, offer it as a SaaS without releasing your modifications, or incorporate it into a larger work without open-sourcing the whole project.

KORROCORP, July 2026.
