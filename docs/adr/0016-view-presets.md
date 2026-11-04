# 0016 — Four view presets; detailed settings collapsed

**Status:** Accepted

## Context
By issue #3 the panel had grown to about 40 controls (base maps, six
underlays with sliders, the live-DTM modes, 3D sliders, overlays, roads, sites,
period, and a long legend). Feedback: too many options to start with.

## Decision
- **Preset buttons** sit under the search box, from plainest to richest. Each
  one resets every panel setting to its default, then applies its own:

  | Preset | Settings |
  |---|---|
  | **LiDAR** | The defaults: EA ready-shaded hillshade at 60% under the roads and sites. |
  | **Old maps** | NLS OS 6-inch 2nd edition at 85% under the LiDAR at 45%. The map is drawn under the hillshade, so at 70% LiDAR it was barely visible. |
  | **Earthworks** | Live 1 m DTM, local relief model at 85%; scheduled monuments and HE Roman aerial mapping on. |
  | **3D** | 3D terrain (1 m EA heights) at 2×, tilted to 60°, with the live one-sun hillshade at 80%. Multi-direction looked flat at a tilt. |

- **Collapsed sections:** everything else moves into a collapsed **All layers
  and settings** section, and the legend into a **Legend** section that starts
  open on desktop and folded on phones.
- **Highlighting:** the active preset is highlighted, with a one-line
  description under the buttons. Changing any setting by hand marks the view
  "custom", unless the result matches a preset.
- **Share links:** presets write the same query string as manual changes
  ([0015](0015-live-dtm.md)). A link whose settings match no preset opens
  *All layers and settings*, so the reader can see what's switched on.

## Consequences
- **Discovery:** the panel opens with search, four buttons and two collapsed
  headings. Finding a specific layer takes one extra click.
- **Turning presets off:** a preset switches off anything it doesn't name,
  including 3D (which returns the camera to flat and north-up) and the
  Itiner-e comparison.
