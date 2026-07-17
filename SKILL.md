# /oddly — AI-Powered Special Situations Arbitrage

**Structural edges institutions can't touch. Gated with maximum severity.**

## How To Use

You don't run a daemon. You don't set a cron. You open Claude Code and type `/oddly` whenever you think of it — once a week, once a month, whatever. The scanner looks back far enough to catch anything you missed:

- **Tender offers**: 45-day lookback (deadlines are short)
- **Spin-offs**: 90-day lookback (filed months before spin date)
- **Rights offerings**: 60-day lookback (moderate window)

No opportunity is stale because **Gate 0 kills anything that's already expired.**

## The 11 Gates (Gate 0 + 10 Severity Gates)

### Gate 0: STILL ACTIVE? — BEFORE all other gates

Is this opportunity still actionable RIGHT NOW?
- Tender deadline passed? → REJECTED. Don't even read the filing.
- Spin-off already completed? → REJECTED.
- Rights subscription closed? → REJECTED.

This gate runs automatically. If it fails, the opportunity doesn't reach AI evaluation.

```
G1: ODD-LOT PROVISION — EXPLICIT in filing text
    AI MUST quote the exact sentence from the SEC filing.
    "We think there might be" = REJECTED.
    No odd-lot language found = REJECTED.
    This gate is BINARY. Pass or fail. No scoring.

G2: ALL CASH — No stock-for-stock, no "subject to financing"
    Tender consideration must be 100% cash.
    "Subject to financing" or "financing condition" = REJECTED.
    Stock-for-stock, cash+stock mix = REJECTED.
    Must quote the cash consideration clause from filing.

G3: AFFORDABLE — 99 shares ≤ 50% of user's capital
    user_capital × 0.5 ÷ 99 = max stock price.
    At $500 capital: max $2.50/share.
    At $1,000: max $5.05/share.
    At $5,000: max $25.25/share.
    Stock above threshold = REJECTED. No partial fills.
    This is MATH, not judgment.

G4: PREMIUM ≥ 10% — Over current market price
    (tender_price - current_price) / current_price × 100 ≥ 10.
    Below 10% = REJECTED. No exceptions.
    This accounts for spread, adverse price movement, deal risk.
    At 8%: "close but no" = REJECTED.

G5: DEADLINE ≤ 60 DAYS from today
    Capital lock is real cost to a small account.
    61+ days = REJECTED.
    Calculate annualized return: premium ÷ (days/365).

G6: LISTED — NYSE or NASDAQ only
    No OTC (OTCQX, OTCQB, Pink Sheets).
    No foreign exchanges (TSX, LSE, etc.).
    Must be buyable in standard US brokerage.
    Check via yfinance: ticker.info["exchange"] must contain "Nasdaq" or "NYSE".

G7: DEAL RISK — 2 specific failure scenarios WRITTEN
    AI must write 2 CONCRETE scenarios where this deal fails.
    Not generic ("market risk"). SPECIFIC:
    "Antitrust: deal exceeds HSR threshold and DOJ challenges"
    "Shareholder vote: activist investor opposes, owns 15%"
    If AI can't think of 2 specific risks → it doesn't understand the deal → REJECTED.

G8: PRICE VERIFIED — Tender price quoted from filing text
    The automated parser gives a HINT. The AI CONFIRMS.
    AI must quote: "Filing states: '$X.XX per share in cash'"
    Parser price ≠ AI-verified price → REJECTED.
    Can't find price in filing → REJECTED.

G9: NO RED FLAGS — Check before entry
    Any insider selling in past 30 days? (check OpenInsider or SEC Form 4)
    Any pending litigation against the deal?
    Any unusual options activity?
    Any going concern warning for the company?
    ONE red flag → discuss with user, default to REJECTED.

G10: GRANDMOTHER TEST — Explain in 2 sentences
    "Company X offers to buy back stock at $Y/share."
    "You buy at market price $Z (<$Y) because you own <100 shares."
    "You're guaranteed $Y. Profit = $Profit in ~30 days."
    If it takes more than 2 sentences → too complex → REJECTED.
```

## Commands

- `/oddly` or `/oddly scan` — Full multi-strategy special situations scan
- `/oddly portfolio` — View positions, deadlines, expected profit
- `/oddly setup` — Configure capital and preferences

## Scan Protocol — `/oddly`

### Step 1: Fetch Opportunities (Tenders + Spin-offs)

```
python -c "
from oddly import scan_opportunities, load_config
cfg = load_config()
opps = scan_opportunities()
print(f'FOUND|{len(opps)}')
for o in opps:
    print(f'OPP|{o.symbol}|{o.strategy}|{o.company_name}|{o.filing_type}|{o.filing_date}|{o.current_price}|{o.target_price}|{o.premium_pct}|{o.odd_lot_shares}|{o.still_active}|{o.deadline}|{o.filing_url}')
"
```

### Step 2: Read Each Filing

For every tender found, download and read the actual SEC filing:

```
python -c "
import requests
url = '<filing_url>'.replace('-index.htm', '.txt').replace('-index.html', '.txt')
resp = requests.get(url, headers={'User-Agent': 'Oddly/1.0 (github.com/KorroAi/oddly)'})
print(resp.text[:15000])
"
```

### Step 3: Apply 10 Gates

For each tender, apply ALL 10 gates in order. If ANY gate fails → REJECTED. Stop and move to next tender.

**G1** — Search filing for odd-lot language. Quote the sentence.
**G2** — Search for "cash," "financing condition," "stock consideration."
**G3** — Calculate: user_capital × 0.5 ÷ 99. Compare to stock price.
**G4** — Calculate premium. Must be ≥ 10%.
**G5** — Find expiration date. Must be ≤ 60 days from now.
**G6** — Check exchange via yfinance.
**G7** — Write 2 specific failure scenarios.
**G8** — Quote the tender price from the filing text.
**G9** — Quick scan for red flags.
**G10** — Write the 2-sentence explanation.

### Step 4: Output

Only present signals that PASSED ALL 10 GATES:

```
╔══════════════════════════════════════════╗
║  ODD-LOT TENDER: [SYMBOL] — [Company]   ║
╠══════════════════════════════════════════╣
║  Tender Price:   $X.XX (VERIFIED)       ║
║  Current Price:  $X.XX                  ║
║  Premium:        +XX.X% ≥ 10% ✓         ║
║  Odd-Lot:        ≤99 shares GUARANTEED  ║
║  Deadline:       [Date] (X days)        ║
║  Buy:            99 shares @ $X.XX      ║
║  Cost:           $XXX.XX                ║
║  Expected Profit: $XX.XX                 ║
║  ─────────────────────────────────────  ║
║  G1 Odd-Lot:   ✓ "[quote from filing]" ║
║  G2 All-Cash:  ✓ "[quote from filing]" ║
║  G3 Afford:    ✓ $X ≤ $max             ║
║  G4 Premium:   ✓ XX% ≥ 10%            ║
║  G5 Deadline:  ✓ X days ≤ 60          ║
║  G6 Listed:    ✓ NASDAQ/NYSE          ║
║  G7 Deal Risk: ✓ [risk 1], [risk 2]   ║
║  G8 Verified:  ✓ "[exact price quote]"║
║  G9 No Flags:  ✓ Clean                ║
║  G10 Explain:  "[2-sentence summary]"  ║
║  ─────────────────────────────────────  ║
║  VERDICT: APPROVED — 10/10 gates      ║
╚══════════════════════════════════════════╝
```

If NO opportunities pass all gates:
```
NO SIGNALS — 0/[N] tenders passed all 10 gates.
This is NORMAL. Real odd-lot opportunities are 2-4/year.
Rejected: [list each tender with which gate failed]
```

## Portfolio — `/oddly portfolio`

Show positions with: current price vs tender, days to deadline, expected profit.

## Principles

1. **Perfection or nothing.** 11/11 gates (Gate 0 + 10 severity) or no trade.
2. **Verifiable, not opinion-based.** Quoting filing text, not "I think."
3. **Honesty.** Zero signals = say so proudly. The system works.
4. **You run `/oddly` when you want.** No daemon. No cron. Scan catches what you missed.
5. **1-6 signals/year.** Each one mathematically positive. That's the game.
6. **English only.**
