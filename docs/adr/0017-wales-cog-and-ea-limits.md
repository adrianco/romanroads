# 0017 — Wales from DataMapWales' COG; living with the EA's rate limit

**Status:** Accepted (issue #3, phase 2). Supersedes the Wales section of
[0006](0006-lidar-hillshade.md); amends [0015](0015-live-dtm.md).

## Context
- **Wales.** The Welsh Government's 1 m DTM is published by DataMapWales as one
  cloud-optimised GeoTIFF on Azure:
  `dmwproductionblob.blob.core.windows.net/cogs/lidar/wales_dtm_32bit_cog.tif`.
  It had no CORS rule, so no web page could read it ([0006](0006-lidar-hillshade.md)).
  - We asked DataMapWales to add one, and they did. The first version allowed
    `https://adrianco.github.io/` with a trailing slash. Browsers send the
    origin without one, so it didn't match until that was fixed.
  - The rule now allows GET with a `Range` header from
    `https://adrianco.github.io` only, so `localhost` is still refused.
- **England.** A user reported the live DTM as slow, with tiles that never
  updated after zooming in. Two causes were found (2026-11-11):
  - **Rate limiting.** After roughly 10–15 requests in a minute, the WCS
    answers `429 You are making too many requests`.
    - The 429 has no CORS header, so the browser sees only a network error.
    - Our 4 quick retries spent the allowance, and MapLibre never asks again
      for a tile that failed.
  - **Hung requests.** Some requests are never answered: 2 of 12, and 2 of 6,
    in two runs. `fetch` had no timeout, so each one held one of the 6 queue
    slots for good.

## What was checked
- **The COG:**
  - Little-endian BigTIFF, EPSG:27700, origin (164993, 397000).
  - 191,007 × 233,000 cells of 1 m float32, nodata −9999.
  - 256 px tiles, deflate, no predictor.
  - Six overviews: 2, 4, 8, 16, 32 and 64 m.
  - All seven directories are in the first 64 KB.
  - The level-0 tile index is 680,517 entries: 5.4 MB of offsets plus 2.7 MB of
    byte counts.
  - A row's tiles are stored next to each other, with an 8-byte gap between
    tiles.
  - Tiles are 65–83 KB each.
  - Its extent in WGS84 is 5.54°W–2.63°W, 51.32°N–53.47°N.
- **Azure from here:** about 0.65 s to the first byte and 1.1 s for 230 KB. 8
  reads in parallel took 1.45 s.
- **The BNG conversion:** written in JS (Helmert to OSGB36, then the OS
  Transverse Mercator). It matches pyproj, which converted the roads, to 0.01 m
  at six test points, so terrain and roads line up.
- **EA blocks:** a 2×2 block of tiles takes 2.8 s and a 4×4 block 6.3 s
  (3.2 MB), against 1.7 s for one tile.

## Decision
1. **Wales.** Range-read the COG in the browser.
   - **Header:** one 64 KB read, parsed once per session.
   - **Tile index:** read in blocks of 8,192 entries. A round trip costs far
     more than the bytes.
   - **Tiles:**
     - Requests from every map tile on screen are gathered for 15 ms, then
       read one row at a time: each run of adjacent tiles is a single range.
       A run can skip up to 3 tiles in between.
     - Decoded tiles are kept in memory (up to 240).
   - **Level:** each map tile uses the coarsest overview whose cells are no
     bigger than its pixels.
   - **Reprojection:** the tile's pixels are mapped to BNG every 16 px and
     interpolated between.
   - **`cache: "no-store"`:** without it, the browser's HTTP cache lets only
     one request at a time through for the same URL. That queued every read
     of the one file behind the last: 18 s for a screen, against under 2 s
     with it.
   - **Zoom:** Wales shows from zoom 10, England from 13. The overviews make
     zoomed-out Welsh tiles cheap.
   - **Ready-shaded mode** (the default) now also uses this layer, for Wales
     only, shaded to look like the EA's: one sun from 315° at 45°. Before, it
     showed no LiDAR in Wales at all.
   - **3D terrain and profiles** use Welsh heights from zoom 13, like England.
2. **England:**
   - **Fewer requests:** fetch 4×4 blocks, so a screen at any zoom is 2–6
     requests instead of 20–30.
   - **Back-off:** at most 3 in flight, each with a 15 s timeout. After any
     failure, every request waits 2 s, doubling up to 30 s. A tile still wanted
     after 6 tries fails.
   - **Recovery:** once the map is idle and the back-off has passed, the
     sources are given a new URL (`&e=n`). Failed tiles are then requested
     again; tiles already loaded re-shade from memory.
   - **Skipping the EA:**
     - In Wales the EA is asked only for gaps the Welsh data leaves.
     - It isn't asked at all for tiles west of the Dee and the Wye, where
       there's no England.
   - **Status line:** shows when the EA is limiting requests and how long the
     viewer will wait.
3. **Local testing:** `?wales-cog=<url>` (honoured on `localhost` only) points
   at a CORS proxy for the COG, since DataMapWales allows only the live site.

## Verified (localhost, through a CORS proxy for Wales)
- **Tomen-y-Mur, z15:**
  - 8 tiles in 1.8 s with `no-store`, against 18 s without.
  - No seams between tiles.
  - Field banks and drainage are clear.
- **Knighton, on the border, z14:**
  - 30 tiles, with Wales done in 9.3 s and no seam at the border.
  - One EA request hung. It timed out, and the retry succeeded.
- **Ready-shaded mode at Monmouth, z11:**
  - The Welsh layer meets the EA's own layer almost invisibly.
  - No requests went to the EA's WCS.
- **England while rate-limited:** the status line showed the wait, and nothing
  hung.

## Consequences
- **Load on Wales:** a fresh screen reads a few MB from Azure (about 1–1.5
  cells per screen pixel, ~1.1 bytes per cell compressed). Nothing is cached
  between visits.
- **Load on England:** 4×4 blocks over-fetch at the edges of the view, around
  10–20 MB per fresh screen. The first tiles in a block take ~6 s to appear.
- **Two-way dependency:** the Welsh layer depends on DataMapWales keeping the
  CORS rule and the file's URL. If either changes, Wales goes blank and England
  is unaffected.
- **Rate limit:** the EA's limit is undocumented and per IP. Heavy use from one
  network (an office or a class) will meet it sooner. A shared caching relay
  would help, if it's ever needed.
