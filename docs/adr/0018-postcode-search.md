# 0018 — Postcode search through postcodes.io

**Status:** Accepted

## Context
Search found only the dataset's own names: modern and Roman place names, and
Margary road numbers. People often know where they live, or where they're
going, by postcode. The viewer is a static page with no server and no API keys
([0002](0002-single-page-delivery.md)), so a lookup has to be a free, keyless
service that a browser may call directly.

## What was checked (2026-11-22)
- **[postcodes.io](https://postcodes.io/)**, `api.postcodes.io`:
  - No key, and it sends `Access-Control-Allow-Origin: *`.
  - `GET /postcodes/SW1A%201AA` gives latitude and longitude, parish and
    district.
  - `GET /outcodes/LD7` gives a district's centre and its councils
    (Powys, Shropshire).
  - `GET /postcodes/LD71/autocomplete` gives up to 10 full postcodes.
  - `GET /terminated_postcodes/E1W%201UU` finds a retired postcode and its
    position.
  - An unknown postcode gives `404 Postcode not found`.
- **Licences** (from the project's `docs/licences.mdx`):
  - Great Britain postcode data is under the OS OpenData licence.
  - Northern Ireland (`BT`) data is under the ONSPD licence. Non-commercial
    use is free, which this viewer is.
  - The required statements are "Contains Ordnance Survey data / Royal Mail
    data / National Statistics data / NRS data © Crown copyright and database
    right" (Royal Mail's is © Royal Mail copyright and database right).
- **Usage terms:** no rate limit is documented for the public API. The code is
  MIT-licensed and can be self-hosted if that ever changes.

## Decision
- **What gets sent.** A query is sent only if it starts with one of the 121
  UK postcode areas (`LD`, `SW`, `B`…) followed by a digit. So road numbers
  (`RR2`, `2a`), milecastles (`MC39`) and place names never leave the browser.
  The match covers:
  - a full postcode, with any spacing or case (`ld71aa`);
  - a district (`LD7`);
  - a partial code (`LD7 1`).
- **Results:**
  - **Full postcode:** one result, "LD7 1AA · Postcode · Knighton, Powys".
    If it's retired: "Postcode, no longer in use (2015)".
  - **Unknown postcode:** a "postcode not found" row that can't be chosen.
  - **District:** its centre ("Postcode district · Powys, Shropshire") plus
    the first few full postcodes in it.
  - **Partial code:** the first 8 completions. Each is looked up when chosen.
- **Ordering.** Local matches show at once. The postcode results are put above
  them when postcodes.io answers: 200 ms after typing stops, and only if the
  text hasn't changed. Pressing Enter before the answer arrives waits for it.
- **Choosing a result:**
  - The map flies there (zoom 16 for a postcode, 13 for a district).
  - A blue pin marks the spot.
  - The next postcode moves the pin; clearing the search removes it.
- **Caching:** answers are kept for the session.
- **Credit:** the attribution goes in the panel's credit section.

## Consequences
- **Privacy:** typing a postcode sends it to a third party (postcodes.io, run
  by Ideal Postcodes), so they see which postcodes people look up. Other
  searches stay in the browser.
- **Precision:** a postcode's position is its centroid, typically within a
  street or two. A district's centre is only a rough guide.
- **Coverage:** Crown dependency postcodes (`GY`, `JE`, `IM`) aren't
  recognised. The dataset has no sites there.
- **Dependency:** if postcodes.io is down, the search says "Postcode lookup
  unavailable"; the other searches still work.
