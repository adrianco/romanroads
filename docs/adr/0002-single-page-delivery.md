# 0002 — Per-layer GeoJSON, single page on GitHub Pages

**Status:** Accepted

## Context
The brief says: deliver a single self-contained page if the full-fidelity
GeoJSON is under about 5 MB; otherwise build PMTiles with tippecanoe
(`--no-line-simplification --no-tiny-polygon-reduction`, maxzoom ≥ 18).

Measured output from `scripts/process.py`:

| layer | features | size |
|-------|---------:|-----:|
| roads | 3,572 | 3,057 KiB |
| military | 517 | 378 KiB |
| camps | 617 | 331 KiB |
| settlement | 485 | 219 KiB |
| milestones | 137 | 198 KiB |
| walls | 29 | 58 KiB |
| milecastles | 81 | 52 KiB |
| **total** | | **4.19 MiB** |

## Decision
- We're under the threshold, so no PMTiles and no tippecanoe dependency.
- `docs/index.html` is the whole viewer. It fetches the seven GeoJSON files from
  `docs/data/`.
- Serve it with GitHub Pages from the `/docs` folder of the default branch.
- Keep data out of the HTML. Separate files cache well, the processing script
  can regenerate them without touching the page, and the layers load in parallel.

## Consequences
- GitHub Pages also gzips the GeoJSON in transit, so the real download is a
  fraction of 4.19 MiB.
- Opening `index.html` from `file://` won't work, because browsers block `fetch`
  of local files. Use Pages, or `python3 -m http.server` inside `docs/`.
- If a later data version grows past ~5 MB, switch to PMTiles as the brief
  specifies.
