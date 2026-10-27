# 0005 — MapLibre GL JS with Esri Canvas / OSM base maps

**Status:** Accepted (revised: CARTO replaced, see below)

## Context
The brief names MapLibre GL. We need a base map that needs no API key, allows
non-commercial use, and leaves the archaeology as the visual focus.

## What changed during the build
The first choice was **CARTO Positron / Dark Matter**. A curl check returned
HTTP 200 PNG tiles, so they looked fine. In the browser, though, every tile
reads **"API KEY REQUIRED"**: CARTO now serves a 2 KB watermark tile to keyless
requests. A status-code check isn't enough to verify a tile service. You have to
look at the tile.

## Decision
- MapLibre GL JS 4.7.1, pinned, from unpkg.
- Base maps (radio choice), all raster XYZ with no key:
  - **Esri World Light Gray Canvas** (default): light and low-contrast, so the
    red roads stand out. I checked this one visually: it shows real map detail
    for London at z12.
  - **Esri World Dark Gray Canvas**: for use with bright overlays.
  - **OpenStreetMap standard**: modern detail.
- Attribution comes from each source's `attribution` field, plus a permanent
  data credit and an "unofficial" notice.

## Consequences
- No keys or accounts, and no build step.
- The Esri Canvas basemaps allow attributed non-commercial use; the native
  maxzoom is 16, and higher zooms overzoom. OSM tile usage policy: low volume
  only. Heavy traffic should move to a commercial or self-hosted tile provider.
