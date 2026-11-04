# romanroads

Visualiser for the RRRA's Roman road dataset.

An **unofficial** web map viewer for
[Digital Britannia v1](https://roadsofromanbritain.org/digital-britannia/downloads.html)
from the Roman Roads Research Association. It shows the dataset's engineered
Roman roads, forts, temporary camps, settlements, milestones and Hadrian's /
Antonine Wall features over LiDAR hillshade, historic OS maps and aerial
imagery.

> Data: Digital Britannia v1, © Roman Roads Research Association / Mike Haken.
> CC BY-NC 4.0, non-commercial use only. This viewer is not endorsed by the RRRA.

## View the map

### Online
The map is live at **https://adrianco.github.io/romanroads/**, served by
GitHub Pages from the `docs/` folder of `main`. Each push to `main` redeploys
it within a minute or two.

### Locally
The viewer fetches its GeoJSON over HTTP, so opening `docs/index.html` straight
from disk (`file://`) won't work. Serve the `docs/` folder instead:
```bash
python3 -m http.server 8765 --directory docs
```
Then open http://localhost:8765.

### Using the viewer
- **Views:** four buttons at the top of the panel (still showing on phones with the panel folded) set up the map in one click:
  - **LiDAR:** hillshade under the roads and sites, the plainest view.
  - **Old maps:** the OS 6-inch map of about 1890–1910 blended with the
    LiDAR.
  - **Earthworks:** the 1 m local relief model, with scheduled monuments and
    Roman aerial mapping.
  - **3D:** tilted terrain from 1 m heights.

  Everything else is under **All layers and settings**.
- **Search** (top of the panel): a modern place name (`Housesteads`), a Roman
  name (`Vercovicium`) or a road number (`RR2`, `2a`). Road results zoom to the
  whole route.
- **Click** any road or site for a popup with every attribute and clickable
  links. Clicking a road highlights its entire Margary route in blue.
- **Underlays:** tick LiDAR hillshade, historic OS maps (choose the edition),
  aerial imagery, the Roman Empire map or geology, and set each one's opacity
  with its slider. Untick **Show roads** to look at the bare terrain. Tick
  **3D terrain** to show its sliders: **Tilt** (0–85°), **Rotation**,
  **Altitude** (zoom) and **Relief** (vertical exaggeration, 1–5×). The
  sliders follow the map as you move it, and turning 3D off returns to a flat,
  north-up view. In England the 3D terrain uses the EA's 1 m heights from
  zoom 13.
- **Live LiDAR (England):** under LiDAR hillshade, switch the source from
  *Ready-shaded by the EA* to *Live 1 m DTM*. From zoom 13 your browser
  fetches raw 1 m heights from the EA and shades them itself, so you can move
  the sun, raise the exaggeration, or change the visualisation:
  multi-direction hillshade, slope, **local relief model** (best for aggers and
  low earthworks) or sky-view factor. It's slower than the ready-shaded layer.
- **Elevation profile:** click a road, then *Elevation profile*, to chart the
  ground along that segment, with its climb, fall and steepest 100 m. Move
  along the chart to see where you are on the map.
- **Heritage overlays:** scheduled monuments and Roman-period aerial mapping
  load for the area in view once you zoom in. The line under each one says how
  many features are showing.
- **Period slider:** shows only military sites occupied in the chosen period,
  coloured by their type in that period.
- The URL keeps the current view (`#zoom/lat/lon`) and every panel setting you
  change (`?lidar-src=live&dtm-mode=lrm`), so a link opens the same map.

## What was built, and how

1. **Data processing** (`scripts/process.py`). The GeoPackage's layers are
   reprojected from British National Grid (EPSG:27700) to WGS84 (EPSG:4326) and
   written as one GeoJSON file per layer.
   - **No simplification.** Every original vertex is kept; coordinates are
     only rounded to 7 decimal places (~1 cm). Road positions carry stated
     accuracies of ±30 m and ±200 m, and simplifying would degrade them.
   - **Cleanup** of the source's inconsistent values: category spellings
     (`Legionary Fortress` / `Legionary fortress`), one garbled settlement
     type, `NULL` text glued onto values (which broke some links), and padding
     whitespace. The GeoPackage itself is never modified.
   - The empty *Hadrians Wall Turrets* layer is skipped.
2. **Symbology** follows the author's own QGIS styles, read from the
   GeoPackage's `layer_styles` table. Roads are solid / dashed / dotted by
   confidence; sites are coloured by type, as in the author's project.
3. **Viewer** (`docs/index.html`). A single page using MapLibre GL JS, with no
   build step and no API keys. The full-fidelity data is 4.19 MiB in total,
   under the 5 MB budget for a single page, so no vector-tile pipeline was
   needed.
4. **Underlays.** Each service was checked before it was wired in: its URL,
   whether it returns real tiles (one base-map provider returned
   "API KEY REQUIRED" watermarks and was dropped), its coverage, and its
   licence.
5. **Errata** (`docs/ERRATA.md`). Every data issue found along the way, with
   counts and examples, written up for the RRRA's next release.
6. **Decisions** are recorded as ADRs in [`docs/adr/`](docs/adr/README.md).

## Features
- **Roads** styled by `Segment Confidence`: solid = certain ±30 m,
  dashed = probable ±200 m, dotted = conjectured. "No evidence" segments are
  hidden by default. Margary `RR` number labels. Roads get a white halo so they
  stay readable over the underlays.
- **Sites** symbolised by type, with a toggle for "possible" sites.
- **Period slider** using the per-period type fields (Claudio-Neronian …
  4th century).
- **Underlays**, each with an opacity slider:
  - LiDAR hillshade:
    - **England:** Environment Agency 1 m composite, either ready-shaded or
      live: raw heights from the EA's WCS shaded in the browser with an
      adjustable sun, multi-direction hillshade, slope, local relief model or
      sky-view factor ([ADR 0015](docs/adr/0015-live-dtm.md), issue #3).
    - **Scotland** (from zoom 11): DTMs from the Scottish Remote Sensing
      Portal, shaded on the fly by its server.
    - **Wales:** not yet. The Welsh hillshades aren't available in any form a
      web page can use ([ADR 0006](docs/adr/0006-lidar-hillshade.md)).
  - Historic OS maps: National Library of Scotland, 6-inch 2nd edition (GB)
    and other editions
  - Aerial imagery: Esri World Imagery
  - Roman Empire map: the Digital Atlas of the Roman Empire (DARE), with Latin
    place names
  - Bedrock geology: BGS, 1:625k zoomed out and 1:50k zoomed in
  - 3D terrain: tilts the view with real elevation (1 m EA heights in
    England from zoom 13)
- **Road elevation profiles** from the same 1 m heights, with climb, fall and
  the steepest 100 m.
- **Heritage overlays:**
  - Scheduled monuments for England (Historic England), Scotland (HES) and
    Wales (Cadw).
  - Historic England's aerial mapping of Roman-period features (England, from
    zoom 14): cropmark and earthwork ditches, banks and structures.
- **Itiner-e comparison:** tick *Compare: Itiner-e roads* to draw the
  Itiner-e 2024 network for Britain in magenta, under the RRRA roads, to see
  where the two datasets agree and differ. Dashed means hypothetical. It's
  fetched only when switched on. The British Itiner-e segments are stored
  ~100 m out of place (OSGB36 lat/lon labelled as WGS84), so the viewer
  corrects them; see [ADR 0013](docs/adr/0013-itinere-datum-fix.md).
- **Pleiades links:** 533 forts and settlements link straight to their
  Pleiades place, matched at build time by Roman name, or by modern name where
  there's no Roman one, within 2 km
  ([ADR 0014](docs/adr/0014-pleiades-matching.md)). The rest fall back to a
  Pleiades search for the modern name; they're listed in
  `data/unmatched_pleiades.csv` for review. Roman names display in title case
  (`VERCOVICIVM` → "Vercovicium"). Search accepts the modern spelling and
  Pleiades' standard name (`Durnovaria` finds Dorchester's `DVROVARIA`).
- Phone layout with a bottom sheet.

Why each source was chosen, and why others were rejected, is in
[ADR 0012](docs/adr/0012-optional-extras.md).

## Layout
```
data/digital-britannia_v1.gpkg   source GeoPackage (EPSG:27700)
scripts/process.py               GeoPackage -> per-layer GeoJSON (EPSG:4326)
requirements.txt                 pinned Python dependencies
docs/index.html                  the viewer (single page, MapLibre GL JS)
docs/data/*.geojson              processed layers + manifest.json (itinere.geojson = Britain subset)
data/external/                   third-party downloads (gitignored)
docs/ERRATA.md                   data issues to report back to the RRRA
docs/adr/                        architecture decision records
```

## Rebuild the data
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/process.py
```
The Itiner-e comparison layer comes from a 33.6 MB empire-wide file that isn't
committed. Only the Britain subset (`docs/data/itinere.geojson`) is. To rebuild
it, download `itinere_roads.gpkg` from
[Zenodo record 17122148](https://doi.org/10.5281/zenodo.17122148) into
`data/external/` (gitignored) and rerun the script. Without the file, the
script keeps the committed subset.

Pleiades matching works the same way. Download `pleiades-places-latest.csv.gz`
and `pleiades-names-latest.csv.gz` from
[the Pleiades dumps](https://atlantides.org/downloads/pleiades/dumps/) into
`data/external/pleiades/`, and the script re-matches and rewrites
`data/pleiades_matches.csv` and `data/unmatched_pleiades.csv`. Without
them, it reuses the committed match table.

## How
A blog post records the development process over two days. [Dev.to blog](https://dev.to/adrianco_54/mapping-roman-britain-an-ai-built-viewer-for-digital-britannia-594g)

## Credits
- Data: Digital Britannia v1 © Roman Roads Research Association / Mike Haken (CC BY-NC 4.0)
- LiDAR (England): contains Environment Agency information © Environment Agency and/or database right
- Live DTM idea: [LiDAR Lens](https://lidarlens.sarsen.org/) by Tim Daw ([MIT](https://github.com/TimDaw37/lidar-lens)); the shading here is written separately, with the multi-direction hillshade following GDAL
- LiDAR (Scotland): © Crown copyright Scottish Government, SEPA, Fugro, Historic Environment Scotland and partners, via the Scottish Remote Sensing Portal (OGL)
- Historic maps: National Library of Scotland
- Roman Empire map: Digital Atlas of the Roman Empire, Johan Åhlfeldt (CC BY 4.0)
- Places: Pleiades, Copyright © The Contributors (CC BY 3.0), https://pleiades.stoa.org
- Comparison roads: Itiner-e static version 2024, Brughmans, de Soto, Pažout & Bjerregaard Vahlstrup (CC BY 4.0), https://doi.org/10.5281/zenodo.17122148
- Geology: contains British Geological Survey materials © UKRI
- Heritage (England): © Historic England, contains OS data © Crown copyright (OGL)
- Scheduled monuments (Scotland): © Historic Environment Scotland, Scottish Charity No. SC045925, © Crown copyright (OGL)
- Scheduled monuments (Wales): Cadw, via DataMapWales (OGL)
- Terrain: Mapzen terrain tiles on AWS Open Data; UK terrain data © Environment Agency 2015; EU-DEM (Copernicus); SRTM/GMTED2010 (USGS)
- Imagery and base maps: © Esri, Maxar, Earthstar Geographics, HERE, Garmin, and the GIS User Community
- Base map: © OpenStreetMap contributors
