# 0008 — Aerial imagery from Esri World Imagery

**Status:** Accepted

## Context
Cropmarks and parchmarks show buried road lines in aerial imagery. This is one
of the three core underlays. It needs to work without a key and allow
non-commercial use.

## Verification (2026-10-27)
`https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}`
returned a JPEG tile for London at z12. Note the **z/y/x** order.

## Decision
- Esri World Imagery as an underlay with an opacity slider. It can also stand
  in as the base map: set opacity to 100% and pick any base.
- Attribution: "Imagery © Esri, Maxar, Earthstar Geographics, and the GIS User
  Community".

## Consequences
- Esri's terms allow attributed non-commercial use of this basemap. Commercial
  or high-volume use needs an ArcGIS licence.
- Bing aerial was considered and rejected: it needs a key.
