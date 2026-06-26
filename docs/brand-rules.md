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
| Cap Blue / Cap Yellow | Capstan, blend = Blue / Yellow (blend is just the color) |
| KC Flake | Samuel Gawith Kendal Cream Flake |
| BS Flake | Samuel Gawith Brown Sugar Flake |
| WCC / W.C. | Watch City Cigars |
| McC | McClelland |
| OGS | Orlik Golden Sliced |
| LTF | Peter Stokkebye Luxury Twist Flake |
| LNF | Peter Stokkebye Luxury Navy Flake |
| SPC PP | Seattle Pipe Club Plum Pudding |
| GdO Flake | Savinelli Giubileo d'Oro Flake (confidence 0.78) |
| KBV | Ken Byron Ventures |
| NM403 | Newminster No. 403 |
| AJ's VaPer | Hearth & Home AJ's VaPer |
| LGF | uncertain — ask if seen again |

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
| "Oaks original English" | McClelland | 3 Oaks Original |
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
- **Ravenwood Fine Provisions** — US tobacco brand; LOTR-themed blends: "Hobbit's Leaf", "Gates of Argonath", "Frog Morton's Chalet"; separate from "Ravenwood" (blend: "Eleventh Day of Christmas")
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

### Shop house blends

- **Watch City Cigars** — blends: "Rouxgaroux", "Simply Red", "Old Black Magic", "Strange Magic", "Deluxe Crumb Cut", "Rhythm and Blues", "Mistletoe Jam", "Old Dominion", "Bostonian Rhapsody", "Flake #558"
- **Country Squire / The Country Squire Tobacconist** — Mississippi pipe shop; house blends: "Old Toby", "Faulkner Flake"
- **Seattle Pipe Club** — also makes: "Plum Pudding Special Reserve"
- **L.J. Peretti** — Boston tobacconist; house blends include "Thanksgiving Day"
- **Robert Lewis** — London tobacconist; blend: "Tree Mixture"
- **F & K** — St. Louis private-label brand (founded 1926); blend: "Lancer Slices"

### German / European brands

- **Solani** — German brand (Rudiger L. Will); numbered blends: 656 (Aged Burley Flake), 660 (Silver Flake); named: White & Black, Red Label, Blue Label
- **Reiner** — German brand (Rudiger L. Will); Blend No. 71 = Long Golden Flake; Blend No. 25 = aromatic
- **John Aylesbury** — German collective; blends: Sir John's Flake Virginia, Classic Flake, Dragon Flake
- **HU Tobacco** — German brand; blends: "Flanagan", "Aus den Krater" series. NOT Hermit Umbra.
- **Peter Heinrich / Peter Heinrichs** — German brand; blend: "Curly Block" (confirmed NOT Wessex)
- **Troost** — Dutch tobacco brand; blend: "Aromatic Cavendish"
- **Arango** — importer/distributor; "Balkan Supreme" = Arango Balkan Supreme
- **Bengal Slices** — standalone brand name (brand = "Bengal Slices", blend = "Bengal Slices"); originally Sobranie, now Standard Tobacco Co.

### Specific brand notes

- **Cornell & Diehl** — also makes: "From Beyond", "Palmetto Balkan", "Pirate Kake", "Corn Cob Pipe and a Button Nose", "Epiphany", "Golden Days of Yore", "Joie de Vivre", "Bow Legged Bear", "Bijou", "Tom Eltang Virginia", "Eight State Burley", "Speakeasy Navy Blend", "Two Friends English Chocolate". **Oak Alley is C&D, NOT G.L. Pease.**
- **G.L. Pease** — also makes: "Caravan", "JackKnife Plug", "Lagonda", "Odyssey", "Robusto", "Quiet Nights", "25th Anniversary", "Ashbury", "Union Square", "Triple Play", "Sixpence", "Embarcadero", "Fillmore", "Temple Bar", "Key Largo", "Tilbury", "Cumberland", "Abingdon", "Westminster", "Star of the East", "Speakeasy", "Charing Cross", "Vieux Carré"
- **Hearth & Home** — also makes: "Viprati", "Pure Virginia", "Burley Flake", "Acadian", "RO Acadian English", "RO Acadian VaPer"
- **Mac Baren** — also makes: "HH Anniversary Kake", "Capstan Blue", "Capstan Yellow", "Navy Flake", "Pure Virginia", "Mixture Scottish Blend", "Brunello Flake", "Presbyterian Mixture", "Presbyterian Ordained"
- **Samuel Gawith** — also makes: "Hansom Flake" (correct spelling, not "Hansome"), "Balkan Flake", "Bothy Flake", "Chocolate Flake", "Commonwealth", "Perfection", "Best Brown Flake", "SJ Plug", "Skiff Mixture", "Navy Flake"
- **Gawith, Hoggarth & Co.** — also makes: "Curly Cut Deluxe", "Rum Twist Rope", "Whiskey Rope", "Brown Slice", "Dark Plug", "Grasmere Flake", "Latakie Medium Cut", "Rich Dark Honeydew", "Revor Plug", "Sliced Brown Twist"
- **McClelland** — also makes: "Navy Cavendish", "No. 27", "2015", "Tudor Castle", "Blackwoods Flake", "St. James Woods", "No. 24 Ribbon", "3 Oaks Original", "3 Oaks English Blend", "3 Oaks Syrian", "Stave Aged", "Tawny Flake", "Virginia Woods", "Dominican Glory", "Christmas Cheer", "Dark Star", "Beacon Extra", "Balkan Blue". brand=McClelland for all "3 Oaks" variants; do NOT use "3 Oaks" as the brand.
- **McCranie's** — "RR" = Red Ribbon; "1983 Crop" = Red Flake (1983 crop Virginia)
- **Rattray's** — also makes: "Stirling Flake", "Accountant's Mixture", "40 Virginia", "Black Mallory", "Hal O' The Wynd", "Red Rapparee", "Black Virginia", "Old Gowrie", "Professional Mixture", "Bagpiper's Dream", "Brown Clunee", "Jock's Mixture"
- **Dan Tobacco** — also makes: "Devil's Holiday", "Hamborger Veermaster", "Salty Dog", "Dan Milonga", "The Mallard", "Midnight Ride", "Tordenskjold Virginia Slices", "Gordon Pym"
- **Sutliff** — also makes: "Paradoxical" (Birds of a Feather series), "Match Victorian", "Maple Shadows", "Maple Shadows II", "Chocolate Supreme D54", "Anomalous", "Privateer", "No. 6 Phantom", "Cringle Flake", "Eastfarthing", "Sweated", "TS1R", "J4 Burley", "Barrel Aged series", "515 RC-1", "507-C", "701 Crème Brûlée", "707 Sweet Virginia"
- **Erik Stokkebye** — distinct from Peter Stokkebye; "4th Generation" series (1931, 1989, Resolution etc.); also makes "Evening Flake", "4th Generation Night Slice"
- **STG (Scandinavian Tobacco Group)** — makes "Escudo" (Navy De Luxe), "Balkan Sasieni", "Granger" (seller sometimes misspells as "Grainger"). Does NOT make Balkan Sobranie.
- **Erinmore** — brand (STG/Mac Baren); main tin blend = "Flake"; bare "Erinmore" without sub-name = Erinmore Flake
- **Robert McConnell** — makes "Scottish Cake", "Black Flake", "Folded Flake"
- **Ashton** — makes "Artisan's Blend" (English/Syrian Latakia)
- **Drew Estate** — pipe tobacco brand (not just cigars); "Harvest on Hudson", "Heirloom Cherry" are pipe tobacco
- **Captain Black** — aromatic tobacco brand; variants include "Captain Black Grape"
- **Wessex** — UK tobacco brand; blends include "Sovereign Curly Cut". Also a pipe brand shape name; see pipe signals.
- **Astley's** — UK brand; numbered blends: "No. 44 Dark Virginia Flake", "No. 88 Matured Dark Virginia"
- **Tabac Manil** — Belgian brand; "Semois" titles = Tabac Manil La Brumeuse
- **Newminster** — brand for "No. 403 Superior Round Slices"
- **Butera** — tobacco brand; blends: "Dark Stoved", "Pelican"
- **Russ Ouellette** — brand; blend: "Acadian Gold"
- **GH / Gawith Hoggarth** — same as Gawith, Hoggarth & Co.; canonical form: "Gawith, Hoggarth & Co."

---

## Common Misassignments to Avoid

- **Balkan Sobranie** → brand: "J.F. Germain" (NOT STG); "Germain's" = same brand, normalize to "J.F. Germain"
- **Dunbar** → brand: "Esoterica" (NOT Gawith Hoggarth)
- **Oak Alley** → Cornell & Diehl (NOT G.L. Pease)
- **Dunhill Shell/Cumberland + shape number** → is_tin: false (pipe)
- **Comoy's #4 / #7** (bare, no weight) → is_tin: false (pipe shapes); "Comoy's #4 3.5oz" or "Cask No.4" → is_tin: true (tobacco)
- **Dunhill BB** → "Baby's Bottom" blend (NOT an abbreviation for another blend). "BB1938" = Baby's Bottom 1938.
- **Castello Sea Rock / Old Antiquari / Perla Nera** → is_tin: false (pipe lines)
- **Danish Sovereign 341** → is_tin: false (pipe)
- **Davidoff Medallion** → is_tin: false (pipe); Davidoff Green Mixture = tobacco
- **HU** → HU Tobacco (German brand), NOT Hermit Umbra

---

## Blend Naming Rules

- Strip the brand prefix from the blend name: brand=`Cornell & Diehl`, blend=`Bayou Morning` (NOT "C&D Bayou Morning")
- Strip brand prefix from Dunhill blends: brand=`Dunhill`, blend=`Nightcap` (NOT "Dunhill Nightcap")
- Capstan blend is just the color: brand=`Capstan`, blend=`Yellow` (NOT "Capstan Yellow")
- Date/year variants are the same blend: "Carolina Red Flake 09/21/2019" → blend=`Carolina Red Flake` (strip dates)
- "Crumble Kake" format: check Sutliff vs C&D by variant name

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

## How to Apply

1. Check abbreviation table first
2. If brand name is a known pipe maker AND title has shape/condition signals → is_tin: false
3. "x2", "x3" etc. in title → is_tin: false
4. Strip leading brand prefixes (C&D, SG, GH, etc.) and trailing dates/weights from blend name
5. When uncertain, web search: `"<blend name>" pipe tobacco` on tobaccoreviews.com or smokingpipes.com
