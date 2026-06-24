"""Speak-Easy.Club source — WTS (Want To Sell) tin listings from the marketplace.

Login-required XenForo 2.x forum. Credentials come from SPEAKEASY_USERNAME and
SPEAKEASY_PASSWORD environment variables (set via GitHub Secrets).

Run strategy:
  • First run (no prior data): bootstraps up to MAX_AGE_DAYS back.
  • Subsequent runs: only visits threads with activity since the last scrape,
    PLUS any thread seen within RECHECK_DAYS (to catch silent OP edits).
  • Legitimately finding zero new listings is not treated as a failure — only
    an inaccessible forum page triggers a hard exit.

Runs daily. Writes docs/products_speakeasy.json. Shared logic in scrape_core.py.
"""
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone

import cloudscraper
from bs4 import BeautifulSoup

import scrape_core

BASE_URL = "https://speak-easy.club"
FORUM_URL = f"{BASE_URL}/forums/market.39/"
SOURCE = "Speak-Easy.Club"
DATA_FILE = os.path.join(os.path.dirname(__file__), "docs", "products_speakeasy.json")

PAGE_DELAY = 1.5   # seconds between forum index pages
POST_DELAY = 1.2   # seconds between individual thread fetches
MAX_AGE_DAYS = 2 * 365  # bootstrap lookback when no prior scrape exists
RECHECK_DAYS = 14  # re-visit recently-seen threads to catch silent OP edits


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


def _is_wts(thread_el):
    """True when the thread carries a WTS prefix label."""
    label = thread_el.select_one(".label")
    if label:
        return "WTS" in label.get_text(strip=True).upper()
    title_el = (thread_el.select_one(".structItem-title a[data-tp-primary]")
                or thread_el.select_one(".structItem-title a"))
    if title_el:
        t = title_el.get_text(strip=True).upper()
        return t.startswith("[WTS]") or t.startswith("WTS ")
    return False


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
    """Walk forum pages, returning (wts_urls, forum_ok).

    Collects WTS threads with activity since `cutoff`. Stops paginating once
    an entire page is older than the cutoff. forum_ok is False when the first
    page loads but contains no thread elements — indicating a block or login
    failure.
    """
    urls = []
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
        forum_ok = True  # got at least one thread page — forum is reachable

        any_in_range = False
        for thread in threads:
            dt = _thread_date(thread)
            if dt is not None and dt < cutoff:
                continue
            any_in_range = True
            if _is_wts(thread):
                u = _thread_url(thread)
                if u:
                    urls.append(u)

        if not any_in_range:
            print(f"[{SOURCE}] page {page}: all threads older than cutoff — stopping.")
            break

        if not soup.select_one(".pageNav-jump--next, a[rel='next']"):
            break

        page += 1
        time.sleep(PAGE_DELAY)

    return urls, forum_ok


def _parse_first_post(html):
    """Extract (name, price) pairs and post date from the first post of a WTS thread.

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

    # Cutoff: since last scrape on ongoing runs; 2-year bootstrap on first run.
    last_scraped = data.get("last_scraped")
    if last_scraped:
        cutoff = datetime.fromisoformat(last_scraped)
        if cutoff.tzinfo is None:
            cutoff = cutoff.replace(tzinfo=timezone.utc)
    else:
        cutoff = now - timedelta(days=MAX_AGE_DAYS)

    # Prune expired re-check entries.
    recheck = {
        url: exp for url, exp in data.get("thread_recheck", {}).items()
        if datetime.fromisoformat(exp) > now
    }

    # Walk forum for threads with activity since cutoff.
    try:
        new_urls, forum_ok = _collect_new_urls(session, cutoff)
    except Exception as e:
        print(f"[{SOURCE}] ERROR fetching forum pages: {e}", file=sys.stderr)
        sys.exit(1)

    if not forum_ok:
        print(f"[{SOURCE}] ERROR: forum returned no threads — likely blocked or "
              "login expired. Keeping previous data.", file=sys.stderr)
        sys.exit(1)

    # Add newly-seen threads to the re-check cache.
    expiry = (now + timedelta(days=RECHECK_DAYS)).isoformat()
    for url in new_urls:
        recheck.setdefault(url, expiry)

    # Visit new threads + anything still in the re-check window (deduped).
    all_urls = list(dict.fromkeys(new_urls + list(recheck)))
    n_new = len(new_urls)
    n_recheck = len(all_urls) - n_new
    print(f"[{SOURCE}] {n_new} new thread(s), {n_recheck} re-check — "
          f"fetching {len(all_urls)} total…")

    found = []
    for thread_url in all_urls:
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
            })

        if not listings:
            print(f"[{SOURCE}] no priced lines in {thread_url}")

        time.sleep(POST_DELAY)

    scrape_core.merge_products(data, found, now_iso)
    data["thread_recheck"] = recheck
    scrape_core.save(data, DATA_FILE)

    print(f"[{SOURCE}] +{len(found)} listing(s) this run. "
          f"Catalog: {len(data['products'])}. "
          f"Re-check cache: {len(recheck)} thread(s).")


if __name__ == "__main__":
    main()
