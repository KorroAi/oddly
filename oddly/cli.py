"""Oddly CLI — scan odd-lot tenders, manage portfolio."""
import argparse
import sys
from datetime import datetime

from .sec_filings import scan_opportunities
from .config import (
    load_config, save_config, UserConfig,
    load_positions, save_positions, load_history, log_trade, Position,
)


def cmd_setup(args=None):
    """Interactive setup wizard. Pass args for non-interactive mode."""
    cfg = load_config()

    # Non-interactive mode (CLI flags provided)
    if args and (args.capital or args.max_positions or args.min_premium):
        if args.capital:
            cfg.capital = args.capital
        if args.max_positions:
            cfg.max_positions = args.max_positions
        if args.min_premium:
            cfg.min_tender_premium = args.min_premium
        save_config(cfg)
        print(f"\n  Config saved. Capital: ${cfg.capital:,.2f} | "
              f"Max positions: {cfg.max_positions} | "
              f"Min premium: {cfg.min_tender_premium}%")
        print(f"\n  Run 'oddly scan' to find opportunities.\n")
        return

    # Interactive mode
    print("\n  ODDLY SETUP WIZARD\n")
    print(f"  Capital: ${cfg.capital:,.2f}")
    print(f"  Max positions: {cfg.max_positions}")
    print(f"  Min tender premium: {cfg.min_tender_premium}%\n")

    try:
        capital = input(f"  Total capital? [{cfg.capital}]: ").strip()
        if capital:
            cfg.capital = float(capital)

        max_pos = input(f"  Max simultaneous positions? [{cfg.max_positions}]: ").strip()
        if max_pos:
            cfg.max_positions = int(max_pos)

        min_prem = input(f"  Minimum tender premium %? [{cfg.min_tender_premium}]: ").strip()
        if min_prem:
            cfg.min_tender_premium = float(min_prem)
    except (KeyboardInterrupt, EOFError):
        print("\n  Setup cancelled.")
        return

    save_config(cfg)
    print(f"\n  Config saved. Capital: ${cfg.capital:,.2f} | "
          f"Max positions: {cfg.max_positions} | "
          f"Min premium: {cfg.min_tender_premium}%")
    print(f"\n  Run 'oddly scan' to find opportunities.\n")


def cmd_scan():
    """Scan SEC EDGAR for active odd-lot tender offers."""
    cfg = load_config()

    if not cfg.created_at:
        print("\n  No config found. Run 'oddly setup' first.\n")
        cmd_setup()
        return

    print("\n  Scanning SEC EDGAR for special situations...")
    print("  Tender offers + spin-offs. This may take a minute.\n")

    tenders = scan_opportunities()

    if not tenders:
        print("  No tender offers found in the last 30 days.")
        print("  This is rare — check https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=SC+TO-I&count=40")
        return

    actionable = [t for t in tenders if t.status == "actionable"]
    review = [t for t in tenders if t.status == "review_needed"]
    missing = [t for t in tenders if t.status == "data_missing"]

    print(f"  Found {len(tenders)} tender offers "
          f"({len(actionable)} actionable, {len(review)} need review, {len(missing)} incomplete)\n")

    for t in actionable:
        # Never exceed odd-lot limit (99) or account budget
        max_shares = min(t.odd_lot_shares, int(cfg.capital / t.current_price)) if t.current_price > 0 else 0
        if max_shares <= 0:
            continue
        cost = t.current_price * max_shares
        profit = (t.target_price - t.current_price) * max_shares
        print(f"  {'─' * 55}")
        print(f"  {t.symbol:6s} | [{t.strategy:7s}] {t.company_name[:35]:35s}")
        print(f"  {'─' * 55}")
        print(f"  Target Price:  ${t.target_price:.2f}")
        print(f"  Current Price: ${t.current_price:.2f}")
        print(f"  Premium:       {t.premium_pct:+.1f}%")
        print(f"  Odd-Lot:       Up to {t.odd_lot_shares} shares")
        print(f"  Deadline:      {t.deadline or 'Unknown — check filing'}")
        print(f"  Condition:     {t.condition or 'None detected'}")
        print(f"  ───────────────────────────────────────")
        print(f"  Cost:          ${cost:,.2f} ({max_shares} shares)")
        print(f"  Expected Profit: ${profit:,.2f}")
        print(f"  Score:         {t.score}/10")
        print(f"  Filing:        {t.filing_url}")
        print()

    if review:
        print(f"\n  Need Review ({len(review)}):")
        for t in review:
            print(f"  {t.symbol:6s} | {t.company_name[:40]:40s} | "
                  f"Premium: {t.premium_pct:+.1f}% | Score: {t.score}/10")
        print()

    if missing:
        print(f"  Incomplete Data ({len(missing)}):")
        for t in missing:
            print(f"  {t.symbol:6s} | {t.company_name[:40]:40s} | "
                  f"Filed: {t.filing_date} | {t.filing_type}")
        print()

    print(f"  Total: {len(tenders)} tenders | "
          f"Actionable: {len(actionable)} | "
          f"Review: {len(review)} | "
          f"Incomplete: {len(missing)}\n")


def cmd_analyze(args):
    """Deep-dive a specific tender offer."""
    print(f"\n  Fetching tender details for {args.symbol.upper()}...\n")
    # This is where the AI should read the actual SEC filing
    print(f"  Open this filing in your browser to analyze:")
    print(f"  https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={args.symbol}&type=SC+TO-I")
    print(f"\n  Then run /oddly to have the AI evaluate the opportunity.\n")


def cmd_portfolio():
    """Show current positions and P&L."""
    positions = load_positions()
    cfg = load_config()
    history = load_history()

    if not positions:
        print("\n  No active positions.\n")
    else:
        print(f"\n  PORTFOLIO (Capital: ${cfg.capital:,.2f})\n")
        print(f"  {'Sym':6s} | {'Entry':8s} | {'Shares':6s} | {'Tender':8s} | {'Prem':6s} | {'Profit':8s} | {'Deadline':12s}")
        print(f"  {'-' * 80}")

        for p in positions:
            print(f"  {p.symbol:6s} | ${p.entry_price:<7.2f} | {p.shares:6d} | "
                  f"${p.tender_price:<7.2f} | {p.premium_pct:+.1f}% | "
                  f"${p.expected_profit:<7.2f} | {p.tender_deadline:12s}")

        print()

    if history:
        total_pnl = sum(h["pnl_pct"] for h in history)
        wins = sum(1 for h in history if h["pnl_pct"] > 0)
        print(f"  History: {len(history)} trades | {wins} wins | Total P&L: {total_pnl:+.1f}%\n")
    else:
        print("  No trade history yet.\n")


def cmd_buy(args):
    """Log a new position."""
    if args.entry_price <= 0:
        print("\n  Error: entry_price must be > 0\n")
        return
    if args.shares <= 0 or args.shares > 99:
        print("\n  Error: shares must be 1-99 (odd-lot limit)\n")
        return
    if args.tender_price <= args.entry_price:
        print("\n  Error: tender_price must be > entry_price (no profit)\n")
        return

    positions = load_positions()
    cfg = load_config()

    symbol = args.symbol.upper()
    entry_price = args.entry_price
    shares = args.shares
    tender_price = args.tender_price
    deadline = args.deadline or "unknown"

    premium = (tender_price / entry_price - 1) * 100
    expected_profit = (tender_price - entry_price) * shares

    pos = Position(
        symbol=symbol,
        entry_price=entry_price,
        entry_date=datetime.now().strftime("%Y-%m-%d"),
        shares=shares,
        tender_price=tender_price,
        tender_deadline=deadline,
        premium_pct=round(premium, 1),
        expected_profit=round(expected_profit, 2),
    )

    positions.append(pos)
    save_positions(positions)

    print(f"\n  BOUGHT {shares} {symbol} @ ${entry_price:.2f}")
    print(f"  Tender price: ${tender_price:.2f} (+{premium:.1f}%)")
    print(f"  Expected profit: ${expected_profit:.2f}")
    print(f"  Deadline: {deadline}\n")


def cmd_sell(args):
    """Close a position."""
    positions = load_positions()
    symbol = args.symbol.upper()

    survivors = []
    closed = None
    for p in positions:
        if p.symbol == symbol:
            closed = p
        else:
            survivors.append(p)

    if not closed:
        print(f"\n  No position found for {symbol}\n")
        return

    exit_price = args.exit_price
    pnl = (exit_price - closed.entry_price) / closed.entry_price * 100
    reason = args.reason or "manual"

    save_positions(survivors)
    log_trade(closed, exit_price, pnl, datetime.now().strftime("%Y-%m-%d"), reason)

    print(f"\n  SOLD {symbol}: ${closed.entry_price:.2f} → ${exit_price:.2f} ({pnl:+.1f}%)")
    print(f"  Reason: {reason}")
    print(f"  Remaining positions: {len(survivors)}\n")


def main():
    parser = argparse.ArgumentParser(
        prog="oddly",
        description="Oddly -- AI-powered special situations arbitrage scanner",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("scan", help="Scan SEC EDGAR for tender offers and spin-offs")
    setup_p = sub.add_parser("setup", help="Configure capital, risk, preferences")
    setup_p.add_argument("--capital", type=float, help="Total trading capital (e.g. 500, 1000)")
    setup_p.add_argument("--max-positions", type=int, help="Max simultaneous positions")
    setup_p.add_argument("--min-premium", type=float, help="Minimum tender premium percentage")
    sub.add_parser("portfolio", help="View positions, P&L, trade history")

    analyze_p = sub.add_parser("analyze", help="Deep-dive a specific SEC filing")
    analyze_p.add_argument("symbol", help="Stock symbol (e.g. XYZ)")

    buy_p = sub.add_parser("buy", help="Log a special situations position")
    buy_p.add_argument("symbol", help="Stock symbol")
    buy_p.add_argument("entry_price", type=float, help="Entry price per share")
    buy_p.add_argument("shares", type=int, help="Number of shares (max 99)")
    buy_p.add_argument("tender_price", type=float, help="Tender offer price")
    buy_p.add_argument("--deadline", help="Tender deadline (YYYY-MM-DD)")

    sell_p = sub.add_parser("sell", help="Close a position and record P&L")
    sell_p.add_argument("symbol", help="Stock symbol")
    sell_p.add_argument("exit_price", type=float, help="Exit price per share")
    sell_p.add_argument("--reason", help="Reason: tendered, expired, manual")

    args = parser.parse_args()

    if args.command == "scan":
        cmd_scan()
    elif args.command == "setup":
        cmd_setup(args)
    elif args.command == "portfolio":
        cmd_portfolio()
    elif args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "buy":
        cmd_buy(args)
    elif args.command == "sell":
        cmd_sell(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
