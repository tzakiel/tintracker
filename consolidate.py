"""Consolidation overlay — groups raw listings into canonical tins.

NON-DESTRUCTIVE: reads the per-source scrape files read-only and writes a
separate docs/canonical.json. Deleting that file fully reverts the feature.

A "tin" is one (brand, blend, quantity) within a single source. Year-variants
collapse together (e.g. McClelland Christmas Cheer 100g across 2008–2017 becomes
one tin with many price points). We only group when brand/blend/quantity are
cleanly extracted; anything uncertain stays a group of one (never mis-merged).

v1 scope: intra-source only. No cross-source merging (the data showed low
overlap and high false-merge risk there).
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

DOCS = os.path.join(os.path.dirname(__file__), "docs")
OUT_FILE = os.path.join(DOCS, "canonical.json")
LOG_FILE = os.path.join(DOCS, "unmatched.log")

# Each source file maps to the parser that understands its naming style.
SOURCE_FILES = {
    "products.json": "pipestud",
    "products_tinbids.json": "generic",
    "products_treasuredsmokes.json": "treasured",
    "products_4noggins.json": "generic",
}

# Words dropped from the grouping key so connective noise doesn't split a group
# ("Blend 500 in a 50g" vs "Blend 500 50g" must land in the same bucket).
KEY_STOP = {"in", "a", "of", "the", "an"}

QTY_RE = re.compile(r"(\d+\s*g\b|\d+(?:[\-/]\d+)?\s*oz\b|\d+/\d+\s*oz\b|\d+\s*ounce\b)", re.I)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
# pack/lot count: "Lot of 2", "3-Pack", "5 Pack of" → number of tins in the listing
PACK_RE = re.compile(r"(?:lot of\s*(\d+)|(\d+)\s*[-\s]?pack)", re.I)
# variety/sampler packs hold DIFFERENT blends — price can't be split per tin
VARIETY_RE = re.compile(r"\b(variety|sampler|assort\w*)\b", re.I)


def _pack_count(s):
    """How many identical tins the listing sells. Returns None for variety packs
    (different contents — not divisible), 1 for a single tin, N for an N-pack/lot."""
    if VARIETY_RE.search(s or ""):
        return None
    m = PACK_RE.search(s or "")
    if m:
        try:
            n = int(m.group(1) or m.group(2))
            if n > 1:
                return n
        except (TypeError, ValueError):
            pass
    return 1


def _strip_pack(s):
    """Remove the pack phrase so it doesn't pollute brand/blend extraction."""
    return re.sub(r"\b(?:lot of\s*\d+|\d+\s*[-\s]?pack(?:\s+of)?)\b", " ", s or "", flags=re.I)


def _divide_price(price, pack):
    """Per-tin price = listing price / pack count. Non-numeric prices pass through."""
    if not pack or pack <= 1:
        return price
    m = re.search(r"[\d,]+(?:\.\d+)?", price or "")
    if not m:
        return price
    val = float(m.group(0).replace(",", ""))
    return "${:,.2f}".format(val / pack)


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _key_norm(s):
    """Normalize a brand/blend string for grouping: drop stop-words + punctuation."""
    toks = re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()).split()
    return "".join(t for t in toks if t not in KEY_STOP)


def _qty(s):
    m = QTY_RE.search(s or "")
    if not m:
        return ""
    q = re.sub(r"\s+", "", m.group(1)).lower().replace("ounce", "oz")
    return q


def _year(s):
    # year range like "2009-10" → keep the leading year for display
    rng = re.search(r"\b((?:19|20)\d{2})\s*[-–]\s*\d{2,4}\b", s or "")
    if rng:
        return rng.group(1)
    m = YEAR_RE.search(s or "")
    return m.group(0) if m else ""


def parse_pipestud(name):
    """'Brand['s] Blend QTY tin[s] – Year/era tail' → fields (or None if unsure)."""
    pack = _pack_count(name)
    if pack is None:        # variety/sampler pack — can't attribute price to one blend
        return None
    m = QTY_RE.search(name)
    if not m:
        return None
    head = _strip_pack(name[:m.start()]).strip()        # brand + blend (+ connective)
    # trim trailing connectives left dangling before the quantity ("in a", "in", "of")
    head = re.sub(r"\s+(in|of|&|and)(\s+a)?\s*$", "", head, flags=re.I).strip()
    if not head:
        return None
    # brand = leading proper-noun run up to a possessive, else first word
    bm = re.match(r"([A-Z][\w.&]*(?:’s|'s))", head)
    if bm:
        brand = re.sub(r"(’s|'s)$", "", bm.group(1))
        blend = head[bm.end():].strip()
    else:
        parts = head.split()
        brand = parts[0]
        blend = " ".join(parts[1:])
    return {
        "brand": brand, "blend": blend or head,
        "quantity": _qty(name), "year": _year(name), "pack_count": pack,
    }


def parse_treasured(name):
    """'Brand - Blend - YYYY! [size]' (hyphen-delimited). Quantity often absent."""
    pack = _pack_count(name)
    if pack is None:        # variety/sampler pack — can't attribute price to one blend
        return None
    parts = [p.strip() for p in re.split(r"\s+-\s+", _strip_pack(name)) if p.strip()]
    if len(parts) < 2:
        return None
    brand, blend = parts[0], parts[1]
    tail = " ".join(parts[2:])
    if not brand or not blend:
        return None
    return {
        "brand": brand, "blend": blend,
        "quantity": _qty(name), "year": _year(tail + " " + blend), "pack_count": pack,
    }


def parse_generic(name):
    """Fallback: no reliable structure → always a group of one."""
    return None


PARSERS = {
    "pipestud": parse_pipestud,
    "treasured": parse_treasured,
    "generic": parse_generic,
}


def _display(parsed):
    bits = [parsed["brand"], parsed["blend"]]
    name = " ".join(b for b in bits if b)
    if parsed["quantity"]:
        name += f" {parsed['quantity']}"
    return name.strip()


def main():
    groups = {}          # id -> tin record
    name_to_id = {}
    unmatched = []
    counts = {"listings": 0, "grouped_tins": 0, "collapsed_listings": 0}

    for fname, kind in SOURCE_FILES.items():
        path = os.path.join(DOCS, fname)
        if not os.path.exists(path):
            continue
        data = json.load(open(path, encoding="utf-8"))
        source_label = None
        for p in data.get("products", []):
            counts["listings"] += 1
            name = p.get("name", "")
            source = p.get("source", fname)
            source_label = source
            parsed = PARSERS[kind](name)

            # Per-tin pricing: a 4-pack's listing price is divided across 4 tins.
            # pack_count is NOT part of identity, so packs group with singles.
            pack = (parsed or {}).get("pack_count", 1) or 1
            listing_price = p.get("price", "")
            member = {
                "name": name, "source": source, "url": p.get("url", ""),
                "listing_price": listing_price, "pack_count": pack,
                "price": _divide_price(listing_price, pack),   # per-tin, used for compare
                "last_seen": p.get("last_seen", ""),
                "year": (parsed or {}).get("year", "") or _year(name),
                "price_history": [
                    {"price": _divide_price(h.get("price", ""), pack), "date": h.get("date", "")}
                    for h in p.get("price_history", [])
                ],
            }

            # Gate on brand+blend only. Quantity stays IN the key (so different
            # sizes separate) but is NOT required — Treasured rarely states size,
            # and its missing-size listings should still collapse by brand+blend.
            if parsed and parsed["brand"] and parsed["blend"]:
                key = f"{_norm(source)}|{_key_norm(parsed['brand'])}|{_key_norm(parsed['blend'])}|{_norm(parsed['quantity'])}"
                if key not in groups:
                    groups[key] = {
                        "id": key, "brand": parsed["brand"], "blend": parsed["blend"],
                        "quantity": parsed["quantity"], "source": source,
                        "display_name": _display(parsed), "members": [],
                    }
                groups[key]["members"].append(member)
                name_to_id[name] = key
            else:
                # standalone: a group of one, keyed by the raw name
                key = f"{_norm(source)}|solo|{_norm(name)}"
                groups[key] = {
                    "id": key, "brand": (parsed or {}).get("brand", ""),
                    "blend": (parsed or {}).get("blend", ""),
                    "quantity": (parsed or {}).get("quantity", ""),
                    "source": source, "display_name": name, "members": [member],
                }
                name_to_id[name] = key
                if not parsed:
                    unmatched.append(f"[{source}] {name}")

    # stats + finalize: sort members by year, attach years list
    tins = []
    for g in groups.values():
        g["members"].sort(key=lambda m: m["year"] or "")
        g["years"] = sorted({m["year"] for m in g["members"] if m["year"]})
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
        },
        "tins": tins,
        "name_to_id": name_to_id,
    }
    json.dump(out, open(OUT_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"# {len(unmatched)} listings could not be structurally parsed "
                f"(left as standalone tins):\n\n")
        f.write("\n".join(sorted(unmatched)) + "\n")

    s = out["stats"]
    print(f"Listings: {s['total_listings']}  ->  Tins: {s['total_tins']}")
    print(f"Multi-member tins: {s['multi_member_tins']} "
          f"(collapsing {s['listings_in_groups']} listings)")
    print(f"Unparsed (standalone): {len(unmatched)}  — see {os.path.basename(LOG_FILE)}")
    print("\nLargest groups:")
    for g in sorted(tins, key=lambda x: -len(x["members"]))[:8]:
        if len(g["members"]) > 1:
            print(f"  {len(g['members']):>2}x  {g['display_name']}  "
                  f"[{', '.join(g['years'])}]")


if __name__ == "__main__":
    main()
