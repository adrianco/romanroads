# 0013 — Itiner-e datum fix: British segments are OSGB36 lat/lon labelled as WGS84

**Status:** Accepted

## Context
The project owner noticed that around Dorchester the Itiner-e comparison roads
look *consistently offset* from the RRRA roads. A route-by-route disagreement
would be expected between two datasets, but a constant offset points to a
coordinate-reference problem.

## Measurement
All measurements are in British National Grid metres. The RRRA roads come
straight from the GeoPackage in its native EPSG:27700; Itiner-e is converted
from its EPSG:3395.
1. Take Itiner-e vertices within 300 m of an RRRA road of confidence 2–3.
2. Grid-search the single (dx, dy) shift that minimises the median distance
   to the RRRA lines. Perpendicular distances alone can't reveal a
   translation, so the shift has to be fitted.

| Area | Median gap | Best-fit correction (E, N) | Shift predicted if OSGB36 lat/lon is read as WGS84 |
|------|-----------:|---------------------------|----------------------------------------------------|
| Dorchester ±15 km | 73 m | −90, +69 | +92, −64 |
| Rochester ±25 km | 92 m | −109, +59 | +118, −55 |
| High Cross ±25 km | 76 m | −102, +38 | +103, −41 |
| York ±25 km | 85 m | −111, +12 | +105, −22 |
| Hadrian's Wall ±25 km | 37 m | −94, +9 | +96, −8 |
| Brecon ±25 km | 64 m | −79, +35 | +84, −48 |
| All Britain | 81 m | −104, +31 | |

The fitted correction is the mirror image of the predicted datum error at every
site. It even reproduces the regional pattern: the northward part shrinks from
about 65 m in Dorset to about 10 m on the Wall, just as the
OSGB36–WGS84 difference does.

The offset doesn't depend on contributor. All three British citation groups
show it:

| Citation | Segments | Correction (E, N) |
|----------|---------:|-------------------|
| Joseph Lewis | 221 | −103, +34 |
| Joseph Lewis and Pau de Soto | 85 | −126, +60 |
| Mike Bishop, Joseph Lewis and Pau de Soto | 1,065 | −103, +33 |

## Ruling out our own pipeline
The same signature would appear if *our* EPSG:27700↔4326 step had skipped the
datum shift, in which case the RRRA layer would be the one that's wrong. Checks:
- PROJ 9.5.1 picks "OSGB36 to WGS 84 (6)", rated accurate to 2 m. The OSTN15
  grid isn't installed, which only matters at the few-metre level.
- The Airy transit circle (BNG 538874, 177344, on the OSGB36 zero meridian)
  converts to 0.0016° W. That's about 110 m west of the OSGB36 meridian, as it
  should be. With no datum shift it would come out at 0.0000°.
- On screen, the RRRA roads sit on the LiDAR aggers and on the Wall as engraved
  on the NLS 6-inch sheets, and those overlays come from independent sources.

## Decision
In `scripts/process.py`, reinterpret the British Itiner-e coordinates as
**OSGB36 geographic (EPSG:4277)** and convert them to WGS84 with the same PROJ
operation as the RRRA data:
`it.set_crs(4277, allow_override=True).to_crs(4326)`. This is a principled
datum correction, not a fitted nudge.

## Result (re-measured on the published `docs/data/itinere.geojson`)

| Area | Median gap before | After | Remaining best-fit shift |
|------|------------------:|------:|--------------------------|
| Dorchester | 73 m | 14 m | +1, +6 m |
| Rochester | 92 m | 14 m | +1, +11 m |
| High Cross | 76 m | 6 m | +1, −2 m |
| York | 85 m | 25 m | −11, −11 m |
| Hadrian's Wall | 37 m | 5 m | −1, −1 m |
| Brecon | 64 m | 17 m | +8, −9 m |
| **All Britain** | **81 m** | **17 m** | **+1, −2 m** |

The datum correction beats the best single constant shift (24 m median),
because it varies across the country the way the error does. The 5–25 m that
remains reflects genuine differences in route, Itiner-e's straight-line
conjectures, and generalisation.

## Consequences
- The viewer's Itiner-e layer is **our corrected version**, not the published
  coordinates. The panel says so, and the manifest records it.
- Only the British subset was examined. Other provinces may or may not be
  affected.
- This is worth reporting to the Itiner-e team. The British contributions
  appear to have been digitised in OSGB36 lat/lon and stored as WGS84. The
  evidence is the table above; their CRS is EPSG:3395 (WGS84 World Mercator).
- If a future Itiner-e release fixes the source, delete the `set_crs(4277…)`
  line. The re-measurement above is the test: a correct source should show a
  best-fit shift near zero *without* the fix.
