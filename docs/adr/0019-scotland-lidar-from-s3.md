# 0019 — Scotland: LiDAR read from the portal's open-data bucket, terrain tiles between

**Status:** Accepted. Supersedes the Scotland section of [0006](0006-lidar-hillshade.md);
extends [0017](0017-wales-cog-and-ea-limits.md).

## Context
A user noticed that Scotland had "a white background", unlike England and Wales. On
2026-11-22 two things turned out to be wrong:
- **The server-side shading had stopped working.** The Scottish Remote Sensing Portal's WMS
  moved: `srsp-ows.jncc.gov.uk` now redirects to `ows.remotesensing.data.gov.scot/geoserver`.
  - The new server ignores `SLD_BODY`, so the `ShadedRelief` style ([0006](0006-lidar-hillshade.md))
    was dropped. Each layer came back in its default colour ramp.
  - The 11 stacked layers came back as one solid near-black tile. The viewer showed nothing
    useful in Scotland at any zoom.
- **Even when it worked, most of Scotland was blank.** The surveys cover only part of the country,
  and the layer started at map zoom 10.

## What was checked
- **The new server:**
  - Its WMS still lists the same DTM layers, but only with colour-ramp styles.
  - Its WCS is switched off ("Service WCS version 2.0.1 is disabled").
  - `format=image/geotiff` gives 8-bit styled grey, not heights.
  - So it can't be the source of heights any more.
- **The open-data bucket:** `srsp-open-data.s3.eu-west-2.amazonaws.com`.
  - It's public, can be listed, and answers `Access-Control-Allow-Origin: *`.
  - Each survey's DTM is under `lidar/<survey>/dtm/27700/gridded/`, one GeoTIFF per OS grid
    square.
  - 11,800 files are used (625 GB). The Outer Hebrides' 25 cm copy is skipped in favour of its
    50 cm one.
  - The layouts vary, from one header read per survey:

    | Survey | Square | Cell | Layout | Overviews |
    |---|---|---|---|---|
    | Phases 1–2 | 10 km | 1 m | LZW, 256 px tiles | none |
    | Phases 3–6 | 5 km | 50 cm | LZW, 256 px tiles | to 16–32 m |
    | National LiDAR Programme | 1 km | 50 cm | LZW, 528–736 px tiles | to 2 m |
    | Coastal 2025–26 | 1 km | 50 cm | LZW, 256 px tiles | to 4 m |
    | Outer Hebrides | 5 km | 50 cm | LZW, 512 px tiles | to 16 m |
    | Orkney 2023 | 1 km | 50 cm | uncompressed strips | none |
    | HES projects | 1 km | 25–50 cm | strips or LZW tiles | some |

    All are little-endian classic TIFFs: float32, no predictor, on the British National Grid.
- **Licence:** the portal's About page says all data is under the Open Government Licence v3
  unless stated otherwise. The portal's pages don't name the bucket itself. Its name (SRSP) and
  folder layout match the portal's surveys, and the credit is unchanged from [0006](0006-lidar-hillshade.md).
- **Between the surveys:** the viewer already loads the AWS (Mapzen) terrain tiles for 3D. In
  Scotland they're EU-DEM / SRTM at about 30 m.

## Decision
1. **One Scottish layer, shaded here,** through the same live DTM pipeline as Wales and England
   ([0015](0015-live-dtm.md), [0017](0017-wales-cog-and-ea-limits.md)). It uses the same sun,
   tone and modes. In ready-shaded mode it is shaded like Wales.
2. **The LiDAR, from tile zoom 14 (map zoom 13):**
   - **Index:** `scripts/scotland_index.py` lists the bucket (names only) into
     `docs/data/scot-lidar.json`: 83 KB, 27 KB gzipped, fetched once when first needed.
   - **Reading a file:** for each map tile, read the header of each file whose square it touches
     (64 KB), choose the coarsest level no coarser than the pixels, then range-read the tiles or
     strips needed.
     - Reads are gathered for 15 ms into runs, as for Wales.
     - The browser decodes LZW (a small decoder written here), deflate or raw data.
     - Decoded blocks are kept up to 24 M heights.
   - **Too-fine files:** a file is skipped while its cells are under a third of a pixel. So:
     - phases 3–6 and the National LiDAR Programme show from map zoom 13;
     - phases 1–2 from 14;
     - Orkney from 15.
   - **Overlaps:** where surveys overlap, the newer one wins, with HES's archaeological surveys on
     top (as in 0006).
3. **Terrain between, and zoomed out:**
   - Wherever there's no LiDAR (and at every zoom below that), the AWS terrain tiles fill
     Scotland, from map zoom 5.
   - They're smoother than LiDAR, so their shading flattens as you zoom out. Their heights are
     scaled for shading only: 2.4× at tile zoom 6, 2× at 7, 1.6×, 1.35×, 1.25×, 1.15×, 1.07×, then
     1× from tile zoom 13. That matches the 5th–95th percentile spread of the EA's tiles on the same
     northern Pennine hills (e.g. at tile zoom 9: EA 66–172, scaled terrain 72–178).
   - These heights aren't used for 3D or profiles. Those use the AWS tiles as before, plus the new
     Scottish LiDAR.
4. **Where Scotland stops:**
   - **England:** cut out wherever the EA's ready-shaded tile for the same tile has data, so the
     two never overlap. The EA's tiles can't be cached (`no-store`) and count towards its rate
     limit. So that tile is fetched only for tiles that can reach England: three boxes round the
     border from the Solway to the Tweed.
   - **Ireland and Man:** a latitude/longitude rule leaves out Northern Ireland, Donegal and the
     Isle of Man (all south of 55.45°N and west of 5.45–5.95°W) and keeps Kintyre and Islay.
   - **The sea:** terrain at or below 0 m is left clear.
   - In live mode the EA's WCS isn't asked for tiles with no England in them.
5. **The broken WMS layer is removed.**

## Verified (localhost, 2026-11-22)
- **Zoomed out (map zoom 5.5):** all of Scotland is shaded.
- **The border:**
  - The Scottish and EA layers share no pixel at tile zooms 7, 9, 10 and 11.
  - At Liddesdale (zoom 9.6) there's no visible gap or dark seam, though Scotland's side is
    smoother.
- **Rough Castle, Antonine Wall, zoom 15:** the rampart and ditch are clear from the LiDAR.
- **Tile times:**
  - Rough Castle: tile zoom 14 in 1.4 s, 15 in 0.5 s.
  - Inchtuthil: 0.3 s at tile zoom 15. Its phase-1 data has no overviews, so it shows terrain at
    tile zoom 14.
  - Ardoch has no survey in the bucket, so it shows terrain.
- **Carter Bar (live mode, tile zoom 14):** the EA and Scottish LiDAR between them fill the tile.

## Consequences
- **Coverage:** most of Scotland's LiDAR now shows. Before, the server-side shading was broken
  everywhere. Areas no survey covers (much of the Highlands) are shaded from ~30 m terrain:
  hills and valleys, but no earthworks.
- **Mixed detail:** the change from terrain to LiDAR at map zoom 13–15 is visible: smooth, then
  sharp. Where the two meet inside a tile, the edge can show.
- **Load:** a fresh screen at zoom 14 reads tens of headers and a few MB from S3. The browser
  allows 6 connections to S3 at once, so a first view takes a second or two.
- **Dependencies:**
  - The bucket's layout and CORS rule.
  - The AWS terrain tiles.
  - The EA's tiles near the border.
  - If the bucket changes, `scripts/scotland_index.py` rebuilds the index; if it disappears,
    Scotland falls back to terrain shading.
- **The HES scheduled-monument overlay** is a separate service and unaffected.
