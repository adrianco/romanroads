#!/usr/bin/env python3
"""Process the Digital Britannia v1 GeoPackage into per-layer GeoJSON.

- Reproject every layer from EPSG:27700 (British National Grid) to EPSG:4326.
- NO geometry simplification: every original vertex is kept. Coordinates are
  rounded to 7 decimal places (~1 cm) only.
- Normalise the messy category fields (Military "Main site type",
  Settlement "TYPE"), following the author's QGIS layer_styles categories.
- Write one GeoJSON FeatureCollection per layer to docs/data/, plus a
  manifest.json describing layers, counts and total size.

Data: Digital Britannia v1, (c) Roman Roads Research Association / Mike Haken.
CC BY-NC 4.0. https://roadsofromanbritain.org/digital-britannia/downloads.html
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np
import geopandas as gpd
import shapely

ROOT = Path(__file__).resolve().parent.parent
GPKG = ROOT / "data" / "digital-britannia_v1.gpkg"
OUT = ROOT / "docs" / "data"
OUT.mkdir(parents=True, exist_ok=True)

NDIGITS = 7


def round_coords(geom):
    """Round every coordinate to NDIGITS decimals, keeping all vertices."""
    return shapely.transform(geom, lambda a: np.round(a, NDIGITS))


# --- category normalisation -------------------------------------------------

MILITARY_FIX = {
    "Legionary Fortress": "Legionary fortress",   # capitalisation
    "Other military site": "Other",               # match author's "Other" category
    "Possible military site": "Possible other",
}

SETTLEMENT_FIX = {
    # garbled duplication in the source
    "Military vicus - size uncertaMilitary vicus - size uncertainin":
        "Military vicus - size uncertain",
}


def clean_str(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    s = str(v).strip()
    return s if s else None


NULL_GLUED = re.compile(r"^NULL(?=\S)")


def clean_text(v):
    """Trim padding and drop database-export 'NULL' artefacts from a text value."""
    if not isinstance(v, str):
        return v
    s = NULL_GLUED.sub("", v.strip()).strip()   # 'NULLhttps://…' -> 'https://…'
    return None if s == "" or s.upper() == "NULL" else s


def read_layer(name):
    gdf = gpd.read_file(GPKG, layer=name)
    gdf = gdf.to_crs(epsg=4326)
    gdf["geometry"] = gdf["geometry"].apply(round_coords)
    for col in gdf.columns:
        if col != "geometry":   # clean_text passes non-strings through unchanged
            gdf[col] = gdf[col].apply(clean_text)
    return gdf


def write_geojson(gdf, filename):
    path = OUT / filename
    # Coordinates are pre-rounded; COORDINATE_PRECISION keeps the writer from
    # re-expanding them into floating-point noise.
    gdf.to_file(path, driver="GeoJSON", COORDINATE_PRECISION=NDIGITS)
    return path.stat().st_size


manifest = {
    "source": "Digital Britannia v1",
    "attribution": "Data: Digital Britannia v1, © Roman Roads Research "
                   "Association / Mike Haken",
    "licence": "CC BY-NC 4.0",
    "url": "https://roadsofromanbritain.org/digital-britannia/downloads.html",
    "crs": "EPSG:4326",
    "simplified": False,
    "coordinate_precision": NDIGITS,
    "layers": {},
}


def record(key, filename, size, count, note=""):
    manifest["layers"][key] = {
        "file": f"data/{filename}",
        "bytes": size,
        "features": int(count),
        "note": note,
    }
    print(f"  {key:28} {count:5} feats  {size/1024:8.1f} KiB  {filename}")


print("Processing Digital Britannia v1 -> docs/data/\n")

# --- Engineered Roman roads --------------------------------------------------
roads = read_layer("Engineered Roman roads")
roads = roads.rename(columns={"Road number ": "Road number"})
conf = roads["Segment Confidence"]
roads["_conf"] = conf.apply(lambda v: int(v) if v is not None and not (isinstance(v, float) and math.isnan(v)) else -1)
roads["_margary"] = roads["Road number"].apply(clean_str)
roads["_name"] = roads["Road name (if any)"].apply(clean_str)
sz = write_geojson(roads, "roads.geojson")
record("roads", "roads.geojson", sz, len(roads),
       "Segment Confidence 3/2/1/0; -1 = unspecified (hidden by default)")

# --- Military Installations --------------------------------------------------
mil = read_layer("Military Installations")
mil["Main site type"] = mil["Main site type"].apply(clean_str)
mil["_type"] = mil["Main site type"].apply(
    lambda v: MILITARY_FIX.get(v, v) if isinstance(v, str) else "Unknown")
mil["_possible"] = mil["_type"].apply(
    lambda v: isinstance(v, str) and v.lower().startswith("possible"))
# write the cleaned value back into the displayed field (null where missing)
mil["Main site type"] = mil["_type"].apply(lambda v: None if v == "Unknown" else v)
sz = write_geojson(mil, "military.geojson")
record("military", "military.geojson", sz, len(mil),
       "Main site type normalised; _possible flag; per-period Type-* fields")

# --- Temporary Camps ---------------------------------------------------------
camps = read_layer("Temporary Camps")
camps["Camp type"] = camps["Camp type"].apply(clean_str)
camps["_type"] = camps["Camp type"].apply(lambda v: v if isinstance(v, str) else "Unknown")
camps["_possible"] = camps["_type"].apply(
    lambda v: isinstance(v, str) and v.lower().startswith("possible"))
sz = write_geojson(camps, "camps.geojson")
record("camps", "camps.geojson", sz, len(camps), "Camp type; _possible flag; Area (Ha)")

# --- Settlement --------------------------------------------------------------
settle = read_layer("Settlement")
settle["TYPE"] = settle["TYPE"].apply(clean_str)
settle["_type"] = settle["TYPE"].apply(
    lambda v: SETTLEMENT_FIX.get(v, v) if isinstance(v, str) else "Unknown")
# write the de-garbled value back into the displayed field (null where missing)
settle["TYPE"] = settle["_type"].apply(lambda v: None if v == "Unknown" else v)
sz = write_geojson(settle, "settlement.geojson")
record("settlement", "settlement.geojson", sz, len(settle), "TYPE normalised (garble fixed)")

# --- milestones --------------------------------------------------------------
miles = read_layer("milestones")
sz = write_geojson(miles, "milestones.geojson")
record("milestones", "milestones.geojson", sz, len(miles), "inscription, translation, image links")

# --- Hadrian's Wall milecastles ---------------------------------------------
mc = read_layer("Hadrians_Wall_milecastle")
mc["_status"] = mc["Status"].apply(clean_str)
sz = write_geojson(mc, "milecastles.geojson")
record("milecastles", "milecastles.geojson", sz, len(mc), "Status Confirmed/Assumed")

# --- Antonine and Hadrian's Walls -------------------------------------------
walls = read_layer("Antonine and Hadrian's Walls")
walls["_feature"] = walls["Feature"].apply(clean_str)
sz = write_geojson(walls, "walls.geojson")
record("walls", "walls.geojson", sz, len(walls), "Feature: wall / ditch / vallum")

total = sum(l["bytes"] for l in manifest["layers"].values())
manifest["total_bytes"] = total
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))

print(f"\n  TOTAL GeoJSON: {total/1024/1024:.2f} MiB")
print(f"  {'UNDER' if total < 5*1024*1024 else 'OVER'} the ~5 MB single-page threshold")
print(f"\n  Wrote manifest.json")
