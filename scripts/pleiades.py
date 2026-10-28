"""Match Digital Britannia sites to Pleiades places (issue #1).

The dataset writes Roman names as inscribed (DVROVARIA, VERCOVICIVM) while
Pleiades uses the standard spelling (Durnovaria, Vercovicium), and its site
search is exact-word, so a search link rarely lands. Instead, at build time:

- take the Pleiades places within RADIUS_M of each site,
- compare the site's Roman name with every name Pleiades holds for them
  (place titles and the names table), after normalising both sides the same
  way: accents stripped, lower case, u/v and i/j merged,
- keep the best match at or above ROMAN_THRESHOLD; for a site with no usable
  Roman name, accept a Pleiades title that contains its modern name
  (MODERN_THRESHOLD), e.g. a fort catalogued under its modern place name.

Pleiades: Copyright The Contributors, CC BY 3.0, https://pleiades.stoa.org
"""
from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd
from rapidfuzz import fuzz

RADIUS_M = 2000
ROMAN_THRESHOLD = 80    # rapidfuzz ratio between normalised Roman names
MODERN_THRESHOLD = 90   # token-set ratio of the modern name within a Pleiades title
BASE_URI = "https://pleiades.stoa.org"


def latinise(s):
    """Inscribed spelling -> modern (VERCOVICIVM -> vercovicium); '' if no name."""
    s = str(s or "").lower()
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"\b(possibly|probably|unknown|uncertain)\b", "", s).replace("?", "")
    s = re.split(r"[/,;]", s)[0].strip()
    s = s.replace("qv", "qu").replace("vv", "vu")
    return re.sub(r"v(?=[^aeiou]|$)", "u", s)


def norm(s):
    """Comparison key: no accents, lower case, letters only, u/v and i/j merged."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z ]+", " ", s).replace("v", "u").replace("j", "i")
    return re.sub(r"\s+", " ", s).strip()


# Words that say what a place is, not which place: matching on them would pair
# any two "Roman forts" within 2 km. Dropped before comparing.
GENERIC_LATIN = {"col", "colonia", "portus", "castra", "castrum", "statio", "mansio", "civitas",
                 "municipium", "vicus", "ad"}
GENERIC_MODERN = {"roman", "fort", "fortlet", "fortress", "camp", "camps", "castle", "hill", "hillfort",
                  "fort", "villa", "settlement", "vicus", "site", "temporary", "signal", "station",
                  "possible", "the", "of", "at", "near", "nr", "and", "ancient", "bath", "baths",
                  "farm", "town", "city", "colonia", "civitas", "amphitheatre", "amphitheater"}
# Latin endings differ between sources (BOMIVM vs Itinerary 'Bomio', NIDVM vs 'Nido')
ENDING = re.compile(r"(ium|ion|ios|iae|ia|ae|um|us|is|io|os|on|o|a|e)$")


# Pleiades featureTypes that describe a whole town or military site. Among equal name
# matches these beat monuments within them (Caerwent: 'Venta', not 'Walls of Caerwent').
SITE_TYPES = {"settlement", "fort", "fort-2", "fortlet", "fortified-settlement", "vicus", "station",
              "military-installation-or-camp-temporary", "port", "tower-defensive", "tower-single",
              "hillfort"}


def words(s, generic):
    return [w for w in s.split() if w not in generic and len(w) >= 3]


def word_score(a, b):
    """Similarity of two single words, also comparing their stems without case endings."""
    s = fuzz.ratio(a, b)
    sa, sb = ENDING.sub("", a), ENDING.sub("", b)
    if len(sa) >= 3 and sa == sb:
        return 100.0
    if min(len(sa), len(sb)) >= 4:
        s = max(s, fuzz.ratio(sa, sb))
    return s


def roman_score(site, cand):
    """Whole-name ratio, or the best single distinctive word: the Roman core name
    (VENTA BELGARVM ~ 'Venta', CAMELODVNVM ~ 'Col. Camulodunum')."""
    best = fuzz.ratio(site, cand)
    for a in words(site, GENERIC_LATIN):
        for b in words(cand, GENERIC_LATIN):
            best = max(best, word_score(a, b))
    return best


def modern_score(site, title):
    """Does the Pleiades title name the site's modern place? Generic words removed."""
    a, b = " ".join(words(site, GENERIC_MODERN)), " ".join(words(title, GENERIC_MODERN))
    return fuzz.token_set_ratio(a, b) if a and b else 0.0


def clean_title(title):
    """Pleiades title for display: drop the reconstruction mark and quotes."""
    return re.sub(r"[*‘’']", "", str(title)).strip()


def variants(title):
    """Pleiades titles mark alternatives: '*Vercovicium', 'Londinium/Augusta',
    'Durno(no)varia'. Return each readable spelling."""
    out = set()
    for part in str(title).replace("*", "").replace("?", "").split("/"):
        part = part.strip()
        if not part:
            continue
        out.add(re.sub(r"\(.*?\)", "", part).strip())          # Durnovaria
        out.add(part.replace("(", "").replace(")", "").strip())  # Durnonovaria
    return {v for v in out if v}


class Gazetteer:
    def __init__(self, places_csv, names_csv, bbox):
        w, s, e, n = bbox
        pl = pd.read_csv(places_csv, low_memory=False)
        pl = pl[pl.reprLat.between(s, n) & pl.reprLong.between(w, e)].reset_index(drop=True)
        self.places = pl
        self.lat = np.radians(pl.reprLat.to_numpy())
        self.lon = np.radians(pl.reprLong.to_numpy())
        # every readable name per place: its title plus the names table
        names = {p: set(variants(t)) for p, t in zip(pl.path, pl.title)}
        nm = pd.read_csv(names_csv, low_memory=False)
        nm = nm[nm.pid.isin(names)]
        for col in ("title", "nameTransliterated", "nameAttested"):
            for pid, v in zip(nm.pid, nm[col]):
                if isinstance(v, str) and v.strip():
                    names[pid] |= variants(v)
        self.names = [[(norm(v), v) for v in sorted(names[p]) if norm(v)] for p in pl.path]

    def near(self, lon, lat):
        """Indices and distances (m) of places within RADIUS_M, nearest first."""
        la, lo = np.radians(lat), np.radians(lon)
        a = (np.sin((self.lat - la) / 2) ** 2
             + np.cos(la) * np.cos(self.lat) * np.sin((self.lon - lo) / 2) ** 2)
        d = 2 * 6371008.8 * np.arcsin(np.sqrt(a))
        idx = np.where(d <= RADIUS_M)[0]
        return idx[np.argsort(d[idx])], np.sort(d[idx])

    def match(self, roman, modern, lon, lat):
        """Best Pleiades match for one site, plus the best near-miss for review."""
        idx, dist = self.near(lon, lat)
        key_roman = norm(latinise(roman))
        key_modern = norm(modern or "")
        best, miss = None, None
        for i, d in zip(idx, dist):
            title = self.places.title[i]
            types = {t.strip() for t in str(self.places.featureTypes[i]).split(",")}
            is_site = bool(types & SITE_TYPES)
            for key, shown in self.names[i]:
                cands = []
                if key_roman:
                    cands.append(("roman name", roman_score(key_roman, key), ROMAN_THRESHOLD,
                                  fuzz.ratio(key_roman, key)))
                if key_modern:
                    cands.append(("modern name", modern_score(key_modern, norm(title)), MODERN_THRESHOLD,
                                  fuzz.ratio(key_modern, norm(title))))
                for basis, score, threshold, whole in cands:
                    row = {"uri": BASE_URI + self.places.path[i], "title": clean_title(title),
                           "matched_name": shown, "place_title": title,
                           "score": round(score, 1), "basis": basis, "distance_m": round(float(d))}
                    # prefer a Roman-name match, then score, then a town or fort over a monument
                    # in it, then the place whose whole name fits best (the town 'Deva', not
                    # 'Roman amphitheater at Deva'), then the nearer
                    rank = (basis == "roman name", score, is_site, whole, -d)
                    if score >= threshold:
                        if best is None or rank > best[0]:
                            best = (rank, row)
                    elif miss is None or rank > miss[0]:
                        miss = (rank, row)
        return (best[1] if best else None), (miss[1] if miss else None)


def site_key(layer, name, lon, lat):
    """Stable key for the committed match table (the layers have no shared ID)."""
    return f"{layer}|{name or ''}|{lon:.5f},{lat:.5f}"
