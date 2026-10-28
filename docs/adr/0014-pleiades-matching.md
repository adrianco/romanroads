# 0014 — Pleiades links matched at build time

**Status:** Accepted (issue #1)

## Context
The first Pleiades links ([0012](0012-optional-extras.md)) were search URLs
built from the Roman name. They mostly failed. The dataset writes names as
inscribed (`DVROVARIA`), Pleiades uses the standard spelling (Durnovaria), and
Pleiades search is exact-word. Even my V→U conversion produced "Durovaria",
which Pleiades doesn't know.

## Decision
`scripts/pleiades.py`, run from `process.py`, matches each Military
Installation and Settlement against the Pleiades open-data dumps
(`pleiades-places` and `pleiades-names`, CC BY 3.0, downloaded to the
gitignored `data/external/pleiades/`):

1. **Candidates:** every Pleiades place within **2 km** (haversine distance
   to its representative point).
2. **Names compared:** each place's title variants (Pleiades marks
   alternatives as `*Vercovicium`, `Londinium/Augusta`, `Durno(no)varia`)
   plus all its entries in the names table. Both sides are normalised the
   same way: accents stripped, lower case, letters only, u/v and i/j merged.
3. **Roman-name score (threshold 80):** the better of the whole-name
   `rapidfuzz` ratio and the best single distinctive word. The word score
   also compares stems with the Latin ending removed. This was needed because:
   - plain ratios missed the major towns, as Pleiades adds prefixes and the
     dataset adds tribal suffixes: `GLEVVM` vs "Col. Glevum", `VENTA BELGARVM`
     vs "Venta", `VIROCONIVM CORNOVIORVM` vs "Viroconium";
   - Itinerary forms differ in case ending: `BOMIVM` vs 'Bomio', `NIDVM` vs
     'Nido'.

   Generic words (`col`, `colonia`, `portus`, `castra`, …) are ignored.
4. **Modern-name score (threshold 90)** for sites with no usable Roman name: a
   token-set ratio between the modern name and the Pleiades title, with
   generic words removed. Without that removal, any two "… Roman fort" titles
   within 2 km would match.
5. **Ranking:**
   - a Roman-name match wins;
   - then the higher score;
   - then a **town or fort** (Pleiades `featureTypes` such as settlement,
     fort-2, fortlet, vicus, hillfort, tower-defensive) over a monument
     within it;
   - then the better whole-name fit;
   - then the nearer place.

   Without the place-type and whole-name keys, the London fort linked to
   "Roman forum of London", Chester to "Roman amphitheater at Deva", and
   Caerwent to "Walls of Caerwent". With them, London links to
   Londinium/Augusta, Chester to Deva, and Caerwent to Venta.

## Outputs
- Features get `_pleiades_uri`, `_pleiades_title`, `_pleiades_basis` and
  `_pleiades_score`. The popup links straight to the place. A
  **modern-name** match is labelled "(matched by modern place name)", because
  it may point to a related feature at the same place, such as Ribchester's
  bath house, rather than the fort itself.
- **`data/pleiades_matches.csv`** (committed): every match, with its score,
  basis, distance and the name variant that matched. If the dumps aren't
  downloaded, the build **reuses this table**, so links survive a rebuild from
  a fresh clone. It's also the file to correct by hand. Rows are keyed on
  layer, modern name and position to 5 dp, since the layers have no shared
  ID; two Settlement records for "Usk (Burrium)" at the same point share a
  key, and both get the same match.
- **`data/unmatched_pleiades.csv`** (committed): the sites for manual review,
  with the nearest candidate and its score. Their popups fall back to a
  Pleiades search for the **modern** name.
- Roman names are **displayed in title case** with the U/V reading, qualifiers
  kept (`possibly FANUM COCIDI (Ravenna)` → "possibly Fanum Cocidi
  (Ravenna)"). The data files keep the dataset's spelling. Search also indexes
  the Pleiades title, so "Durnovaria" finds Dorchester.

## Result (Pleiades dump of 2026-10-28)

| | Roman name | Modern name | Total |
|---|---:|---:|---:|
| Military Installations | 101 | 197 | 298 of 517 |
| Settlement | 118 | 117 | 235 of 482 with geometry |
| **All** | **219** | **314** | **533** |

- **Spot checks:** Durnovaria, Vercovicium, Londinium, Calleva, Viroconium,
  Deva, Isca Silurum, Glevum, Camulodunum, Lindum, Venta (Winchester,
  Caerwent, Caistor), Durovernum, Noviomagus, Ratae, Corinium and Isurium all
  link to the right place, and all four checked URIs resolve.
- **Review list:** 466 sites. 449 of them have no Roman name, and 316 have no
  Pleiades place within 2 km at all. Only 17 have a real Roman name and no
  match. These are genuine gaps or disagreements: Petuaria (Brough) has no
  Pleiades place within 2 km; Malton is `DELGOVICIA` in the dataset but
  Derventio in Pleiades; Spinis, Clausentum and Onna aren't located nearby.
- **Bath** isn't matched. Its settlement record has no Roman name, and "bath"
  is a generic word for matching, so its popup offers a search.

## Consequences
- New build dependency: `rapidfuzz` (in `requirements.txt`).
- Matching is heuristic. The thresholds, generic-word lists and place-type
  list are tuned on this dataset, and `pleiades_matches.csv` is the audit
  trail. The radius stays at 2 km, as specified in the issue, although a
  wider radius for strong Roman-name matches would find Petuaria.
- Camps aren't matched, since the issue scopes this to settlements and
  military sites. Their popups use the modern-name search.
- Adds about 120 KiB to the start-up GeoJSON (4.31 MiB, still under budget).
