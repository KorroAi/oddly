# Oddly

A Claude Code skill and Python package for scanning SEC EDGAR filings to find odd-lot tender offers. The skill provides an 11-gate AI evaluation pipeline that reads each filing and determines whether the opportunity is actionable.

## What It Does

When a company or closed-end fund files a tender offer with the SEC (forms SC TO-I, SC TO-T, SC 13E3), the filing may include an *odd-lot provision*: shareholders holding 99 or fewer shares receive priority acceptance without proration. These provisions exist under SEC Rule 14d-10(f) and are standard in many closed-end fund tender programs.

Oddly scans EDGAR's current filings feed, extracts the relevant data, and hands each candidate to an AI evaluation pipeline. The AI reads the full text of the SEC filing and applies 11 verification gates before any opportunity is presented.

The scanner also monitors spin-off registrations (Form 10-12B) and rights offering filings (Forms S-3, FWP). Each strategy type has its own lookback window and gate adaptations.

## Claude Code Skill

The primary interface is the `/oddly` slash command in Claude Code. When invoked, the skill:

1. Checks the user's configuration (capital, position limits, minimum premium)
2. Runs `oddly scan` to fetch current filings from SEC EDGAR
3. Downloads and reads the full text of each filing
4. Applies all 11 gates in sequence, stopping at the first failure
5. Presents a verdict with quoted evidence from the filing text

If no config exists on first run, the skill prompts for capital and preferences.

### Skill Installation

The skill file is at `~/.claude/skills/oddly/SKILL.md` in this repository. To install:

```bash
cp SKILL.md ~/.claude/skills/oddly/SKILL.md
```

Or copy it manually into your Claude Code skills directory. The skill auto-registers when the repository is present in your working directory.

The skill is also available by installing the package and invoking `/oddly` in any Claude Code session.

## Installation

```bash
git clone https://github.com/KorroAi/oddly.git
cd oddly
pip install -e .
```

Requires Python 3.10 or later. Dependencies: `requests`, `yfinance`. No API keys needed — SEC EDGAR is free and public.

## Commands

```
oddly scan         Scan EDGAR for active tender offers and spin-offs
oddly setup        Configure capital and risk parameters
oddly portfolio    View positions, deadlines, P&L
oddly analyze SYM  Open the SEC filing for a specific ticker
oddly buy ...      Record a position (symbol, price, shares, tender price, deadline)
oddly sell ...     Close a position with exit price and reason
```

`oddly setup` accepts optional flags for scripting:

```bash
oddly setup --capital 1000 --max-positions 2 --min-premium 5
```

## 11-Gate Evaluation

Each candidate filing is evaluated through 11 sequential gates. If any gate fails, evaluation stops and the candidate is rejected with a specific reason.

| Gate | Criterion | Method |
|------|-----------|--------|
| G0 | Still Active | Filing date within lookback window, deadline not passed |
| G1 | Odd-Lot Provision | Exact sentence must be quoted from the filing text |
| G2 | All-Cash Consideration | No stock-for-stock, no financing conditions |
| G3 | Affordable | 99 shares costs at most 50% of account capital |
| G4 | Premium >= 10% | Verified tender price vs current market price |
| G5 | Deadline <= 60 Days | Capital lock duration |
| G6 | Exchange-Listed | NYSE or NASDAQ, no OTC |
| G7 | Deal Risk | Two specific, concrete failure scenarios required |
| G8 | Price Verified | Tender price confirmed by quoting the filing |
| G9 | No Red Flags | Insider selling, litigation, going concern |
| G10 | Grandmother Test | Fully explainable in two plain sentences |

Gates are binary and verifiable. The filing either contains the odd-lot language or it does not. The premium is either above 10% or it is not. No scoring, no gray zones, no "close enough."

## Architecture

Three layers, operating in sequence:

**Scanner (rate-limited, 8 req/sec):**
Queries the SEC EDGAR current filings ATOM feed for SC TO-I, SC TO-T, SC 13E3, 10-12B, S-3, and FWP form types. Maps CIK numbers to ticker symbols via the SEC company tickers JSON endpoint, cached for 24 hours.

**Parser:**
Downloads each filing as plain text, extracts the tender price, odd-lot provision language, expiration deadline, and deal conditions using regex patterns. Fetches the current market price via yfinance. Applies Gate 0 (still-active check based on filing date and parsed deadline).

**AI Evaluation (Claude):**
Reads the full filing text. Applies gates 1 through 10. Quotes the exact filing language for each gate that requires it. Produces a binary pass/reject verdict with supporting evidence.

The output is either a detailed opportunity breakdown or "no signals today" with a list of what was rejected and why.

## Backtest

The repository includes `oddly/backtest.py`, which simulates 30 closed-end fund tender arbitrage trades from January 2024 through July 2026. Each trade assumes purchase of 99 shares at market price approximately 5 days before a known tender announcement, with exit at the tender offer price. 27 of the 30 trades use historical prices fetched from yfinance; 3 use NAV-based estimates for tickers that have since been delisted.

Results are saved as JSON in `oddly/.backtests/` and can be regenerated:

```bash
python -m oddly.backtest
```

The backtest is provided for methodology review. It illustrates how the strategy behaves on known historical tender events. It is not a forward-looking prediction and each tender situation carries its own deal-specific risks.

## Paper

A research paper covering the regulatory basis, academic literature, methodology, backtest results, and risk analysis is included as `PAPER.pdf` and `PAPER.md`.

## Files

```
oddly/
  oddly/
    __init__.py
    sec_filings.py    EDGAR client, filing parser, scanner
    config.py          User configuration, portfolio tracking, trade history
    cli.py             Command-line interface
    backtest.py        CEF tender backtest engine
  .github/workflows/   CI (Python 3.10, 3.11, 3.12)
  SKILL.md             Claude Code skill definition
  PAPER.md             Research paper (Markdown)
  PAPER.pdf            Research paper (PDF)
```

## Limitations

Tender offers with odd-lot provisions that meet all 11 gates are infrequent. The scanner finds filings but most are rejected: third-party acquisition tenders (SC TO-T) where the filing entity is the bidder, not the target; closed-end funds that are not exchange-listed; premiums below the 10% threshold; and stocks priced too high for small accounts. This is expected behavior. The gates exist specifically to reject these cases.

SEC EDGAR filings may appear hours to days after the corporate announcement. A filing that triggers an alert on financial news may not yet be available in the EDGAR feed.

Broker support for tender offer participation varies. Confirm with your broker before entering a position.

This is not financial advice. The authors are not registered investment advisors.

## License

GNU Affero General Public License v3.0. Personal use, modification, and sharing are permitted. Commercial use as part of a proprietary product, offering the software as a service without releasing source modifications, or incorporating it into a closed-source work are prohibited under the terms of the license.
