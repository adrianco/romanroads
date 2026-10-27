# 0012 — Optional extras: what was added, what was rejected, and why

**Status:** Accepted

## Context
The brief lists optional layers beyond the core three underlays. As with the
core, each one had to be checked before use: its URL, that it returns real
content (a status code alone isn't enough; see ADR 0005), that it's reachable
from an https page with CORS, and its licence. Checked 2026-10-27.

## Added

| Layer | Service | Checks | Licence / credit |
|-------|---------|--------|------------------|
| **Roman Empire map** (underlay) | DARE tiles `https://dh.gu.se/tiles/imperium/{z}/{x}/{y}.png`, z4–11, overzoomed above | PNG, CORS `*`; Latin names line up with the dataset's forts and roads in the north of England | CC BY 4.0 per the University of Gothenburg hosting. An older 2012 statement for the Lund tiles said CC BY-SA 3.0, so the current licence should be confirmed with the DARE project. Credit: Johan Åhlfeldt, DARE |
| **Bedrock geology** (underlay) | BGS 1:625k WMS (`ogc.bgs.ac.uk`, `GBR_BGS_625k_BLT`) below z11; BGS 1:50k WMS (`map.bgs.ac.uk`, `BGS.50k.Bedrock`) from z11 | EPSG:3857, CORS; visually correct at GB scale and at Bath | OGL, "Contains British Geological Survey materials © UKRI [year]" (from the WMS `AccessConstraints`) |
| **3D terrain** | Mapzen Terrarium tiles on AWS Open Data (`elevation-tiles-prod/terrarium`), `raster-dem`, exaggeration 1.5 | PNG, CORS `*`; drapes cleanly at Housesteads | Tilezen attribution list: UK terrain © Environment Agency 2015, EU-DEM (Copernicus), SRTM/GMTED2010 (USGS) |
| **Scheduled monuments (England)** | Historic England ArcGIS Online FeatureServer `National_Heritage_List_for_England_NHLE_v02_VIEW/6`, queried for the current view from z11 | GeoJSON, CORS `*`; returns "Roman town at High Cross" at Venonis | OGL, "© Historic England …, contains OS data" (from the service's `copyrightText`) |
| **Scheduled monuments (Scotland)** | HES designations WMS, layer `2` | PNG, CORS; shows the Antonine Wall corridor | OGL; HES-required attribution string (from its SpatialData.gov.scot record) |
| **Scheduled monuments (Wales)** | DataMapWales WMS `geonode:wom_scheduled_monument` | PNG, CORS `*`; Caerleon polygons | OGL, Cadw (from the layer page) |
| **Aerial mapping: Roman features (England)** | HE AIM FeatureServer `HE_AIM_data/0`, `PERIOD LIKE '%ROMAN%'`, from z14 | 45,483 Roman-period features, 1,798 of them roads; CORS `*` | OGL, "© Historic England" |
| **Pleiades links** | `https://pleiades.stoa.org/search?SearchableText=<name>` in popups of sites that have a Roman name | Returns 200 | (link only) |

### Design notes
- **Historic England layers aren't tiled.** HE publishes FeatureServers only,
  so `loadDynamic()` queries the features in view after each move. Queries
  only run at or above the layer's minimum zoom and only over England. An
  `AbortController` cancels stale requests. Each service has a record cap
  (2,000), and the panel shows "first N in view" when the cap is reached.
- **AIM styling:** a viewer palette by `LAYER`: ditch red, bank green, scarp
  brown, structure grey, extent purple at low opacity. These colours are mine,
  not HE's convention, and the legend gives them.
- **Roman-name spelling:** names in the data are written as inscribed
  (`VERCOVICIVM`). `latinise()` gives the modern form (`Vercovicium`): `qv`→`qu`,
  `vv`→`vu`, `v` before a consonant or at the end of a word → `u`, and it
  strips `?`, "possibly …" and parenthetical notes. It feeds both the Pleiades
  links and search, so `Vercovicium` now finds Housesteads.
- **Ordering:** DARE and geology sit just above the base map, below the aerial
  and historic layers. The scheduled-monument and AIM overlays sit above the
  LiDAR but below Digital Britannia's own layers.

## Rejected

| Candidate | Reason |
|-----------|--------|
| AWMC / CAWM ancient-world tiles | The current host only answers on `http://`; `https://` fails. GitHub Pages is https, so browsers would block the tiles as mixed content. The coastline layer would have been useful around the Fens, the Wash and the Somerset Levels. |
| Canmore (Scotland) site points | The `CANMORE/Canmore_Points` WMS responds, but its layers have no titles, no abstract and no licence or access-constraint statement, so it fails the verify-the-licence rule. |
| Coflein (Wales) | No Coflein / RCAHMW sites layer in the DataMapWales WMS. It only has RCAHMW historic boundary layers. |
| OS Maps API (1:25k Leisure) / OS Open Zoomstack | They need an OS Data Hub key, and the Leisure style needs a paid tier. |
| Bing aerial | Needs a key. |
| Old OS "Map of Roman Britain" editions | Not in the NLS tileset bucket (no `roman` prefix) and no other tiled source found. |
| Heritage Gateway as a layer | Links only. The popups already carry the HER links from the data. |

## Pending
- **Itiner-e** (CC BY 4.0) comparison roads. The smallest usable file in
  Zenodo record 17122148 is `itinere_roads.gpkg` (33.6 MB, empire-wide). The
  plan is to clip it to Britain in `scripts/process.py` and commit only that
  subset. This needs the owner's approval for the download.
