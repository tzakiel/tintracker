"""Tinbids source — records actual SALES from tinbids.com (sold prices only).

We never record asking prices or in-progress listings — only what actually sold:

  • "Tinbids BIN"     — sold via Buy-It-Now (ended with a price and 0 bids).
  • "Tinbids Auction" — sold via bidding with the reserve met (ended with a
                        price and >0 bids).

Unsold listings, in-progress listings, and bid-but-reserve-not-met auctions are
never recorded. A sale only becomes visible once a listing ends, and ended
listings drop off the browse page — so each run keeps a watchlist of every live
listing's URL + end date, then revisits each page after it ends and reads the
"Sold for: $X [N Bids]" line (the one display that means a completed sale).

Runs twice daily. Shared logic lives in scrape_core.py.
"""
import os
import re
import sys
import time
from datetime import datetime, timezone

import cloudscraper
from bs4 import BeautifulSoup, Comment

import scrape_core

# Scrape the FULL category (not the buy-it-now filter, which hides auction-only
# listings). "ending-soon" returns every tobacco listing, ~624 vs ~360.
BASE_URL = "https://tinbids.com/browse/?category=tobaccos&sort=ending-soon"
BIN_SOURCE = "Tinbids BIN (Sold)"
AUCTION_SOURCE = "Tinbids Auction (Sold)"
DATA_FILE = os.path.join(os.path.dirname(__file__), "docs", "products_tinbids.json")

MAX_ATTEMPTS = 4            # whole-scrape retries (used only on a total block)
RETRY_WAIT_SECONDS = 20
PAGE_DELAY = 1.2            # politeness between pages — avoids 503 rate-limiting
PAGE_RETRIES = 4           # per-page retries on transient 503/timeout
MAX_REVISITS_PER_RUN = 300  # bound runtime; comfortably above the ~140/day peak
                            # of endings, so a day's auctions all harvest same-run


def _page_url(n):
    if n == 1:
        return BASE_URL
    return f"https://tinbids.com/browse/page/{n}/?category=tobaccos&sort=ending-soon"


def _field(comment_text, name):
    """Read one field out of the var_dump object embedded in each listing."""
    m = re.search(
        r'\["' + re.escape(name) + r'"\]=>\s*\n?\s*'
        r'(?:string\(\d+\)\s*"([^"]*)"|int\((\d+)\)|(NULL))',
        comment_text,
    )
    if not m:
        return None
    if m.group(3):
        return None  # NULL
    return m.group(1) if m.group(1) is not None else m.group(2)


def _parse_listing(el):
    title_el = el.select_one(".auction-entry-title a")
    if not title_el:
        return None
    comments = [c for c in el.descendants if isinstance(c, Comment) and "date_end" in c]
    data = comments[0] if comments else ""
    return {
        "name": title_el.get_text(strip=True),
        "url": title_el.get("href", ""),
        "bin_price": _field(data, "BIN_price"),
        "bid_count": int(_field(data, "bid_count") or 0),
        "date_end": _field(data, "date_end"),  # "YYYY-MM-DD HH:MM:SS", site local time
    }


def _get(session, url):
    """GET with per-request retries on transient errors (503, timeouts)."""
    last = None
    for i in range(PAGE_RETRIES):
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            return resp
        except Exception as e:
            last = e
            time.sleep(2 * (i + 1))  # 2s, 4s, 6s…
    raise last


def fetch_listings():
    """One full attempt: walk every browse page. Tolerates a page that keeps
    failing by returning what was gathered so far (partial is better than none —
    the catalog never deletes unseen items, it just doesn't refresh them)."""
    session = cloudscraper.create_scraper()
    listings = []

    soup = BeautifulSoup(_get(session, _page_url(1)).text, "lxml")
    entries = soup.select(".auction-entry")
    if not entries:
        return [], session

    max_page = 1
    for a in soup.select(".page-numbers"):
        t = a.get_text(strip=True).replace(",", "")
        if t.isdigit():
            max_page = max(max_page, int(t))

    def collect(soup):
        for el in soup.select(".auction-entry"):
            item = _parse_listing(el)
            if item and item["name"]:
                listings.append(item)

    collect(soup)

    for n in range(2, max_page + 1):
        time.sleep(PAGE_DELAY)
        try:
            page_soup = BeautifulSoup(_get(session, _page_url(n)).text, "lxml")
        except Exception as e:
            print(f"[Tinbids] page {n} failed after retries ({e}); "
                  f"continuing with {len(listings)} listings gathered so far.")
            break
        if not page_soup.select(".auction-entry"):
            break
        collect(page_soup)

    return listings, session


def fetch_listings_with_retry():
    """Retry the browse scrape — blocking is intermittent."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            listings, session = fetch_listings()
        except Exception as e:
            print(f"[Tinbids] attempt {attempt}/{MAX_ATTEMPTS} error: {e}")
            listings, session = [], None
        if listings:
            print(f"[Tinbids] attempt {attempt}/{MAX_ATTEMPTS} succeeded: {len(listings)} listings.")
            return listings, session
        if attempt < MAX_ATTEMPTS:
            print(f"[Tinbids] attempt {attempt}/{MAX_ATTEMPTS} found 0 — retrying in {RETRY_WAIT_SECONDS}s…")
            time.sleep(RETRY_WAIT_SECONDS)
    return [], None


def _parse_ended_sale(html):
    """From an ended auction page, read the outcome. Returns (closed?, price, bids).

    A real sale always renders "Sold for: $<number> [N Bids]":
      • N == 0  → sold via Buy-It-Now            → Tinbids BIN
      • N  > 0  → sold via bidding (reserve met) → Tinbids Auction
    Everything that did NOT sell renders differently and yields price=None:
      • unsold            → "Sold for: $ [0 Bids]"   (no number)
      • reserve not met   → "Highest Bid: $X [N Bids]" (says "Highest Bid", not "Sold for")
    """
    closed = ("wpa-auction-closed" in html) or ("Auction closed" in html)
    if not closed:
        return False, None, 0
    m = re.search(r"Sold for:\s*\$([\d,]+\.\d{2})\s*(?:<[^>]*>)*\s*\[(\d+)\s*Bids?\]", html)
    if m:
        return True, f"${m.group(1)}", int(m.group(2))
    return True, None, 0


def main():
    now = datetime.now(timezone.utc).isoformat()
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)

    listings, session = fetch_listings_with_retry()

    # Guard: blocked browse scrape must never wipe either catalog.
    if not listings:
        print("[Tinbids] ERROR: 0 listings found — keeping previous data unchanged. "
              "Likely blocked; not committing.", file=sys.stderr)
        sys.exit(1)

    data = scrape_core.load_existing(DATA_FILE)

    # ── Watchlist: track EVERY live listing so we can revisit it after it ends.
    #    Nothing is recorded while a listing is live — we only capture SALES.
    pending = {p["url"]: p for p in data.get("pending", []) if p.get("url")}
    for x in listings:
        if x["url"]:
            pending[x["url"]] = {"url": x["url"], "name": x["name"], "date_end": x["date_end"]}

    def is_due(p):
        try:
            return datetime.strptime(p["date_end"], "%Y-%m-%d %H:%M:%S") < now_naive
        except (TypeError, ValueError):
            return False

    # ── Revisit ended listings and record ONLY confirmed sales:
    #      sold with 0 bids  → Buy-It-Now sale   → Tinbids BIN
    #      sold with >0 bids → auction sale      → Tinbids Auction
    #    In-progress, unsold, and reserve-not-met listings are never recorded.
    due = sorted((p for p in pending.values() if is_due(p)),
                 key=lambda p: p["date_end"] or "")[:MAX_REVISITS_PER_RUN]
    sold_found = []
    if due and session is None:
        session = cloudscraper.create_scraper()
    revisit_errors = 0
    for p in due:
        try:
            html = _get(session, p["url"]).text  # same retry window as browse —
                                                  # a single GET gets Cloudflare-blocked
                                                  # from CI datacenter IPs
        except Exception as e:
            revisit_errors += 1
            print(f"[Tinbids] revisit error {p['url']}: {e}")
            continue
        closed, sold_price, bids = _parse_ended_sale(html)
        if not closed:
            continue  # not actually ended yet (e.g. timezone slack) — keep watching
        if sold_price:
            sold_found.append({
                "name": p["name"], "price": sold_price, "url": p["url"],
                "source": AUCTION_SOURCE if bids > 0 else BIN_SOURCE,
            })
        pending.pop(p["url"], None)  # ended (sold or not) — stop watching
        time.sleep(0.4)

    # If most revisits failed we're likely being blocked — surface it loudly so a
    # block doesn't look like a quiet "no sales today" (data is still kept).
    if due and revisit_errors > len(due) // 2:
        print(f"[Tinbids] WARNING: {revisit_errors}/{len(due)} revisits failed — "
              f"likely blocked; sales may be undercounted this run.", file=sys.stderr)

    scrape_core.merge_products(data, sold_found, now)
    # The catalog is entirely sales, so the homepage snapshot is all of them.
    data["latest_scrape"] = list(data["products"])
    data["pending"] = list(pending.values())
    scrape_core.save(data, DATA_FILE)

    n_auction = sum(1 for p in data["products"] if p["source"] == AUCTION_SOURCE)
    n_bin = sum(1 for p in data["products"] if p["source"] == BIN_SOURCE)
    print(f"[Tinbids] +{len(sold_found)} sales this run. "
          f"Catalog: {len(data['products'])} sales ({n_bin} BIN, {n_auction} auction). "
          f"Watching: {len(pending)}.")


if __name__ == "__main__":
    main()
