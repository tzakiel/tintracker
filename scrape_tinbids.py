"""Tinbids source — tobacco listings from tinbids.com (one file, two sources).

TinBids items come in two shapes: auction-only, and auctions that also carry a
Buy-It-Now price. We classify each into one of two sources in a single file:

  • "Tinbids BIN"     — any live listing that has a Buy-It-Now price. It stays
                        BIN for as long as it's live, even once it's taking bids.
  • "Tinbids Auction" — a listing's FINAL price, recorded only once it has ended
                        AND it sold via bidding (>0 bids). An item that ends via
                        Buy-It-Now or expires unsold stays BIN.

The final price only exists once an auction ends, and ended auctions drop off
the browse page — so we keep a watchlist of every listing's URL + end date and
revisit each page after it ends to read "Sold for: $X [N Bids]". An item that
ends as an auction flips its source from BIN to Auction.

Runs daily. Shared logic lives in scrape_core.py.
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
BIN_SOURCE = "Tinbids BIN"
AUCTION_SOURCE = "Tinbids Auction"
DATA_FILE = os.path.join(os.path.dirname(__file__), "docs", "products_tinbids.json")

MAX_ATTEMPTS = 4            # whole-scrape retries (used only on a total block)
RETRY_WAIT_SECONDS = 20
PAGE_DELAY = 1.2            # politeness between pages — avoids 503 rate-limiting
PAGE_RETRIES = 4           # per-page retries on transient 503/timeout
MAX_REVISITS_PER_RUN = 120  # bound runtime; overdue leftovers wait for next run


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
    """From an ended auction page, read the sale. Returns (closed?, price_or_None).

    "Sold for: $X [N Bids]" — only a sale with at least one bid counts as an
    auction result; "Sold for: $ [0 Bids]" means it ended without selling.
    """
    closed = ("wpa-auction-closed" in html) or ("Auction closed" in html)
    if not closed:
        return False, None
    m = re.search(r"Sold for:\s*\$([\d,]+\.\d{2})\s*(?:<[^>]*>)*\s*\[(\d+)\s*Bids?\]", html)
    if m and int(m.group(2)) > 0:
        return True, f"${m.group(1)}"
    return True, None


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

    # ── BIN side: any live listing that has a Buy-It-Now price stays "BIN"
    #    while it's live — even once it's taking bids. ──────────────────────────
    def has_bin(x):
        return x["bin_price"] not in (None, "", "0", "0.00")

    bin_found = [
        {"name": x["name"], "price": f"${x['bin_price']}", "url": x["url"], "source": BIN_SOURCE}
        for x in listings if has_bin(x)
    ]

    # ── Watchlist: track EVERY live listing so we can revisit it after it ends.
    pending = {p["url"]: p for p in data.get("pending", []) if p.get("url")}
    for x in listings:
        if x["url"]:
            pending[x["url"]] = {"url": x["url"], "name": x["name"], "date_end": x["date_end"]}

    def is_due(p):
        try:
            return datetime.strptime(p["date_end"], "%Y-%m-%d %H:%M:%S") < now_naive
        except (TypeError, ValueError):
            return False

    # ── Revisit ended listings. A listing only becomes a "Tinbids Auction"
    #    record if it ended WITH bids (sold via bidding). If it ended via
    #    Buy-It-Now / expired (0 bids), we leave it as-is — a BIN item stays BIN.
    due = [p for p in pending.values() if is_due(p)][:MAX_REVISITS_PER_RUN]
    auction_found = []
    if due and session is None:
        session = cloudscraper.create_scraper()
    for p in due:
        try:
            html = session.get(p["url"], timeout=30).text
        except Exception as e:
            print(f"[Tinbids] revisit error {p['url']}: {e}")
            continue
        closed, sold_price = _parse_ended_sale(html)
        if not closed:
            continue  # not actually ended yet (e.g. timezone slack) — keep watching
        if sold_price:  # ended as an auction → switch this item to the auction source
            auction_found.append({
                "name": p["name"], "price": sold_price, "url": p["url"], "source": AUCTION_SOURCE,
            })
        pending.pop(p["url"], None)  # ended (auction sale, BIN sale, or unsold) — stop watching
        time.sleep(0.4)

    # Merge BIN listings, then auction results. Merging auctions second lets an
    # item that ended as an auction flip its source from BIN to Auction.
    scrape_core.merge_products(data, bin_found, now)
    scrape_core.merge_products(data, auction_found, now)

    # Homepage snapshot: currently-live BIN listings + every auction result.
    bin_live = {x["name"] for x in bin_found}
    data["latest_scrape"] = [
        p for p in data["products"]
        if p["source"] == AUCTION_SOURCE or (p["source"] == BIN_SOURCE and p["name"] in bin_live)
    ]
    data["pending"] = list(pending.values())
    scrape_core.save(data, DATA_FILE)

    n_auction = sum(1 for p in data["products"] if p["source"] == AUCTION_SOURCE)
    print(f"[Tinbids] {len(bin_found)} live BIN listings, +{len(auction_found)} auction sales this run. "
          f"Catalog: {len(data['products'])} ({n_auction} auction). Watching: {len(pending)}.")


if __name__ == "__main__":
    main()
