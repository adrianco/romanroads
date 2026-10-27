# Digital Britannia v1 — data errata

Issues found while building an independent map viewer from
`digital-britannia_v1.gpkg` (Digital Britannia v1). Offered back to the Roman
Roads Research Association for consideration in a future release. None of these
are judgements on the scholarship — they are data-hygiene notes that would make
the GeoPackage easier to consume programmatically.

- **Reviewer:** built from the published v1.0 GeoPackage.
- **Date:** 2026-10-27.
- **Method:** read every layer with GeoPandas; tabulated category fields;
  parsed the embedded `layer_styles` QGIS styles.

Severity key: 🔴 breaks automated use · 🟠 inconsistent / fragile · 🟡 cosmetic.

---

## Settlement

| # | Sev | Field | Issue | Suggested fix |
|---|-----|-------|-------|---------------|
| S1 | 🔴 | `TYPE` | One record is garbled by a copy/paste duplication: `Military vicus - size uncertaMilitary vicus - size uncertainin` | `Military vicus - size uncertain` |
| S2 | 🟠 | `TYPE` | 3 records have a blank/null type | assign a type or mark explicitly `Unknown` |
| S3 | 🟠 | `TYPE` | **270 of 485** values carry **double spaces** (e.g. `Vicus - large  >9Ha`, `Vicus - medium  4-8Ha`, `Defended vicus - medium  4-8Ha`). They match the style labels, but double spaces are easy to break on edit | single-space consistently |
| S4 | 🟡 | style | The style **value** `Military vicus - size uncertain` has the **label** `Military vicus - defence & size uncertain` — value/label drift | align label to value (or vice-versa) |

## Military Installations

| # | Sev | Field | Issue | Suggested fix |
|---|-----|-------|-------|---------------|
| M1 | 🔴 | `Main site type` | Inconsistent capitalisation: `Legionary Fortress` (1 record) vs `Legionary fortress` (11). Treated as two categories by anything case-sensitive | standardise to one spelling |
| M2 | 🟠 | `Main site type` | Values absent from the categorised style: `Other military site` (1) and `Possible military site` (1). The style defines `Other` and `Possible other`, so these rows fall through to the default symbol | reconcile data values with the style's categories |
| M3 | 🟠 | `Main site type` | 1 record has a null type | assign or mark `Unknown` |
| M4 | 🟡 | style | `Signal station` and `Possible signal station` marker symbols have fill **alpha = 0** (fully transparent). If a renderer relies on fill rather than outline they vanish | set an opaque fill or confirm this is intentional |
| M5 | 🟠 | attrs | The downloads page notes some installation **names are missing**, flagged for v1.1 — confirmed: **7 of 517** records have an empty `Modern Name` | populate in v1.1 as planned |

## Engineered Roman roads

| # | Sev | Field | Issue | Suggested fix |
|---|-----|-------|-------|---------------|
| R1 | 🟠 | `Road number ` | The column name has a **trailing space**. Brittle for code that looks up `Road number` | trim trailing whitespace from the field name |
| R2 | 🟠 | `Segment Confidence` | 2 of 3,572 segments have a **null** confidence (expected 0–3) | assign 0–3, or document null as a fourth state |
| R3 | 🟡 | style | Confidence-0 category label reads `No evidence - Requires invetsigation` — **"invetsigation"** is a typo | `investigation` |
| R4 | 🟠 | `Road number ` | 239 of 533 distinct road numbers (1,211 segments) don't follow the plain Margary `<digits><letters>` form. Some look like deliberate conventions that aren't documented anywhere: the `(x)` suffix (136, e.g. `1cc(x)`), and `none-…` IDs (56, e.g. `none-Lon1`). Others look like real anomalies: uncertainty markers (18, e.g. `220?`, `79aa ???`, `?none?`), several numbers in one field (10, e.g. `1b & 1c`, `142/145`, `80a / 2e`), and inconsistent spellings (e.g. `75 link` / `85b - link` / `85-link`; `855(X)` vs `(x)`) | document the numbering conventions; move uncertainty into a separate field; use one form for "link" roads and one case for `(x)` |

## Layers / structure

| # | Sev | Issue | Suggested fix |
|---|-----|-------|---------------|
| L1 | 🟠 | `Hadrians Wall Turrets` layer is present but **empty** (0 features), yet still carries a stored QGIS style | populate it, or drop the empty layer + style |
| L2 | 🟡 | Field-naming conventions differ across layers: `SITE_NAME` / `ROMAN NAME` (Settlement) vs `Modern Name` / `Roman name (if known)` (Military); mixed case and trailing spaces elsewhere | adopt one naming convention across layers |
| L3 | 🟡 | Downloads page notes milestone **icons may not render** from the GeoPackage | confirm icon/image handling in v1.1 |
| L4 | 🔴 | The string **`NULL` is glued onto the front of real values**, apparently a database-export artefact: road `Main References` (`NULLGraham, A. & Richmond, I.A., 1955…`), military `Link 1` ×2 (`NULLhttps://www.heritagegateway…`, which breaks the link), milestone `link2`. One further road `Main References` value is just the literal text `NULL` | strip the `NULL` prefix; store empty values as real nulls |
| L5 | 🟠 | **592 text values have leading/trailing whitespace**, including 196 that contain links (170 in road `Main References`, 12 in road `Link 1.`; e.g. military `Link 3` = `␣https://www.heritagegateway…`) | trim all text fields |

## Licensing / documentation

| # | Sev | Issue | Suggested fix |
|---|-----|-------|---------------|
| D1 | 🟠 | The downloads page states **CC BY-NC 4.0** in the body but the page header cites **CC BY-NC 2.0 UK: England & Wales** — the two conflict | publish one canonical licence |
| D2 | 🟡 | No single ready-to-use **attribution string** is given; reuse must credit author + contributors + RRRA, but the exact wording is left to the user | provide a copy-paste credit line |

---

## What this viewer did about them

So the viewer could render cleanly, the processing step (`scripts/process.py`)
applied these **non-destructive** normalisations (originals in the GeoPackage
are untouched):

- **S1** garble corrected to `Military vicus - size uncertain`.
- **M1** `Legionary Fortress` → `Legionary fortress`.
- **M2** `Other military site` → `Other`; `Possible military site` → `Possible other`
  (mapped onto the author's own style categories).
- **R1** `Road number ` read as `Road number`.
- **L4** leading `NULL` stripped (`NULLhttps://…` → `https://…`); bare `NULL` → null.
- **L5** whitespace trimmed from every text value. Internal double spaces (S3)
  are kept, because the style categories depend on them.
- **R4** road numbers kept exactly as given.
- Null category values surfaced as `Unknown` rather than dropped.

These are editorial choices for display; see `docs/adr/0003-category-normalisation.md`.
