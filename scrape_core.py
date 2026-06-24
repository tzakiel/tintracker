"""Shared scraping engine used by every source.

Each source provides a `fetch_fn()` that returns a list of dicts:
    {"name": str, "price": str, "url": str, "source": str}

The core handles the parts that are identical across sources:
  - retrying the whole fetch (Cloudflare blocking is intermittent)
  - the safety guard: a scrape that finds nothing NEVER overwrites good data
  - price-history tracking (an entry is added only when the price changes)
  - writing the per-source JSON file the website reads
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

MAX_ATTEMPTS = 6
RETRY_WAIT_SECONDS = 20
HISTORY_LIMIT = 1000  # scrape-history entries kept per source (~1.4 yrs twice-daily)


def load_existing(data_file):
    if os.path.exists(data_file):
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"products": [], "last_scraped": None}


def save(data, data_file):
    os.makedirs(os.path.dirname(data_file), exist_ok=True)
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run(source, fetch_fn, data_file,
        max_attempts=MAX_ATTEMPTS, retry_wait=RETRY_WAIT_SECONDS):
    now = datetime.now(timezone.utc).isoformat()

    # Retry the whole scrape — a fresh session a few seconds later often gets
    # through when an individual attempt is blocked.
    found = []
    for attempt in range(1, max_attempts + 1):
        try:
            found = fetch_fn()
        except Exception as e:
            print(f"[{source}] attempt {attempt}/{max_attempts} error: {e}")
            found = []
        if found:
            print(f"[{source}] attempt {attempt}/{max_attempts} succeeded: {len(found)} products.")
            break
        if attempt < max_attempts:
            print(f"[{source}] attempt {attempt}/{max_attempts} found 0 — retrying in {retry_wait}s…")
            time.sleep(retry_wait)

    data = load_existing(data_file)

    # Guard: a scrape that finds nothing is almost always a block or an outage,
    # NOT the store going empty. Never let it wipe the last good catalog.
    if not found:
        print(f"[{source}] ERROR: 0 products found — keeping previous data unchanged. "
              "This usually means the request was blocked. Not committing an empty catalog.",
              file=sys.stderr)
        sys.exit(1)

    merge_products(data, found, now)
    save(data, data_file)
    print(f"[{source}] Scraped {len(found)} products. Total in catalog: {len(data['products'])}")
    return data


def merge_products(data, found, now, latest=None):
    """Merge a list of scraped items into `data`, tracking price history.

    Each item is keyed by name. `latest` controls what the homepage shows as
    the current snapshot (defaults to everything found this run); pass an
    explicit list for sources where "currently listed" differs from "found".
    """
    existing = {p["name"]: p for p in data.get("products", [])}

    # Optional fields a source may supply (e.g. description/weight for tin-size
    # recovery). Carried through verbatim so consolidate.py can read them.
    EXTRA_FIELDS = ("description", "weight")

    added = 0          # new records created this run
    price_changed = 0  # existing records whose price moved this run

    for p in found:
        if p["name"] in existing:
            ex = existing[p["name"]]
            if "price_history" not in ex:
                ex["price_history"] = [{"price": ex["price"], "date": ex.get("first_seen", now)}]
            # Migration: seed last_updated from the most recent price_history entry.
            if "last_updated" not in ex:
                ex["last_updated"] = ex["price_history"][-1]["date"]
            if ex["price"] != p["price"]:
                ex["price_history"].append({"price": p["price"], "date": now})
                ex["last_updated"] = now
                price_changed += 1
            ex["price"] = p["price"]
            ex["url"] = p["url"]
            ex["source"] = p["source"]
            for f in EXTRA_FIELDS:
                if p.get(f):
                    ex[f] = p[f]
        else:
            first_seen_date = p.get("first_seen") or now
            rec = {
                "name": p["name"],
                "price": p["price"],
                "url": p["url"],
                "source": p["source"],
                "first_seen": first_seen_date,
                "last_updated": now,
                "price_history": [{"price": p["price"], "date": first_seen_date}],
            }
            for f in EXTRA_FIELDS:
                if p.get(f):
                    rec[f] = p[f]
            existing[p["name"]] = rec
            added += 1

    data["products"] = sorted(existing.values(),
        key=lambda x: x.get("last_updated") or x.get("last_seen", ""), reverse=True)
    data["last_scraped"] = now
    if latest is None:
        latest = found
    data["latest_scrape"] = [existing[p["name"]] for p in latest if p["name"] in existing]

    # Persistent run-by-run scrape log — one entry per successful merge (including
    # zero-add runs), so the admin dashboard can show real scrape cadence rather
    # than only runs that happened to add a listing. Capped to bound file growth.
    entry = {
        "date": now,
        "found": len(found),
        "added": added,
        "price_changed": price_changed,
        "total": len(data["products"]),
    }
    history = data.get("scrape_history", [])
    history.append(entry)
    data["scrape_history"] = history[-HISTORY_LIMIT:]
    return data
