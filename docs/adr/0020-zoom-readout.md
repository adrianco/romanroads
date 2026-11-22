# 0020 — Show the map's zoom level; quote every threshold as a map zoom

**Status:** Accepted

## Context
The panel says when things appear: "Wales from zoom 10", "Scotland from 11",
"monuments from zoom 10". A user said it wasn't clear what the zoom number was,
because the viewer didn't show one anywhere.

There were also two different zoom numbers in use:
- **Map zoom:** what MapLibre reports, and what the page address shows
  (`#zoom/lat/lon`).
- **Tile zoom:** what a raster source's `minzoom` and the code's constants
  (`DTM_MIN_Z`, `WALES_MIN_Z`, `SCOT_LIDAR_MIN_Z`) refer to. MapLibre loads
  256 px raster tiles one level above the map zoom: tile zoom =
  round(map zoom + 1).

The panel's notes had quoted the tile zooms. So a reader who checked the address
bar would find each layer appearing a level earlier than it said.

## Decision
- **A readout,** "Zoom 9.5", to one decimal place.
  - It sits under the zoom buttons at the top right. The panel can cover the
    bottom-left corner, where the scale bar is.
  - It's a MapLibre control that updates on every `zoom` event.
  - Its tooltip says it's the map zoom, also in the page address.
- **Every number shown to the user is a map zoom.** That covers the panel's
  notes, the live-DTM status line, the preset descriptions and the README.
  - Code thresholds stay in tile zoom, because that's what the sources take.
  - The status line converts with `mapZoomFor(tileZ) = tileZ − 1`.
- **The numbers at the time (2026-11-22):**

  | What | Tile zoom | Shown as |
  |---|---|---|
  | England, live DTM and 1 m 3D heights | 13 | 12 |
  | Wales, live DTM | 10 | 9 |
  | Scottish and Welsh scheduled monuments | 10 | 9 |
  | Scottish LiDAR ([0019](0019-scotland-lidar-from-s3.md)) | 14–16 by survey | 13–15 |

  Vector layers queried by map zoom (English monuments from 11, HE aerial
  mapping from 14) were already map zooms and didn't change.

## Consequences
- What the panel says matches what the readout and the address show.
- **Older ADRs quote tile zooms.** [0015](0015-live-dtm.md) and
  [0017](0017-wales-cog-and-ea-limits.md) (e.g. "Wales from zoom 10, England
  from 13") are one higher than what the panel now says. The behaviour is
  unchanged.
- New thresholds must be quoted as a map zoom wherever a user will read them.
- The readout takes a little space on phones, under the zoom buttons.
