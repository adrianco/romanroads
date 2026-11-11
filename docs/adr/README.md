# Architecture Decision Records

Each file records one decision taken while building the Digital Britannia viewer:
context, decision, and consequences. Status is `Accepted` unless noted.

| ADR | Decision |
|-----|----------|
| [0001](0001-full-fidelity-geometry.md) | Reproject to EPSG:4326 with no simplification; round to 7 dp |
| [0002](0002-single-page-delivery.md) | Per-layer GeoJSON + single page on GitHub Pages (no PMTiles) |
| [0003](0003-category-normalisation.md) | Normalise messy category values, write cleaned values back for display |
| [0004](0004-follow-author-qgis-styles.md) | Symbology follows the author's embedded QGIS `layer_styles` |
| [0005](0005-maplibre-and-base-maps.md) | MapLibre GL JS with Esri Canvas / OSM base maps (CARTO rejected: needs a key) |
| [0006](0006-lidar-hillshade.md) | LiDAR hillshade: EA WMS (England), SRSP server-side shading (Scotland); Wales blocked by provider |
| [0007](0007-nls-historic-maps.md) | NLS historic OS 6-inch via the seamless `6inchsecond` tileset |
| [0008](0008-aerial-imagery.md) | Aerial imagery from Esri World Imagery |
| [0009](0009-label-glyphs.md) | Label glyphs from MapLibre demotiles (Noto Sans Regular) |
| [0010](0010-road-rendering.md) | One line layer per confidence level, with a halo |
| [0011](0011-data-in-repo.md) | Commit the source GeoPackage to the repository |
| [0012](0012-optional-extras.md) | Optional extras: DARE, BGS geology, 3D terrain, scheduled monuments, HE aerial mapping, Pleiades, Itiner-e comparison; rejected candidates |
| [0013](0013-itinere-datum-fix.md) | Itiner-e British segments are OSGB36 lat/lon labelled WGS84; corrected (median gap 81 m → 17 m) |
| [0014](0014-pleiades-matching.md) | Pleiades links matched at build time: fuzzy Roman/modern-name match within 2 km (issue #1) |
| [0015](0015-live-dtm.md) | Live 1 m EA DTM shaded in the browser (adjustable sun, multi-direction, slope, LRM, sky-view), 1 m 3D terrain, road elevation profiles, share links (issue #3) |
| [0016](0016-view-presets.md) | Four view presets (LiDAR, Old maps, Earthworks, 3D); detailed settings and legend collapsed |
| [0017](0017-wales-cog-and-ea-limits.md) | Wales: live 1 m DTM range-read from DataMapWales' COG; EA requests in 4×4 blocks with timeouts, back-off and recovery from its rate limit (issue #3) |
