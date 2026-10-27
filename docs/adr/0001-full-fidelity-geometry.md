# 0001 — Full-fidelity geometry: no simplification, 7 dp

**Status:** Accepted

## Context
All Digital Britannia layers are in EPSG:27700 (British National Grid). Web maps
need EPSG:4326 GeoJSON. The first draft of the brief proposed simplifying lines
to about 5 m. The revised brief asks for every original vertex to be kept: road
positions carry stated accuracies (±30 m certain, ±200 m probable), and
simplification would quietly degrade the author's work.

## Decision
- Reproject with GeoPandas/pyproj (`to_crs(4326)`).
- No simplification of any kind.
- Round every coordinate to 7 decimal places (~1 cm) with
  `shapely.transform(geom, np.round(a, 7))`. This keeps the vertex count and
  only shortens the numbers.
- Write with `COORDINATE_PRECISION=7` so GDAL doesn't re-expand the rounded
  values into float noise.

## Consequences
- Vertex counts match the source exactly.
- Rounding error (~1 cm) is far smaller than the source accuracy.
- Output is bigger than a simplified version would be (4.19 MiB in total), but it
  still fits the single-page budget (see [0002](0002-single-page-delivery.md)).
