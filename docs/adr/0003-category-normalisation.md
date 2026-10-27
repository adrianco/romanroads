# 0003 — Category normalisation

**Status:** Accepted

## Context
Several category fields are messy (full detail in [ERRATA.md](../ERRATA.md)):
- Military `Main site type`: `Legionary Fortress` vs `Legionary fortress`, and
  the values `Other military site` / `Possible military site`, which the
  author's style doesn't define.
- Settlement `TYPE`: one garbled value
  (`Military vicus - size uncertaMilitary vicus - size uncertainin`).
- Nulls in both fields, and in road `Segment Confidence`.

The viewer needs clean values for symbology and the "possible" toggle. Popups
also show every attribute, so a garbled value would appear there too.

## Decision
- Explicit lookup tables in `scripts/process.py` (`MILITARY_FIX`,
  `SETTLEMENT_FIX`) map each bad value onto one of the author's own style
  categories. There is no fuzzy matching, so every change can be audited.
- Derived properties have a leading underscore: `_type`, `_possible`, `_conf`,
  `_margary`, `_status`, `_feature`.
- The cleaned value is also written back into the display field (`Main site type`,
  `TYPE`) so popups never show the garble. Missing values stay null in the
  display field and become `Unknown` in `_type`.
- `_possible` is true when the normalised type starts with "Possible".
- A null road confidence becomes `_conf = -1` and is hidden by default, the same
  as confidence 0.
- Every text attribute in every layer goes through `clean_text`. It trims
  padding (592 padded values, many of them links), strips `NULL` glued to the
  front of a value (`NULLhttps://…` → `https://…`, 4 cases), and turns a bare
  `NULL` into a real null. Internal double spaces are left alone, because the
  author's style categories depend on them.
- Road numbers are kept exactly as given, including `(x)`, `none-…`, `?` and
  `&` forms. The `none-…` IDs don't get an `RR` label on the map.
- The GeoPackage is never modified.

## Consequences
- The fixes are reproducible and listed in ERRATA.md, so the RRRA can fix the
  source and these tables can then shrink to nothing.
- Popups show cleaned values. Anyone who needs the raw values has the GeoPackage.
