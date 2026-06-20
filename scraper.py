import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import json
import os

BASE_URL = "https://www.pipestud.com/products/tobacco-tins/"
SOURCE = "pipestud.com"
DATA_FILE = os.path.join(os.path.dirname(__file__), "docs", "products.json")


def load_existing():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"products": [], "last_scraped": None}


def save(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def scrape():
    now = datetime.now(timezone.utc).isoformat()
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
            break

        for item in items:
            name_el = item.select_one(".woocommerce-loop-product__title")
            price_el = item.select_one(".price")
            link_el = item.select_one("a.woocommerce-LoopProduct-link")

            name = name_el.get_text(strip=True) if name_el else ""
            price = price_el.get_text(strip=True) if price_el else ""
            url_p = link_el["href"] if link_el else ""

            if name:
                found.append({"name": name, "price": price, "url": url_p, "source": SOURCE})

        if not soup.select_one("a.next.page-numbers"):
            break
        page += 1

    data = load_existing()
    existing = {p["name"]: p for p in data["products"]}

    for p in found:
        if p["name"] in existing:
            existing[p["name"]]["price"] = p["price"]
            existing[p["name"]]["url"] = p["url"]
            existing[p["name"]]["source"] = p["source"]
            existing[p["name"]]["last_seen"] = now
        else:
            existing[p["name"]] = {
                "name": p["name"],
                "price": p["price"],
                "url": p["url"],
                "source": p["source"],
                "first_seen": now,
                "last_seen": now,
            }

    data["products"] = sorted(existing.values(), key=lambda x: x["last_seen"], reverse=True)
    data["last_scraped"] = now
    data["last_scrape_names"] = [p["name"] for p in found]
    save(data)
    print(f"Scraped {len(found)} products. Total in catalog: {len(data['products'])}")
    return data


if __name__ == "__main__":
    scrape()
