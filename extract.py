"""LLM blend-identity extraction — turns messy scraped titles into {brand, blend}.

WHY THIS EXISTS
  The scraped product titles name the same blend four different ways (see the
  four sources below). Regex parsing of that (the old consolidate.py approach)
  bailed on 60%+ of listings. An LLM reads the title and pulls out a clean
  (brand, blend) identity; consolidate.py then groups deterministically on it.

HOW IT'S "TRAINED"
  Three authority levels, highest first:
    1. overrides.json  — human-authoritative {title -> {...}}. Always wins.
                         Every wrong extraction gets one line added here and is
                         then locked forever. This is how you correct the model.
    2. blend_cache.json — past LLM extractions, keyed by exact title. Only NEW
                         titles cost an API call, so reruns are ~free.
    3. the LLM         — called only for titles in neither file above.

  Run locally (needs ANTHROPIC_API_KEY); commit blend_cache.json + overrides.json.
  CI never calls the API — consolidate.py just reads the committed cache.

USAGE
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    python extract.py            # extract new titles, refresh cache, print review list
    python extract.py --recheck  # re-extract everything (ignores cache; keeps overrides)
"""
import argparse
import json
import os
import sys

import anthropic

HERE = os.path.dirname(__file__)
DOCS = os.path.join(HERE, "docs")
CACHE_FILE = os.path.join(HERE, "blend_cache.json")
OVERRIDES_FILE = os.path.join(HERE, "overrides.json")

# Source file -> human label for the source's naming convention (helps the model).
SOURCE_FILES = {
    "products.json": "pipestud.com — 'Brand['s] Blend SIZE tin – Year/era …'",
    "products_tinbids.json": "tinbids — freeform auction titles (years, lot counts, condition words, BIN prices mixed in)",
    "products_treasuredsmokes.json": "treasuredsmokes — 'Brand - Blend - Year!' (hyphen-delimited)",
    "products_4noggins.json": "4noggins.com — 'Brand: BLEND NAME SIZE YEAR - C'",
    "products_speakeasy.json": "speakeasy — freeform WTS forum descriptions; typically 'Brand Blend SIZE' or 'Brand Blend SIZE Year condition' (e.g. 'McClelland Christmas Cheer 100g', 'GL Pease Kensington 2oz 2018 sealed')",
}

MODEL = "claude-opus-4-8"
BATCH = 25                # titles per API call
CONFIDENCE_REVIEW = 0.75  # below this → printed for human review

SYSTEM = """You normalize messy pipe-tobacco listing titles into a clean blend identity for grouping.

For each title return:
  brand      The manufacturer / house. Canonical, no possessive, no era. "McClelland's" -> "McClelland", "Robert McConnell's" -> "Robert McConnell". Keep ampersands ("Cornell & Diehl", "Gawith & Hoggarth"). "" if you genuinely can't tell.
  blend      The blend/product name ONLY — no brand, no size, no year, no condition words, no lot/pack counts, no auction cruft (NR, BIN, $price, "Sealed", "Very Nice", "Collectible Tobacco Sealed Tin", "Bid or Buy Now"). Expand obvious abbreviations ("Syr." -> "Syrian", "Va." -> "Virginia"). Drop series/line prefixes from the blend only when they are clearly a collection label, but keep them if they're part of the blend's actual name.
  is_tin     true ONLY for a SINGLE retail pipe-tobacco tin/jar/bag of ONE blend. false for any multi-tin listing — multi-packs, N-packs, "lot of N", "N tins/bags of …", "several tins" (even of the SAME blend) — and for cigars, variety/sampler/assortment packs, multi-blend lots, or blending-chest sets. Anything that isn't exactly one tin is false; those listings are dropped, not tracked.
  confidence 0.0–1.0. Be honest: lower it when brand vs. blend is ambiguous, when a token might be a reseller/collection rather than the maker, or when the title is barely parseable.

Rules of thumb:
- A leading "Word:" on 4noggins is usually the brand, but NOT always — e.g. a reseller's own collection name can sit there with the real maker inside the title. If unsure which is the maker, pick your best guess and LOWER confidence.
- Year-variants of the same blend must produce the IDENTICAL brand+blend (years live elsewhere).
- Never invent a brand. Empty string + low confidence beats a guess presented as certain.
- "HH" as a prefix or standalone abbreviation in a pipe tobacco title almost always refers to the Mac Baren HH product line (e.g. "HH Acadian Perique", "HH Old Dark Fired", "HH Mature Virginia", "HH Burley Flake"). Always extract brand as "Mac Baren" and keep the full "HH …" name as the blend. Do NOT classify "HH …" listings as Hearth & Home.

Examples:
  "McClelland’s Christmas Cheer 100g tin – Year 2014" -> brand "McClelland", blend "Christmas Cheer", is_tin true, confidence 0.98
  "Mullingar’s Syr. Latakia Kenmare 2oz tin – 1980’s …" -> brand "Mullingar", blend "Syrian Latakia Kenmare", is_tin true, confidence 0.9
  "Lot of 2 Excellent 2019 & 2020 Cornell & Diehl Kings Stride Warped Series Until the End 2oz. Tins" -> brand "Cornell & Diehl", blend "Until the End", is_tin false, confidence 0.9
  "Very Nice Sealed 2018 Dunhill My Mixture 965 50g. Tin" -> brand "Dunhill", blend "My Mixture 965", is_tin true, confidence 0.95
  "Ashton: BLACK PARROT 50g 2003 - C" -> brand "Ashton", blend "Black Parrot", is_tin true, confidence 0.97
  "Fuente and Montecristo Bundle" -> brand "", blend "", is_tin false, confidence 0.95
  "Dunhill Variety 5-Pack of 50g tins – Various Years" -> brand "Dunhill", blend "", is_tin false, confidence 0.9
  "72 hour auction! 3 bags of Esoterica and 15 tins! Plus 2 tins of Germain's Balkan Sobranie!" -> brand "", blend "", is_tin false, confidence 0.9
"""

SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "i": {"type": "integer", "description": "the index given in the input"},
                    "brand": {"type": "string"},
                    "blend": {"type": "string"},
                    "is_tin": {"type": "boolean"},
                    "confidence": {"type": "number"},
                },
                "required": ["i", "brand", "blend", "is_tin", "confidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}


def load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def collect_titles():
    """Unique titles in catalog order, each tagged with its source convention."""
    out = {}  # title -> source hint
    for fname, hint in SOURCE_FILES.items():
        data = load_json(os.path.join(DOCS, fname), None)
        if not data:
            continue
        for p in data.get("products", []):
            name = (p.get("name") or "").strip()
            if name and name not in out:
                out[name] = hint
    return out


def extract_batch(client, batch):
    """batch: list of (title, source_hint). Returns {title: record}."""
    lines = []
    for idx, (title, hint) in enumerate(batch):
        lines.append(f"[{idx}] (source: {hint})\n{title}")
    user = "Extract identity for each title. Return one result per index.\n\n" + "\n\n".join(lines)

    resp = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
    )
    text = next(b.text for b in resp.content if b.type == "text")
    parsed = json.loads(text)

    out = {}
    for r in parsed["results"]:
        i = r["i"]
        if 0 <= i < len(batch):
            title = batch[i][0]
            out[title] = {
                "brand": r["brand"].strip(),
                "blend": r["blend"].strip(),
                "is_tin": bool(r["is_tin"]),
                "confidence": float(r["confidence"]),
                "source": "llm",
            }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recheck", action="store_true", help="re-extract every title (ignore cache)")
    args = ap.parse_args()

    titles = collect_titles()
    overrides = load_json(OVERRIDES_FILE, {})
    cache = {} if args.recheck else load_json(CACHE_FILE, {})

    # overrides always win; mark their source so consolidate/eval can tell them apart
    for title, rec in overrides.items():
        merged = {"brand": "", "blend": "", "is_tin": True, "confidence": 1.0}
        merged.update(rec)
        merged["source"] = "override"
        cache[title] = merged

    todo = [(t, h) for t, h in titles.items() if t not in cache]
    print(f"{len(titles)} unique titles · {len(overrides)} overrides · "
          f"{len(cache) - len(overrides)} cached · {len(todo)} to extract")

    if todo:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("ANTHROPIC_API_KEY is not set — needed to extract new titles.")
        client = anthropic.Anthropic()
        for start in range(0, len(todo), BATCH):
            batch = todo[start:start + BATCH]
            print(f"  extracting {start + 1}–{start + len(batch)} of {len(todo)} …")
            cache.update(extract_batch(client, batch))

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2, sort_keys=True)

    # Review list: anything the model was unsure about or flagged non-identity,
    # excluding titles already pinned in overrides.
    review = []
    for title in titles:
        rec = cache.get(title, {})
        if rec.get("source") == "override":
            continue
        if (not rec.get("is_tin")) or (not rec.get("brand")) or rec.get("confidence", 1) < CONFIDENCE_REVIEW:
            review.append((title, rec))

    print(f"\nWrote {os.path.basename(CACHE_FILE)} ({len(cache)} entries).")
    print(f"\n{len(review)} titles need your eyes (add fixes to {os.path.basename(OVERRIDES_FILE)}):\n")
    for title, rec in review:
        flag = "NOT-TIN" if not rec.get("is_tin") else f"conf={rec.get('confidence', 0):.2f}"
        print(f"  [{flag}] brand={rec.get('brand','')!r} blend={rec.get('blend','')!r}")
        print(f"           {title}")


if __name__ == "__main__":
    main()
