"""Speak-Easy.Club source — WTS, SOLD, and CLOSED tin listings from the marketplace.

Login-required XenForo 2.x forum. Credentials come from SPEAKEASY_USERNAME and
SPEAKEASY_PASSWORD environment variables (set via GitHub Secrets).

Run strategy:
  • First run (no prior data): bootstraps up to MAX_AGE_DAYS back.
  • Subsequent runs: only visits threads with activity since the last scrape,
    PLUS any thread seen within RECHECK_DAYS (to catch silent OP edits).
  • Set SPEAKEASY_BACKFILL=1 to force a full MAX_AGE_DAYS lookback regardless
    of last_scraped (used for the one-time historical backfill).
  • Legitimately finding zero new listings is not treated as a failure — only
    an inaccessible forum page triggers a hard exit.

Collects WTS (active), SOLD, and CLOSED threads. CLOSED threads are filtered
by a title-text blocklist of non-sale types (WTT, WTB, Giveaway, etc.) since
XenForo does not retain the original tag after a thread is closed. Price-signal
presence in the first post is the final guard. Each listing record carries a
"tag" field for future use; not surfaced in the UI.

Runs daily. Writes docs/products_speakeasy.json. Shared logic in scrape_core.py.
"""
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone

import cloudscraper
from bs4 import BeautifulSoup, NavigableString

import scrape_core

BASE_URL = "https://speak-easy.club"
FORUM_URL = f"{BASE_URL}/forums/market.39/"
SOURCE = "Speak-Easy.Club"
DATA_FILE = os.path.join(os.path.dirname(__file__), "docs", "products_speakeasy.json")

PAGE_DELAY = 1.5   # seconds between forum index pages
POST_DELAY = 1.2   # seconds between individual thread fetches
MAX_AGE_DAYS = 2 * 365  # bootstrap lookback when no prior scrape exists
RECHECK_DAYS = 10  # re-visit recently-seen threads to catch silent OP edits

# CLOSED threads whose title contains any of these terms are skipped — they are
# non-sale types (trades, giveaways, etc.) that lose their original tag when closed.
# PENDING is intentionally absent: pending sales are worth collecting.
CLOSED_BLOCKLIST = [
    "wtt", "wtb", "to trade", "giveaway", "contest", "pif",
    "baccyball", "sampleswap", "expired", "deal",
]


def _find_price(line):
    """Return (re.Match, price_str) for the best price signal on this line.

    Three patterns tried in descending confidence:
      1. Explicit $ amount      — "$85", "$85.00"
      2. Number + sale keyword  — "85 shipped", "85 obo", "85 ppd", "85 tyd"
      3. Bare number after a separator at line-end — "MacBaren HH | 85"
         Range-checked to 5–999 to exclude years (2014) and weights (100).

    Returns (None, None) when no price signal is found.
    """
    # 1. Explicit dollar sign
    m = re.search(r'\$\s*(\d[\d,]*(?:\.\d{1,2})?)', line)
    if m:
        return m, f"${m.group(1).replace(',', '')}"

    # 2. Number followed by a shipping / sale keyword
    m = re.search(
        r'\b(\d+(?:\.\d{1,2})?)\s*(?:dollars?)?\s*'
        r'(?:shipped|obo|ppd|tyd|takes?\s+it|each\b|ea\b)',
        line, re.I,
    )
    if m:
        return m, f"${m.group(1)}"

    # 3. Bare number after a separator, near the end of the line
    m = re.search(r'[-–|:]\s*(\d+(?:\.\d{1,2})?)\s*(?:\w+\s*)?$', line.rstrip())
    if m:
        val = float(m.group(1))
        if 5 <= val <= 999:
            return m, f"${m.group(1)}"

    return None, None


def _xf_token(session, url):
    """Fetch a page and return XenForo's CSRF token (_xfToken or csrf meta)."""
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    el = (soup.select_one('input[name="_xfToken"]')
          or soup.select_one('meta[name="csrf"]'))
    return (el.get("value") or el.get("content") or "") if el else ""


def _login(session):
    username = os.environ["SPEAKEASY_USERNAME"]
    password = os.environ["SPEAKEASY_PASSWORD"]
    token = _xf_token(session, f"{BASE_URL}/login/")
    resp = session.post(f"{BASE_URL}/login/login", data={
        "login": username,
        "password": password,
        "_xfToken": token,
        "remember": "1",
    }, timeout=30)
    resp.raise_for_status()
    if "/login" in resp.url:
        raise RuntimeError(
            "Login failed — check SPEAKEASY_USERNAME / SPEAKEASY_PASSWORD secrets"
        )


def _get_tag(thread_el):
    """Return "WTS", "SOLD", "CLOSED", or None (skip thread)."""
    label = thread_el.select_one(".label")
    if label:
        text = label.get_text(strip=True).upper()
        if "WTS" in text:
            return "WTS"
        if "SOLD" in text:
            return "SOLD"
        if "CLOSED" in text:
            return "CLOSED"
    title_el = (thread_el.select_one(".structItem-title a[data-tp-primary]")
                or thread_el.select_one(".structItem-title a"))
    if title_el:
        t = title_el.get_text(strip=True).upper()
        if t.startswith("[WTS]") or t.startswith("WTS "):
            return "WTS"
        if t.startswith("[SOLD]") or t.startswith("SOLD "):
            return "SOLD"
        if t.startswith("[CLOSED]") or t.startswith("CLOSED "):
            return "CLOSED"
    return None


def _thread_title(thread_el):
    """Return the thread title text, or empty string."""
    title_el = (thread_el.select_one(".structItem-title a[data-tp-primary]")
                or thread_el.select_one(".structItem-title a"))
    return title_el.get_text(strip=True) if title_el else ""


def _is_closed_blocklisted(title):
    """True if the thread title contains a non-sale type marker."""
    lower = title.lower()
    return any(term in lower for term in CLOSED_BLOCKLIST)


def _thread_date(thread_el):
    """Return the thread's latest-activity datetime (UTC), or None if unreadable."""
    time_el = thread_el.select_one(
        ".structItem-latestDate time, .structItem-cell--latest time"
    )
    if not time_el:
        return None
    ts = time_el.get("data-time")
    if ts and ts.isdigit():
        return datetime.fromtimestamp(int(ts), tz=timezone.utc)
    dt_str = time_el.get("datetime", "")
    if dt_str:
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except ValueError:
            pass
    return None


def _thread_url(thread_el):
    title_el = (thread_el.select_one(".structItem-title a[data-tp-primary]")
                or thread_el.select_one(".structItem-title a"))
    if not title_el:
        return None
    href = title_el.get("href", "")
    return href if href.startswith("http") else BASE_URL + href


def _collect_new_urls(session, cutoff):
    """Walk forum pages, returning (url_tag_pairs, forum_ok).

    Collects WTS, SOLD, and CLOSED threads with activity since `cutoff`. CLOSED
    threads matching the blocklist are skipped. Returns a list of (url, tag)
    tuples. forum_ok is False when no thread elements were found on the first
    page — indicating a block or login failure.
    """
    url_tags = []
    page = 1
    forum_ok = False

    while True:
        url = FORUM_URL if page == 1 else f"{FORUM_URL}page-{page}"
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        threads = soup.select(".structItem--thread")
        if not threads:
            break
        forum_ok = True

        any_in_range = False
        for thread in threads:
            dt = _thread_date(thread)
            if dt is not None and dt < cutoff:
                continue
            any_in_range = True
            tag = _get_tag(thread)
            if not tag:
                continue
            if tag == "CLOSED" and _is_closed_blocklisted(_thread_title(thread)):
                continue
            u = _thread_url(thread)
            if u:
                url_tags.append((u, tag))

        if not any_in_range:
            print(f"[{SOURCE}] page {page}: all threads older than cutoff — stopping.")
            break

        if not soup.select_one(".pageNav-jump--next, a[rel='next']"):
            break

        page += 1
        time.sleep(PAGE_DELAY)

    return url_tags, forum_ok


def _table_to_lines(table):
    """Convert an HTML <table> to one 'name price' string per data row.

    Identifies the price column by header text containing 'price', and the
    name column by 'item'/'blend'/'tobacco'/'name'/'desc' (defaults to col 0).
    Falls back to emitting the full pipe-joined row when no price column is
    found, so _find_price can still extract a bare number via pattern 3.
    """
    rows = table.select("tr")
    if not rows:
        return []

    headers = []
    data_start = 0
    for i, row in enumerate(rows):
        ths = row.select("th")
        if ths:
            headers = [th.get_text(strip=True).lower() for th in ths]
            data_start = i + 1
            break

    if not headers and rows:
        tds = rows[0].select("td")
        if tds:
            headers = [td.get_text(strip=True).lower() for td in tds]
            data_start = 1

    price_col = next(
        (i for i, h in enumerate(headers) if "price" in h), None
    )
    name_col = next(
        (i for i, h in enumerate(headers)
         if any(k in h for k in ("item", "blend", "tobacco", "name", "desc"))),
        0,
    )
    # A separate brand/maker column is common in cellar tables (Brand | Blend |
    # … | Price). The blend cell alone ("Kagayaki") has no maker, so prepend the
    # brand cell ("Tsuge") when present and distinct from the name column.
    brand_col = next(
        (i for i, h in enumerate(headers)
         if any(k in h for k in ("brand", "maker", "manufacturer"))),
        None,
    )

    lines = []
    for row in rows[data_start:]:
        cells = row.select("td")
        if not cells:
            continue
        name = cells[name_col].get_text(strip=True) if name_col < len(cells) else ""
        if not name:
            continue
        if brand_col is not None and brand_col != name_col and brand_col < len(cells):
            brand = cells[brand_col].get_text(strip=True)
            if brand and brand.lower() not in name.lower():
                name = f"{brand} {name}".strip()
        price_text = (
            cells[price_col].get_text(strip=True)
            if price_col is not None and price_col < len(cells)
            else ""
        )
        if price_text:
            lines.append(f"{name} {price_text}")
        else:
            lines.append(" | ".join(c.get_text(strip=True) for c in cells))
    return lines


def _parse_first_post(html):
    """Extract (name, price) pairs and post date from the first post of a thread.

    Returns (listings, post_date_iso_or_None). Each line containing a price
    signal yields one listing. Quoted replies and list markers are stripped.
    """
    soup = BeautifulSoup(html, "lxml")

    messages = soup.select(".message--post")
    if not messages:
        return [], None
    post_body = messages[0].select_one(".message-body .bbWrapper")
    if not post_body:
        return [], None

    # Extract the first post's timestamp (thread creation date).
    post_date = None
    time_el = messages[0].select_one(
        ".message-attribution time, .message-date time, "
        ".message-attribution-main time, header time"
    )
    if time_el:
        ts = time_el.get("data-time")
        if ts and ts.isdigit():
            post_date = datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
        else:
            dt_str = time_el.get("datetime", "")
            if dt_str:
                try:
                    post_date = datetime.fromisoformat(
                        dt_str.replace("Z", "+00:00")
                    ).isoformat()
                except ValueError:
                    pass

    for el in post_body.select("blockquote, .bbCodeBlock--quote"):
        el.decompose()

    # Convert tables to one line per data row before text extraction so rows
    # aren't smashed together by get_text().
    for table in post_body.select("table"):
        tbl_lines = _table_to_lines(table)
        table.replace_with(NavigableString("\n" + "\n".join(tbl_lines) + "\n"))

    for el in post_body.select("br"):
        el.replace_with("\n")
    for el in post_body.select("p, li, div"):
        el.insert_before("\n")

    lines = post_body.get_text().splitlines()

    listings = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        m, price = _find_price(line)
        if not m:
            continue

        desc = line[:m.start()].strip()
        desc = re.sub(r'^[\-\*•\d]+[\.\):\s]+', '', desc).strip()
        desc = re.sub(r'[\-–|\.]+\s*$', '', desc).strip()

        if len(desc) < 5:
            continue

        listings.append((desc, price))

    return listings, post_date


def main():
    session = cloudscraper.create_scraper()
    _login(session)

    data = scrape_core.load_existing(DATA_FILE)
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    # SPEAKEASY_BACKFILL=1 forces the full 2-year lookback for the one-time
    # historical run regardless of what last_scraped says.
    backfill = os.environ.get("SPEAKEASY_BACKFILL", "").strip() == "1"

    if backfill:
        cutoff = now - timedelta(days=MAX_AGE_DAYS)
        print(f"[{SOURCE}] BACKFILL mode: scanning {MAX_AGE_DAYS} days back.")
    else:
        last_scraped = data.get("last_scraped")
        if last_scraped:
            cutoff = datetime.fromisoformat(last_scraped)
            if cutoff.tzinfo is None:
                cutoff = cutoff.replace(tzinfo=timezone.utc)
        else:
            cutoff = now - timedelta(days=MAX_AGE_DAYS)

    # Prune expired re-check entries. Values may be plain ISO strings (legacy)
    # or dicts with an "expiry" key.
    def _recheck_expiry(val):
        return val if isinstance(val, str) else val["expiry"]

    recheck = {
        url: val for url, val in data.get("thread_recheck", {}).items()
        if datetime.fromisoformat(_recheck_expiry(val)) > now
    }
    recheck_tags = data.get("thread_recheck_tags", {})

    # Walk forum for threads with activity since cutoff.
    try:
        new_url_tags, forum_ok = _collect_new_urls(session, cutoff)
    except Exception as e:
        print(f"[{SOURCE}] ERROR fetching forum pages: {e}", file=sys.stderr)
        sys.exit(1)

    if not forum_ok:
        print(f"[{SOURCE}] ERROR: forum returned no threads — likely blocked or "
              "login expired. Keeping previous data.", file=sys.stderr)
        sys.exit(1)

    # Add newly-seen threads to the re-check cache.
    expiry = (now + timedelta(days=RECHECK_DAYS)).isoformat()
    for url, tag in new_url_tags:
        recheck.setdefault(url, expiry)
        recheck_tags[url] = tag  # always update — tag can change (WTS → SOLD)

    # Build deduped (url, tag) list: new threads first, then recheck remainder.
    seen = dict(new_url_tags)
    for url in recheck:
        if url not in seen:
            seen[url] = recheck_tags.get(url, "WTS")  # fallback for legacy entries
    all_url_tags = list(seen.items())

    n_new = len(new_url_tags)
    n_recheck = len(all_url_tags) - n_new
    print(f"[{SOURCE}] {n_new} new thread(s), {n_recheck} re-check — "
          f"fetching {len(all_url_tags)} total…")

    found = []
    for thread_url, tag in all_url_tags:
        try:
            resp = session.get(thread_url, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            print(f"[{SOURCE}] skipping {thread_url}: {e}")
            time.sleep(POST_DELAY)
            continue

        listings, post_date = _parse_first_post(resp.text)
        for name, price in listings:
            found.append({
                "name": name,
                "price": price,
                "url": thread_url,
                "source": SOURCE,
                "first_seen": post_date,
                "tag": tag,
            })

        if not listings:
            print(f"[{SOURCE}] no priced lines in {thread_url}")

        time.sleep(POST_DELAY)

    scrape_core.merge_products(data, found, now_iso)
    data["thread_recheck"] = recheck
    data["thread_recheck_tags"] = recheck_tags
    scrape_core.save(data, DATA_FILE)

    print(f"[{SOURCE}] +{len(found)} listing(s) this run. "
          f"Catalog: {len(data['products'])}. "
          f"Re-check cache: {len(recheck)} thread(s).")


if __name__ == "__main__":
    main()
