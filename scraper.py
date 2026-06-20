import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import json
import os
import sys
import time

BASE_URL = "https://www.pipestud.com/products/tobacco-tins/"
SOURCE = "pipestud.com"
DATA_FILE = os.path.join(os.path.dirname(__file__), "docs", "products.json")

# Cloudflare blocking is intermittent from datacenter IPs, so retry the whole
# scrape several times with fresh sessions before giving up.
MAX_ATTEMPTS = 6
RETRY_WAIT_SECONDS = 20


def load_existing():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"products": [], "last_scraped": None}


def save(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_all_products():
    """One full attempt: walk every page once. Returns a list (may be empty if blocked)."""
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
            # Diagnostic: detect a Cloudflare challenge / block page so CI logs are clear
            body = resp.text.lower()
            if page == 1 and ("just a moment" in body or "cf-challenge" in body
                              or "challenge-platform" in body or "enable javascript" in body):
                print(f"[scraper] blocked: page {page} returned a Cloudflare challenge "
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


def scrape():
    now = datetime.now(timezone.utc).isoformat()

    # Retry the whole scrape — Cloudflare blocking is intermittent, so a fresh
    # session a few seconds later often gets through.
    found = []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            found = fetch_all_products()
        except Exception as e:
            print(f"[scraper] attempt {attempt}/{MAX_ATTEMPTS} error: {e}")
            found = []
        if found:
            print(f"[scraper] attempt {attempt}/{MAX_ATTEMPTS} succeeded: {len(found)} products.")
            break
        if attempt < MAX_ATTEMPTS:
            print(f"[scraper] attempt {attempt}/{MAX_ATTEMPTS} found 0 — retrying in {RETRY_WAIT_SECONDS}s…")
            time.sleep(RETRY_WAIT_SECONDS)

    data = load_existing()

    # Guard: a scrape that finds nothing is almost always a block or an outage,
    # NOT the store going empty. Never let it wipe the last good catalog.
    if not found:
        print("[scraper] ERROR: 0 products found — keeping previous data unchanged. "
              "This usually means the request was blocked. Not committing an empty catalog.",
              file=sys.stderr)
        sys.exit(1)

    existing = {p["name"]: p for p in data["products"]}

    for p in found:
        if p["name"] in existing:
            ex = existing[p["name"]]
            # Initialize history from old data if not present
            if "price_history" not in ex:
                ex["price_history"] = [{"price": ex["price"], "date": ex.get("first_seen", now)}]
            # Record price change
            if ex["price"] != p["price"]:
                ex["price_history"].append({"price": p["price"], "date": now})
            ex["price"] = p["price"]
            ex["url"] = p["url"]
            ex["source"] = p["source"]
            ex["last_seen"] = now
        else:
            existing[p["name"]] = {
                "name": p["name"],
                "price": p["price"],
                "url": p["url"],
                "source": p["source"],
                "first_seen": now,
                "last_seen": now,
                "price_history": [{"price": p["price"], "date": now}],
            }

    data["products"] = sorted(existing.values(), key=lambda x: x["last_seen"], reverse=True)
    data["last_scraped"] = now
    # Full snapshot of this scrape — homepage reads this directly, no matching needed
    data["latest_scrape"] = [existing[p["name"]] for p in found]
    save(data)
    print(f"Scraped {len(found)} products. Total in catalog: {len(data['products'])}")
    return data


if __name__ == "__main__":
    scrape()
