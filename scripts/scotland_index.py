"""List the Scottish Remote Sensing Portal's LiDAR DTM files for the viewer (ADR 0019).

The portal's open-data bucket (s3://srsp-open-data, public, CORS *) holds each survey as one
GeoTIFF per OS grid square: 10 km (HY20), 5 km quadrants (NS16NE) or 1 km (NG2104). The viewer
range-reads the files under the view, so it needs to know which squares each survey has. This
lists the bucket (names and sizes only, nothing else is read) and writes docs/data/scot-lidar.json:

  {"base": "...", "sets": [{"name", "dir", "suffix", "squares": "HY20 HY21 ..."}, ...]}

Sets are in drawing order: later ones are drawn over earlier ones where they overlap.

Usage: python3 scripts/scotland_index.py
"""
import json
import re
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

BASE = "https://srsp-open-data.s3.eu-west-2.amazonaws.com/"
OUT = Path(__file__).resolve().parent.parent / "docs" / "data" / "scot-lidar.json"
# drawing order, oldest and coarsest first; HES's archaeological surveys go on top (as in ADR 0006)
ORDER = ["phase-1", "phase-2", "phase-3", "phase-4", "phase-5", "phase-6", "outer-hebrides",
         "orkney-islands-council-23", "national-lidar-programme", "coastal", "hes"]
SKIP = ["/25cm/"]   # the Outer Hebrides are also published at 50 cm, with overviews


def keys(prefix):
    token, out = None, []
    while True:
        q = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if token:
            q["continuation-token"] = token
        x = urllib.request.urlopen(BASE + "?" + urllib.parse.urlencode(q), timeout=60).read().decode()
        out += re.findall(r"<Key>([^<]*)</Key>", x)
        m = re.search(r"<NextContinuationToken>([^<]*)", x)
        if not m:
            return out
        token = m.group(1)


def main():
    sets = []
    for ds in ORDER:
        groups = defaultdict(list)
        for k in keys(f"lidar/{ds}/"):
            if "/dtm/" not in k or not k.lower().endswith(".tif") or any(s in k for s in SKIP):
                continue
            d, f = k.rsplit("/", 1)
            m = re.match(r"([A-Z]{2}\d+(?:[NS][EW])?)(_.*)$", f)
            if not m:
                print("  skipped (name not a grid square):", k)
                continue
            groups[(d + "/", m.group(2))].append(m.group(1))
        for (d, suffix), squares in sorted(groups.items()):
            sets.append({"name": ds, "dir": d, "suffix": suffix, "squares": " ".join(sorted(squares))})
            print(f"{ds:28} {len(squares):5}  {d}*{suffix}")
    OUT.write_text(json.dumps({"base": BASE, "sets": sets}, separators=(",", ":")) + "\n")
    print(f"Wrote {OUT} ({OUT.stat().st_size / 1000:.0f} KB)")


if __name__ == "__main__":
    main()
