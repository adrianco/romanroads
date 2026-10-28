# 0006 — LiDAR hillshade: England (EA), Scotland (SRSP); Wales not possible yet

**Status:** Accepted. England and Scotland are live; Wales is blocked by the
provider (see below).

## Context
LiDAR is a core feature: aggers (raised road embankments) show up in hillshade
where nothing survives on the surface. The brief lists three national sources
and asks for each URL and licence to be checked before use, preferring a
multi-directional hillshade where one is offered.

## England: Environment Agency (verified 2026-10-27)
- WMS: `https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wms`,
  layer **`Lidar_Composite_Hillshade_DTM_1m`**. Supports **EPSG:3857**, and a
  test GetMap returned a 256×256 PNG.
- The capabilities `AccessConstraints` say only that the data is "made freely
  available by Defra and its agencies", with `Fees: NONE`; the licence isn't
  named there. Defra publishes its LiDAR under the Open Government Licence. The
  viewer credits "Contains Environment Agency information © Environment Agency
  and/or database right". Confirm against the data.gov.uk record before any
  wider reuse.
- Only one hillshade style is published; there's no multi-directional variant.
- This path replaces the older `…-dtm-1m-2022/wms` and Esri ImageServer
  endpoints, which the EA has retired.

## Scotland: Scottish Remote Sensing Portal (verified 2026-10-27)
- WMS: `https://srsp-ows.jncc.gov.uk/ows` (GeoServer, hosted by JNCC). It
  supports EPSG:3857, and its capabilities list `AccessConstraints: none`,
  `Fees: none`.
- Licence: each survey's metadata record on SpatialData.gov.scot gives the
  **Open Government Licence**, with its own Crown-copyright credit line (for
  example "Crown copyright Scottish Government, SEPA and Fugro (2020)"). The
  viewer gives one combined credit naming the Scottish Government, SEPA,
  Fugro, Historic Environment Scotland and partners.
- **No hillshade layer is published.** The DTMs are only offered with
  elevation colour-ramp styles (`lidar-dem`, `lidar-dem-viridis`), which hide
  subtle earthworks. The `lidar-aggregate` layer is a flat-grey coverage mask
  and ignores custom styles.
- **Decision:** ask the server to shade the DTMs itself. GeoServer accepts an
  inline style (`SLD_BODY`) using `RasterSymbolizer/ShadedRelief`
  (`BrightnessOnly`, `ReliefFactor 8`). One request stacks 11 DTM layers, in
  draw order:
  1. LiDAR for Scotland phases 1–6
  2. the 2020s National LiDAR Programme (`nlp-dtm`)
  3. four Historic Environment Scotland archaeological surveys
  Later layers draw over earlier ones, so newer and higher-resolution data
  wins where they overlap.
- Checked visually at Rough Castle (Antonine Wall) and Inchtuthil (legionary
  fortress), where the earthworks are clearly legible, and across the border
  at Carter Bar, where it matches the EA tone after `raster-brightness-max 0.8`
  and `raster-contrast 0.2`.
- **Limits:**
  - The server only renders these layers from about **zoom 11**, so the
    source has `minzoom: 11`.
  - Tiles take about 1–2.5 s each, because the server computes the shading
    for every request.
  - The URL is about 4.9 KB, under the ~8 KB GET limit many proxies enforce.
    I tested 17 layers (7.4 KB) and it worked, but chose 11 to keep a margin.
    The Orkney, Outer Hebrides and Luing surveys are left out, since no Roman
    roads reach them.
  - There are genuine coverage gaps: **Ardoch** fort returned no data from any
    of the 17 layers.
  - Visible straight-line seams are boundaries between surveys; I checked that
    they don't fall on tile edges.

## Wales: DataMapWales (checked 2026-10-27), not wired in
- The public GeoServer WMS (`datamap.gov.wales/geoserver/ows`, 14 MB of
  capabilities, 2,100 layers) carries only LiDAR **tile indexes**, not
  elevation or hillshade rasters.
- DataMapWales lists hillshade layers, including a 2020–23 DTM hillshade and a
  **multi-directional** DSM hillshade, but they aren't in the public WMS. A
  GetMap by name returns a ServiceException, and the layer pages sit behind a
  sign-in.
- The same hillshades are public as cloud-optimised GeoTIFFs on
  `dmwproductionblob.blob.core.windows.net/cogs/`. The DTM one is 1.05 GB and
  the multi-directional DSM one is 22 GB. Range requests work, but the blob
  has **no CORS rule**: the preflight returns
  `403 CORS not enabled or no matching rule found`. A web page can't read them.
- Pre-rendering our own tiles isn't practical: Wales at z16–17 would be
  several GB, beyond GitHub Pages limits.
- **Unblocking:** either DataMapWales publishes the hillshade in its public
  WMS, or it enables CORS on the `cogs` container. Its GeoServer already sends
  `Access-Control-Allow-Origin: *`, so a WMS layer would drop straight in.
  Either change would be worth requesting.

## Reliability: retries (added 2026-10-28)
The EA WMS **fails some tiles transiently** when requested from a browser.
- **Live viewer at Dorchester (z13):** 7 of 29 tiles ended up permanently
  `errored`. Each failure shows up as a CORS error, because the failed
  response carries no `Access-Control-Allow-Origin`.
- **Bursts of 30 `fetch()` calls from a page:** 0, 1, 3 and 8 failures, with
  or without MapLibre's `Accept: image/webp` header, so the header isn't the
  cause.
- **Retrying works:** the same URLs succeed when requested again.
- **Outside a browser** (curl, also over HTTP/2, and parallel Python), every
  request succeeded, so it can't be reproduced outside a browser.

MapLibre never retries a failed raster tile, so each failure left a **hole**
in the hillshade until the view changed. An earlier diagnosis blamed
cancelled requests and survey patchwork; that was wrong for these tiles.

**Decision:** both LiDAR sources load through a `retry://` protocol
(`maplibregl.addProtocol`). It fetches the tile and, on a network error or
non-2xx response, retries up to 3 times after about 0.4, 1.2 and 3 s, with
jitter. An `AbortError` (the map moved and the tile is no longer needed) is
passed straight through.

**Verified:**
- I patched `fetch` so the first attempt of every third LiDAR tile failed
  (14 of 42). All 42 tiles loaded, using 56 fetches.
- Three fresh loads (Dorchester, London, York) finished with every tile
  `loaded`.
- The browser still logs a CORS error for each failed *first* attempt. That's
  expected, and the tile is fetched again.

## Rendering
- Both live sources are MapLibre raster sources using WMS GetMap templates with
  `crs=EPSG:3857&bbox={bbox-epsg-3857}` and 256 px tiles.
- They are drawn above the base map and below all archaeology layers. One
  "LiDAR hillshade" checkbox and one opacity slider control both.
- Roads stay visible over the hillshade thanks to their halos (see
  [0010](0010-road-rendering.md)). A "hide roads" toggle shows the bare terrain.
