# Brand Rules for Speak-Easy Title Classification

This file is the canonical source for brand abbreviations, non-obvious brand facts, pipe signals,
and misassignment guards used when classifying Speak-Easy.Club listings into `blend_cache.json`.

Update this file whenever a new brand rule or correction is learned during a `/process-unmatched` session.

---

## Brand Abbreviations

| Abbreviation | Full brand name |
|---|---|
| SG | Samuel Gawith |
| GH / G&H / G.H. | Gawith, Hoggarth & Co. |
| C&D / CD | Cornell & Diehl |
| GLP / GL Pease | G.L. Pease |
| HH (standalone) | Hearth & Home — BUT "HH [blend]" as a prefix almost always means Mac Baren HH (see Mac Baren HH section) |
| MB / MacB / MacBaren | Mac Baren |
| HU | HU Tobacco (German) |
| DSK | Orlik Dark Strong Kentucky (brand: Orlik) |
| FVF | Samuel Gawith Full Virginia Flake |
| SJF | Samuel Gawith St. James Flake |
| ODF (standalone) | Hearth & Home Old Dark Fired |
| HH ODF / MB ODF | Mac Baren HH Old Dark Fired |
| CRF | Cornell & Diehl Carolina Red Flake |
| Cap Blue / Cap Yellow | Mac Baren, blend = "Capstan Blue" / "Capstan Yellow" (keep full "Capstan [color]" as blend name) |
| KC Flake | Samuel Gawith Kendal Cream Flake |
| BS Flake | Samuel Gawith Brown Sugar Flake |
| WCC / W.C. | Watch City |
| McC | McClelland |
| OGS | Orlik Golden Sliced |
| LTF | Peter Stokkebye Luxury Twist Flake |
| LNF | Peter Stokkebye Luxury Navy Flake |
| SPC PP | Seattle Pipe Club Plum Pudding (see Seattle Pipe Club Brand Separation) |
| GdO Flake | Savinelli Giubileo d'Oro Flake (confidence 0.78) |
| KBV | Ken Byron Ventures |
| NM403 | Newminster No. 403 |
| AJ's VaPer | Hearth & Home AJ's VaPer |
| LGF | Reiner Long Golden Flake (brand: Reiner, blend: Long Golden Flake) |
| MM 965 / MM965 | Dunhill My Mixture No. 965 (canonical blend name; alias exists) |
| PS-84 / No. 84 | Peter Stokkebye Turkish Export |

---

## Mac Baren HH Line

"HH [blend]" as a blend prefix means Mac Baren, not Hearth & Home. This applies to any blend — known or new. Examples: HH Acadian Perique, HH Old Dark Fired, HH Mature Virginia, HH Burley Flake, HH Bold Kentucky, HH Vintage Syrian, HH Rustica, HH Latakia Flake, HH Old Dark Fired Plug Cut — and any future "HH Whatever". Extract brand as "Mac Baren" and keep the full "HH …" as the blend name.

Note: "H&H Anniversary Flake" = Hearth & Home (not Mac Baren). "HH Anniversary Kake" (Kake spelling) = Mac Baren.

---

## Learned Blend Nicknames

| Title shorthand | Brand | Canonical blend name |
|---|---|---|
| "Phantom Cake" | Sutliff | No. 6 Phantom |
| "Annie Kake" | Hearth & Home | Anniversary Cake |
| "Semois" (any) | Tabac Manil | La Brumeuse |
| "Va Slices" without brand | Sutliff | Virginia Slices |
| "Rustica" alone | Mac Baren | HH Rustica (0.65 confidence; could also be SG Rustica Flake) |
| "SPC PP Special Res." | Seattle Pipe Club | Plum Pudding Special Reserve |
| "Oaks original English" | McClelland | 3 Oaks Original Blend |
| "Reiner Golden" | Reiner | Blend No. 71 |
| "GH Best Brown Flake" / "Best Brown" | Gawith, Hoggarth & Co. | Best Brown Flake |

---

## Non-obvious Brands

### Tobacco brands that look like something else

- **Chacom** — French pipe brand that ALSO makes tobacco; blend: "Saint Claude" (50g tin)
- **Savinelli** — primarily pipes but ALSO makes tobacco; blends: "Brunello Flake", anniversary blends. Do NOT mark as pipe when a blend name is present.
- **Missouri Meerschaum** — cob pipe brand that ALSO makes tobacco; blend: "Orchard Mist"
- **Brebbia** — Italian pipe AND tobacco brand; blend: "Balkan (Mixture No. 10)"
- **Per Jensen** — Danish tobacco brand (NOT just pipes); "Port Guardian" etc. are tobacco blends
- **Boswell** — Pennsylvania pipe shop; house blends sold in ~30g bags: "Cherry Smash", "Penn Dutch Treat", "Sweet and Mild", "Christmas Cookie"
- **Warped** — cigar/pipe tobacco brand; "The Haunting" is a pipe tobacco blend

### Small / private-label US brands

- **Cascadia** — tobacco brand; blend: "Campsite" etc.
- **Bufflehead** — tobacco brand; blend: "Bufflehead Decoy"
- **Ravenwood** — US tobacco brand; LOTR-themed blends: "Hobbit's Leaf", "Gates of Argonath", "Frog Morton's Chalet"; also makes "Eleventh Day of Christmas"
- **Emerson Southern Forged** — US small-batch blender (Jim Steffey); blends: "Abercastle", "Aberdeen", "Thomas' Blend"
- **Ken Byron Ventures (KBV)** — US brand; whimsical blend names: "Mr. Christian's…", "Byronic Fragments", "B. Frog's…", "King's Ransom", "Live Wire", "VEO", "Dungeon Meister", "Full Metal Balkanist", "Myrkwood", "Notorious", "River of Deceit", "Verge Engine Overdrive"; "Hellstar" series = KBV. NOT Kohlhase, Kopp & Voss.
- **Mike & Russ** — collaborative blenders; blend: "The Mind Meld Virginia/Perique"
- **Rivertown Tobacco Works** — US bulk/house blend brand; blends: "Crimson Shadow", "Mystic Moor"
- **Two Friends** — collaboration brand (C&D + GLP founders); blend: "Redwood"
- **Low Country** — retail brand blended by Cornell & Diehl; blends: "Waccamaw", "Santee", "Cooper"
- **PCCA** — Pipe Collector's Club of America; blend: "Full Balkan Reserve" (mfg by McClelland); discontinued/collectible
- **Synjeco** — tobacco brand; blends: "Bad Nun", "Bad Nun II"
- **Ole Shenandoah** — tobacco brand; blend: "Appalachian Berry"
- **Cult** — tobacco brand; blend: "Abacus"
- **Strauss** — tobacco brand; blend: "Sleepy Hollow"
- **Whitehall** — brand and blend name are identical ("Whitehall")
- **Briarshire** — small-batch brand (blended by Ravenwood Fine Provisions, sold via TinBids / pipe shows); blend: "Benedictine Abbey"

### Shop house blends

- **Watch City** — blends: "Rouxgaroux", "Simply Red", "Old Black Magic", "Strange Magic", "Deluxe Crumb Cut", "Rhythm and Blues", "Mistletoe Jam", "Old Dominion", "Bostonian Rhapsody", "Flake #558"
- **Country Squire** — Mississippi pipe shop; house blends: "Old Toby", "Faulkner Flake"
- **Seattle Pipe Club** — also makes: "Plum Pudding Special Reserve". Classify SPC listings with brand `Seattle Pipe Club` and the plain blend name (no "SPC " prefix). `consolidate.py` handles the manufacturer split and adds the prefix — see Seattle Pipe Club Brand Separation below.
- **L.J. Peretti** — Boston tobacconist; house blends include "Thanksgiving Day"
- **Robert Lewis** — London tobacconist; blend: "Tree Mixture"
- **F & K** — St. Louis private-label brand (founded 1926); blend: "Lancer Slices"
- **SHPC** — Sherlock Holmes Pipe Club (of Boston); club blend "Great Hiatus" (English mixture, made by Pipes & Cigars / Russ Ouellette). Brand = "SHPC" per TobaccoReviews.

### German / European brands

- **Solani** — German brand (Rudiger L. Will); numbered blends: 656 (Aged Burley Flake), 660 (Silver Flake), 663 (Va and Perique → blend name = "663"); named: White & Black, Red Label, Blue Label
- **Reiner** — German brand (Rudiger L. Will); Blend No. 71 = Long Golden Flake; Blend No. 25 = aromatic
- **John Aylesbury** — German collective; blends: Sir John's Flake Virginia, Classic Flake, Dragon Flake
- **HU Tobacco** — German brand; blends: "Flanagan", "Aus den Krater" series. NOT Hermit Umbra.
- **Peter Heinrichs** — German brand; blend: "Curly Block" (confirmed NOT Wessex)
- **Troost** — Dutch tobacco brand; blend: "Aromatic Cavendish"
- **Arango** — importer/distributor; "Balkan Supreme" = Arango Balkan Supreme
- **Bengal Slices** — brand = "Sutliff", blend = "Bengal Slices"; blended by Sutliff (NOT a standalone brand, NOT Sobranie/Standard Tobacco Co.)

### Specific brand notes

- **Cornell & Diehl** — also makes: "From Beyond", "Palmetto Balkan", "Pirate Kake", "Corn Cob Pipe and a Button Nose", "Epiphany", "Golden Days of Yore", "Joie de Vivre", "Bow Legged Bear", "Bijou", "Tom Eltang Virginia", "Eight State Burley", "Speakeasy Navy Blend", "Two Friends English Chocolate". **Oak Alley is C&D, NOT G.L. Pease.**
- **G.L. Pease** — also makes: "Caravan", "JackKnife Plug", "Lagonda", "Odyssey", "Robusto", "Quiet Nights", "25th Anniversary", "Ashbury", "Union Square", "Triple Play", "Sixpence", "Embarcadero", "Fillmore", "Temple Bar", "Key Largo", "Cumberland", "Abingdon", "Westminster", "Star of the East", "Speakeasy", "Charing Cross", "Vieux Carré". **"Tilbury" → Esoterica Tilbury, NOT G.L. Pease.**
- **Hearth & Home** — also makes: "Viprati", "Pure Virginia", "Burley Flake", "Acadian", "RO Acadian English", "RO Acadian VaPer"
- **Mac Baren** — also makes: "HH Anniversary Kake", "Capstan Blue", "Capstan Yellow", "Navy Flake", "Pure Virginia", "Mixture Scottish Blend", "Brunello Flake", "Presbyterian Mixture", "Presbyterian Ordained", "St. Bruno Ready Rubbed", "St. Bruno Flake". Capstan blends: brand = "Mac Baren", blend = "Capstan Blue" or "Capstan Yellow" (full blend name, not just color).
- **Samuel Gawith** — also makes: "Hansom Flake" (correct spelling, not "Hansome"), "Balkan Flake", "Bothy Flake", "Chocolate Flake", "Commonwealth", "Perfection", "Best Brown Flake", "SJ Plug", "Skiff Mixture", "Navy Flake"
- **Gawith, Hoggarth & Co.** — also makes: "Curly Cut Deluxe", "Rum Twist Rope", "Whiskey Rope", "Brown Slice", "Dark Plug", "Grasmere Flake", "Latakie Medium Cut", "Rich Dark Honeydew", "Revor Plug", "Sliced Brown Twist". **"Louisiana Flake" → canonical blend name is "LA Flake"** (GH's own abbreviation); the Burnt Ends variant = **"LA Flake Burnt Ends"** (not "Louisiana Flake Burnt Ends").
- **McClelland** — also makes: "Navy Cavendish", "No. 27", "2015", "Tudor Castle", "Blackwoods Flake", "St. James Woods", "No. 24 Ribbon", "3 Oaks Original Blend", "3 Oaks Syrian", "Stave Aged", "Tawny Flake", "Virginia Woods", "Dominican Glory", "Christmas Cheer", "Dark Star", "Beacon Extra", "Balkan Blue". brand=McClelland for all "3 Oaks" variants; do NOT use "3 Oaks" as the brand. "3 Oaks English Blend" is NOT a separate blend — it's the same product as "3 Oaks Original Blend" (McClelland's Grand Orientals-adjacent English-style Virginia/Latakia blend); always normalize to "3 Oaks Original Blend". "Blue Mountain" (2011-era name, later renamed "Balkan Blue") is kept as its OWN blend entry, separate from "Balkan Blue" — do not merge (user confirmed 2026-07-04). "UPCA Traveler" → blend "Traveler" (UPCA club series).
- **McClelland bulk numbers** — bulk blends are titled by number (often "#2010", "#5100"); expand to the full canonical name: **2010 → "2010 Classic Virginia"**, **5100 → "5100 Red Cake"** (alias "5100" exists). Also makes **"Grey Havens"** (Craftsbury Collection; Virginia/white Burley/Perique — a real McClelland blend despite the Tolkien name, NOT Ravenwood).
- **Bell's** — vintage brand for **Three Nuns** (created 1890s by J & F Bell, Glasgow; later Imperial/Ogden's). Kept as its OWN brand entry, separate from **Mac Baren | Three Nuns** (Mac Baren has made it since the 2013 US reintroduction, with a changed recipe: VaPer → Va + dark-fired Kentucky). A vintage/"BELLS"-titled Three Nuns tin → brand `Bell's`; a modern one → brand `Mac Baren`.
- **Brigham** — Canadian pipe brand that ALSO makes tobacco (blended in Germany); blend: **"Klondike Gold"** (Virginia flake). Do not mark as pipe when a blend name is present.
- **Peter Stokkebye** — numbered PS bulk range; **No. 84 / PS-84 = "Turkish Export"** (Turkish Samsun + Virginia).
- **McCranie's** — "RR" = Red Ribbon; "1983 Crop" = Red Flake (1983 crop Virginia)
- **Rattray's** — also makes: "Stirling Flake", "Accountant's Mixture", "40 Virginia", "Black Mallory", "Hal O' The Wynd", "Red Rapparee", "Black Virginia", "Old Gowrie", "Professional Mixture", "Bagpiper's Dream", "Brown Clunee", "Jock's Mixture"
- **Dan Tobacco** (canonical name; "Dan" alone = Dan Tobacco) — also makes: "Devil's Holiday", "Hamborger Veermaster", "Salty Dog", "Dan Milonga", "The Mallard", "Midnight Ride", "Tordenskjold Virginia Slices", "Gordon Pym"
- **Sutliff** — also makes: "Paradoxical" (Birds of a Feather series), "Match Victorian", "Maple Shadows", "Maple Shadows II", "Chocolate Supreme D54", "Anomalous", "Privateer", "No. 6 Phantom", "Cringle Flake", "Eastfarthing", "Sweated", "TS1R", "J4 Burley", "Barrel Aged series", "515 RC-1", "507-C", "701 Crème Brûlée", "707 Sweet Virginia", "Bengal Slices", "War Horse Bar"
- **Erik Stokkebye** — distinct from Peter Stokkebye; "4th Generation" series: bare "4th Generation" = "4th Generation 1931" (default); also "4th Generation 1989", "4th Generation Resolution", "4th Generation Night Slice", "Evening Flake"
- **STG (Scandinavian Tobacco Group)** — makes "Escudo Navy Deluxe" (blend name = "Escudo Navy Deluxe"); bare "Escudo" alone is NOT a valid entry — always expand to "Escudo Navy Deluxe". Also makes "Balkan Sasieni" (blend name = "Balkan Sasieni", NOT "Sasieni Balkan"). Does NOT make Balkan Sobranie. (Granger is a separate standalone brand, not STG.)
- **Erinmore** — brand (STG/Mac Baren); main tin blend = "Flake"; bare "Erinmore" without sub-name = Erinmore Flake
- **Robert McConnell** — makes "Scottish Cake", "Black Flake", "Folded Flake"
- **Ashton** — makes "Artisan's Blend" (English/Syrian Latakia)
- **Drew Estate** — pipe tobacco brand (not just cigars); "Harvest on Hudson", "Heirloom Cherry" are pipe tobacco
- **Captain Black** — aromatic tobacco brand; variants include "Captain Black Grape"
- **Wessex** — UK tobacco brand; blends include "Sovereign Curly Cut". Also a pipe brand shape name; see pipe signals.
- **Astley's** — UK brand; numbered range is No. 1/2/33/44/55/66/88/99/109 (there is NO "No. 9"). Blends: "No. 44 Dark Virginia Flake", "No. 88 Matured Dark Virginia", "No. 109 Medium Virginia Flake", "No. 99 Royal Tudor". A seller "No.9 Medium Flake" is a truncation of **No. 109 Medium Virginia Flake** (blend_alias added).
- **Tabac Manil** — Belgian brand; "Semois" titles = Tabac Manil La Brumeuse
- **Newminster** — brand for "No. 403 Superior Round Slices"
- **Butera** — tobacco brand; blends: "Dark Stoved", "Pelican"
- **Russ Ouellette** — brand; blend: "Acadian Gold"
- **Cobblestone** — brand; "High Spirits" spirits-themed aromatics → blend name = flavor only, e.g. "Spiced Rum", "Plum Rum"
- **GBD** — better known as a pipe maker, but also sold vintage pipe tobacco tins; blends: "Original Mixture", "Black Cavendish Mixture". A GBD *tobacco tin* is is_tin: true (distinct from GBD pipes → see pipe signals)
- **GH / Gawith Hoggarth** — same as Gawith, Hoggarth & Co.; canonical form: "Gawith, Hoggarth & Co."
- **St. Bruno disambiguation** — "St. Bruno Ready Rubbed" and "St. Bruno Flake" → brand: "Mac Baren"; "Ogden St. Bruno" (or "St. Bruno" without further qualifier in Ogden's context) → brand: "Ogden's", blend: "St. Bruno"
- **Samuel Gawith blend names** — strip weights/sizes from blend names; e.g. "Full Virginia Flake 50g" → blend: "Full Virginia Flake" (not "Full Virginia Flake 50g")

---

## Common Misassignments to Avoid

- **Balkan Sobranie** → brand: "J.F. Germain" (NOT STG); "Germain's" = same brand, normalize to "J.F. Germain"
- **Dunbar** → brand: "Esoterica" (NOT Gawith Hoggarth)
- **Tilbury** → brand: "Esoterica", blend: "Tilbury" (NOT G.L. Pease)
- **Oak Alley** → Cornell & Diehl (NOT G.L. Pease)
- **Dunhill Shell** → is_tin: false (pipe line); "Dunhill Shell [shape]" is always a pipe, not tobacco
- **Dunhill Elizabethan** → brand: "Dunhill", blend: "Elizabethan Mixture" (same blend, two title forms)
- **Comoy's #4 / #7** (bare, no weight) → is_tin: false (pipe shapes); "Comoy's #4 3.5oz" or "Cask No.4" → is_tin: true (tobacco)
- **Dunhill BB** → "Baby's Bottom" blend (NOT an abbreviation for another blend). "BB1938" = Baby's Bottom 1938.
- **Castello Sea Rock / Old Antiquari / Perla Nera** → is_tin: false (pipe lines)
- **Danish Sovereign 341** → is_tin: false (pipe)
- **Davidoff Medallion** → is_tin: false (pipe); Davidoff Green Mixture = tobacco
- **HU** → HU Tobacco (German brand), NOT Hermit Umbra
- **"Rainer Levant" / "Rainier Levant"** → brand: "Seattle Pipe Club", blend: "Rainier Levant" (**NOT Reiner** — Reiner makes no Levant blend). SPC's tribute to Drucquer & Sons' Levant Mixture; named for Mt. Rainier. Sellers frequently misspell it "Rainer", which looks like the German brand Reiner. Canonical: `Sutliff | SPC Rainier Levant` (consolidate.py applies the SPC year split).
- **"Escudo" bare** → always expand to brand: "STG", blend: "Escudo Navy Deluxe"; never leave as just "Escudo"
- **"Paradoxical"** → always brand: "Sutliff", blend: "Paradoxical" — including titles that say "Birds of a Feather", "Bird Blends", or "Per Jensen"/"Per Georg Jensen" (that's the series/designer name, not the brand; Sutliff manufactures and sells it). NOT Cornell & Diehl, NOT "Per Jensen" as brand (user confirmed 2026-07-01, reversing an earlier attempt to split it into two brands).

---

## Seattle Pipe Club Brand Separation

Seattle Pipe Club does not blend its own tobacco — it contracts a manufacturer, and
that manufacturer changed. SPC tins are split into two brands by **tin year**
(user confirmed 2026-07-05):

- **Sutliff** — tins from **2024 and earlier**.
- **Cornell & Diehl** — tins from **2025 and later**.
- **Unknown year** → default to **Sutliff** for now; going forward rely on context or
  the tin year.
- If a listing explicitly names one of these two manufacturers (e.g. "SPC Plum Pudding
  (Sutliff)", "Cornell & Diehl … Mississippi River"), that stated brand wins over the
  year rule.

The blend keeps an **`SPC ` prefix** so its origin stays visible: brand `Sutliff`, blend
`SPC Plum Pudding` → display "Sutliff SPC Plum Pudding". Every SPC blend gets the prefix
(SPC Plum Pudding, SPC Mississippi River, SPC Potlatch, …).

**Where this is applied:** `consolidate.py` performs the split deterministically using the
per-listing parsed year. When classifying into `blend_cache.json` / `overrides.json`, keep
`brand: "Seattle Pipe Club"` and the plain blend name (no prefix) — do NOT pre-split or
pre-prefix in the cache; consolidate does it.

---

## Blend Naming Rules

- Strip the brand prefix from the blend name: brand=`Cornell & Diehl`, blend=`Bayou Morning` (NOT "C&D Bayou Morning")
- Strip brand prefix from Dunhill blends: brand=`Dunhill`, blend=`Nightcap` (NOT "Dunhill Nightcap")
- Capstan: brand=`Mac Baren`, blend=`Capstan Yellow` or `Capstan Blue` (keep full "Capstan [color]" as blend name; brand is Mac Baren)
- Date/year variants are the same blend: "Carolina Red Flake 09/21/2019" → blend=`Carolina Red Flake` (strip dates)
- Strip weights from all Samuel Gawith blend names: "Full Virginia Flake 50g" → blend=`Full Virginia Flake`; applies to any SG entry with a trailing weight (50g, 250g, 4oz, etc.)
- "Crumble Kake" is a Sutliff blend (all variants)

### Exact canonical casing/naming (do NOT create variants — these have bitten before)

| Seller title form | Canonical blend |
|---|---|
| "Jack Knife Plug" / "JackKnife Plug" | G.L. Pease **Jackknife Plug** (distinct from "Jack Knife Ready Rubbed") |
| "Frog Morton On the Town" | McClelland **Frog Morton on the Town** (lowercase "on") |
| "My Mixture 965" / "MM 965" | Dunhill **My Mixture No. 965** |
| "Grand Oriental …" (singular) | McClelland **Grand Orientals …** (plural; aliases exist) |

Always grep `canonical.json` for the blend before declaring it new — case-only and
punctuation-only differences are the same blend and must map to the existing entry.

---

## Pipe Signals → is_tin: false

If a pipe brand name appears **and** any of these descriptors are present, mark is_tin: false.

**Pipe brands:** Castello, Comoy's, Savinelli (without blend name), Peterson (with shape # e.g. X220), Ben Wade, Cavicchi, Alpha, BBB (Best British Briar), Kaywoodie, Davidoff Medallion, Ser Jacopo, Il Ceppo, Radice, Ascorti, Ardor, Nørding, Stanwell, Vauen, Ropp, Paronelli, Rattray (pipe maker, not the tobacco brand Rattray's), Morta pipes, Eldritch pipes, Kriswill, Tinsky, Steve Morrisette, Wayne Teipen, Nate Rose

**Shape names:** billiard, dublin, poker, bulldog, lovat, apple, cherrywood, calabash, oom paul, rhodesian, hawkbill, bamboo cutty, freehand, bent, straight, canadien, cutty

**Condition / construction words:** unsmoked, NIB (new in box), smoked once/twice, sandblasted, rusticated, smooth finish, natural finish

**Measurements:** "chamber diameter", "chamber depth", "bowl height", "9mm filter", "P-Lip", "spigot", "push tenon", "non-plip"

**Exception:** Savinelli makes tobacco (e.g. "Brunello Flake", anniversary blends) — if a blend name follows, is_tin: true.

---

## Multi-pack / Lot Signals → is_tin: false

- "x2", "x3", "x4" etc. in title
- "lot of N", "pack of N", "bundle", "set of N"
- "SOLD" prefix → always is_tin: false (sold listing fragment, not a product title)
- "several tins", "multiple", "variety pack", "sampler", "assortment"
- Chewing tobacco brands (Stokers, Levi Garrett, etc.) → is_tin: false

---

## Additional Known Tobacco Brands

These are confirmed tobacco brands not yet heavily represented in the cache. When a listing title contains one of these names, treat it as is_tin: true (unless other signals override) and assign the brand accordingly.

| Brand | Notes |
|---|---|
| Barclay-Rex | NYC tobacconist; house blends |
| Bond Street | classic aromatic blend (various manufacturers over time) |
| Borkum Riff | Swedish Match aromatic brand |
| Carter Hall | Standard Commercial Corp; American Burley aromatic |
| Casey Jones | budget American aromatic line (pouches/cans); blends include "Beyond Brave" (user confirmed 2026-07-04) |
| Clan | Swedish Match; aromatic blend |
| Condor | classic UK ready-rubbed |
| Daughters & Ryan | US retailer/blender |
| Drexel | vintage US brand |
| Edward G. Robinson | vintage US aromatic blend |
| Field & Stream | vintage US brand |
| Five Brothers | vintage US Burley; sold in pouches |
| Former's | vintage US brand |
| George Washington | vintage US Burley |
| Gladora | vintage brand |
| Gold Block | classic UK ready-rubbed (Ogden's/BAT) |
| Granger | American Burley aromatic; standalone brand (not an STG blend) |
| Hampton House | US house-blend brand |
| Holger Danske | Danish brand |
| House of Windsor | US aromatic brand |
| James J. Fox | London tobacconist; house blends |
| Kentucky Club | vintage US Burley aromatic |
| Kohlhase & Kopp | German brand; distinct from Ken Byron Ventures |
| Niall of Nine | Irish/Celtic-themed brand |
| Ogden's | UK brand (BAT); "Gold Block" is an Ogden's blend |
| Paladin | vintage US Black Cherry aromatic |
| Pipeworks & Wilke | Chicago tobacconist; house blends |
| Poschl Tabak | German brand |
| Poul Winslow | Danish brand |
| Sail | Dutch aromatic brand (various blends) |
| Scotty's | US house-blend tobacconist |
| Sir Walter Raleigh | vintage US aromatic (Brown & Williamson) |
| Smoker's Pride | US value aromatic brand |
| Sullivan Powell | London tobacconist; house blends |
| Super Value | US value brand |
| Svendborg | Danish brand |
| Tinder Box | US retail chain; house blends |
| Union Leader | vintage US Burley |
| Who Dat Pipe Works | New Orleans-area tobacconist; house blends |
| Wills | UK brand (Imperial Tobacco); "Wills's Whiffs" etc. |

---

## How to Apply

1. Check abbreviation table first
2. If brand name is a known pipe maker AND title has shape/condition signals → is_tin: false
3. "x2", "x3" etc. in title → is_tin: false
4. Strip leading brand prefixes (C&D, SG, GH, etc.) and trailing dates/weights from blend name
5. When uncertain, web search: `"<blend name>" pipe tobacco` on tobaccoreviews.com or smokingpipes.com
