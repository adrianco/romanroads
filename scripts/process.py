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

import csv
import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from shapely.geometry import box
from shapely.ops import unary_union

from pleiades import Gazetteer, site_key

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


# --- Pleiades links (issue #1) ----------------------------------------------
# Matching needs the Pleiades CSV dumps (CC BY 3.0) in data/external/pleiades/
# (gitignored). Each run with them rewrites the committed match table and the
# manual-review list; a run without them reuses the committed table, so links
# survive a rebuild from a fresh clone.
PLEIADES = ROOT / "data" / "external" / "pleiades"
PLEIADES_PLACES = PLEIADES / "pleiades-places-latest.csv.gz"
PLEIADES_NAMES = PLEIADES / "pleiades-names-latest.csv.gz"
MATCHES = ROOT / "data" / "pleiades_matches.csv"
UNMATCHED = ROOT / "data" / "unmatched_pleiades.csv"
if PLEIADES_PLACES.exists() and PLEIADES_NAMES.exists():
    gazetteer = Gazetteer(PLEIADES_PLACES, PLEIADES_NAMES, bbox=(-8.7, 49.8, 1.9, 61.0))
    saved_matches = {}
else:
    gazetteer = None
    saved_matches = ({r["key"]: r for r in csv.DictReader(MATCHES.open())} if MATCHES.exists() else {})
match_rows, unmatched_rows = [], []


def link_pleiades(gdf, layer, roman_col, modern_col):
    """Add _pleiades_uri/_title/_basis/_score to a point layer."""
    found = []
    for roman, modern, geom in zip(gdf[roman_col], gdf[modern_col], gdf.geometry):
        if geom is None or geom.is_empty:     # 3 blank Settlement rows (ERRATA S5)
            found.append(None)
            continue
        key = site_key(layer, modern, geom.x, geom.y)
        site = {"key": key, "layer": layer, "modern_name": modern, "roman_name": roman,
                "lon": round(geom.x, 5), "lat": round(geom.y, 5)}
        if gazetteer:
            best, miss = gazetteer.match(roman, modern, geom.x, geom.y)
            if best:
                match_rows.append({**site, **best})
            else:
                unmatched_rows.append({**site, "nearest_title": (miss or {}).get("title"),
                                       "nearest_place_title": (miss or {}).get("place_title"),
                                       "nearest_score": (miss or {}).get("score"),
                                       "nearest_basis": (miss or {}).get("basis"),
                                       "nearest_distance_m": (miss or {}).get("distance_m"),
                                       "nearest_uri": (miss or {}).get("uri")})
        else:
            best = saved_matches.get(key)
        found.append(best)
    gdf["_pleiades_uri"] = [b["uri"] if b else None for b in found]
    gdf["_pleiades_title"] = [b["title"] if b else None for b in found]
    gdf["_pleiades_basis"] = [b["basis"] if b else None for b in found]
    gdf["_pleiades_score"] = [float(b["score"]) if b else None for b in found]
    return sum(b is not None for b in found)


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
n_mil = link_pleiades(mil, "military", "Roman name (if known)", "Modern Name")
sz = write_geojson(mil, "military.geojson")
record("military", "military.geojson", sz, len(mil),
       f"Main site type normalised; _possible flag; per-period Type-* fields; {n_mil} Pleiades links")

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
n_set = link_pleiades(settle, "settlement", "ROMAN NAME", "SITE_NAME")
sz = write_geojson(settle, "settlement.geojson")
record("settlement", "settlement.geojson", sz, len(settle),
       f"TYPE normalised (garble fixed); {n_set} Pleiades links")

if gazetteer:
    pd.DataFrame(match_rows).to_csv(MATCHES, index=False)
    pd.DataFrame(unmatched_rows).to_csv(UNMATCHED, index=False)
    print(f"  Pleiades: {len(match_rows)} matched, {len(unmatched_rows)} for review -> "
          f"{MATCHES.relative_to(ROOT)}, {UNMATCHED.relative_to(ROOT)}")
elif saved_matches:
    print(f"  Pleiades: dumps not downloaded; reused {len(saved_matches)} matches from {MATCHES.relative_to(ROOT)}")
else:
    print("  Pleiades: no dumps and no saved matches; popups fall back to a modern-name search")

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

# --- Itiner-e comparison roads (optional third-party input) ------------------
# Itiner-e static version 2024 (Brughmans, de Soto, Pažout, Bjerregaard Vahlstrup),
# CC BY 4.0, https://doi.org/10.5281/zenodo.17122148. The empire-wide file is not
# committed: download itinere_roads.gpkg to data/external/ to rebuild the subset.
ITINERE = ROOT / "data" / "external" / "itinere_roads.gpkg"
# Britain, minus the Picardy/Normandy coast that a simple box would let in
BRITAIN = box(-8.7, 49.8, 1.9, 61.0).difference(
    unary_union([box(1.45, 49.8, 1.9, 51.1), box(-2.5, 49.0, 1.9, 50.5)]))
if ITINERE.exists():
    it = gpd.read_file(ITINERE).to_crs(epsg=4326)
    it = it[it.intersects(BRITAIN)].copy()              # whole features, not cut
    # Datum fix (ADR 0013): the British segments sit 85-125 m ESE of the RRRA roads in
    # exactly the pattern of OSGB36 latitude/longitude stored as if it were WGS84.
    # Reinterpret them as OSGB36 (EPSG:4277) and convert properly to WGS84.
    it = it.set_crs(epsg=4277, allow_override=True).to_crs(epsg=4326)
    it["geometry"] = shapely.force_2d(it.geometry).apply(round_coords)
    for col in it.columns:
        if col != "geometry":
            it[col] = it[col].apply(clean_text)
    for col in ("Lower_Date", "Low_Date_E", "Upper_Date", "Up_Date_E"):   # 9999 = no date given
        it[col] = it[col].apply(lambda v: None if v is None or v != v or v == 9999 else int(v))
    it = it.drop(columns=["Cons_per_e", "Shape_Leng", "InLine_FID", "MaxSimpTol", "MinSimpTol"])
    it = it.rename(columns={"Descriptio": "Description", "Bibliograp": "Bibliography",
                            "passabilit": "Passability", "Segment_s": "Segment certainty"})
    sz = write_geojson(it, "itinere.geojson")
    record("itinere", "itinere.geojson", sz, len(it),
           "Itiner-e 2024 roads intersecting Britain (CC BY 4.0); source simplified at 1 m; "
           "OSGB36->WGS84 datum fix applied (ADR 0013)")
elif (OUT / "itinere.geojson").exists():
    sz = (OUT / "itinere.geojson").stat().st_size
    n = len(json.loads((OUT / "itinere.geojson").read_text())["features"])
    record("itinere", "itinere.geojson", sz, n, "kept from a previous build (source not downloaded)")

# Comparison layers are fetched only when switched on, so they don't count
# towards the page-load budget (ADR 0002).
ON_DEMAND = {"itinere"}
for key, layer in manifest["layers"].items():
    layer["on_demand"] = key in ON_DEMAND
total = sum(l["bytes"] for l in manifest["layers"].values())
core = sum(l["bytes"] for l in manifest["layers"].values() if not l["on_demand"])
manifest["total_bytes"] = total
manifest["core_bytes"] = core
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))

print(f"\n  TOTAL GeoJSON: {total/1024/1024:.2f} MiB "
      f"(loaded at start: {core/1024/1024:.2f} MiB; on demand: {(total-core)/1024/1024:.2f} MiB)")
print(f"  page load is {'UNDER' if core < 5*1024*1024 else 'OVER'} the ~5 MB single-page threshold")
print(f"\n  Wrote manifest.json")
