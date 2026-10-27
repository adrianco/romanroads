# 0010 — Road rendering: one layer per confidence level, with a halo

**Status:** Accepted

## Context
Road styling depends on `Segment Confidence`: solid, dashed or dotted. In
MapLibre, `line-dasharray` can't be data-driven; it takes a single constant per
layer. The roads also have to stay readable over hillshade and imagery, which
can be dark or busy.

## Decision
- Four line layers (`roads-c3`, `roads-c2`, `roads-c1`, `roads-c0`), each
  filtered on `_conf` and given its own dash pattern.
- Each line has a matching **halo** layer underneath: wider, white, partly
  transparent. Halos are drawn as dashed lines too, so the gaps in the dashes
  stay readable.
- Confidence 0 and unspecified (−1) are hidden by default. A checkbox shows
  confidence 0.
- **Route highlight:** clicking a road or a search result sets a filter on a
  separate highlight layer matching `_margary`, so the whole Margary route lights
  up, not just the one segment.
- Margary labels: a symbol layer along the line (`symbol-placement: line`),
  from zoom 9.
- A "hide roads" toggle switches off every road layer and its halo, so the
  terrain underneath can be checked.

## Consequences
- More layers (4 halo + 4 line + highlight + labels), but each one is simple and
  MapLibre handles a few thousand lines easily.
- Line widths scale with zoom, so roads stay thin over LiDAR at high zoom.
