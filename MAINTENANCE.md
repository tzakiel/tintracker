# Maintaining the tin groupings

How the "Grouped tins" consolidation stays correct as the scrapers keep running.
No Anthropic API key is required for any of this — it's all local + CI.

## The moving parts

| File | What it is | Who edits it |
|---|---|---|
| `docs/products_*.json` | Raw scrapes (one per source) | Scrapers only — never edit by hand |
| `blend_cache.json` | `title → {brand, blend, is_tin}` — Claude's extracted identities | Grows as new titles get labeled |
| `overrides.json` | Your authoritative corrections — **wins over the cache** | You (or Claude) |
| `consolidate.py` | The regroup step. **Key-free, run anytime.** | — |
| `docs/canonical.json` | Output: the grouped tins the site reads | Generated — don't edit |
| `docs/unmatched.log` | Kept but **ungrouped** listings (need identity) | Generated — your to-do list |
| `docs/excluded.log` | Listings **dropped** as multi-packs / lots / variety | Generated — audit surface |

## How a listing flows through `consolidate.py`

1. **Multi-pack / lot / variety / bundle?** → dropped (logged to `excluded.log`).
   Caught two ways: the LLM's `is_tin: false` flag in the cache, and the
   `_is_multi` regex backstop (handles `3-pack`, `4x`, `lot of N`, `N tins`,
   `variety`, … even on never-seen titles).
2. **Has a brand + blend identity?** (from `overrides.json`, else `blend_cache.json`)
   → grouped with every other listing sharing that `(brand, blend, size)`,
   across all sources.
3. **No identity yet?** → kept as a standalone one-off, logged to `unmatched.log`.

## What happens automatically (CI, every scrape)

`.github/commit-scrape.sh` runs `python consolidate.py` after each scrape. With
no action from you:

- ✅ Packs / lots / variety packs stay out — the site never gets dirty.
- ✅ Known titles keep grouping from the committed `blend_cache.json`.
- ⚠️ A **new** title is not auto-grouped. The cache is keyed by *exact title*,
  so a fresh listing — even of a blend already tracked (e.g. next year's
  `McClelland: CHRISTMAS CHEER 100g 2026`) — has no identity yet and shows as a
  standalone one-off until it's labeled.

So the site stays clean on its own; new arrivals just accumulate *ungrouped*
until folded in. That folding-in is the only recurring task.

## The recurring task (key-free, ~monthly or whenever)

1. `python consolidate.py`
2. Open `docs/unmatched.log` — the new ungrouped singles.
3. Give them identity, either:
   - **paste that list into a Claude chat** → Claude extracts brand/blend and
     updates `blend_cache.json` (this is what a key'd `extract.py` run would do), or
   - add lines to `overrides.json` yourself:
     ```json
     "<exact title>": {"brand": "Brand", "blend": "Blend"}
     ```
4. `python consolidate.py` again → the new listings now merge.
5. Commit/push `docs/canonical.json`, `blend_cache.json`, `overrides.json`.

### Fixing mistakes (anytime, permanent)

Add a line to `overrides.json` and rerun `consolidate.py`:

- **Re-group / fix identity:** `"<title>": {"brand": "X", "blend": "Y"}`
- **Drop a pack the regex missed:** `"<title>": {"brand": "", "blend": "", "is_tin": false}`

Overrides are matched by **exact title string** (including curly quotes / double
spaces) and are locked forever once added.

### One caveat

`_is_multi` runs *before* identity, so if it ever wrongly drops a real single
tin (a blend name containing "trio", "4x", etc.), an override **can't** rescue it
— that needs a small regex tweak in `consolidate.py`. If you spot one in
`excluded.log` that shouldn't be there, flag it.

## `extract.py` (optional, needs a key — not used today)

`extract.py` is the automated version of step 3: it calls the Anthropic API to
label new titles in bulk and writes `blend_cache.json`. It only runs when you
choose to (`export ANTHROPIC_API_KEY=…; python extract.py`). Currently unused —
the key-free loop above (Claude-in-chat or hand overrides) replaces it.
