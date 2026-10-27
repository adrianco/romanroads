# 0006 — LiDAR hillshade from the Environment Agency WMS

**Status:** Accepted (England). Wales and Scotland deferred.

## Context
LiDAR is a core feature: aggers (raised road embankments) show up in hillshade
where nothing survives on the surface. The brief lists three national sources
and asks for each URL and licence to be checked before use.

## Verification (2026-10-27)
- **England, Environment Agency:** GetCapabilities at
  `https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wms`
  returns layer **`Lidar_Composite_Hillshade_DTM_1m`**. It supports
  **EPSG:3857**, and a test GetMap returned a 256×256 PNG. The capabilities
  `AccessConstraints` say only that the data is "made freely available by Defra
  and its agencies", with `Fees: NONE`. The licence isn't named there. Defra
  publishes its LiDAR under the Open Government Licence, so the viewer credits
  "Contains Environment Agency information © Environment Agency and/or database
  right". Confirm the licence against the data.gov.uk record before any wider
  reuse. This path replaces the older `…-dtm-1m-2022/wms` and
  Esri ImageServer endpoints, which the EA has retired.
- Only one hillshade style is published. No multi-directional variant is
  offered, so we use the standard one.
- **Wales (DataMapWales)** and **Scotland (Scottish Remote Sensing Portal):**
  not verified in this pass. Under the brief's rule, they stay out until they
  are verified.

## Decision
- MapLibre raster source using the WMS GetMap template with
  `crs=EPSG:3857&bbox={bbox-epsg-3857}`, 256 px tiles, `transparent=true`.
- Drawn above the base map and below all archaeology layers, with an opacity
  slider.
- Roads stay visible over it: each road line has a light halo underneath (see
  [0010](0010-road-rendering.md)). A "hide roads" toggle shows the bare terrain.

## Consequences
- Coverage is England only for now; elsewhere the hillshade is blank.
- Follow-up: verify and add Welsh and Scottish LiDAR, ideally a multi-directional
  hillshade if either service offers one.
