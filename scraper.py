"""Pipestud source — scrapes tobacco tins from pipestud.com (WooCommerce).

Runs weekly. Writes docs/products.json. Shared logic lives in scrape_core.py.
Uses Playwright (real Chromium browser) to bypass Cloudflare protection.

Pipestud paginates 12 tins per page across ~8 pages. We read the highest page
number from page 1's pagination, then walk every page with a polite delay and
per-page retries. Cloudflare rate-limits rapid requests in one browser session,
so each page load gets a FRESH browser context (fresh cookies/fingerprint) —
that alone clears most throttling — and an empty page is retried (also with a
fresh context) rather than silently ending the walk.
"""
import os
import time

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

import scrape_core

BASE_URL = "https://www.pipestud.com/products/tobacco-tins/"
SOURCE = "pipestud.com"
DATA_FILE = os.path.join(os.path.dirname(__file__), "docs", "products.json")

PAGE_DELAY = 2.0      # politeness between pages — avoids Cloudflare rate-limiting
PAGE_RETRIES = 4      # reloads for a page that comes back empty
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


def _page_url(n):
    return BASE_URL if n == 1 else f"{BASE_URL}page/{n}/"


def _parse_products(soup):
    out = []
    for item in soup.select("li.product"):
        name_el = item.select_one(".woocommerce-loop-product__title")
        price_el = item.select_one(".price")
        link_el = item.select_one("a.woocommerce-LoopProduct-link")

        name = name_el.get_text(strip=True) if name_el else ""
        if price_el:
            for sr in list(price_el.select(".screen-reader-text")):
                sr.decompose()
            sale_el = price_el.select_one("ins .woocommerce-Price-amount")
            regular_el = price_el.select_one(".woocommerce-Price-amount")
            target = sale_el or regular_el
            price = target.get_text(strip=True) if target else price_el.get_text(strip=True)
        else:
            price = ""
        url_p = link_el["href"] if link_el else ""

        if name:
            out.append({"name": name, "price": price, "url": url_p, "source": SOURCE})
    return out


def _load_page(browser, n):
    """Load page n in a FRESH context, retrying on an empty/throttled response.
    A fresh context per attempt resets the cookies Cloudflare rate-limits on.
    Returns the parsed BeautifulSoup, or None if it never loaded products."""
    for attempt in range(1, PAGE_RETRIES + 1):
        context = browser.new_context(user_agent=USER_AGENT)
        page_obj = context.new_page()
        try:
            page_obj.goto(_page_url(n), wait_until="domcontentloaded", timeout=60000)
            try:
                page_obj.wait_for_selector("li.product, .cf-error-overview, #challenge-form",
                                           timeout=20000)
            except Exception:
                pass
            soup = BeautifulSoup(page_obj.content(), "lxml")
        finally:
            context.close()
        if soup.select("li.product"):
            return soup
        # Empty — likely rate-limited. Back off and retry with a fresh context.
        if attempt < PAGE_RETRIES:
            wait = PAGE_DELAY * (attempt + 1)
            print(f"[pipestud.com] page {n} empty (attempt {attempt}/{PAGE_RETRIES}); "
                  f"retrying in {wait:.0f}s…")
            time.sleep(wait)
    return None


def fetch():
    """One full attempt: walk every page once. Returns a list (empty if blocked)."""
    found = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Page 1 — also tells us how many pages exist.
        soup = _load_page(browser, 1)
        if soup is None:
            print("[pipestud.com] blocked: could not load page 1 (Cloudflare challenge).")
            browser.close()
            return []

        found.extend(_parse_products(soup))

        max_page = 1
        for a in soup.select("a.page-numbers"):
            t = a.get_text(strip=True).replace(",", "")
            if t.isdigit():
                max_page = max(max_page, int(t))

        for n in range(2, max_page + 1):
            time.sleep(PAGE_DELAY)
            page_soup = _load_page(browser, n)
            if page_soup is None:
                print(f"[pipestud.com] page {n}/{max_page} failed after retries; "
                      f"continuing with {len(found)} products so far.")
                continue
            found.extend(_parse_products(page_soup))

        print(f"[pipestud.com] walked {max_page} pages, collected {len(found)} products.")
        browser.close()

    return found


if __name__ == "__main__":
    scrape_core.run(SOURCE, fetch, DATA_FILE)
