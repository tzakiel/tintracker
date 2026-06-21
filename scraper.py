"""Pipestud source — scrapes tobacco tins from pipestud.com (WooCommerce).

Runs weekly. Writes docs/products.json. Shared logic lives in scrape_core.py.
Uses Playwright (real Chromium browser) to bypass Cloudflare protection.
"""
import os

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

import scrape_core

BASE_URL = "https://www.pipestud.com/products/tobacco-tins/"
SOURCE = "pipestud.com"
DATA_FILE = os.path.join(os.path.dirname(__file__), "docs", "products.json")


def fetch():
    """One full attempt: walk every page once. Returns a list (empty if blocked)."""
    found = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            )
        )
        page_obj = context.new_page()
        page_num = 1

        while True:
            url = BASE_URL if page_num == 1 else f"{BASE_URL}page/{page_num}/"
            page_obj.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Wait for products to render (or detect a Cloudflare challenge)
            try:
                page_obj.wait_for_selector("li.product, .cf-error-overview, #challenge-form",
                                           timeout=15000)
            except Exception:
                pass

            html = page_obj.content()
            soup = BeautifulSoup(html, "lxml")

            items = soup.select("li.product")
            if not items:
                body = html.lower()
                if page_num == 1 and ("just a moment" in body or "cf-challenge" in body
                                      or "challenge-platform" in body
                                      or "enable javascript" in body):
                    print(f"[pipestud.com] blocked: Cloudflare challenge on page {page_num}.")
                break

            for item in items:
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
                    found.append({"name": name, "price": price, "url": url_p, "source": SOURCE})

            if not soup.select_one("a.next.page-numbers"):
                break
            page_num += 1

        browser.close()

    return found


if __name__ == "__main__":
    scrape_core.run(SOURCE, fetch, DATA_FILE)
