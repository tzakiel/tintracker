"""SEO page generator — static, crawlable pages derived from canonical.json.

NON-DESTRUCTIVE OVERLAY: reads docs/canonical.json (read-only) and writes
  docs/tin/<slug>.html   one lightweight static page per canonical tin
  docs/tin/index.html    A-Z index linking every tin page (crawl path)
  docs/sitemap.xml       homepage + tin index + every tin page

Deleting docs/tin/ and docs/sitemap.xml fully reverts the feature.

Runs automatically at the end of consolidate.py, so the pages track
canonical.json through every scrape and every unmatched-processing pass:
new tins gain pages, renamed tins keep their URL (the slug comes from the
stable canonical id, never the display name), and tins that vanish from
canonical.json have their pages deleted.

Churn control: files are only written when their content actually changed,
and no generation timestamps are embedded in pages, so a scrape that changes
nothing produces zero diff here. Sitemap <lastmod> comes from real content
events (a listing appearing, or a price change) — not from run time.
"""
import html
import json
import os
import re

HERE = os.path.dirname(__file__)
DOCS = os.path.join(HERE, "docs")
CANONICAL_FILE = os.path.join(DOCS, "canonical.json")
TIN_DIR = os.path.join(DOCS, "tin")
SITEMAP_FILE = os.path.join(DOCS, "sitemap.xml")

BASE_URL = "https://tintracker.xyz"

# Cap listing rows per page: enough for unique content, bounded page size.
MAX_ROWS = 100

_SLUG_OK = re.compile(r"^[a-z0-9-]+$")


def tin_slug(tin_id):
    """URL slug from the canonical id ('brand|blend', both already reduced to
    [a-z0-9] by consolidate's _norm). '|' -> '-' preserves the brand/blend
    boundary, so distinct ids can never collide."""
    slug = tin_id.replace("|", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug) or "tin"
    return slug


def _money(s):
    m = re.search(r"[\d,]+(?:\.\d+)?", s or "")
    return float(m.group(0).replace(",", "")) if m else None


def _date_only(iso):
    return (iso or "")[:10]


def _members(tin):
    for sz in tin.get("sizes", []):
        for m in sz.get("members", []):
            yield sz.get("quantity", ""), m


def _lastmod(tin):
    """Date of the last content-affecting event: a listing first appearing or
    a recorded price change. Deliberately NOT last_updated, which advances on
    every scrape even when nothing changed."""
    dates = []
    for _, m in _members(tin):
        if m.get("first_seen"):
            dates.append(m["first_seen"])
        for h in m.get("price_history", []):
            if h.get("date"):
                dates.append(h["date"])
    return _date_only(max(dates)) if dates else ""


def _esc(s):
    return html.escape(str(s or ""), quote=True)


def _fmt_usd(v):
    return f"${v:,.2f}"


def _page_head(title, description, canonical, extra=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{_esc(title)}</title>
<meta name="description" content="{_esc(description)}" />
<link rel="canonical" href="{_esc(canonical)}" />
<link rel="icon" type="image/png" href="/favicon.png" />
<meta name="theme-color" content="#1a0e06" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Tin Tracker" />
<meta property="og:title" content="{_esc(title)}" />
<meta property="og:description" content="{_esc(description)}" />
<meta property="og:url" content="{_esc(canonical)}" />
<meta property="og:image" content="{BASE_URL}/favicon.png" />
<meta name="twitter:card" content="summary" />
<link rel="stylesheet" href="/tokens.css" />
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{-webkit-text-size-adjust:100%;text-size-adjust:100%}}
body{{font-family:var(--font-body,sans-serif);background-color:var(--bg-page,#f5f0e8);background-image:var(--bg-dot-gradient);background-size:var(--bg-dot-size);color:var(--text-primary,#1a0f08);min-height:100vh}}
header{{background:var(--bg-header,#1a0e06);color:var(--text-header,#fdf0e2);padding:1rem 1.5rem;text-align:center;box-shadow:var(--shadow-header)}}
header a{{color:inherit;text-decoration:none;font-family:var(--font-display,serif);font-size:1.4rem;letter-spacing:.03em}}
main{{max-width:900px;margin:1.6rem auto 2.5rem;padding:0 1.5rem}}
h1{{font-family:var(--font-display,serif);font-weight:400;font-size:1.7rem;color:var(--text-strong,#3d2810);margin-bottom:.4rem}}
.meta{{color:var(--text-muted,#7a5a3c);font-size:.9rem;margin-bottom:1.2rem}}
.card{{background:var(--bg-card,#fff);border:1px solid var(--border-card,#f2eae0);border-radius:16px;box-shadow:var(--shadow-card);padding:1.2rem 1.3rem;margin-bottom:1.2rem;overflow-x:auto}}
h2{{font-family:var(--font-display,serif);font-weight:400;font-size:1.1rem;color:var(--text-strong,#3d2810);margin-bottom:.6rem}}
table{{border-collapse:collapse;width:100%;font-size:.85rem}}
th,td{{text-align:left;padding:.5rem .8rem;border-bottom:1px solid var(--border-default,#e5d5be)}}
th{{color:var(--text-label,#a88060);font-weight:600;font-size:.75rem;text-transform:uppercase;letter-spacing:.05em}}
tr:last-child td{{border-bottom:none}}
a{{color:var(--text-link,#5c3820)}}
.cta{{display:inline-block;background:var(--accent,#d45d35);color:#fff;padding:.6rem 1.1rem;border-radius:999px;text-decoration:none;font-weight:600;font-size:.9rem}}
.cta:hover{{background:var(--accent-hover,#b84a22)}}
footer{{text-align:center;color:var(--text-faint,#a88060);font-size:.78rem;padding:1.5rem;margin-top:1rem}}
ul.tin-index{{list-style:none;columns:2;column-gap:2rem}}
ul.tin-index li{{padding:.18rem 0;font-size:.9rem;break-inside:avoid}}
@media(max-width:640px){{ul.tin-index{{columns:1}}}}
</style>
{extra}</head>
<body>
<header><a href="/">Tin Tracker</a></header>
<main>
"""


_PAGE_FOOT = """</main>
<footer>Prices collected automatically from public listings. ALPHA release — expect bugs &amp; inaccuracies.</footer>
</body>
</html>
"""


def render_tin_page(tin):
    slug = tin_slug(tin["id"])
    name = tin.get("display_name") or tin.get("blend") or slug
    brand = tin.get("brand", "")
    blend = tin.get("blend", "")
    years = tin.get("years") or []
    sources = tin.get("sources") or []
    page_url = f"{BASE_URL}/tin/{slug}.html"
    app_url = f"{BASE_URL}/?tin={slug}"

    rows = []
    for qty, m in _members(tin):
        rows.append({
            "year": m.get("year", ""),
            "size": qty,
            "price": m.get("price", ""),
            "price_num": _money(m.get("price")),
            "source": m.get("source", ""),
            "url": m.get("url", ""),
            "first_seen": _date_only(m.get("first_seen")),
        })
    prices = [r["price_num"] for r in rows if r["price_num"] is not None]
    n = len(rows)

    # meta description: name, listing count, price range, sources
    bits = [f"Resale prices for {name} pipe tobacco tins."]
    if n:
        bits.append(f"{n} listing{'s' if n != 1 else ''} tracked")
        if prices:
            lo, hi = min(prices), max(prices)
            bits.append(f"from {_fmt_usd(lo)} to {_fmt_usd(hi)}"
                        if lo != hi else f"at {_fmt_usd(lo)}")
        if years:
            bits.append(f"tin years {years[0]}–{years[-1]}"
                        if len(years) > 1 else f"tin year {years[0]}")
    desc = " ".join(bits[:1]) + (" " + ", ".join(bits[1:]) + "." if bits[1:] else "")
    desc += " Compare current values on Tin Tracker."

    # JSON-LD: Product with aggregate offer + breadcrumb
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Product",
                "name": name,
                "url": page_url,
                "category": "Pipe Tobacco",
                **({"brand": {"@type": "Brand", "name": brand}} if brand else {}),
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Tin Tracker",
                     "item": BASE_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": "All Tins",
                     "item": BASE_URL + "/tin/"},
                    {"@type": "ListItem", "position": 3, "name": name,
                     "item": page_url},
                ],
            },
        ],
    }
    if prices:
        ld["@graph"][0]["offers"] = {
            "@type": "AggregateOffer",
            "priceCurrency": "USD",
            "lowPrice": min(prices),
            "highPrice": max(prices),
            "offerCount": len(prices),
        }
    extra = ('<script type="application/ld+json">'
             + json.dumps(ld, ensure_ascii=False, separators=(",", ":"))
             + "</script>\n")

    title = f"{name} — Pipe Tobacco Tin Prices & Value | Tin Tracker"
    out = [_page_head(title, desc, page_url, extra)]
    out.append(f"<h1>{_esc(name)}</h1>\n")

    meta_bits = []
    if brand:
        meta_bits.append(f"Brand: {_esc(brand)}")
    if blend and blend != name:
        meta_bits.append(f"Blend: {_esc(blend)}")
    if years:
        meta_bits.append("Tin years: " + _esc(", ".join(years)))
    if sources:
        meta_bits.append("Sources: " + _esc(", ".join(sources)))
    if meta_bits:
        out.append(f'<p class="meta">{" · ".join(meta_bits)}</p>\n')

    # per-size price summary
    sizes = tin.get("sizes") or []
    if any(sz.get("members") for sz in sizes):
        out.append('<div class="card">\n<h2>Price summary</h2>\n<table>\n'
                   "<thead><tr><th>Tin size</th><th>Listings</th>"
                   "<th>Low</th><th>High</th></tr></thead>\n<tbody>\n")
        for sz in sizes:
            ms = sz.get("members") or []
            if not ms:
                continue
            ps = [p for p in (_money(m.get("price")) for m in ms) if p is not None]
            lo = _fmt_usd(min(ps)) if ps else "—"
            hi = _fmt_usd(max(ps)) if ps else "—"
            out.append(f"<tr><td>{_esc(sz.get('quantity') or '—')}</td>"
                       f"<td>{len(ms)}</td><td>{lo}</td><td>{hi}</td></tr>\n")
        out.append("</tbody>\n</table>\n</div>\n")

    # listings table (most recent first, capped)
    if rows:
        rows.sort(key=lambda r: r["first_seen"], reverse=True)
        shown = rows[:MAX_ROWS]
        label = (f"Listings (latest {len(shown)} of {n})"
                 if n > len(shown) else "Listings")
        out.append(f'<div class="card">\n<h2>{label}</h2>\n<table>\n'
                   "<thead><tr><th>Year</th><th>Size</th><th>Price</th>"
                   "<th>Source</th><th>Seen</th></tr></thead>\n<tbody>\n")
        for r in shown:
            src = (f'<a href="{_esc(r["url"])}" rel="nofollow noopener">'
                   f'{_esc(r["source"] or "link")}</a>'
                   if r["url"] else _esc(r["source"] or "—"))
            out.append(f"<tr><td>{_esc(r['year'] or '—')}</td>"
                       f"<td>{_esc(r['size'] or '—')}</td>"
                       f"<td>{_esc(r['price'] or '—')}</td>"
                       f"<td>{src}</td><td>{_esc(r['first_seen'] or '—')}</td></tr>\n")
        out.append("</tbody>\n</table>\n</div>\n")

    out.append(f'<p><a class="cta" href="{_esc(app_url)}">'
               "View live prices &amp; charts in Tin Tracker</a></p>\n")
    out.append(f'<p class="meta" style="margin-top:1rem">'
               f'<a href="/tin/">Browse all tracked tins</a></p>\n')
    out.append(_PAGE_FOOT)
    return "".join(out)


def render_index_page(tins):
    title = "All Tracked Pipe Tobacco Tins — Tin Tracker"
    desc = (f"Alphabetical index of all {len(tins)} pipe tobacco tins tracked by "
            "Tin Tracker, with resale prices from Speak-Easy, Tinbids, pipestud, "
            "4noggins and Treasured Smokes.")
    out = [_page_head(title, desc, f"{BASE_URL}/tin/")]
    out.append("<h1>All Tracked Tins</h1>\n")
    out.append(f'<p class="meta">{len(tins)} pipe tobacco tins with resale price '
               f'data. Prefer searching? Use the <a href="/">live tracker</a>.</p>\n')
    out.append('<div class="card">\n<ul class="tin-index">\n')
    for t in sorted(tins, key=lambda t: (t.get("display_name") or "").lower()):
        slug = tin_slug(t["id"])
        out.append(f'<li><a href="/tin/{slug}.html">'
                   f'{_esc(t.get("display_name") or slug)}</a></li>\n')
    out.append("</ul>\n</div>\n")
    out.append(_PAGE_FOOT)
    return "".join(out)


def render_sitemap(tins):
    out = ['<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n']

    def url(loc, lastmod=""):
        e = f"  <url><loc>{_esc(loc)}</loc>"
        if lastmod:
            e += f"<lastmod>{lastmod}</lastmod>"
        return e + "</url>\n"

    site_mod = max((_lastmod(t) for t in tins), default="")
    out.append(url(BASE_URL + "/", site_mod))
    out.append(url(BASE_URL + "/tin/", site_mod))
    for t in sorted(tins, key=lambda t: tin_slug(t["id"])):
        out.append(url(f"{BASE_URL}/tin/{tin_slug(t['id'])}.html", _lastmod(t)))
    out.append("</urlset>\n")
    return "".join(out)


def _write_if_changed(path, content):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            if f.read() == content:
                return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return True


def generate(data=None):
    """Generate all SEO pages + sitemap. `data` is the canonical dict; if
    omitted, docs/canonical.json is read. Returns (written, deleted) counts."""
    if data is None:
        with open(CANONICAL_FILE, encoding="utf-8") as f:
            data = json.load(f)
    tins = [t for t in data.get("tins", []) if not t.get("_easter")]

    os.makedirs(TIN_DIR, exist_ok=True)

    slugs = {}
    for t in tins:
        slug = tin_slug(t["id"])
        if slug in slugs:  # can't happen with well-formed ids; refuse to clobber
            raise ValueError(f"slug collision: {t['id']!r} vs {slugs[slug]!r}")
        slugs[slug] = t["id"]
        assert _SLUG_OK.match(slug), slug

    written = 0
    for t in tins:
        if _write_if_changed(os.path.join(TIN_DIR, tin_slug(t["id"]) + ".html"),
                             render_tin_page(t)):
            written += 1
    if _write_if_changed(os.path.join(TIN_DIR, "index.html"),
                         render_index_page(tins)):
        written += 1
    if _write_if_changed(SITEMAP_FILE, render_sitemap(tins)):
        written += 1

    # remove pages for tins no longer in canonical.json
    keep = {s + ".html" for s in slugs} | {"index.html"}
    deleted = 0
    for fname in os.listdir(TIN_DIR):
        if fname.endswith(".html") and fname not in keep:
            os.remove(os.path.join(TIN_DIR, fname))
            deleted += 1

    print(f"SEO pages: {len(tins)} tins -> {written} file(s) written, "
          f"{deleted} stale page(s) deleted -> docs/tin/, docs/sitemap.xml")
    return written, deleted


if __name__ == "__main__":
    generate()
