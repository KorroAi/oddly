<p align="center">
  <img src="preview.png" alt="Oddly" width="100%">
</p>

# Oddly

A tool that scans SEC filings to find odd-lot tender offers. Built as a Claude Code skill and Python package.

## How It Works

Some companies and closed-end funds file tender offers with the SEC. They offer to buy back shares at a fixed price. Under SEC Rule 14d-10(f), these offers can include an odd-lot provision: anyone holding 99 shares or fewer gets priority. No proration. No partial fill. You buy shares at the market price. You tender them at the offer price. You keep the difference.

Institutions managing billions of dollars cannot use this. A 99-share position is invisible at their scale. The regulation was written to protect small shareholders from institutional mechanics, and in doing so it created a structural asymmetry that only retail can exploit.

Oddly automates the first part: scanning SEC EDGAR for these filings, parsing the details, and handing each candidate to an AI evaluation pipeline. The AI reads the full text of the filing and applies 11 verification gates. Each gate is binary and verifiable. The filing either contains the odd-lot language or it does not. If any gate fails, the candidate is rejected with a reason.

Most filings are rejected. That is the point.

## Claude Code Skill

`/oddly` in Claude Code runs the full pipeline:

1. Checks configuration (capital, position limits, minimum premium)
2. Scans SEC EDGAR for recent tender offers and spin-off registrations
3. Downloads and reads each filing
4. Applies all 11 gates, stopping at the first failure
5. Presents a verdict with evidence quoted from the filing

If no configuration exists, the skill prompts for it on first run.

## Installation

```bash
git clone https://github.com/KorroAi/oddly.git
cd oddly
pip install -e .
oddly setup
```

Python 3.10 or later. Dependencies: `requests`, `yfinance`. No API keys. SEC EDGAR is public.

## Commands

```
oddly scan          Scan EDGAR for tender offers and spin-offs
oddly setup         Configure capital and preferences
oddly portfolio     View positions and deadlines
oddly analyze SYM   Open the SEC filing for a ticker
oddly buy ...       Record a position
oddly sell ...      Close a position
```

## 11 Gates

Each candidate is evaluated through all 11 gates. Gates are sequential. A failure at any gate stops evaluation.

| Gate | What It Checks |
|------|---------------|
| G0 | Is the filing still active? Deadline not passed? |
| G1 | Is there an explicit odd-lot provision in the filing text? |
| G2 | Is the consideration 100% cash? No financing conditions? |
| G3 | Can you afford 99 shares with 50% of your capital? |
| G4 | Is the premium at least 10% over the current market price? |
| G5 | Is the deadline within 60 days? |
| G6 | Is the stock listed on NYSE or NASDAQ? |
| G7 | Can you write two specific failure scenarios for this deal? |
| G8 | Can you quote the exact tender price from the filing? |
| G9 | Any insider selling, litigation, or going concern warnings? |
| G10 | Can you explain this opportunity in two plain sentences? |

Gates are verifiable, not opinion-based. The filing has the language or it does not.

## Research Paper

[PAPER.pdf](PAPER.pdf) covers the regulatory basis (SEC Rule 14d-10), academic literature (Lakonishok & Vermaelen 1990, Larcker & Lys 1987, Dann 1981, Greenblatt 1997), the full 11-gate methodology, a 30-trade backtest of closed-end fund tender arbitrage, risk analysis, and capital requirements.

Also available as [Markdown](PAPER.md).

## Backtest Data

The backtest simulates 30 closed-end fund tender arbitrage trades from January 2024 through July 2026. Entry: 99 shares at market price approximately 5 days before tender announcement. Exit: tender at the offer price. 27 of 30 trades use historical prices from yfinance. 3 use NAV estimates for delisted tickers.

Run it:
```bash
python -m oddly.backtest
```

Results saved to `oddly/.backtests/` as JSON.

The backtest is provided for methodology review. It shows how the strategy behaved on known historical events. It is not forward-looking.

## Files

```
oddly/
  oddly/
    sec_filings.py    EDGAR client, filing parser
    config.py          Configuration, portfolio tracking
    cli.py             Command-line interface
    backtest.py        Backtest engine
  .github/workflows/   CI (Python 3.10, 3.11, 3.12)
  SKILL.md             Claude Code skill definition
  PAPER.pdf            Research paper
  PAPER.md             Research paper (source)
  preview.png          Banner
```

## License

GNU Affero General Public License v3.0. See [LICENSE](LICENSE).

Personal use, modification, and sharing are permitted. Commercial use as part of a proprietary product, offering the software as a service without releasing source code, or incorporating it into closed-source work is prohibited.

## Links

[Discord](https://discord.gg/RSBHHjxnYt) · [X @korrocorp](https://x.com/korrocorp) · [GitHub](https://github.com/KorroAi) · [contact.korro@gmail.com](mailto:contact.korro@gmail.com)
