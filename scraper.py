"""Pipestud source — scrapes tobacco tins from pipestud.com (WooCommerce).

Runs weekly. Writes docs/products.json. Shared logic lives in scrape_core.py.
"""
import os

import cloudscraper
from bs4 import BeautifulSoup

import scrape_core

BASE_URL = "https://www.pipestud.com/products/tobacco-tins/"
SOURCE = "pipestud.com"
DATA_FILE = os.path.join(os.path.dirname(__file__), "docs", "products.json")


def fetch():
    """One full attempt: walk every page once. Returns a list (empty if blocked)."""
    session = cloudscraper.create_scraper()
    found = []
    page = 1

    while True:
        url = BASE_URL if page == 1 else f"{BASE_URL}page/{page}/"
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        items = soup.select("li.product")
        if not items:
            body = resp.text.lower()
            if page == 1 and ("just a moment" in body or "cf-challenge" in body
                              or "challenge-platform" in body or "enable javascript" in body):
                print(f"[pipestud.com] blocked: page {page} returned a Cloudflare challenge "
                      f"(HTTP {resp.status_code}, {len(resp.text)} bytes), 0 products parsed.")
            break

        for item in items:
            name_el = item.select_one(".woocommerce-loop-product__title")
            price_el = item.select_one(".price")
            link_el = item.select_one("a.woocommerce-LoopProduct-link")

            name = name_el.get_text(strip=True) if name_el else ""
            if price_el:
                # Strip screen-reader-only spans ("Original price was:", "Current price is:", etc.)
                for sr in list(price_el.select(".screen-reader-text")):
                    sr.decompose()
                # Sale price lives in <ins>, regular price in first .woocommerce-Price-amount
                sale_el = price_el.select_one("ins .woocommerce-Price-amount")
                regular_el = price_el.select_one(".woocommerce-Price-amount")
                target = sale_el or regular_el
                price = target.get_text(strip=True) if target else price_el.get_text(strip=True)
            else:
                price = ""
            url_p = link_el["href"] if link_el else ""

            if name:
                found.append({"name": name, "price": price, "url": url_p, "source": SOURCE})

        if not soup.select_one("a.next.page-numbers"):
            break
        page += 1

    return found


if __name__ == "__main__":
    scrape_core.run(SOURCE, fetch, DATA_FILE)
