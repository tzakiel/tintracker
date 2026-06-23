"""Consolidation overlay — groups raw listings into canonical tins.

NON-DESTRUCTIVE: reads the per-source scrape files read-only and writes a
separate docs/canonical.json. Deleting that file fully reverts the feature.

Blend identity (brand + blend) comes from the LLM-extracted blend_cache.json,
with overrides.json winning over it (see extract.py / build_cache.py). The
deterministic bits — tin size, year, pack count, per-tin price — are still
parsed here with regex, because those are reliable.

A "tin" is one (brand, blend, size). Year-variants collapse together (e.g.
McClelland Christmas Cheer 100g across 2008–2017 = one tin, many price points),
and the SAME blend from DIFFERENT vendors collapses too (cross-source). Listings
with no clean identity (unknown brand, or not a single blend — variety packs,
cigars) stay as a group of one, never mis-merged.
"""
import json
import os
import re
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
DOCS = os.path.join(HERE, "docs")
OUT_FILE = os.path.join(DOCS, "canonical.json")
LOG_FILE = os.path.join(DOCS, "unmatched.log")
CACHE_FILE = os.path.join(HERE, "blend_cache.json")
OVERRIDES_FILE = os.path.join(HERE, "overrides.json")

SOURCE_FILES = [
    "products.json",
    "products_tinbids.json",
    "products_treasuredsmokes.json",
    "products_4noggins.json",
]

# tin weight, in a name OR a free-text description: "50g", "100 grams", "2oz",
# "2 ounce", "1-3/4 oz", "1.76oz". (NOT pack counts — that's PACK_RE.)
QTY_RE = re.compile(r"(\d+\s*(?:g|grams?)\b|\d[\d.\-/]*\s*(?:oz|ounces?)\b)", re.I)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
PACK_RE = re.compile(r"(?:lot of\s*(\d+)|(\d+)\s*[-\s]?pack|(\d+)\s*x\b)", re.I)
VARIETY_RE = re.compile(r"\b(variety|sampler|assort\w*)\b", re.I)


def _pack_count(s):
    if VARIETY_RE.search(s or ""):
        return None
    m = PACK_RE.search(s or "")
    if m:
        try:
            n = int(m.group(1) or m.group(2) or m.group(3))
            if n > 1:
                return n
        except (TypeError, ValueError):
            pass
    return 1


def _divide_price(price, pack):
    if not pack or pack <= 1:
        return price
    m = re.search(r"[\d,]+(?:\.\d+)?", price or "")
    if not m:
        return price
    val = float(m.group(0).replace(",", ""))
    return "${:,.2f}".format(val / pack)


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _qty(s):
    m = QTY_RE.search(s or "")
    if not m:
        return ""
    raw = m.group(1)
    num = re.match(r"[\d.\-/]+", raw.replace(" ", "")).group(0)
    unit = "oz" if re.search(r"oz|ounce", raw, re.I) else "g"
    return f"{num}{unit}".lower()


def _year(s):
    rng = re.search(r"\b((?:19|20)\d{2})\s*[-–]\s*\d{2,4}\b", s or "")
    if rng:
        return rng.group(1)
    m = YEAR_RE.search(s or "")
    return m.group(0) if m else ""


def load_identity():
    """title -> {brand, blend, is_tin}. Overrides win over the cache."""
    cache = json.load(open(CACHE_FILE, encoding="utf-8")) if os.path.exists(CACHE_FILE) else {}
    ident = {t: {"brand": r.get("brand", ""), "blend": r.get("blend", ""),
                 "is_tin": r.get("is_tin", True)} for t, r in cache.items()}
    if os.path.exists(OVERRIDES_FILE):
        for t, r in json.load(open(OVERRIDES_FILE, encoding="utf-8")).items():
            ident[t] = {"brand": r.get("brand", ""), "blend": r.get("blend", ""),
                        "is_tin": r.get("is_tin", True)}
    return ident


def main():
    ident = load_identity()
    groups = {}
    name_to_id = {}
    unmatched = []
    counts = {"listings": 0, "grouped_tins": 0, "collapsed_listings": 0}

    for fname in SOURCE_FILES:
        path = os.path.join(DOCS, fname)
        if not os.path.exists(path):
            continue
        data = json.load(open(path, encoding="utf-8"))
        for p in data.get("products", []):
            counts["listings"] += 1
            name = (p.get("name") or "").strip()
            source = p.get("source", fname)

            id_rec = ident.get(name, {})
            brand = (id_rec.get("brand") or "").strip()
            blend = (id_rec.get("blend") or "").strip()
            is_tin = id_rec.get("is_tin", True)

            pc = _pack_count(name)
            pack = pc if pc else 1
            listing_price = p.get("price", "")
            quantity = (_qty(name) or p.get("weight", "") or _qty(p.get("description", "")))

            member = {
                "name": name, "source": source, "url": p.get("url", ""),
                "listing_price": listing_price, "pack_count": pack,
                "price": _divide_price(listing_price, pack),
                "last_seen": p.get("last_seen", ""),
                "first_seen": p.get("first_seen", ""),
                "year": _year(name),
                "price_history": [
                    {"price": _divide_price(h.get("price", ""), pack), "date": h.get("date", "")}
                    for h in p.get("price_history", [])
                ],
            }

            # Group cross-source on (brand, blend, size) — but only when we have a
            # clean single-blend identity. Otherwise it's a standalone tin.
            if is_tin and brand and blend:
                key = f"{_norm(brand)}|{_norm(blend)}|{_norm(quantity)}"
                g = groups.get(key)
                if not g:
                    disp = f"{brand} {blend}".strip()
                    if quantity:
                        disp += f" {quantity}"
                    g = groups[key] = {
                        "id": key, "brand": brand, "blend": blend,
                        "quantity": quantity, "display_name": disp,
                        "sources": [], "members": [],
                    }
                g["members"].append(member)
                if source not in g["sources"]:
                    g["sources"].append(source)
            else:
                key = f"solo|{_norm(source)}|{_norm(name)}"
                groups[key] = {
                    "id": key, "brand": brand, "blend": blend,
                    "quantity": quantity, "display_name": name,
                    "sources": [source], "members": [member],
                }
                if not (brand and blend) or not is_tin:
                    unmatched.append(f"[{source}] {name}")
            name_to_id[name] = key

    tins = []
    for g in groups.values():
        g["members"].sort(key=lambda m: m["year"] or "")
        g["years"] = sorted({m["year"] for m in g["members"] if m["year"]})
        g["source"] = g["sources"][0] if len(g["sources"]) == 1 else "Multiple sources"
        if len(g["members"]) > 1:
            counts["grouped_tins"] += 1
            counts["collapsed_listings"] += len(g["members"])
        tins.append(g)
    tins.sort(key=lambda g: g["display_name"].lower())

    out = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "total_listings": counts["listings"],
            "total_tins": len(tins),
            "multi_member_tins": counts["grouped_tins"],
            "listings_in_groups": counts["collapsed_listings"],
            "cross_source_tins": sum(1 for g in tins if len(g["sources"]) > 1),
        },
        "tins": tins,
        "name_to_id": name_to_id,
    }
    json.dump(out, open(OUT_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"# {len(unmatched)} listings have no clean blend identity "
                f"(left as standalone tins):\n\n")
        f.write("\n".join(sorted(unmatched)) + "\n")

    s = out["stats"]
    print(f"Listings: {s['total_listings']}  ->  Tins: {s['total_tins']}")
    print(f"Multi-member tins: {s['multi_member_tins']} "
          f"(collapsing {s['listings_in_groups']} listings)")
    print(f"Cross-source tins: {s['cross_source_tins']}")
    print(f"Standalone (no identity): {len(unmatched)}  — see {os.path.basename(LOG_FILE)}")
    print("\nLargest groups:")
    for g in sorted(tins, key=lambda x: -len(x["members"]))[:10]:
        if len(g["members"]) > 1:
            print(f"  {len(g['members']):>2}x  {g['display_name']}  "
                  f"[{', '.join(g['sources'])}]")


if __name__ == "__main__":
    main()
