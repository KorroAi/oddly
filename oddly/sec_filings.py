"""SEC EDGAR client — find odd-lot tender offers before they close."""
import json
import time
import re
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import xml.etree.ElementTree as ET

import requests
import yfinance as yf

CACHE_DIR = Path(__file__).parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)
TICKERS_CACHE = CACHE_DIR / "company_tickers.json"

SEC_HEADERS = {
    "User-Agent": "Oddly/1.0 (korrocorp@proton.me) AI-powered odd-lot tender scanner",
    "Accept": "application/json, application/xml, */*",
}

TENDER_FORMS = ["SC TO-I", "SC TO-T", "SC 13E3", "SC TO-C"]
SPINOFF_FORMS = ["10-12B", "10-12B/A"]
RIGHTS_FORMS = ["S-3", "FWP"]  # rights offerings often filed under these
RATE_LIMIT = 0.12  # ~8 req/sec, SEC limit is 10/sec

# Lookback windows per strategy
LOOKBACK = {
    "tender": 45,
    "tender_third_party": 45,
    "spinoff": 90,
    "rights": 60,
}


@dataclass
class Opportunity:
    symbol: str
    company_name: str
    cik: str
    filing_date: str
    filing_type: str
    filing_url: str
    strategy: str = "tender"  # tender, spinoff, rights
    current_price: float = 0.0
    target_price: float = 0.0  # tender price, NAV, or spin-off estimated value
    premium_pct: float = 0.0
    odd_lot_shares: int = 99
    odd_lot_provision: bool = False
    deadline: str = ""
    condition: str = ""
    status: str = "unknown"
    still_active: bool = True
    notes: str = ""
    score: int = 0


def _load_ticker_map() -> dict[str, dict]:
    """Load CIK-to-ticker mapping, cached for 24h."""
    if TICKERS_CACHE.exists():
        age = time.time() - TICKERS_CACHE.stat().st_mtime
        if age < 86400:
            try:
                data = json.loads(TICKERS_CACHE.read_text())
                return {str(v["cik_str"]): v for v in data.values()}
            except (json.JSONDecodeError, KeyError):
                TICKERS_CACHE.unlink(missing_ok=True)

    url = "https://www.sec.gov/files/company_tickers.json"
    try:
        resp = requests.get(url, headers=SEC_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        TICKERS_CACHE.write_text(json.dumps(data))
        time.sleep(RATE_LIMIT)
        return {str(v["cik_str"]): v for v in data.values()}
    except Exception:
        # SEC API down or cache corrupt — return empty, will use submissions API fallback
        return {}


def _cik_to_ticker(cik: str, ticker_map: dict) -> Optional[str]:
    """Map a CIK (with or without leading zeros) to a ticker symbol."""
    cik_clean = cik.lstrip("0")
    for key, val in ticker_map.items():
        if key == cik_clean:
            return val["ticker"]

    # Try to find by padded CIK in submissions data
    submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        resp = requests.get(submissions_url, headers=SEC_HEADERS, timeout=15)
        time.sleep(RATE_LIMIT)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("tickers", [None])[0]
    except Exception:
        pass
    return None


def _extract_cik_from_url(url: str) -> Optional[str]:
    """Extract CIK from SEC filing URL or URN."""
    match = re.search(r'cik(?:=|/)(\d+)', url, re.IGNORECASE)
    if match:
        return match.group(1).lstrip("0")

    match = re.search(r'data/(\d+)/', url)
    if match:
        return match.group(1).lstrip("0")

    return None


def _extract_accession_from_url(url: str) -> Optional[str]:
    """Extract accession number from SEC URL."""
    match = re.search(r'accession_number=(\d{10}-\d{2}-\d{6})', url)
    if match:
        return match.group(1)
    return None


def _filing_text_urls(url: str) -> list[str]:
    """Generate candidate URLs for the filing plain text (full submission)."""
    urls = []
    # URL from ATOM feed: .../ACCESSION-index.htm → .../ACCESSION.txt
    if "-index.htm" in url or "-index.html" in url:
        base = re.sub(r'-index\.html?$', '', url)
        # base is now .../ACCESSION (the accession number without -index.htm)
        urls.append(base + ".txt")
    elif url.endswith(".htm") or url.endswith(".html"):
        urls.append(re.sub(r'\.html?$', '.txt', url))
    else:
        urls.append(url)
    return urls


def _parse_tender_filing_html(url: str) -> dict:
    """Attempt to parse tender price and odd-lot provision from filing."""
    result = {"tender_price": 0.0, "odd_lot_shares": 99, "deadline": "", "condition": "", "odd_lot_provision": False}

    text = ""
    for candidate_url in _filing_text_urls(url):
        try:
            resp = requests.get(candidate_url, headers={**SEC_HEADERS, "Accept": "text/plain, text/html"}, timeout=20)
            time.sleep(RATE_LIMIT)
            if resp.status_code == 200 and len(resp.text) > 500:
                text = resp.text[:80000]
                break
        except Exception:
            continue

    if not text:
        return result

    try:
        # Look for tender price patterns
        price_patterns = [
            r'(?:tender|offer|purchase)\s+price\s+(?:of|is|:)\s*\$?(\d+\.?\d*)',
            r'\$(\d+\.?\d*)\s+per\s+share',
            r'(?:price|consideration)\s+(?:of|is|:)\s*\$(\d+\.?\d*)',
            r'cash\s+(?:payment|consideration)\s+(?:of|is|:)\s*\$(\d+\.?\d*)',
        ]
        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["tender_price"] = float(match.group(1))
                break

        # Look for odd-lot provision
        odd_lot_patterns = [
            r'odd[\s-]*lot[\s\w]*(\d+)\s*(?:share|stock)',
            r'(?:less than|fewer than|under)\s+(\d+)\s+shares',
            r'(?:holders? of|owning)\s+(?:less than|fewer than|under)\s+(\d+)\s+share',
            r'odd[\s-]*lot[\s\w]*provision',
            r'odd[\s-]*lot[\s\w]*tender',
        ]
        for pattern in odd_lot_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    result["odd_lot_shares"] = int(match.group(1))
                except (IndexError, ValueError):
                    pass
                result["odd_lot_provision"] = True
                break

        # Look for deadline
        deadline_patterns = [
            r'(?:expir|deadline|terminat).*?(\w+\s+\d{1,2},?\s*\d{4})',
            r'(?:until|through|close).*?(\w+\s+\d{1,2},?\s*\d{4})',
            r'(\d{1,2}:\d{2}\s*[AP]M).*?(\w+\s+\d{1,2},?\s*\d{4})',
        ]
        for pattern in deadline_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["deadline"] = match.group(1) if len(match.groups()) == 1 else " ".join(match.groups())
                break

        # Check conditions
        if "minimum" in text.lower() and "tender" in text.lower():
            cond_match = re.search(r'minimum\s+(?:of\s+)?(\d+[\.,]?\d*\s*%?)', text, re.IGNORECASE)
            if cond_match:
                result["condition"] = f"Minimum {cond_match.group(1)} shares tendered"

        if "subject to" in text.lower():
            result["condition"] = result.get("condition", "") + " — Subject to conditions"

    except Exception:
        pass

    return result


def get_recent_tenders(days: int = 30) -> list[Opportunity]:
    """Fetch recent tender offers from SEC EDGAR current filings feed."""
    tenders = []
    ticker_map = _load_ticker_map()

    for form_type in TENDER_FORMS:
        url = (
            f"https://www.sec.gov/cgi-bin/browse-edgar"
            f"?action=getcurrent&type={form_type.replace(' ', '%20')}"
            f"&count=40&output=atom"
        )

        try:
            resp = requests.get(url, headers=SEC_HEADERS, timeout=15)
            time.sleep(RATE_LIMIT)

            if resp.status_code != 200:
                continue

            root = ET.fromstring(resp.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            for entry in root.findall("atom:entry", ns):
                title = entry.find("atom:title", ns)
                updated = entry.find("atom:updated", ns)
                link = entry.find("atom:link", ns)
                summary = entry.find("atom:summary", ns)

                if title is None:
                    continue

                title_text = title.text or ""
                filing_url = link.get("href", "") if link is not None else ""
                updated_date = updated.text[:10] if updated is not None and updated.text else ""

                # Only keep recent filings
                if updated_date:
                    try:
                        filing_dt = datetime.strptime(updated_date, "%Y-%m-%d")
                        if (datetime.now() - filing_dt) > timedelta(days=days):
                            continue
                    except ValueError:
                        pass

                # Extract company name from title (format: "COMPANY NAME - FORM TYPE")
                company_name = title_text.split(" - ")[0].strip()

                # Extract CIK from URL
                cik = _extract_cik_from_url(filing_url)
                if not cik:
                    continue

                # Map to ticker
                symbol = _cik_to_ticker(cik, ticker_map)
                if not symbol:
                    continue

                # SC TO-T = third-party tender: filer is BIDDER, ticker is WRONG.
                # AI must read filing to find the TARGET company's ticker.
                strategy = "tender_third_party" if form_type == "SC TO-T" else "tender"

                tender = Opportunity(
                    symbol=symbol.upper(),
                    company_name=company_name,
                    cik=cik,
                    filing_date=updated_date,
                    filing_type=form_type,
                    filing_url=filing_url,
                    strategy=strategy,
                )

                tenders.append(tender)

        except Exception:
            continue

    # Deduplicate by symbol
    seen = set()
    unique = []
    for t in tenders:
        if t.symbol not in seen:
            seen.add(t.symbol)
            unique.append(t)

    return unique


def enrich_opportunity(opp: Opportunity) -> Opportunity:
    """Add market price, parse filing, apply Gate 0 (still active check)."""
    # Gate 0: Is this still actionable?
    opp.still_active = _check_still_active(opp)

    # Get current price
    try:
        ticker = yf.Ticker(opp.symbol)
        info = ticker.fast_info
        opp.current_price = getattr(info, "last_price", 0.0) or getattr(info, "regular_market_previous_close", 0.0)
    except Exception:
        pass

    # Try to parse the filing for details
    details = _parse_tender_filing_html(opp.filing_url)
    opp.target_price = details["tender_price"]
    opp.odd_lot_shares = details["odd_lot_shares"]
    opp.odd_lot_provision = details.get("odd_lot_provision", False)
    opp.deadline = details["deadline"]
    opp.condition = details["condition"]

    # Re-check active status with parsed deadline
    if opp.deadline and not opp.still_active:
        opp.still_active = _verify_deadline(opp.deadline)

    # Calculate premium
    if opp.target_price > 0 and opp.current_price > 0:
        opp.premium_pct = round((opp.target_price / opp.current_price - 1) * 100, 1)

    # Score (0-10) — quick automated pass, AI does final scoring
    score = 0
    if opp.premium_pct > 5:
        score += 3
    elif opp.premium_pct > 2:
        score += 1
    if opp.odd_lot_provision:
        score += 3
    if opp.target_price > 0:
        score += 2
    if opp.current_price > 1:
        score += 1
    if opp.still_active:
        score += 1
    opp.score = min(10, score)

    # Status
    if not opp.still_active:
        opp.status = "expired"
    elif opp.premium_pct > 5 and opp.odd_lot_provision:
        opp.status = "actionable"
    elif opp.target_price > 0:
        opp.status = "review_needed"
    else:
        opp.status = "data_missing"

    return opp


def _check_still_active(opp: Opportunity) -> bool:
    """Gate 0: verify the opportunity hasn't expired based on filing date."""
    if not opp.filing_date:
        return False  # No date = can't verify = assume expired

    try:
        filing_dt = datetime.strptime(opp.filing_date, "%Y-%m-%d")
        max_age = LOOKBACK.get(opp.strategy, 45)
        if (datetime.now() - filing_dt) > timedelta(days=max_age):
            return False
    except ValueError:
        return False  # Can't parse date = can't verify = assume expired

    return True


def _verify_deadline(deadline_str: str) -> bool:
    """Check if a parsed deadline is still in the future. Returns True only if VERIFIED."""
    for fmt in ["%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%m/%d/%Y"]:
        try:
            dl = datetime.strptime(deadline_str.strip(), fmt)
            return dl > datetime.now()
        except ValueError:
            continue
    return False  # Can't parse = can't verify = NOT confirmed active


def get_recent_spinoffs(days: int = 90) -> list[Opportunity]:
    """Fetch recent spin-off registrations from SEC EDGAR."""
    spinoffs = []
    ticker_map = _load_ticker_map()

    for form_type in SPINOFF_FORMS:
        url = (
            f"https://www.sec.gov/cgi-bin/browse-edgar"
            f"?action=getcurrent&type={form_type}"
            f"&count=40&output=atom"
        )
        try:
            resp = requests.get(url, headers=SEC_HEADERS, timeout=15)
            time.sleep(RATE_LIMIT)
            if resp.status_code != 200:
                continue

            root = ET.fromstring(resp.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            for entry in root.findall("atom:entry", ns):
                title = entry.find("atom:title", ns)
                updated = entry.find("atom:updated", ns)
                link = entry.find("atom:link", ns)

                if title is None:
                    continue

                title_text = title.text or ""
                filing_url = link.get("href", "") if link is not None else ""
                updated_date = updated.text[:10] if updated is not None and updated.text else ""

                if updated_date:
                    try:
                        filing_dt = datetime.strptime(updated_date, "%Y-%m-%d")
                        if (datetime.now() - filing_dt) > timedelta(days=days):
                            continue
                    except ValueError:
                        pass

                company_name = title_text.split(" - ")[0].strip()
                cik = _extract_cik_from_url(filing_url)
                if not cik:
                    continue

                symbol = _cik_to_ticker(cik, ticker_map)
                if not symbol:
                    continue

                spinoffs.append(Opportunity(
                    symbol=symbol.upper(),
                    company_name=company_name,
                    cik=cik,
                    filing_date=updated_date,
                    filing_type=form_type,
                    filing_url=filing_url,
                    strategy="spinoff",
                ))
        except Exception:
            continue

    seen = set()
    unique = []
    for s in spinoffs:
        if s.symbol not in seen:
            seen.add(s.symbol)
            unique.append(s)

    return unique


def scan_opportunities() -> list[Opportunity]:
    """Full scan: tenders + spin-offs, enriched, scored, filtered."""
    tenders = get_recent_tenders(LOOKBACK["tender"])
    spinoffs = get_recent_spinoffs(LOOKBACK["spinoff"])

    all_opps = tenders + spinoffs
    enriched = [enrich_opportunity(o) for o in all_opps]

    # Filter out expired
    active = [o for o in enriched if o.still_active]
    active.sort(key=lambda o: o.score, reverse=True)

    return active
