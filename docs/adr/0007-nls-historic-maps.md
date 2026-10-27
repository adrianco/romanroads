# 0007 — NLS historic OS 6-inch via `6inchsecond`

**Status:** Accepted

## Context
Historic Ordnance Survey maps show where a Roman road survives as a lane, hedge
line or parish boundary, and the 6-inch sheets often mark "Roman Road" outright.
The brief asks for NLS 6-inch as one of the three core underlays.

## Verification (2026-10-27)
NLS serves its georeferenced layers as public XYZ PNG tiles from
`https://mapseries-tilesets.s3.amazonaws.com/`. Each tileset's `metadata.json`
gives its bounds:

| tileset | coverage (bounds) | maxzoom | London / York tile |
|---------|-------------------|--------:|-------------------|
| `os/6inchfirst` | **Scotland only** (lat 54.6–60.9) | 17 | 404 / 404 |
| `os/6inchsecond` | **all of GB** (lat 49.9–60.9) | 17 | 200 / 200 |
| `os/britain10knatgrid` | GB, 1:10,560 National Grid (1950s+) | 16 | 200 / 200 |
| `os/newpopular` | E&W + S. Scotland, One-Inch New Popular | 16 | 200 / 200 |

The obvious choice, `6inchfirst`, turned out to be Scotland only. England and
Wales 6-inch first editions exist only as per-county tilesets
(`os/six-inch-kent`, …), which can't be combined into one seamless layer
without a manifest of about 50 sources.

## Decision
- Default historic layer: **`os/6inchsecond`**, the OS Six-Inch 2nd edition
  (c. 1890s–1910s), seamless across GB.
- Offer `6inchfirst` (Scotland), `britain10knatgrid` and `newpopular` as
  alternative editions in the same historic-map selector.
- Attribution: "Historic maps: National Library of Scotland", linked to
  maps.nls.uk. The NLS map images are CC BY (re-use) and free for
  non-commercial use.

## Consequences
- The default historic layer is seamless where the roads actually are (mostly
  England).
- We use the 2nd edition rather than the 1st. It still marks Roman roads and
  antiquities in the same Gothic/Egyptian lettering.
- The tile URLs aren't a published, versioned API. If NLS moves them, update
  `docs/index.html`.
