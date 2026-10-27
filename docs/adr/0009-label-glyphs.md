# 0009 — Label glyphs from MapLibre demotiles

**Status:** Accepted

## Context
Margary road-number labels are MapLibre symbol layers, which need an SDF glyph
endpoint. Raster base maps don't provide one.

## Verification (2026-10-27)
| endpoint | result |
|----------|--------|
| `fonts.openmaptiles.org/Noto Sans Regular/0-255.pbf` | HTML page, not glyphs |
| `demotiles.maplibre.org/font/Open Sans Regular/…` | 404 |
| `demotiles.maplibre.org/font/Noto Sans Regular/0-255.pbf` | **200, 76 KB pbf** |
| `tiles.versatiles.org/assets/glyphs/noto_sans/…` | 404 |

## Decision
`glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf"`, using
only the `Noto Sans Regular` fontstack.

## Consequences
- Demotiles is MapLibre's demo server, with no availability guarantee. If it
  goes away, self-host the glyph PBFs under `docs/fonts/`. A single fontstack
  takes about 1–2 MB.
- No bold weight is available, so emphasis uses halo width and size instead.
