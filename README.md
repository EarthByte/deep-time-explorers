# Deep Time Explorers

<p align="center"><img src="logo.png" alt="Deep Time Explorers -- AuScope and GPlates, topped with a graduation cap" width="360"></p>

A **Year 4 (~9–10 years old)** spin-off of the main [GPlately + pyGMT tutorial
suite](https://github.com/EarthByte/GPlately-pyGMT-tutorials), built around the same real EarthByte plate-reconstruction
data — but with none of the install complexity. No pyGMT, no GPlately, no
pygplates on the student's own machine: just `numpy`, `pandas`, `matplotlib`
and `ipywidgets`.

**Status: prototype, not yet classroom-tested.**

## Why this exists

A Year 4 teacher and EarthByte alumnus has been running his own
ocean-current particle-tracking notebook with his class. That sparked the idea
for a plate-tectonics sibling: same spirit (real code, real data, highly
visual, age-appropriate), built around this repository's deep-time plate
reconstructions instead.

An early version of this ran as live Jupyter notebooks in the browser
(JupyterLite, below) — which turned out to be too cognitively demanding
for a primary-school audience, and a real ipywidgets/JupyterLite bug meant
some sliders silently stopped updating. The missions below are the fix:
the same real data and the same mission structure, with every map baked in
ahead of time instead of computed live, so there's no code, no cells, and
no kernel that can get stuck.

## Try the missions

Six short, self-contained web pages — pick one and start dragging the
slider, nothing to install or run:

**[→ Open the missions](https://earthbyte.github.io/deep-time-explorers/missions/index.html)**
*(live once GitHub Pages is switched on for this repo — see 'Running it' below).*

| # | Mission | Big idea |
|---|---|---|
| 1 | Continents on the Move | A time slider redraws the continents — real paleo-elevation, real plate boundaries, and real plate-velocity arrows — from 300 Ma to today |
| 2 | The Jigsaw Continents | South America and Africa's coastlines fit together — Wegener's own evidence, plus a real mountain belt stitching them |
| 3 | Where the Ground Shakes | 246 real earthquakes, switched on and off over today's real plate boundaries |
| 4 | Follow the Duck through Deep Time | A simplified 'duck' journey shows how an ocean gateway opening changes the shortest sea route |
| 5 | Postcard from Deep Time | Pick an Australian town and an age, get a postcard of where it used to sit |
| 6 | Fossil Climate Detectives | Real fossil and rock climate clues — coal swamps, desert dunes, crocodile fossils — plotted through six deep-time ages |

These are built straight from the same reconstructions as the six research
notebooks below — same coordinates, same datasets, no separate simplified
copy of the science. The notebooks stay as the citable, inspectable 'how
it's built' layer; the missions are what a classroom actually opens.

## The six notebooks

| # | Notebook | Big idea |
|---|---|---|
| 1 | `01_Continents_on_the_Move.ipynb` | A time slider redraws the continents — real paleo-elevation, real plate boundaries, and a second map of real plate-velocity arrows — from 300 Ma to today |
| 2 | `02_The_Jigsaw_Continents.ipynb` | South America and Africa's coastlines fit together — Wegener's own evidence, plus a real mountain belt stitching them |
| 3 | `03_Where_the_Ground_Shakes.ipynb` | Real earthquake locations plotted against plate boundaries, with ridges and subduction zones drawn on top of the dots for a clear view of both |
| 4 | `04_Follow_the_Duck_through_Deep_Time.ipynb` | A simplified "duck" journey shows how an ocean gateway opening changes flow — a deep-time cousin of an ocean-current particle-tracking activity |
| 5 | `05_Postcard_from_Deep_Time.ipynb` | Pick an Australian town and an age, get a postcard showing where it used to be |
| 6 | `06_Fossil_Climate_Detectives.ipynb` | Real fossil and rock climate clues — coal swamps, desert dunes, crocodile fossils — plotted as picture icons through deep time |

Each notebook is self-contained, short, heavily commented, and ends with a
"Try this next!" section for kids who want to push further.

## What the maps look like

Every map in this suite is a **real, properly-projected map**, not a flat
cartoon — and every background is built by reusing the main tutorial
suite's own `gplately.PlotTopologies` plotting layer (the same pattern
demonstrated in `T01_Hello_Deep_Time.ipynb`'s Cartopy cell), not a
from-scratch reimplementation:

- Notebooks 1, 3, 5 and 6 use a full-globe **Robinson projection** with a
  latitude/longitude graticule — the same kind of "properly curved" world map
  used in atlases.
- Notebooks 2 and 4 use a simple, zoomed-in latitude/longitude crop of just
  the region that matters (the Atlantic; the Southern Ocean).
- **Every** background shows real **bathymetry and topography** — how deep
  the ocean floor and how high the land actually stood at that point in
  time — from the [Scotese & Wright (2018) PaleoDEM](https://zenodo.org/records/5460860)
  dataset, coloured with a hypsometric/bathymetric scheme in the same spirit
  as this suite's own house convention (`T43_Geochem_Corrected_Paleo_
  Elevation.ipynb` uses GMT's "earth" cpt for the same purpose). Blues are
  ocean depth, green/tan/brown/white are land elevation — mid-ocean ridges
  and deep trenches are visible on the sea floor itself, not just implied.
- The continent outlines drawn on top of that DEM use the **Scotese &
  Wright (2018) plate model itself** (`scotese_and_wright2018`, via
  `plate_model_manager`) — not this suite's usual `Zahirovic2022` — because
  that's the model the DEM was built from. A different model's coastlines
  don't land in the same place at a given age, especially in deep time; the
  continent outline has to come from the DEM's *own* plate model for the
  two to actually line up. **Every** background also has real **plate
  boundaries** drawn on it, reconstructed to that exact age, typed by kind
  using `gplately`'s own `plot_ridges` / `plot_transforms` / `plot_trenches`
  methods: red for spreading ridges, orange for transforms, a thick
  dark-blue line for subduction zones — so Notebook 1 (which is *about*
  plates) actually shows the plates' edges, and the ridge/trench lines
  usually line up visibly with real bathymetric highs and lows underneath
  them. (Subduction zones use `plot_trenches`, not gplately's directional
  `plot_subduction_teeth` — this model's topology doesn't carry the
  resolved polarity that teeth need, so that method silently draws nothing
  for `scotese_and_wright2018`.) This only
  works for ages of **100 million years or
  more recent** — the Scotese & Wright model's plate-boundary topology
  doesn't resolve any further back than that (its continent outlines do,
  across the whole 0-410 Ma range this suite uses) — so basemaps older than
  100 Ma show a correctly-aligned coastline with no boundary lines on top.
- Notebook 1 also has a **plate-velocity map**: real direction-and-speed
  arrows for every age on its slider, straight from `gplately`'s own
  `plot_plate_motion_vectors` method (the same one demonstrated in
  gplately's own official `04-VelocityBasics.ipynb` example) — so kids can
  see which plates are racing along and which are barely moving, not just
  infer it from the boundary story. A reference arrow in the corner gives
  a real speed to check against, and every age uses the same arrow scale,
  so lengths are directly comparable across the whole time slider.
- Notebook 6's fossil "climate clues" are drawn as **hand-made picture icons**
  (a coal-forest conifer, a palm tree, a crocodile, a desert dune — plus a
  snowflake, defined but switched off by default, see below) built entirely
  from `matplotlib` shapes — no image files, no fonts, no internet
  connection needed, and they render identically on every computer. The
  map has its own legend row underneath it (not overlapping the globe) that
  reuses these exact same icon-drawing functions (not a separate matplotlib
  auto-legend) so what's in the legend always matches what's on the map.

### A design note on Notebook 6's data

Notebook 6 uses the climate-sensitive-lithology dataset from Boucot, Xu &
Scotese (2013) — the same dataset the main suite's `T62_Boucot_Climate_
Sensitive_Lithologies.ipynb` uses, simplified from its 15 rock/fossil
categories down to a handful of kid-friendly climate types. A few things
worth knowing:

- **There's no literal "coral" category.** Boucot's categories don't include
  coral reefs, so Notebook 6 doesn't have a coral icon — the crocodile icon
  (his "warm temperate" group, which also covers palms and mangroves) is the
  closest real match to "warm and wet." Real coral/reef occurrence data does
  exist in the main suite (see `T57_Reef_Builders_Paleolatitude.ipynb` and
  `T60_PBDB_Paleobiogeography.ipynb`, both PBDB-sourced) — folding that in as
  a real 6th icon is good future work, not done here.
- **The "cold" (ice-age) category is in the data but not switched on by
  default.** Across the six rock-clue ages, cold-climate points range from
  0 to 21 out of totals in the hundreds — genuinely rare, and the basemap's
  elevation-based colouring doesn't depict ice sheets either, so a lone
  snowflake had little visual context to land on. `draw_snowflake` is still
  defined in the notebook; "Try this next!" invites kids to add
  `"cold": draw_snowflake` back into `CLIMATE_ICON` themselves. (The
  "warm temperate"/crocodile bin is similarly rare — 0 points at three of
  the six ages, 2–5 at the rest — but it stays switched on since a
  reflection question is already built around it; see the redrawn
  `draw_crocodile` note just below.)
- **The crocodile icon has a jagged back ridge and a visible jaw line** —
  the features that read most clearly as "crocodile" rather than a generic
  shape at small size — with the eye placed at the head end.
- **Notebook 6 uses the same Scotese & Wright (2018) model/frame as its own
  basemap** (mantle frame, anchor 0 — the same as Notebooks 1–5's basemaps),
  so the climate-clue points always land on the continent shown underneath
  them, at every age.
- **The time slider goes all the way to today (0 Ma), on purpose without
  fake data.** There's no real Boucot rock-clue data for the present day —
  that dataset exists specifically to infer a climate nobody could observe
  directly — so rather than invent a fake "today" data point, the 0 Ma
  frame shows an icon-free map with a short note explaining why: we don't
  need rock clues for a climate we can just look outside and see.

## Curriculum links (NSW / Australian Curriculum v9)

- **NSW Science and Technology K–6, Stage 2, Earth and Space** — natural
  processes that change Earth's surface (currently framed around erosion;
  plate tectonics is the more dramatic companion story).
- **AC9S4U02** (Year 4 Science) — the water cycle, including movement of
  water through the ocean — the direct peg for Notebook 4.
- **AC9S4I04** (Year 4 Science Inquiry Skills) — constructing and using
  representations (tables, graphs, visual models) to show patterns — what
  every notebook here actually does.
- **AC9TDI4K03** (Digital Technologies, Years 3–4) — recognising that the
  same data can be represented differently. Note: real Python/Jupyter is
  *above* the formal Years 3–4 Digital Technologies expectation (which
  targets visual programming) — pitch this as science/numeracy enrichment,
  not core DT coverage.

## Running it

### One-time setup (a grown-up does this once)

The student notebooks need a handful of small data files that don't exist
yet in a fresh checkout — they're generated from the real plate model using
`export_data.py`. From a terminal, in your existing `gplately` conda
environment:

```bash
conda activate gplately
python export_data.py
```

This is designed to sit as a sibling folder to the main
[`GPlately-pyGMT_tutorials`](https://github.com/EarthByte/GPlately-pyGMT-tutorials)
checkout on disk — if it finds `../GPlately-pyGMT_tutorials/gplately_data`,
it reuses the `Zahirovic2022` model already cached there (no re-download).
If that folder isn't there (e.g. this repo has been cloned somewhere else
entirely), it falls back to its own local `gplately_data/` cache and
downloads the model once (~50 MB). It also downloads a second, smaller
model — `scotese_and_wright2018` (~12 MB) — into this repo's own local
`gplately_data/` cache regardless of whether the sibling folder is found;
that one's used only for drawing continents/plate boundaries on the
basemaps, to match the plate model the PaleoDEM itself was built from (see
"What the maps look like" above). Either way, output goes to `data/`. It
also fetches a small real earthquake catalogue from the public USGS service
(falls back to a short built-in list if there's no internet at the time).
Re-run it any time you add a town to the list inside the script.

**New requirement for the map backgrounds and Notebook 6**: the script also
needs the real [Scotese & Wright (2018) PaleoDEM](https://zenodo.org/records/5460860)
grids and the Boucot 2013 lithology tables, both of which already live in
the main suite's large-data archive at
`../GPlately-pyGMT_tutorials/zenodo_data/paleoDEM_ScoteseWright2018/` and
`../GPlately-pyGMT_tutorials/data/Boucot2013_Lithology_Data_Tables/`. If
you're running this from a fresh checkout of the main suite, make sure
you've unzipped its Zenodo companion archive first (see that repo's
README) — `export_data.py` will raise a clear error naming the missing
folder if it can't find these.

`cartopy`, `xarray` and `netCDF4` (used only by this script, never by the
student notebooks) are already listed in the main suite's `environment.yml`.

### For students

Once `data/` is populated, each notebook runs standalone with nothing beyond
a normal Jupyter install (`pip install ipywidgets` if it isn't already
there). No conda environment, no GPlately, no cartopy, no internet
connection needed.

### Zero-install notebook lab (the research layer, not the classroom one)

For anyone who wants to run the actual research notebooks in a browser —
not the missions above, the real `ipywidgets`-driven notebooks — this
suite is also packaged as a static
**[JupyterLite](https://jupyterlite.readthedocs.io/)** site: the same six
notebooks running entirely in the browser on **Pyodide** (a full Python
interpreter compiled to WebAssembly). `numpy`, `pandas`, `matplotlib` and
`ipywidgets` all run exactly as they do in a normal notebook — no server,
no accounts, no local install, nothing to break.

This is *not* the recommended path for a classroom — see 'Try the
missions' above for that, and 'Why this exists' for why. It's here for
anyone who wants to see, tweak, or re-run the real analysis code itself.

**[Open the notebook lab](https://earthbyte.github.io/deep-time-explorers/lab/index.html)**
*(live once GitHub Pages is switched on for this repo — see below).*

`.github/workflows/deploy-jupyterlite.yml` rebuilds and redeploys this site
automatically on every push to `main`, straight from the same six root
notebooks and the `data/` folder above — there's no separate hand-maintained
copy of the notebooks to keep in sync. The only one-time step is turning
Pages on: **Settings → Pages → Source: GitHub Actions**. After that the link
above goes live and stays current automatically.

## Data files (generated, not hand-edited)

| File | Used by | Contents |
|---|---|---|
| `data/basemap_<age>Ma.png` (×13: 0, 15, 50, 80, 100, 150, 155, 200, 240, 250, 300, 330, 410 Ma) | 1, 3, 5, 6 | Real bathymetry+topography, real plate boundaries (ridges/transforms/subduction zones), full-globe Robinson projection + graticule |
| `data/basemap_subduction_0Ma.png` | 3 | Same Robinson basemap/extent as `basemap_0Ma.png`, but with ONLY the subduction-zone line drawn (no ridges/transforms) — the backdrop for Notebook 3's earthquake map, so the vector ridge/subduction overlays plotted on top aren't competing with a busier background |
| `data/subduction_zones_0Ma.csv` | 3 | Real subduction-zone (trench) line geometry as plain lon/lat + Robinson x/y, one row per vertex, grouped by `segment_id` (~38 disconnected lines) — plotted in the notebook itself, in dark blue, on top of the earthquake dots, so the line can't be buried by markers drawn after it |
| `data/ridges_0Ma.csv` | 3 | Real mid-ocean-ridge (spreading boundary) line geometry, same shape as `subduction_zones_0Ma.csv` (~26 segments) — plotted alongside it, in red, on top of the earthquake dots |
| `data/velocity_<age>Ma.png` (×7: 0, 50, 100, 150, 200, 250, 300 Ma) | 1 | Real plate-velocity arrows (direction + speed) at each age, plain continents/coastlines/boundaries background, full-globe Robinson projection |
| `data/basemap_atlantic_<age>Ma.png` (0, 300 Ma) | 2 | Same, zoomed to the Atlantic region |
| `data/basemap_southern_ocean_<age>Ma.png` (0, 60 Ma) | 4 | Same, zoomed to the Southern Ocean |
| `data/land_<age>Ma.geojson` (×7, ages 0–300 Ma) | — | Simplified land polygons; kept for reference, no longer used by any notebook now that real elevation backgrounds exist |
| `data/towns_through_time.csv` | 5 | Reconstructed positions (lat/lon + Robinson x/y) of ~11 Australian places at each age, using the same `scotese_and_wright2018` model + reconstruction as the basemap it's plotted on |
| `data/notable_earthquakes.csv` | 3 | M ≥ 7.5 earthquakes since 1970 (USGS) with Robinson x/y, or a small static fallback |
| `data/fossils_through_time.csv` | 6 | Boucot 2013 climate-sensitive lithology points, reconstructed with the same `scotese_and_wright2018` model as the basemap, at 6 ages, with climate bin + Robinson x/y |
| `data/duck_path.csv` | 4 | The duck's ocean-only shortest-path route (Dijkstra over real PaleoDEM elevation, land excluded by construction) at 2 ages, with lat/lon + Robinson x/y per step |
| `data/postcard_<town>_<age>Ma.png` | 5 | Whichever postcard(s) you generate by running Notebook 5 — saved alongside the rest of this suite's generated pictures rather than at the top level of the repo |

## License

The notebooks and scripts in this repository are released under the [MIT
License](LICENSE). The underlying scientific datasets (below) are each
under their original source's own terms, not this repository's license.

## Attribution

Developed by the EarthByte Group, University of Sydney, in the same spirit
as the main [GPlately-pyGMT tutorial suite](https://github.com/EarthByte/GPlately-pyGMT-tutorials) — see that
repository's own [CONTRIBUTORS.md](https://github.com/EarthByte/GPlately-pyGMT-tutorials/blob/main/CONTRIBUTORS.md).

Paleo-elevation data: Scotese, C.R. & Wright, N. (2018). PALEOMAP PaleoDEM
Elevation Models. Zenodo. https://doi.org/10.5281/zenodo.5460860

Climate-sensitive lithology data: Boucot, A.J., Xu, C. & Scotese, C.R.
(2013). *Phanerozoic Paleoclimate: An Atlas of Lithologic Indicators of
Climate*. SEPM Concepts in Sedimentology and Paleontology No. 11.
https://doi.org/10.2110/sepmcsp.11
