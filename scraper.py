"""Pipestud source — scrapes tobacco tins from pipestud.com (WooCommerce).

Runs weekly. Writes docs/products.json. Shared logic lives in scrape_core.py.
Uses Playwright (real Chromium browser) to bypass Cloudflare protection.

Pipestud paginates 12 tins per page. We walk pages sequentially and stop when
a page is empty after retries OR returns only already-seen products (WooCommerce
wraps out-of-bounds page numbers to the last real page). Each page load gets a
FRESH browser context (fresh cookies/fingerprint) to clear Cloudflare
throttling.
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


MAX_PAGES = 50  # hard ceiling — prevents an infinite walk if the site misbehaves


def fetch():
    """One full attempt: walk every page once. Returns a list (empty if blocked).

    Rather than detecting max_page from page-1's pagination links (unreliable
    when Cloudflare delays JS rendering), we walk sequentially and stop when:
      - a page comes back empty after retries (past the last page), OR
      - a page returns only products already seen this run (WooCommerce
        wraps out-of-bounds page numbers back to the last real page).
    Each page load gets a FRESH browser context to clear Cloudflare throttling.
    """
    found = []
    seen_names = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for n in range(1, MAX_PAGES + 1):
            if n > 1:
                time.sleep(PAGE_DELAY)
            soup = _load_page(browser, n)
            if soup is None:
                if n == 1:
                    print("[pipestud.com] blocked: could not load page 1 (Cloudflare challenge).")
                    browser.close()
                    return []
                # Empty after retries past page 1 = past the last page.
                print(f"[pipestud.com] page {n} empty after retries — stopping at {n - 1} pages.")
                break
            batch = _parse_products(soup)
            new_on_page = [item for item in batch if item["name"] not in seen_names]
            if not new_on_page:
                # All products already seen — WooCommerce wrapped around.
                print(f"[pipestud.com] page {n} all duplicates — stopping at {n - 1} pages.")
                break
            found.extend(new_on_page)
            seen_names.update(item["name"] for item in new_on_page)
            print(f"[pipestud.com] page {n}: {len(new_on_page)} new (running total: {len(found)})")

        print(f"[pipestud.com] collected {len(found)} products.")
        browser.close()

    return found


if __name__ == "__main__":
    scrape_core.run(SOURCE, fetch, DATA_FILE)
