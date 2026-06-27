# Process Unmatched Tobacco Entries

Process the next batch of 50 unclassified Speak-Easy.Club titles from `docs/unmatched.log` into `blend_cache.json`.

## Context

`docs/unmatched.log` contains titles scraped from Speak-Easy.Club that haven't been matched to a brand/blend yet. Each line is formatted as `[Speak-Easy.Club] <title>`. The first 2 lines are headers; the Speak-Easy entries start at line 3.

`blend_cache.json` maps title text (without the `[Speak-Easy.Club] ` prefix) to `{brand, blend, is_tin, confidence}`.

Brand rules, abbreviations, and pipe signals live in **`docs/brand-rules.md`** (canonical, in the repo). Read it before classifying. The memory file `speakeasy_brand_rules.md` is a pointer to that file.

Progress is tracked in memory at `~/.claude/projects/-Users-jvandalen-Documents-tintracker-cloned/memory/blend_cache_progress.md`.

## Step 1 — Find current position

Read `blend_cache_progress.md`. Find the "Next batch to process" entry, e.g. "batch 15" = entries 751–800.

Entry N (1-indexed) lives at line N+2 of `unmatched.log`. So batch starting at entry 751 = Read offset 752, limit 50.

## Step 2 — Read the batch

Read 50 lines starting at the correct offset. Strip the `[Speak-Easy.Club] ` prefix from each line — the remainder is the cache key.

## Step 3 — Classify each entry

For each title, determine:
- **`is_tin`** — `true` if it's a specific tobacco product (tin, bag, pouch, bulk block). `false` for:
  - Forum noise / partial sentences ("We'll start at", "Spend", "Take everything for", etc.)
  - Pipes and pipe accessories (see pipe signals below)
  - Lots / multi-packs ("x2", "x3", "lot", "bundle", "full box", multiple qty/weights in one title)
  - Chewing tobacco, cigars, cigar brands
  - Table header artifacts ("TobaccoYearPrice...")
- **`brand`** — canonical brand name, or `""` if unknown
- **`blend`** — canonical blend name, or `""` if unknown
- **`confidence`** — 0.0–1.0 (use 0.90+ for confirmed, 0.70–0.89 for likely, 0.50–0.69 for uncertain)

### Pipe signals → is_tin: false

If a pipe brand name appears **and** any of these descriptors are present, it's a pipe:
- Shape names: billiard, dublin, poker, bulldog, lovat, apple, rhodesian, hawkbill, freehand, bent, straight, canadien, cutty, oom paul
- Condition: unsmoked, NIB, smoked once/twice, sandblasted, rusticated, smooth finish, natural finish
- Measurements or "9mm filter", "P-Lip", "spigot", "push tenon", "non-plip"
- Makers: Castello, Comoy's, Savinelli (without a tobacco blend name), Peterson (with shape # e.g. X220), Stanwell, Vauen, Kaywoodie, Ben Wade, Nørding, Ser Jacopo, Ardor, Talbert, Tinsky, Steve Morrisette, Wayne Teipen, Nate Rose, Boswell

**Exception:** Savinelli makes tobacco (e.g. "Brunello Flake", "145th Anniversary") — if a blend name follows, is_tin: true.

### Brand abbreviations

| Shorthand | Full brand |
|---|---|
| SG | Samuel Gawith |
| GH / G&H / G.H. | Gawith, Hoggarth & Co. |
| C&D / CD | Cornell & Diehl |
| GLP / GL Pease | G.L. Pease |
| HH | Hearth & Home |
| MB / MacB | Mac Baren |
| HU | HU Tobacco |
| DSK | Orlik Dark Strong Kentucky |
| FVF | Samuel Gawith Full Virginia Flake |
| SJF | Samuel Gawith St. James Flake |
| ODF | Hearth & Home Old Dark Fired |
| CRF | Cornell & Diehl Carolina Red Flake |
| Cap Blue / Cap Yellow | Capstan Blue / Capstan Yellow |
| WCC / W.C. | Watch City Cigars |
| McC | McClelland |
| OGS | Orlik Golden Sliced |
| BS Flake | Samuel Gawith Brown Sugar Flake |
| KC Flake | Samuel Gawith Kendal Cream Flake |

### Non-obvious brand facts

- **G.L. Pease** makes: Abingdon, Charing Cross, Westminster, Star of the East, Speakeasy, Tilbury, Triple Play, Sixpence, Embarcadero, Fillmore, Temple Bar, Oak... wait — **Oak Alley is Cornell & Diehl**, not GLP
- **Cornell & Diehl** makes: Oak Alley, Manhattan Afternoon, Sunday Picnic, Five O'Clock Shadow, Chenet's Cake, Opening Night, Anthology series, Night Train, We Three Kings, Sun Bear, "CD" prefix = C&D
- **Dan Tobacco** makes: Devil's Holiday, Hamborger Veermaster, Salty Dog, Roper's Roundels, Dan Milonga
- **McClelland** makes: Stave Aged, Tawny Flake, St. James Woods, Virginia Woods, Wilderness, Dominican Glory, Christmas Cheer, Blackwoods Flake, Beacon Extra, Dark Star, 3 Oaks series
- **Samuel Gawith** makes: FVF, SJF, Skiff Mixture, Navy Flake, Brown Sugar Flake, Kendal Cream Flake
- **Sutliff** makes: Cringle Flake, Eastfarthing, Sweated, TS1R, J4 Burley, Anomalous, Virginia Slices ("Va Slices" without context = Sutliff), Barrel Aged series, 515 RC-1
- **Erik Stokkebye** makes: 4th Generation series (1931, 1989, Resolution etc.) — distinct from Peter Stokkebye
- **HU Tobacco** (German) makes: Flanagan, Aus den Krater series
- **Two Friends** makes: Redwood (collaboration brand between C&D/GLP founders)
- **Low Country** makes: Waccamaw, Santee, Cooper (blended by Cornell & Diehl for Low Country shop)
- **Hearth & Home** also makes: Viprati, Pure Virginia, Burley Flake, Acadian
- **Savinelli** also makes: Brunello Flake, anniversary blends
- **Rattray's** makes: Stirling Flake, Accountant's Mixture
- **Watch City Cigars** makes: Rouxgaroux, Simply Red, Old Black Magic, Strange Magic, Deluxe Crumb Cut
- **STG** makes: Balkan Sasieni, Escudo (Navy De Luxe)
- **"x2", "x3"** in title → is_tin: false (multi-pack rule)
- **"Crumble Kake"** is a Sutliff blend (all variants)
- **Chewing tobacco** (Stokers, Levi Garrett, etc.) → is_tin: false

## Step 4 — Web search uncertain entries

For any entry where you can't confidently identify the brand, **search before leaving it blank**. Use:
```
"<blend name> pipe tobacco" site:tobaccoreviews.com OR site:smokingpipes.com
```
or simply: `<blend name> pipe tobacco brand`

This resolves most unknowns in one search. Do searches in parallel for efficiency.

## Step 5 — Write to cache

```python
import json
with open('blend_cache.json') as f:
    cache = json.load(f)
# add new entries (cache.update(batch_dict))
with open('blend_cache.json', 'w') as f:
    json.dump(cache, f, indent=2, ensure_ascii=False)
```

Keys are the title text **without** the `[Speak-Easy.Club] ` prefix.

## Step 6 — Update progress memory

Edit `blend_cache_progress.md`:
- Add the completed batch to the "Completed Batches" table
- Update "Next batch to process" to the next batch number and entry range

## Step 7 — Report to user

After writing the batch, report:
- Entries written, tins vs excluded, branded tins count
- Cache total
- Any remaining uncertain entries (brand still blank) as a table for user input

Then wait for corrections or "continue" before starting the next batch, per CLAUDE.md rules.

## Step 8 — End-of-round sanity check (run only when unmatched.log is exhausted)

After the final batch of a round, run `python3 consolidate.py`, then run this audit and present the results to the user for review before committing:

```python
import json, difflib, re
from itertools import combinations

with open('docs/canonical.json') as f:
    tins = json.load(f)['tins']

entries = [(t['brand'], t['blend'], sum(len(s['members']) for s in t['sizes'])) for t in tins]

def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())

# 1. Near-duplicate brand names (catches "A & C Petersen" vs "A&C Petersen" etc.)
all_brands = sorted({brand for brand, _, _ in entries})
brand_dupes = []
for a, b in combinations(all_brands, 2):
    ratio = difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()
    if ratio >= 0.85 and norm(a) != norm(b):
        ca = sum(cnt for br, _, cnt in entries if br == a)
        cb = sum(cnt for br, _, cnt in entries if br == b)
        brand_dupes.append((ratio, a, ca, b, cb))

# 2. Near-duplicate blends within same brand (ratio >= 0.85)
by_brand = {}
for brand, blend, cnt in entries:
    by_brand.setdefault(brand, []).append((blend, cnt))

near_dupes = []
for brand, blends in sorted(by_brand.items()):
    names = [b for b, _ in blends]
    for a, b in combinations(names, 2):
        ratio = difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()
        if ratio >= 0.85 and norm(a) != norm(b):
            ca = next(c for x, c in blends if x == a)
            cb = next(c for x, c in blends if x == b)
            near_dupes.append((ratio, brand, a, ca, b, cb))

# 3. Same blend name, different brand (possible mis-brand)
by_blend = {}
for brand, blend, cnt in entries:
    by_blend.setdefault(norm(blend), []).append((brand, blend, cnt))

cross_brand = [(g[0][1], [(br, cnt) for br, _, cnt in g])
               for g in by_blend.values()
               if len({br for br, _, _ in g}) > 1]

print("=== NEAR-DUPLICATE BRAND NAMES ===")
for ratio, a, ca, b, cb in sorted(brand_dupes, reverse=True):
    print(f"[{ratio:.2f}] '{a}' ({ca}x total) vs '{b}' ({cb}x total)")

print("\n=== NEAR-DUPLICATE BLENDS (same brand, similarity >= 0.85) ===")
for ratio, brand, a, ca, b, cb in sorted(near_dupes, reverse=True):
    print(f"[{ratio:.2f}] {brand}: '{a}' ({ca}x) vs '{b}' ({cb}x)")

print("\n=== SAME BLEND NAME, DIFFERENT BRAND ===")
for blend, groups in sorted(cross_brand):
    print(f"'{blend}': " + ", ".join(f"{br} ({cnt}x)" for br, cnt in groups))
```

Present the output as two tables to the user. For each potential dupe, ask: **merge, keep-separate, or unsure?** Do not make any changes until the user responds. When they confirm merges, apply them to `blend_cache.json` and `blend_aliases.json` together (same as the standard correction workflow).

## New brand rules

When the user provides a brand correction or a new brand is confirmed:
1. Update `docs/brand-rules.md` (the repo copy — this is the canonical source)
2. Also update `speakeasy_brand_rules.md` in the memory directory to keep it in sync
