# 0011 — Commit the source GeoPackage

**Status:** Accepted

## Context
`digital-britannia_v1.gpkg` is about 3 MB. It could be gitignored and
downloaded at build time, or committed.

## Decision
Per the project owner, commit it at `data/digital-britannia_v1.gpkg`. The
processed GeoJSON in `docs/data/` is committed as well, because GitHub Pages
serves it directly.

## Consequences
- `scripts/process.py` runs from a fresh clone with no network access.
- The repo carries ~3 MB of source plus ~4 MB of derived data. That's fine at
  this size. Later versions (v1.1, …) should replace the file in place, not sit
  alongside it.
- Redistribution falls under CC BY-NC 4.0, with attribution to Mike Haken and
  the RRRA, and the repo README says so.
