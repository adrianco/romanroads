# romanroads

Visualisers for the RRRA's Roman road dataset.

An **unofficial** web map viewer for
[Digital Britannia v1](https://roadsofromanbritain.org/digital-britannia/downloads.html)
from the Roman Roads Research Association. It shows the dataset's engineered
Roman roads, forts, temporary camps, settlements, milestones and Hadrian's /
Antonine Wall features over LiDAR hillshade, historic OS maps and aerial
imagery.

> Data: Digital Britannia v1, © Roman Roads Research Association / Mike Haken.
> CC BY-NC 4.0, non-commercial use only. This viewer is not endorsed by the RRRA.

## View the map

### Online (GitHub Pages)
Once Pages is enabled, the map is at **https://adrianco.github.io/romanroads/**.

To enable it: repo **Settings → Pages → Build and deployment → Deploy from a
branch → `main` / `/docs` → Save**. The first deploy takes a minute or two.

### Locally
The viewer fetches its GeoJSON over HTTP, so opening `docs/index.html` straight
from disk (`file://`) won't work. Serve the `docs/` folder instead:
```bash
python3 -m http.server 8765 --directory docs
```
Then open http://localhost:8765.

### Using the viewer
- **Search** (top of the panel): a modern place name (`Housesteads`), a Roman
  name (`Vercovicium`) or a road number (`RR2`, `2a`). Road results zoom to the
  whole route.
- **Click** any road or site for a popup with every attribute and clickable
  links. Clicking a road highlights its entire Margary route in blue.
- **Underlays:** tick LiDAR hillshade, historic OS maps (choose the edition),
  aerial imagery, the Roman Empire map or geology, and set each one's opacity
  with its slider. Untick **Show roads** to look at the bare terrain. Tick
  **3D terrain** and right-drag (or Ctrl-drag) to tilt the view.
- **Heritage overlays:** scheduled monuments and Roman-period aerial mapping
  load for the area in view once you zoom in. The line under each one says how
  many features are showing.
- **Period slider:** shows only military sites occupied in the chosen period,
  coloured by their type in that period.
- The URL keeps the current view (`#zoom/lat/lon`), so you can share a link to
  a specific spot.

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
    - **England:** Environment Agency 1 m composite.
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
  - 3D terrain: tilts the view with real elevation
- **Heritage overlays:**
  - Scheduled monuments for England (Historic England), Scotland (HES) and
    Wales (Cadw).
  - Historic England's aerial mapping of Roman-period features (England, from
    zoom 14): cropmark and earthwork ditches, banks and structures.
- **Pleiades links** in the popups of sites with a Roman name. Search accepts
  modern spellings of inscribed names (`Vercovicium` finds `VERCOVICIVM`).
- Phone layout with a bottom sheet.

Why each source was chosen, and why others were rejected, is in
[ADR 0012](docs/adr/0012-optional-extras.md).

## Layout
```
data/digital-britannia_v1.gpkg   source GeoPackage (EPSG:27700)
scripts/process.py               GeoPackage -> per-layer GeoJSON (EPSG:4326)
requirements.txt                 pinned Python dependencies
docs/index.html                  the viewer (single page, MapLibre GL JS)
docs/data/*.geojson              processed layers + manifest.json
docs/ERRATA.md                   data issues to report back to the RRRA
docs/adr/                        architecture decision records
```

## Rebuild the data
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/process.py
```

## Credits
- Data: Digital Britannia v1 © Roman Roads Research Association / Mike Haken (CC BY-NC 4.0)
- LiDAR (England): contains Environment Agency information © Environment Agency and/or database right
- LiDAR (Scotland): © Crown copyright Scottish Government, SEPA, Fugro, Historic Environment Scotland and partners, via the Scottish Remote Sensing Portal (OGL)
- Historic maps: National Library of Scotland
- Roman Empire map: Digital Atlas of the Roman Empire, Johan Åhlfeldt (CC BY 4.0)
- Geology: contains British Geological Survey materials © UKRI
- Heritage (England): © Historic England, contains OS data © Crown copyright (OGL)
- Scheduled monuments (Scotland): © Historic Environment Scotland, Scottish Charity No. SC045925, © Crown copyright (OGL)
- Scheduled monuments (Wales): Cadw, via DataMapWales (OGL)
- Terrain: Mapzen terrain tiles on AWS Open Data; UK terrain data © Environment Agency 2015; EU-DEM (Copernicus); SRTM/GMTED2010 (USGS)
- Imagery and base maps: © Esri, Maxar, Earthstar Geographics, HERE, Garmin, and the GIS User Community
- Base map: © OpenStreetMap contributors
