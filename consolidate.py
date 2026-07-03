"""Consolidation overlay — groups raw listings into canonical tins.

NON-DESTRUCTIVE: reads the per-source scrape files read-only and writes a
separate docs/canonical.json. Deleting that file fully reverts the feature.

Blend identity (brand + blend) comes from the LLM-extracted blend_cache.json,
with overrides.json winning over it (see extract.py / build_cache.py). The
deterministic bits — tin size, year, price — are still parsed here with regex,
because those are reliable.

We only track SINGLE tins. Multi-tin listings — multi-packs, lots, variety /
sampler / assortment packs, "3 bags of …", "several tins", etc. — are dropped
entirely (see _is_multi); a price spread across several tins can't be compared
like-for-like against a single tin, so we don't capture it at all.

A "tin" is one (brand, blend). Size/weight variants of the same blend collapse
into a single tin record under a `sizes` array — each size carries its own
listings. Year-variants within a size collapse together (e.g. McClelland
Christmas Cheer 100g across 2008–2017 = one size entry, many price points), and
the SAME blend from DIFFERENT vendors collapses too (cross-source). Listings
with no clean identity (unknown brand, or not a single blend — cigars, bundles)
stay as a group of one, never mis-merged.
"""
import json
import os
import re
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
DOCS = os.path.join(HERE, "docs")
OUT_FILE = os.path.join(DOCS, "canonical.json")
LOG_FILE = os.path.join(DOCS, "unmatched.log")
EXCLUDED_LOG = os.path.join(DOCS, "excluded.log")
CACHE_FILE = os.path.join(HERE, "blend_cache.json")
OVERRIDES_FILE = os.path.join(HERE, "overrides.json")
ALIASES_FILE = os.path.join(HERE, "blend_aliases.json")
BRAND_ALIASES_FILE = os.path.join(HERE, "brand_aliases.json")

SOURCE_FILES = [
    "products.json",
    "products_tinbids.json",
    "products_treasuredsmokes.json",
    "products_4noggins.json",
    "products_speakeasy.json",
]

# tin weight, in a name OR a free-text description: "50g", "100 grams", "2oz",
# "2 ounce", "1-3/4 oz", "1.76oz". (This is a single tin's weight, not a count.)
QTY_RE = re.compile(r"(\d+\s*(?:g|grams?)\b|\d[\d.\-/]*\s*(?:oz|ounces?)\b)", re.I)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")

# Deterministic backstop for "this is not a single tin". The LLM's is_tin flag
# is the primary gate (see main()); this catches obvious multi-tin listings even
# on a fresh scrape, before any extraction has run. Note "8oz. Pack" (a single
# large pack) and "My Mixture 965 50g Tin" (a blend number) are fine — neither a
# weight nor a blend number reads as a count here.
_QTY = r"(?:\d+|two|three|four|five|six|seven|eight|nine|ten)"  # count: digit or word
_WORD_NUM = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
             "seven": 7, "eight": 8, "nine": 9, "ten": 10}

MULTI_RE = re.compile(
    r"""
      \b\d+\s*[-\s]?packs?\b                                   # 3-pack, 4 pack, 5 packs
    | \b\d+\s*[-\s]?pk\b                                       # 3pk
    | \b(?:lot|box|set|bundle|case|pack|selection)\s+of\s+\d+\b  # lot of 2, pack of 3
    | \b\d+\s*x\b                                              # 4x, 5 x 1.5oz, 2 x 50g
    | \b(?:variety|sampler|assort\w*|trio|duo|quartet|quintet|sextet)\b  # variety / trio …
    | \bblending\s+chest\b                                     # blending chest set
    | \b(?:several|multiple)\b                                 # several tins, multiple
    | \b(?:bag|jar|tin|pouch|can|tub)s?\s+and\s+(?:bag|jar|tin|pouch|can|tub)s?\b  # bag and tins
    """,
    re.I | re.X,
)

# A count (>1) then an optional tin weight, then a PLURAL container: "2 tins",
# "Four 50g Tins", "15 tins", "3 bags". The mandatory space after the count is
# load-bearing: it stops a weight like "50g" (digit flush against its unit) from
# reading as a count — pipestud writes "50g tins" generically for SINGLE tins.
# Plural also guards against a lone "… 50g Tin".
COUNT_PLURAL_RE = re.compile(
    r"\b(" + _QTY + r")\s+"
    r"(?:\d[\d.\-/]*\s*(?:g|grams?|oz|ounces?)\s+)?"
    r"(?:tins|jars|bags|pouches|cans|tubs)\b",
    re.I,
)

# A hyphenated count + container, where the hyphen disambiguates a real count
# from a blend number: "7-Jar Set", "3-Tin lot". (Plural not required here.)
COUNT_HYPHEN_RE = re.compile(
    r"\b(" + _QTY + r")\s*-\s*(?:tin|jar|bag|pouch|can|tub)s?\b",
    re.I,
)


def _count_gt_one(m):
    tok = m.group(1).lower()
    return _WORD_NUM.get(tok, int(tok) if tok.isdigit() else 1) > 1


def _is_multi(s):
    """True if the listing is a multi-pack / lot / variety pack / multi-tin set —
    anything that isn't a single tin and so gets dropped from the catalog."""
    s = s or ""
    if MULTI_RE.search(s):
        return True
    return (any(_count_gt_one(m) for m in COUNT_PLURAL_RE.finditer(s))
            or any(_count_gt_one(m) for m in COUNT_HYPHEN_RE.finditer(s)))


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


def _qty_grams(q):
    """Return quantity as grams (float) for size sorting. Unknown → large number."""
    m = re.match(r"([\d.]+)\s*(g|oz)", (q or "").strip(), re.I)
    if not m:
        return 999999.0
    v = float(m.group(1))
    return v if m.group(2).lower() == "g" else v * 28.3495


def _norm_apos(s):
    """Normalize Unicode curly apostrophes/quotes to ASCII so cache keys match source data."""
    return s.replace('’', "'").replace('‘', "'").replace('′', "'")


def load_identity():
    """title -> {brand, blend, is_tin}. Overrides win over the cache."""
    cache = json.load(open(CACHE_FILE, encoding="utf-8")) if os.path.exists(CACHE_FILE) else {}
    ident = {_norm_apos(t): {"brand": r.get("brand", ""), "blend": r.get("blend", ""),
                 "is_tin": r.get("is_tin", True)} for t, r in cache.items()}
    if os.path.exists(OVERRIDES_FILE):
        for t, r in json.load(open(OVERRIDES_FILE, encoding="utf-8")).items():
            ident[_norm_apos(t)] = {"brand": r.get("brand", ""), "blend": r.get("blend", ""),
                        "is_tin": r.get("is_tin", True)}
    return ident


def load_aliases():
    """(brand, bad_blend) -> canonical_blend. Applied after identity lookup."""
    if not os.path.exists(ALIASES_FILE):
        return {}
    return json.load(open(ALIASES_FILE, encoding="utf-8"))


def load_brand_aliases():
    """shorthand_brand -> canonical_brand. Applied after identity lookup."""
    if not os.path.exists(BRAND_ALIASES_FILE):
        return {}
    return json.load(open(BRAND_ALIASES_FILE, encoding="utf-8"))


def main():
    ident = load_identity()
    aliases = load_aliases()
    brand_aliases = load_brand_aliases()
    groups = {}
    name_to_id = {}
    unmatched = []
    excluded = []
    counts = {"listings": 0, "grouped_tins": 0, "collapsed_listings": 0, "excluded": 0}

    for fname in SOURCE_FILES:
        path = os.path.join(DOCS, fname)
        if not os.path.exists(path):
            continue
        data = json.load(open(path, encoding="utf-8"))
        for p in data.get("products", []):
            counts["listings"] += 1
            name = (p.get("name") or "").strip()
            source = p.get("source", fname)

            id_rec = ident.get(_norm_apos(name), {})
            brand = (id_rec.get("brand") or "").strip()
            blend = (id_rec.get("blend") or "").strip()
            is_tin = id_rec.get("is_tin", True)

            # Normalize shorthand brand names to canonical form.
            brand = brand_aliases.get(brand, brand)

            # Normalize Virginia/Perique shorthand: "Va/Per", "Va. Per", "Va. Perique"
            # → "Virginia Perique". The separator (/ or .) is load-bearing: it prevents
            # "AJ's VaPer" (H&H official name, no separator) from being rewritten.
            blend = re.sub(r'\bVa[/.]\s*Per(?:ique)?\b', 'Virginia Perique', blend, flags=re.I)

            # Apply blend aliases: remap known-wrong blend names to canonical.
            # This fires after cache/overrides so no stale entry can roll back a fix.
            blend = aliases.get(brand, {}).get(blend, blend)

            # Drop anything that isn't a single tin. Two gates: the LLM's is_tin
            # flag (catches multi-blend sets, bundles, cigars — things regex can't
            # read), and a deterministic regex backstop for obvious multi-tin
            # quantities on titles not yet extracted.
            if not is_tin or _is_multi(name):
                counts["excluded"] += 1
                excluded.append(f"[{source}] {name}")
                continue

            quantity = (_qty(name) or p.get("weight", "") or _qty(p.get("description", "")))

            member = {
                "name": name, "source": source, "url": p.get("url", ""),
                "price": p.get("price", ""),
                "last_updated": p.get("last_updated") or p.get("last_seen", ""),
                "first_seen": p.get("first_seen", ""),
                "year": _year(name),
                "price_history": [
                    {"price": h.get("price", ""), "date": h.get("date", "")}
                    for h in p.get("price_history", [])
                ],
            }

            # Group cross-source on (brand, blend) — but only when we have a
            # clean single-blend identity. Size/weight is a secondary dimension
            # stored in the `sizes` array. Otherwise it's a standalone tin.
            if brand and blend:
                key = f"{_norm(brand)}|{_norm(blend)}"
                g = groups.get(key)
                if not g:
                    disp = f"{brand} {blend}".strip()
                    g = groups[key] = {
                        "id": key, "brand": brand, "blend": blend,
                        "display_name": disp,
                        "sources": [], "_sizes": {},
                    }
                sz = g["_sizes"].setdefault(quantity, {
                    "quantity": quantity, "members": [], "sources": [],
                })
                sz["members"].append(member)
                if source not in sz["sources"]:
                    sz["sources"].append(source)
                if source not in g["sources"]:
                    g["sources"].append(source)
            else:
                unmatched.append(f"[{source}] {name}")
                continue
            name_to_id[name] = key

    tins = []
    for g in groups.values():
        sizes = sorted(g.pop("_sizes").values(), key=lambda s: _qty_grams(s["quantity"]))
        for sz in sizes:
            sz["members"].sort(key=lambda m: m["year"] or "")
        g["sizes"] = sizes
        all_members = [m for sz in sizes for m in sz["members"]]
        g["years"] = sorted({m["year"] for m in all_members if m["year"]})
        g["source"] = g["sources"][0] if len(g["sources"]) == 1 else "Multiple sources"
        total = len(all_members)
        if total > 1:
            counts["grouped_tins"] += 1
            counts["collapsed_listings"] += total
        tins.append(g)
    tins.sort(key=lambda g: g["display_name"].lower())

    out = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "total_listings": counts["listings"],
            "excluded_multipacks": counts["excluded"],
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
    with open(EXCLUDED_LOG, "w", encoding="utf-8") as f:
        f.write(f"# {len(excluded)} multi-pack / lot / variety-pack listings "
                f"dropped (not single tins):\n\n")
        f.write("\n".join(sorted(excluded)) + "\n")

    s = out["stats"]
    print(f"Listings: {s['total_listings']}  ->  Tins: {s['total_tins']}")
    print(f"Excluded multi-packs/lots: {s['excluded_multipacks']}  — see {os.path.basename(EXCLUDED_LOG)}")
    print(f"Multi-member tins: {s['multi_member_tins']} "
          f"(collapsing {s['listings_in_groups']} listings)")
    print(f"Cross-source tins: {s['cross_source_tins']}")
    print(f"Standalone (no identity): {len(unmatched)}  — see {os.path.basename(LOG_FILE)}")
    print("\nLargest groups:")
    def _total_members(g):
        return sum(len(sz["members"]) for sz in g["sizes"])
    for g in sorted(tins, key=lambda x: -_total_members(x))[:10]:
        total = _total_members(g)
        if total > 1:
            sizes_str = ", ".join(sz["quantity"] or "?" for sz in g["sizes"])
            print(f"  {total:>2}x  {g['display_name']}  [{sizes_str}]  "
                  f"[{', '.join(g['sources'])}]")

    # Regenerate the static SEO pages + sitemap from the canonical data we just
    # wrote, so docs/tin/ never drifts from canonical.json.
    import generate_seo
    generate_seo.generate(out)


if __name__ == "__main__":
    main()
