"""4Noggins source — consignment tins from 4noggins.com (Shopify).

Uses the public Shopify collection JSON API — no browser or Cloudflare bypass needed.
Runs daily. Writes docs/products_4noggins.json. Shared logic in scrape_core.py.
"""
import os

import cloudscraper

import scrape_core

BASE_URL = "https://www.4noggins.com/collections/consignment-tins/products.json"
SOURCE = "4noggins.com"
DATA_FILE = os.path.join(os.path.dirname(__file__), "docs", "products_4noggins.json")


def fetch():
    session = cloudscraper.create_scraper()
    found = []
    page = 1

    while True:
        resp = session.get(BASE_URL, params={"limit": 250, "page": page}, timeout=30)
        resp.raise_for_status()
        products = resp.json().get("products", [])
        if not products:
            break

        for p in products:
            name = p.get("title", "")
            variants = p.get("variants", [])
            raw_price = variants[0].get("price", "") if variants else ""
            price = f"${raw_price}" if raw_price else ""
            handle = p.get("handle", "")
            url = f"https://www.4noggins.com/products/{handle}" if handle else ""
            if name:
                found.append({"name": name, "price": price, "url": url, "source": SOURCE})

        if len(products) < 250:
            break
        page += 1

    return found


if __name__ == "__main__":
    scrape_core.run(SOURCE, fetch, DATA_FILE)
