"""Tinbids BIN source — scrapes buy-it-now tobacco listings from tinbids.com.

Runs daily. Writes docs/products_tinbids.json. Shared logic lives in scrape_core.py.
"""
import os
import time

import cloudscraper
from bs4 import BeautifulSoup, Comment

import scrape_core

BASE_URL = "https://tinbids.com/browse/?category=tobaccos&sort=buy-it-now"
SOURCE = "Tinbids BIN"
DATA_FILE = os.path.join(os.path.dirname(__file__), "docs", "products_tinbids.json")


def _page_url(n):
    if n == 1:
        return BASE_URL
    return f"https://tinbids.com/browse/page/{n}/?category=tobaccos&sort=buy-it-now"


def _parse_entries(soup):
    out = []
    for el in soup.select(".auction-entry"):
        title_el = el.select_one(".auction-entry-title a")
        if not title_el:
            continue
        name = title_el.get_text(strip=True)
        url = title_el.get("href", "")

        price = ""
        price_el = el.select_one(".auction-entry-price")
        if price_el:
            # The price text is followed by an HTML comment holding raw object
            # data — keep only the real (non-comment) text node.
            texts = [t for t in price_el.contents
                     if isinstance(t, str) and not isinstance(t, Comment) and t.strip()]
            price = texts[0].strip() if texts else ""

        if name:
            out.append({"name": name, "price": price, "url": url, "source": SOURCE})
    return out


def fetch():
    """One full attempt: read page 1, learn the page count, walk the rest."""
    session = cloudscraper.create_scraper()

    resp = session.get(_page_url(1), timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    found = _parse_entries(soup)
    if not found:
        body = resp.text.lower()
        if ("just a moment" in body or "challenge-platform" in body
                or "enable javascript" in body):
            print(f"[{SOURCE}] blocked: page 1 returned a Cloudflare challenge "
                  f"(HTTP {resp.status_code}, {len(resp.text)} bytes), 0 products parsed.")
        return found

    # Highest numbered pagination link tells us how many pages there are.
    max_page = 1
    for a in soup.select(".page-numbers"):
        t = a.get_text(strip=True).replace(",", "")
        if t.isdigit():
            max_page = max(max_page, int(t))

    for n in range(2, max_page + 1):
        time.sleep(0.5)  # be polite — ~30 pages
        resp = session.get(_page_url(n), timeout=30)
        resp.raise_for_status()
        page_items = _parse_entries(BeautifulSoup(resp.text, "lxml"))
        if not page_items:
            break
        found += page_items

    return found


if __name__ == "__main__":
    scrape_core.run(SOURCE, fetch, DATA_FILE)
