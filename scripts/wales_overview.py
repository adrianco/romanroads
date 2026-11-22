"""Pre-render zoomed-out hillshade tiles for Wales (ADR 0017).

The viewer shades Wales live from DataMapWales' 1 m DTM COG from map zoom 9. Further out, a
view would need most of the COG's 64 m overview (14.4 MB, and the file doesn't skip empty
tiles), so instead those zooms come from small static tiles made here:

- read the 64 m overview with HTTP range requests (in memory, nothing saved),
- shade it on its own grid (one sun from 315° at 30°, Horn gradients, like the viewer),
- average the shaded cells into Web Mercator tiles for zooms 6-9 (shading first, then
  averaging, as the EA's ready-shaded tiles appear to be made),
- write grey + alpha PNGs to docs/tiles/wales/{z}/{x}/{y}.png. Their alpha also tells the viewer
  where Welsh data exists, so it can cut the EA's overlapping tiles out there.

Usage: .venv/bin/python scripts/wales_overview.py [--ex 2.0]
"""
import argparse
import math
import struct
import urllib.request
import zlib
from pathlib import Path

import numpy as np
from pyproj import Transformer

COG = "https://dmwproductionblob.blob.core.windows.net/cogs/lidar/wales_dtm_32bit_cog.tif"
OUT = Path(__file__).resolve().parent.parent / "docs" / "tiles" / "wales"
BOUNDS = (-5.55, 51.32, -2.63, 53.47)   # the COG's extent, lon/lat
ZOOMS = range(6, 10)
SUPER = 6                               # subsamples per pixel side when averaging
MERC = 20037508.342789244


def get(start, end):
    req = urllib.request.Request(COG, headers={"Range": f"bytes={start}-{end}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        assert r.status == 206, r.status
        return r.read()


def parse_header(b):
    assert b[:2] == b"II" and struct.unpack("<H", b[2:4])[0] == 43, "expected a little-endian BigTIFF"
    size = {1: 1, 2: 1, 3: 2, 4: 4, 11: 4, 12: 8, 16: 8}
    fmt = {1: "B", 3: "H", 4: "I", 12: "d", 16: "Q"}
    ifds, off = [], struct.unpack("<Q", b[8:16])[0]
    while off and off + 8 <= len(b):
        n = struct.unpack("<Q", b[off:off + 8])[0]
        tags = {}
        for i in range(n):
            p = off + 8 + i * 20
            tag, typ, count = struct.unpack("<HHQ", b[p:p + 12])
            at = p + 12 if size[typ] * count <= 8 else struct.unpack("<Q", b[p + 12:p + 20])[0]
            tags[tag] = (typ, count, at)
        ifds.append(tags)
        off = struct.unpack("<Q", b[off + 8 + n * 20:off + 16 + n * 20])[0]

    def val(t, k=0):
        typ, _, at = t
        if typ == 2:
            return None
        return struct.unpack("<" + fmt[typ], b[at + size[typ] * k:at + size[typ] * (k + 1)])[0]

    t0 = ifds[0]
    sx, sy = val(t0[33550], 0), val(t0[33550], 1)
    x0 = val(t0[33922], 3) - val(t0[33922], 0) * sx
    y0 = val(t0[33922], 4) + val(t0[33922], 1) * sy
    w0, h0 = val(t0[256]), val(t0[257])
    levels = []
    for t in ifds:
        assert val(t[259]) == 8 and (317 not in t or val(t[317]) == 1), "expected deflate, no predictor"
        levels.append(dict(W=val(t[256]), H=val(t[257]), TW=val(t[322]), TH=val(t[323]),
                           offs=t[324], counts=t[325]))
    return dict(x0=x0, y0=y0, w0=w0, h0=h0, sx=sx, sy=sy, levels=levels)


def read_level(cog, li):
    L = cog["levels"][li]
    across, down = math.ceil(L["W"] / L["TW"]), math.ceil(L["H"] / L["TH"])
    n = across * down
    def table(t):
        typ, count, at = t
        assert count == n
        sz = 8 if typ == 16 else 4
        raw = get(at, at + count * sz - 1)
        return struct.unpack("<%d%s" % (count, "Q" if sz == 8 else "I"), raw)
    offs, counts = table(L["offs"]), table(L["counts"])
    grid = np.full((down * L["TH"], across * L["TW"]), np.nan, dtype=np.float32)
    total = 0
    for row in range(down):
        i0, i1 = row * across, row * across + across - 1
        cols = [c for c in range(across) if counts[i0 + c]]
        if not cols:
            continue
        start, end = offs[i0 + cols[0]], offs[i0 + cols[-1]] + counts[i0 + cols[-1]] - 1
        buf = get(start, end)
        total += len(buf)
        for c in cols:
            o = offs[i0 + c] - start
            tile = np.frombuffer(zlib.decompress(buf[o:o + counts[i0 + c]]), dtype="<f4").reshape(L["TH"], L["TW"])
            grid[row * L["TH"]:(row + 1) * L["TH"], c * L["TW"]:(c + 1) * L["TW"]] = tile
        print(f"  row {row + 1}/{down}, {total / 1e6:.1f} MB", end="\r")
    print()
    grid = grid[:L["H"], :L["W"]]
    grid[(grid <= -1000) | ~np.isfinite(grid)] = np.nan
    return grid


def hillshade(h, cell, ex, az=315.0, el=30.0):
    """Grey 0-255 like the viewer's one-sun hillshade; NaN where there's no data."""
    filled = np.pad(h, 1, mode="edge")   # gaps (NaN) borrow the centre cell, as in the viewer
    c = filled[1:-1, 1:-1]
    def n(dy, dx):
        v = filled[1 + dy:filled.shape[0] - 1 + dy, 1 + dx:filled.shape[1] - 1 + dx]
        return np.where(np.isnan(v), c, v)
    a, b, cc = n(-1, -1), n(-1, 0), n(-1, 1)
    d, f = n(0, -1), n(0, 1)
    g, hh, ii = n(1, -1), n(1, 0), n(1, 1)
    east = ((cc + 2 * f + ii) - (a + 2 * d + g)) / (8 * cell) * ex
    north = ((a + 2 * b + cc) - (g + 2 * hh + ii)) / (8 * cell) * ex
    azr, elr = math.radians(az), math.radians(el)
    lx, ly, lz = math.sin(azr) * math.cos(elr), math.cos(azr) * math.cos(elr), math.sin(elr)
    shade = np.clip((-east * lx - north * ly + lz) / np.sqrt(east ** 2 + north ** 2 + 1), 0, 1) * 255
    return np.where(np.isnan(h), np.nan, shade)


def png(path, grey, alpha):
    h, w = grey.shape
    raw = np.zeros((h, 1 + 2 * w), dtype=np.uint8)
    raw[:, 1::2], raw[:, 2::2] = grey, alpha
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 4, 0, 0, 0)) +
                     chunk(b"IDAT", zlib.compress(raw.tobytes(), 9)) + chunk(b"IEND", b""))


def tile_range(z):
    def tx(lon): return int((lon + 180) / 360 * 2 ** z)
    def ty(lat):
        r = math.radians(lat)
        return int((1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * 2 ** z)
    return range(tx(BOUNDS[0]), tx(BOUNDS[2]) + 1), range(ty(BOUNDS[3]), ty(BOUNDS[1]) + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ex", type=float, default=2.0, help="vertical exaggeration (default 2, as the viewer)")
    ap.add_argument("--level", type=int, default=6, help="COG level to read (6 = 64 m)")
    args = ap.parse_args()

    print("Reading the COG header…")
    cog = parse_header(get(0, 65535))
    L = cog["levels"][args.level]
    cellx, celly = cog["w0"] * cog["sx"] / L["W"], cog["h0"] * cog["sy"] / L["H"]
    print(f"Reading level {args.level}: {L['W']}×{L['H']} cells of {cellx:.1f} m…")
    h = read_level(cog, args.level)
    shade = hillshade(h, cellx, args.ex)
    valid = ~np.isnan(shade)
    shade0 = np.where(valid, shade, 0)

    to_bng = Transformer.from_crs(3857, 27700, always_xy=True)
    written = 0
    for z in ZOOMS:
        xs, ys = tile_range(z)
        size = 2 * MERC / 2 ** z
        for x in xs:
            for y in ys:
                # SUPER² subsamples per pixel, each looked up in the shaded grid (nearest cell)
                n = 256 * SUPER
                f = (np.arange(n) + 0.5) / n
                mx = -MERC + (x + f) * size
                my = MERC - (y + f) * size
                MX, MY = np.meshgrid(mx, my)
                E, N = to_bng.transform(MX, MY)
                col = np.floor((E - cog["x0"]) / cellx).astype(int)
                row = np.floor((cog["y0"] - N) / celly).astype(int)
                inside = (col >= 0) & (col < L["W"]) & (row >= 0) & (row < L["H"])
                col, row = np.clip(col, 0, L["W"] - 1), np.clip(row, 0, L["H"] - 1)
                ok = inside & valid[row, col]
                v = np.where(ok, shade0[row, col], 0)
                s = v.reshape(256, SUPER, 256, SUPER).sum(axis=(1, 3))
                k = ok.reshape(256, SUPER, 256, SUPER).sum(axis=(1, 3))
                grey = np.where(k > 0, s / np.maximum(k, 1), 0).round().astype(np.uint8)
                alpha = np.where(k * 2 >= SUPER * SUPER, 255, 0).astype(np.uint8)   # opaque where mostly data
                if not alpha.any():   # a transparent tile, so the viewer never asks for a missing one
                    png(OUT / str(z) / str(x) / f"{y}.png", np.zeros((256, 256), np.uint8), np.zeros((256, 256), np.uint8))
                    continue
                png(OUT / str(z) / str(x) / f"{y}.png", grey, alpha)
                written += 1
                g = grey[alpha > 0]
                print(f"  z{z}/{x}/{y}: p5/p50/p95 {np.percentile(g, 5):.0f}/{np.percentile(g, 50):.0f}/{np.percentile(g, 95):.0f}")
    print(f"Wrote {written} tiles to {OUT}")


if __name__ == "__main__":
    main()
