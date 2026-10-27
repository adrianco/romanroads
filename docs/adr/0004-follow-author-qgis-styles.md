# 0004 — Symbology follows the author's QGIS styles

**Status:** Accepted

## Context
The GeoPackage's `layer_styles` table holds the author's default QGIS style for
each layer. The brief says to follow its categories and labels.

## Decision
I parsed the QML `renderer-v2` categories and symbol colours and used them
directly:

- **Roads** (`Segment Confidence`), all `#9d0014`: 3 solid "Certain ±30 m",
  2 dashed "Probable ±200 m", 1 dotted "Conjectured"; 0 is `#f2ff89` dotted,
  "No evidence – requires investigation".
- **Military** (`Main site type`): `#ff0000` for confirmed sites, `#fb9a99` for
  "Possible …", `#000000` for legionary fortress.
- **Settlement** (`TYPE`): military vicus `#98d8f8`, vicus/civitas `#f7ff01`,
  municipium `#fdbf6f`, colonia `#ff6b01`.
- **Milecastles** (`Status`): Confirmed `#ff0000`, Assumed `#fb9a99`.
- The author's labels are used in the legend. The typo "invetsigation" is fixed
  in the legend only.

Layers with a single-symbol QGIS style (temporary camps, milestones) and the
rule-based walls style get a viewer palette, kept visually separate from the
author's colours:
- Camps by `Camp type`; "possible" camps lighter.
- Walls by `Feature`: wall, ditch, vallum.

## Consequences
- The viewer looks like the author's own QGIS project, so RRRA users will
  recognise it.
- Signal stations have fill alpha 0 in the author's style (ERRATA M4). The
  viewer draws them with an outline so they stay visible.
