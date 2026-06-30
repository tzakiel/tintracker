# TinTracker — Full Design System v2 Migration Spec

Goal: bring `docs/index.html` and `docs/admin.html` fully onto the design system **v2 (terracotta) visual direction** — colors, type, spacing, shadows, radii — sourced from `.claude/skills/tintracker-design/tokens/{colors,typography,spacing}.css`. The tokens are the ground truth; the skill's `README.md` documents the *older* dusty-rose palette and is superseded by the token files.

Status when this spec was written: the **accent migration is already done** (chips, pagination, row-hover, search focus ring, back button, tin-badge are on terracotta `#d45d35`). Everything else below is the remaining foundational work.

---

## 0. Architecture decision — how tokens get delivered

These are single-file static pages (GitHub Pages serves `docs/`), no build step. Recommended:

1. Create **`docs/tokens.css`** containing the consolidated v2 `:root` block (section 1 below).
2. Add `<link rel="stylesheet" href="tokens.css" />` to the `<head>` of **both** `index.html` and `admin.html`, before the inline `<style>`.
3. Replace hardcoded values in each `<style>` block with `var(--token)` references per the maps below.

This de-duplicates tokens across the two pages and matches the design system's "one import" intent. (Alternative: paste the `:root` block inline at the top of each `<style>` — simpler but duplicated. Prefer the shared file.)

Do **not** link the skill's `styles.css` directly — it lives outside `docs/` and won't be served.

---

## 1. `docs/tokens.css` — consolidated v2 `:root`

```css
:root {
  /* Surfaces */
  --bg-page:        #f5f0e8;
  --bg-card:        #ffffff;
  --bg-surface:     #fdfbf8;
  --bg-header:      #1a0e06;
  --bg-row-alt:     #fdfbf8;
  --bg-row-hover:   #fdf0eb;
  --bg-chip:        #ffffff;
  --bg-chip-active: #d45d35;
  --bg-dropdown:    #ffffff;
  --bg-tooltip:     #1a0e06;
  --bg-positive:    #daf0d2;

  /* Text */
  --text-primary:     #1a0f08;
  --text-strong:      #3d2810;
  --text-link:        #5c3820;   /* product names */
  --text-muted:       #7a5a3c;
  --text-soft:        #7a5a3c;
  --text-faint:       #a88060;
  --text-placeholder: #c4a07e;
  --text-header:      #fdf0e2;
  --text-header-sub:  #c4a07e;
  --text-header-link: #e8c888;
  --text-accent:      #d45d35;
  --text-label:       #a88060;
  --text-tooltip:     #fdf0e2;
  --text-positive:    #2a7018;

  /* Borders */
  --border-default: #e5d5be;
  --border-card:    #f2eae0;
  --border-subtle:  #f2eae0;
  --border-focus:   #d45d35;

  /* Accent */
  --accent:       #d45d35;
  --accent-hover: #b84a22;
  --accent-dark:  #8f3518;
  --accent-chart: #FF69AF;

  /* Fonts */
  --font-body:       "Work Sans", Helvetica, Arial, sans-serif;
  --font-display:    "Young Serif", Georgia, serif;
  --font-decorative: "Uncial Antiqua", serif;

  /* Type scale */
  --text-2xs: 0.65rem;  --text-xs: 0.70rem;  --text-sm: 0.78rem;
  --text-base: 0.82rem; --text-md: 0.90rem;  --text-rg: 1.00rem;
  --text-lg: 1.15rem;   --text-xl: 1.20rem;  --text-2xl: 1.40rem;
  --text-3xl: 1.70rem;  --text-hero: 2.50rem;

  /* Weights */
  --weight-normal: 400; --weight-medium: 500; --weight-semibold: 600; --weight-bold: 700;

  /* Letter spacing */
  --tracking-wide: 0.03em; --tracking-wider: 0.05em; --tracking-widest: 0.07em;

  /* Radii */
  --radius-xs: 4px; --radius-sm: 6px; --radius-md: 10px;
  --radius-lg: 16px; --radius-xl: 18px; --radius-pill: 999px;

  /* Shadows (darker, two-layer in v2) */
  --shadow-header:      0 4px 14px rgba(18,8,4,.40);
  --shadow-card:        0 1px 3px rgba(26,15,8,.04), 0 4px 18px rgba(26,15,8,.10);
  --shadow-card-lg:     0 2px 6px rgba(26,15,8,.06), 0 8px 28px rgba(26,15,8,.11);
  --shadow-input:       0 2px 10px rgba(26,15,8,.07);
  --shadow-dropdown:    0 8px 24px rgba(26,15,8,.16);
  --shadow-mobile-card: 0 1px 3px rgba(26,15,8,.05), 0 2px 10px rgba(26,15,8,.08);
  --shadow-tooltip:     0 4px 14px rgba(0,0,0,.28);

  /* Focus ring — terracotta (DS spacing.css still has the OLD rose value; use this) */
  --focus-ring: 0 0 0 3px rgba(212,93,53,.18);

  /* Page dot grid (more subtle in v2) */
  --bg-dot-gradient: radial-gradient(rgba(150,110,60,.08) 1px, transparent 1.5px);
  --bg-dot-size: 22px 22px;
}
```

---

## 2. DECISIONS REQUIRED before implementing

These three are not find-replace — they change the app's visual identity. Confirm each.

| # | Change | Current → v2 | Impact |
|---|---|---|---|
| **D1** | **Header & table-head go near-black** | espresso `#5a3a24` → `#1a0e06` (`--bg-header`) | Biggest shift. The warm-brown header becomes near-black coffee. Also drives `theme-color` meta and a much darker `--shadow-header`. Table `<thead>` follows to match. |
| **D2** | **Cards become pure white** | `#fffdf8` → `#ffffff` (`--bg-card`) | Warm-white surfaces become clean white. Affects table bg, mobile cards, detail card, admin cards, chips, dropdown, inputs. |
| **D3** | **Row stripe becomes near-invisible** | even-row `#f6eedd` → `#fdfbf8` (`--bg-row-alt`) | The current visible cream zebra stripe nearly disappears (v2 prefers ultra-subtle). |

Recommendation: adopt all three — they ARE the v2 direction, and all are trivially reversible (one token each). But you should see them rendered before committing. Also flag for the user:

- **DS inconsistency (focus ring):** `spacing.css` `--focus-ring` still uses the old rose `rgba(207,138,115,.18)`; `colors.css` is terracotta. Spec above uses terracotta. Worth fixing upstream in the skill too.
- **No error/danger token exists in v2.** Admin's error styling (`.card.error` border `#e0b4a4`, `.error .stat-big` `#b06a50`) has no token equivalent. Leave as-is, or remap the error text to `--accent-dark` `#8f3518`. Open question — default: leave as-is.
- **Easter-egg green** (`.easter-egg-row` `#4a8c5c`) and **chart pink** (`#FF69AF`) are intentional/decorative — **do not touch**.

---

## 3. `index.html` migration map

### 3a. Head / foundations
- `<meta name="theme-color" content="#5a3a24">` → `#1a0e06` **(D1)**
- `body` bg `#f7f1e5` → `--bg-page` `#f5f0e8`; dot grid `radial-gradient(rgba(180,142,96,.13) 1.5px…)` / `1.6px` → `--bg-dot-gradient` (subtler); color `#3a2a1c` → `--text-primary`; font → `--font-body`
- Young-serif rule (`header h1, thead th, .detail-name, .detail-section-title`) font → `--font-display`

### 3b. Header
- `header` bg `#5a3a24` → `--bg-header` **(D1)**; color `#f5e8c8` → `--text-header`; padding → `--padding-header` (1.4rem 1.5rem 1.6rem); shadow `rgba(90,58,36,.22)` → `--shadow-header`
- `header h1` size `1.7rem` → `--text-3xl`; letter-spacing `.03em` → `--tracking-wide`
- `.brand-tin` color `#f5e8c8` → `--text-header`
- `header p` color `#e6c79c` → `--text-header-sub`; size `.85rem` → `--text-md`
- `.coffee a` `#ffe9c2` → `--text-header-link`, hover `#fff` (keep)

### 3c. Filter bar
- `.search-wrap input`: border `#d8b483` → `--border-default`; bg `#fffdf8` → `--bg-card` **(D2)**; color `#3a2a1c` → `--text-primary`; shadow `0 2px 6px rgba(90,58,36,.08)` → `--shadow-input`; size `1rem` → `--text-rg`; padding → `--padding-input`
- placeholder `#b89a78` → `--text-placeholder`
- `:focus` ring → `border-color: var(--border-focus)`, `box-shadow: var(--focus-ring)` *(already terracotta; switch to tokens)*
- `#dropdown`: bg `#fffdf8` → `--bg-dropdown`; border `#d8b483` → `--border-default`; radius `16px` → `--radius-lg`; shadow → `--shadow-dropdown`
- `.dd-item` border-bottom `#e8dcc8` → `--border-default`; span `#8a6a4a` → `--text-muted`; hover/active `#f0e8d8` → `--bg-surface`
- `#mobile-sort, .detail-mobile-sort`: border `#d8b483` → `--border-default`; bg `#fffdf8` → `--bg-card`; color `#5a3a24` → `--text-strong`
- `.chip` — **already terracotta**; for full consistency switch hardcoded hexes to tokens and set bg `#fffdf8` → `--bg-chip` (`#ffffff`, **D2**), border `--border-default`, text `--text-soft`, active `--bg-chip-active`/`--accent`, hover `--accent`
- `#status` `#7a4a1a` → `--text-link`; `#meta` `#8a6a4a` → `--text-muted`

### 3d. Desktop table
- `table` bg `#fffdf8` → `--bg-card` **(D2)**; radius `16px` → `--radius-lg`; shadow `0 4px 14px rgba(90,58,36,.12)` → `--shadow-card`
- `thead` bg `#5a3a24` → `--bg-header` **(D1)**; color `#f5e8c8` → `--text-header`
- `thead th` size `.8rem` → `--text-sm`; letter-spacing `.06em` → `--tracking-wider`; padding `.75rem 1rem` (keep or → `--padding-cell`)
- `tbody tr:nth-child(even)` `#f6eedd` → `--bg-row-alt` **(D3)**
- `tbody tr:hover` — already `#fdf0eb`; → `--bg-row-hover`
- `tbody td` padding `.65rem 1rem` → `--padding-cell`; size `.9rem` → `--text-md`
- `.col-name` color `#7a4a1a` → `--text-link`
- `.col-meta` `#8a6a4a` → `--text-muted`, size `.78rem` → `--text-sm`

### 3e. Pagination — already terracotta; tokenize
- inactive border `#e5d5be` → `--border-default`; text `#7a5a3c` → `--text-soft`; bg `#fffdf8` → `--bg-card` (**D2**); hover/active `#d45d35` → `--accent`; `.page-ellipsis` `#b89a78` → `--text-faint`; `.page-info` `#8a6a4a` → `--text-muted`

### 3f. Mobile cards (`@media max-width:600px`)
- `tbody tr` bg `#fffdf8` → `--bg-card` **(D2)**; radius → `--radius-lg`; shadow `0 2px 8px rgba(90,58,36,.1)` → `--shadow-mobile-card`
- `:nth-child(even)` `#fffdf8` → `--bg-card`; `:hover` `#fdf0eb` → `--bg-row-hover`
- separators `#efe4d0` (col-source, col-name, col-updated borders) → `--border-default`
- `.col-name` color `#7a4a1a` → `--text-link`
- meta `#6b5640` → `--text-muted`; label `::before` `#a07d57` → `--text-label`
- `.col-price` `#2c2015` → `--text-primary`
- history-card bg `#f3ece0` → `--bg-surface`; radius `10px` → `--radius-md`; td color `#3a2a1c` → `--text-primary`; label `#a07d57` → `--text-label`; `.price` `#2c2015` → `--text-primary`

### 3g. Badges, detail view, chart, footer
- `.tin-badge` — already `#d45d35`; → `--text-accent`
- `.history-table td.price` `#3b2408` → `--text-primary`; `.listing-name` `#9b7b5a` → `--text-faint`
- `.back-btn` — already terracotta; base → `--accent`, hover → `--accent-hover`
- `.detail-card` bg `#fffdf8` → `--bg-card` **(D2)**; radius `18px` → `--radius-xl`; padding `1.6rem 1.85rem` → `--padding-card`; shadow `0 4px 16px rgba(90,58,36,.14)` → `--shadow-card-lg`
- `.detail-name` `#3b2408` → `--text-primary`; size `1.2rem` → `--text-xl`
- `.detail-meta` size `.9rem` → `--text-md`; `.lbl` `#8a6a4a` → `--text-muted`, `.05em` → `--tracking-wider`; `.val` `#2c2015` → `--text-primary`; `a` `#7a4a1a` → `--text-link`
- `.detail-price` `1.4rem` → `--text-2xl`, `#2c2015` → `--text-primary`
- `.detail-section-title` `.78rem` → `--text-sm`, `.07em` → `--tracking-widest`, `#8a6a4a` → `--text-muted`, border `#e8dcc8` → `--border-default`
- `.history-table` radius `6px` → `--radius-sm`; `thead` bg `#5c3510` → `--bg-header` **(D1)**; td/th size `.85rem` → `--text-sm`
- `.ppo-chart-section` border `#e8dcc8` → `--border-default`; `.ppo-chart-label` `#8a6a4a` → `--text-muted`, `.07em` → `--tracking-widest`
- `.ppo-tooltip` bg `#3a2a1c` → `--bg-tooltip` **(D1)**; color `#f5e8c8` → `--text-tooltip`; radius `10px` → `--radius-md`; shadow → `--shadow-tooltip`; `::after` border-top-color `#3a2a1c` → `--bg-tooltip`
- `.ppo-tt-row` `#d4a97a` → `--text-header-sub` (or leave; it's tooltip sub-text)
- `.detail-empty` `#8a6a4a` → `--text-muted`
- `footer` color `#9b7b5a` → `--text-faint`; `.footer-motif svg` `#c9a06f` → keep (decorative)
- `.easter-egg-row` `#4a8c5c` — **leave** (decorative LOTR)
- chart pink `#FF69AF` — **leave**

---

## 4. `admin.html` migration map

### 4a. Foundations & header (mirror index)
- `theme-color` `#5a3a24` → `#1a0e06` **(D1)**
- `body` bg/grid/color/font → page tokens (same as index 3a)
- Young-serif rule (`h1, .card h2, .stat-big`) → `--font-display`
- `header` bg `#5a3a24` → `--bg-header` **(D1)**; color → `--text-header`; padding → `--padding-header`; shadow → `--shadow-header`
- `header h1` `1.7rem`/`.03em` → `--text-3xl`/`--tracking-wide`
- `header p` `#e6c79c` → `--text-header-sub`, `.85rem` → `--text-md`
- `a.back` `#ffe9c2` → `--text-header-link`

### 4b. Toolbar & refresh button
- `#updated` `#8a6a4a` → `--text-muted`
- `button.refresh`: border `#d8b483` → `--border-default`; bg `#fffdf8` → `--bg-card` **(D2)**; color `#9b7b5a` → `--text-soft`; hover `#cf8a73`/`#b06a50` → `--accent` (both)  ← **still old rose, must change**

### 4c. Cards
- `.card` bg `#fffdf8` → `--bg-card` **(D2)**; border `#ecdcc0` → `--border-card`; radius `16px` → `--radius-lg`; padding `1.2rem 1.3rem` → `--padding-card-sm`; shadow `0 4px 14px rgba(90,58,36,.10)` → `--shadow-card`
- `.card h2` `1.15rem` → `--text-lg`; color `#5a3a24` → `--text-strong`
- `.card .sub` `.72rem` → `--text-xs`; `#b89a78` → `--text-faint`
- `.stat-big` `2.5rem` → `--text-hero`; `#3a2a1c` → `--text-primary`
- `.stat-label` `.74rem` → `--text-sm`; `#8a6a4a` → `--text-muted`; `.05em` → `--tracking-wider`

### 4d. Added pills, rows, status
- `.added.zero` bg `#f0e8d8` → `--border-card` (`#f2eae0`); color `#9b7b5a` → `--text-soft`
- `.added.some` bg `#d9ead0` → `--bg-positive`; color `#3f6b2e` → `--text-positive`
- `.rows` / `.hist-detail` borders `#efe4d0` → `--border-default`
- `.row .k` `#8a6a4a` → `--text-muted`; `.v` `#3a2a1c` → `--text-primary`; `.v.rel` `#b89a78` → `--text-faint`

### 4e. Error card (OPEN — see §2)
- `.card.error` border `#e0b4a4` and `.error .stat-big` `#b06a50`: **leave as-is** by default, or remap stat to `--accent-dark`. No token exists. Confirm with user.

### 4f. Scrape history
- `details.history` border `#efe4d0` → `--border-default`; `summary` `#9b7b5a` → `--text-soft`
- `summary::before` `#cf8a73` → `--accent`  ← **old rose**
- `.hist-row` border `#f2e8d6` → `--border-card`; hover `#faf4e8` → `--bg-surface`
- `.hist-row:focus-visible` outline `#cf8a73` → `--border-focus`; radius `4px` → `--radius-xs`  ← **old rose**
- `.hist-row .when` `#5a3a24` → `--text-strong`
- `.hist-row .chev` `#cf8a73` → `--accent`  ← **old rose**
- `.hist-meta` `#b89a78` → `--text-faint`
- `.hist-row .cnt` `#3f6b2e` → `--text-positive`; `.cnt.zeroadd` `#b89a78` → `--text-faint`
- `.hist-prod a` `#5a3a24` → `--text-strong`; `.pp` `#3f6b2e` → `--text-positive`
- `.hist-prod-empty`, `.hist-empty`, `.hist-note` `#b89a78` → `--text-faint`

---

## 5. Recommended implementation order

1. Create `docs/tokens.css` (§1) and `<link>` it in both files.
2. **Foundations first** (body, header, theme-color) on `index.html` — this exposes D1/D2/D3 immediately. Render and get a visual gut-check before going further.
3. Filter bar → table → pagination → mobile cards → detail view → footer.
4. Repeat for `admin.html`.
5. Search both files for leftover literals — should be **zero** of: `#5a3a24 #f7f1e5 #fffdf8 #3a2a1c #d8b483 #8a6a4a #9b7b5a #7a4a1a #f6eedd #e8dcc8 #cf8a73 #b06a50 #2c2015 #3b2408 #efe4d0 #b89a78` (allow-list: chart `#FF69AF`, easter-egg `#4a8c5c`, footer-motif `#c9a06f`, error reds if kept).

## 6. Verification (per `verify` workflow)
- Serve `docs/` (a `tintracker` config exists in `.claude/launch.json`, port 8789; if taken, add a temp config on another port and remove it after — leave `launch.json` clean).
- `preview_inspect` (not screenshots) to confirm computed colors equal the token hexes on: header, thead, a card, an even row, a chip, the detail card, a tooltip.
- Check both desktop and `preview_resize` mobile (cards), and the detail view (open a tin) + admin page.

## 7. Guardrails (from CLAUDE.md)
- This touches ~120 CSS declarations across 2 files — within scope, but **do not `git push`** without explicit confirmation; ask after committing.
- No changes to JSON data, scrape logic, or canonical/alias files. CSS/markup only.
