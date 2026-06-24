"""Speak-Easy.Club source — WTS (Want To Sell) tin listings from the marketplace.

Login-required XenForo 2.x forum. Credentials come from SPEAKEASY_USERNAME and
SPEAKEASY_PASSWORD environment variables (set via GitHub Secrets).

Walk order:
  1. Page through https://speak-easy.club/forums/market.39/ collecting every
     thread that carries a [WTS] prefix label.
  2. Fetch the first post of each thread — sellers typically list multiple tins
     there with individual prices.
  3. Yield one record per line that contains a recognisable $ price.

Runs daily. Writes docs/products_speakeasy.json. Shared logic in scrape_core.py.
"""
import os
import re
import time
from datetime import datetime, timedelta, timezone

import cloudscraper
from bs4 import BeautifulSoup

import scrape_core

BASE_URL = "https://speak-easy.club"
FORUM_URL = f"{BASE_URL}/forums/market.39/"
SOURCE = "Speak-Easy.Club"
DATA_FILE = os.path.join(os.path.dirname(__file__), "docs", "products_speakeasy.json")

PAGE_DELAY = 1.5  # seconds between forum index pages
POST_DELAY = 1.2  # seconds between individual thread fetches
MAX_AGE_DAYS = 2 * 365  # only collect threads active within the past 2 years



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
    # Fallback: prefix baked into the title text
    title_el = (thread_el.select_one(".structItem-title a[data-tp-primary]")
                or thread_el.select_one(".structItem-title a"))
    if title_el:
        t = title_el.get_text(strip=True).upper()
        return t.startswith("[WTS]") or t.startswith("WTS ")
    return False


def _thread_date(thread_el):
    """Return the thread's latest-activity datetime (UTC), or None if unreadable.

    XenForo renders a <time data-time="unix_ts"> in each thread row; the
    datetime attribute is an ISO string fallback.
    """
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


def _collect_wts_urls(session):
    """Walk forum listing pages and return WTS thread URLs active within MAX_AGE_DAYS.

    XenForo sorts threads by latest activity (newest first), so once an entire
    page is beyond the cutoff there is nothing left worth fetching.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    urls = []
    page = 1

    while True:
        url = FORUM_URL if page == 1 else f"{FORUM_URL}page-{page}"
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        threads = soup.select(".structItem--thread")
        if not threads:
            break

        any_in_range = False
        for thread in threads:
            dt = _thread_date(thread)
            if dt is not None and dt < cutoff:
                continue  # thread is too old — skip but keep scanning this page
            any_in_range = True  # within range, or date unreadable (keep to be safe)
            if _is_wts(thread):
                u = _thread_url(thread)
                if u:
                    urls.append(u)

        # Once every thread on a page is past the cutoff we've gone far enough
        if not any_in_range:
            print(f"[{SOURCE}] page {page}: all threads older than {MAX_AGE_DAYS} days — stopping.")
            break

        if not soup.select_one(".pageNav-jump--next, a[rel='next']"):
            break

        page += 1
        time.sleep(PAGE_DELAY)

    return urls


def _parse_first_post(html):
    """Extract (name, price) pairs from the first post of a WTS thread.

    Each line in the post that contains a $ price yields one listing. List
    markers, separators, and quoted replies are stripped before scanning.
    """
    soup = BeautifulSoup(html, "lxml")

    # Isolate the first post only (XenForo 2.x)
    messages = soup.select(".message--post")
    if not messages:
        return []
    post_body = messages[0].select_one(".message-body .bbWrapper")
    if not post_body:
        return []

    # Drop quoted content — prices from earlier posts shouldn't become listings
    for el in post_body.select("blockquote, .bbCodeBlock--quote"):
        el.decompose()

    # Inject newlines at block boundaries before flattening to text
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

        # Description = text before the price signal on this line
        desc = line[:m.start()].strip()
        # Strip leading list markers: "- ", "* ", "1. ", "• " etc.
        desc = re.sub(r'^[\-\*•\d]+[\.\):\s]+', '', desc).strip()
        # Strip trailing separators: " - ", " | ", "…"
        desc = re.sub(r'[\-–|\.]+\s*$', '', desc).strip()

        if len(desc) < 5:
            continue

        listings.append((desc, price))

    return listings


def fetch():
    session = cloudscraper.create_scraper()
    _login(session)

    thread_urls = _collect_wts_urls(session)
    print(f"[{SOURCE}] Found {len(thread_urls)} WTS threads — fetching first posts…")

    found = []
    for thread_url in thread_urls:
        try:
            resp = session.get(thread_url, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            print(f"[{SOURCE}] skipping {thread_url}: {e}")
            time.sleep(POST_DELAY)
            continue

        listings = _parse_first_post(resp.text)
        for name, price in listings:
            found.append({
                "name": name,
                "price": price,
                "url": thread_url,
                "source": SOURCE,
            })

        if not listings:
            print(f"[{SOURCE}] no priced lines in {thread_url}")

        time.sleep(POST_DELAY)

    return found


if __name__ == "__main__":
    scrape_core.run(SOURCE, fetch, DATA_FILE)
