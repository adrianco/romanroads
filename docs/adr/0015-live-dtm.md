# 0015 — Live 1 m DTM: shading in the browser, 1 m 3D terrain, road profiles

**Status:** Accepted (issue #3, phase 1: England)

## Context
Issue #3 pointed to [LiDAR Lens](https://lidarlens.sarsen.org/) (Tim Daw,
[MIT](https://github.com/TimDaw37/lidar-lens)). It fetches raw 1 m heights and
shades them in the browser: an adjustable sun, multi-direction hillshade, slope,
local relief model (LRM), sky-view factor and more. Our EA layer
([0006](0006-lidar-hillshade.md)) is a picture the EA has already shaded, with
one fixed sun.

LiDAR Lens gets its heights through a Cloudflare Worker that caches EA WCS
blocks and range-reads the Welsh COG, which has no CORS. We can't use its relay:
it only answers listed origins, and it isn't ours to load.

## What was checked (2026-11-04)
- **EA WCS** (`…/lidar-composite-digital-terrain-model-dtm-1m/wcs`, coverage
  `Lidar_Composite_Elevation_DTM_1m`) answers cross-origin requests from
  `adrianco.github.io` and `localhost` with float32 GeoTIFFs.
  - With `subsettingCrs`/`outputCrs` EPSG:3857, axes must be named **X/Y**:
    E/N give a 500.
  - `scaleSize` gives a 500; **`scaleFactor` works**. A factor of 1/3 returns
    exactly 256 × 256 for a z15 tile, 183 KB, in about 1.8 s.
  - The output is a big-endian, tiled TIFF with deflate (compression 32946), no
    predictor, nodata −3.4e38, and a ModelTransformation tag.
  - Outside the survey (the sea, Wales, Scotland) every cell is exactly 0.0.
  - Failed responses carry no `Access-Control-Allow-Origin`, so the browser
    reports them as CORS errors, as with the WMS.
- **Scotland:** the SRSP's WCS is disabled ("Service WCS version 2.0.1 is
  disabled"), so Scotland keeps its server-shaded WMS. The `srsp-ows.jncc.gov.uk`
  endpoint now redirects to `ows.remotesensing.data.gov.scot`. Both send
  `Access-Control-Allow-Origin: *`, and the existing layer still loads.
- **Wales:** the COG has no CORS (0006), so it still needs a server-side relay.
  That is phase 2.

## Decision
No server, and no MapLibre upgrade: everything runs through custom tile
protocols (`maplibregl.addProtocol`), like the retry fix.

1. **Heights.** For each tile from z13 to z17 inside the EA bounds:
   - Request the tile from the WCS plus a **16 px margin**. The scale factor
     is chosen so the native 1 m cells map onto the tile's resolution, capped
     at 1, so z17 upsamples.
   - Decode the TIFF with a small reader (`DecompressionStream("deflate")`).
   - Resample bilinearly onto an exact 288 × 288 grid using the TIFF's
     transform.
   - Treat 0.0 and nodata as gaps.
   - Requests share a queue of at most **6 in flight**. A queued tile that no
     map tile or profile still wants is dropped before it's requested. Up to
     **160 decoded tiles** stay in memory.
2. **Shading** (`dtm://`, layer `u-dtm`), in the browser:
   - **Hillshade:** one sun, with azimuth and elevation, using Horn gradients.
   - **Multi-direction:** GDAL's `-multidirectional` method. Four suns at
     225–360°, each weighted by sin² of the difference between sun and aspect.
     A plain average of eight suns came out nearly flat.
   - **Slope:** 0–40°.
   - **LRM:** the DTM minus a gap-aware Gaussian blur, ±1 m full scale at 1×.
   - **Sky-view factor:** 16 directions, out to the chosen radius.

   Exaggeration scales the gradients, the relief and the horizon angles. The
   radius is capped at the 16 px margin: 48 m at z15, 12 m at z17. A setting
   change re-shades from memory with `setTiles`, with no new EA requests.
   Shading times per tile: slope 3 ms, multi-direction 9 ms, LRM 15 ms,
   hillshade 27 ms, sky-view factor 110 ms.
3. **Layering.** The panel's LiDAR source choice is either the "ready-shaded"
   EA WMS (the default, and fast) or the "live 1 m DTM". In live mode the WMS
   still draws below z13, and the Scottish layer is unchanged. The same
   opacity slider controls both.
4. **3D terrain** (`dem1m://`, source `terrain-1m`): terrarium tiles built from
   the same heights from z13, with gaps and non-English areas filled from the
   Mapzen/AWS tiles (z>15 upsampled from z15). Below z13 it passes the AWS
   tiles straight through. It's on by default when 3D is ticked and can be
   unticked ("1 m EA heights in England").
5. **Elevation profile:** a button in every road popup.
   - **Geometry:** the roads source uses `generateId`, so the clicked feature's
     id is its index in `roads.geojson`. That gives the whole segment, not the
     piece clipped to a vector tile.
   - **Sampling:** one sample every ~5 m (more widely spaced on long segments,
     up to 1,500 samples), from z15 tiles (~3 m cells). It drops to z14 or z13
     if a segment needs more than 60 tiles. Heights come from EA where
     available and AWS elsewhere, and the note says which.
   - **Stats:** length, height range, climb and fall (with a 1 m dead band, so
     noise doesn't add up), and the steepest 100 m. Hovering or touching the
     chart moves a marker on the map.
6. **Share links:** every panel setting that differs from its default is
   written to the query string (`?lidar-src=live&dtm-mode=lrm`) and restored
   on load. MapLibre keeps the camera in the `#hash` and leaves the query
   string alone.

## Verified
- **Ackling Dyke (RR4c), Oakley Down, z15–16:**
  - All 16 tiles loaded with no errors.
  - Barrows, field systems and the agger are clear in every mode; the
    LRM is the most legible.
  - Changing the mode made no further WCS requests.
  - Moving the sun to 135° inverts the relief as expected.
- **Profile of RR4c (35.05 km):**
  - 60 EA tiles, 1,512 samples, heights 33–175 m.
  - The steepest 100 m (about 20%) is real: it's where the road ends through
    Old Sarum's earthworks (51.081, −1.814).
- **3D at pitch 70°:** `terrain-1m` served z13–14 tiles from EA heights. One
  transient EA failure was retried.
- **Phone:** the profile panel moves to the top of the map, and the chart
  responds to touch.

## Consequences
- **Slower:** 1–2.5 s per tile from the EA, with up to 6 in flight. The fast
  WMS stays the default.
- **Load on the EA:** each person's browser fetches heights directly, without
  a shared cache. The concurrency cap, the in-memory cache and dropping
  unwanted tiles keep this down. The WCS's rate limits are undocumented.
  Phase 2's relay would also give a shared edge cache.
- On high-DPI screens MapLibre asks for the next zoom up (z16 view → z17
  tiles), which is more requests per view.
- Not ported from LiDAR Lens: the drag lens, auto-contrast, colour ramps,
  openness and red relief, "What's here?" shape analysis, grid references and
  Geograph photos. The code is MIT, so they're open to a later round.
- **Requires** `DecompressionStream` and `OffscreenCanvas`: Chrome 80+,
  Firefox 113+, Safari 16.4+.
