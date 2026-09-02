"""
Deep Time Explorers — data export script.

Run this ONCE (or whenever you want to add a town or change the age list)
from inside your `gplately` conda environment. It uses the real GPlately /
pygplates / cartopy stack to precompute everything the six student
notebooks need, and writes plain CSV / GeoJSON / PNG files into ./data/.
The student notebooks never touch gplately, pygplates, pyGMT, or cartopy
themselves — this script is the only bridge between the "grown-up"
scientific stack and the classroom-safe notebooks.

Usage (from anywhere):
    conda activate gplately
    python export_data.py

Requires: gplately, pygplates, plate_model_manager, geopandas, pandas,
numpy, cartopy, xarray, netCDF4 — all already in this repo's
environment.yml. No pyGMT needed.

--- Map backgrounds (new in v1.1) --------------------------------------
Two kinds of background image are rendered from the real Scotese & Wright
(2018) PaleoDEM grids (paleo-elevation, not just a flat land/ocean mask):

  * render_basemap_robinson(age)  -> data/basemap_<age>Ma.png
    A full-globe Robinson projection with a lat/lon graticule. Because a
    global Robinson map's plot extent is a *fixed* constant regardless of
    what's drawn on it, every notebook that uses these backgrounds shares
    the same ROBINSON_EXTENT tuple (defined below) to correctly place
    overlays with plain matplotlib — no cartopy import required student-side.
    Any point data plotted on top of a Robinson basemap (towns, earthquakes,
    plate boundaries, fossils) is therefore pre-projected into Robinson
    x/y metres here, once, and shipped as extra columns/files.

  * render_basemap_regional(age, extent) -> data/<name>.png
    A simple equirectangular (PlateCarree) crop for the two notebooks that
    zoom into one region (the Jigsaw continents, the Duck's Southern Ocean).
    PlateCarree's data coordinates ARE plain longitude/latitude, so no
    reprojection of overlay data is needed for these two notebooks.

  * render_basemap_subduction_only(age) -> data/basemap_subduction_<age>Ma.png
    (new in v1.3) Same Robinson basemap as render_basemap_robinson, same
    AX_POS/ROBINSON_EXTENT calibration (so it overlays with existing
    Robinson x/y data with zero extra work), but with ONLY the
    subduction-zone (trench) line drawn -- no ridges, no transforms. Built
    for Notebook 3, which pairs this against the full boundary map so kids
    can see earthquakes line up on subduction zones specifically, not just
    "some line or other."
"""
import csv
import json
import re
import urllib.request
import urllib.error
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import gplately
from plate_model_manager import PlateModelManager

# ---------------------------------------------------------------------------
# Paths — resolved relative to this script, so it works from any cwd.
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent  # this repo's own root
OUT_DIR = HERE / "data"
OUT_DIR.mkdir(exist_ok=True)

# Reuses the plate model already cached for the main tutorial suite, if this
# repo is sitting as a sibling folder to GPlately-pyGMT_tutorials on disk (the
# normal layout) -- no re-download needed. Falls back to a local cache (one
# ~50 MB download) if that sibling folder isn't found, e.g. this repo has
# been cloned somewhere else on its own.
MODEL_NAME = "Zahirovic2022"
_SIBLING_REPO = HERE.parent / "GPlately-pyGMT_tutorials"
_SIBLING_CACHE = _SIBLING_REPO / "gplately_data"
if _SIBLING_CACHE.exists():
    MODEL_DATA_DIR = _SIBLING_CACHE
else:
    MODEL_DATA_DIR = HERE / "gplately_data"

# The Scotese & Wright (2018) PALEOMAP plate model -- the SAME reconstruction
# used to build the Scotese & Wright (2018) PaleoDEM grids every basemap in
# this suite is coloured from (see PALEODEM_DIR below). Used ONLY to draw
# continents/plate boundaries on TOP of that DEM, so the coastline actually
# lines up with the elevation data underneath it. Drawing continents from a
# *different* plate model (this suite originally used Zahirovic2022 for
# everything) produces a real, visible misalignment -- two different models'
# idea of where a coastline sits at a given age simply don't agree pixel-for-
# pixel, especially in deep time. Kept in its own local cache (not the main
# suite's shared cache) since the main suite has no other use for it.
MODEL_NAME_SW = "scotese_and_wright2018"
MODEL_DATA_DIR_SW = HERE / "gplately_data"

# This model's topological plate-boundary network (ridges/transforms/
# subduction zones) only resolves for ages <= 100 Ma -- older ages raise
# "No feature(s) to convert" from pygplates (confirmed directly, not
# assumed). Continent outlines themselves resolve fine across the whole
# 0-410 Ma range this suite uses, so basemaps beyond 100 Ma still get a
# correctly-aligned coastline, just without typed boundary lines on top.
# This is also exactly why this model is NOT used for the velocity map
# (render_velocity_robinson) -- that map needs continuous topology across
# the whole time slider, which this model doesn't have; Zahirovic2022 is
# used there instead.
BOUNDARY_MAX_AGE_SW = 100

# The real Scotese & Wright (2018) PaleoDEM grids (1 degree, 5 Myr cadence)
# live in the main tutorial suite's large-data Zenodo archive. This script
# can only render real paleo-elevation backgrounds if that archive is
# unzipped there — see the README for how to get it. There's no local
# fallback for this one (it's ~10 MB total for the files we need, but the
# archive itself isn't bundled with either repo).
PALEODEM_DIR = _SIBLING_REPO / "zenodo_data" / "paleoDEM_ScoteseWright2018"

# age (Ma) -> exact filename, for every age used anywhere in this suite.
# (Confirmed to exist in the Scotese & Wright 2018 1-degree/5-Myr archive.)
PALEODEM_FILES = {
    0:   "Map01_PALEOMAP_1deg_Holocene_0Ma.nc",
    15:  "Map06_PALEOMAP_1deg_Middle_Miocene_15Ma.nc",
    50:  "Map13_PALEOMAP_1deg_Early_Eocene_50Ma.nc",
    60:  "Map15_PALEOMAP_1deg_Paleocene_60Ma.nc",
    80:  "Map19_PALEOMAP_1deg_Late_Cretaceous_80Ma.nc",
    100: "Map23_PALEOMAP_1deg_Early_Cretaceous_100Ma.nc",
    150: "Map33_PALEOMAP_1deg_Late_Jurassic_150Ma.nc",
    155: "Map34_PALEOMAP_1deg_Late_Jurassic_155Ma.nc",
    200: "Map43_PALEOMAP_1deg_Late_Triassic_200Ma.nc",
    240: "Map47_PALEOMAP_1deg_Middle_Triassic_240Ma.nc",
    250: "Map49_PALEOMAP_1deg_Permo-Triassic Boundary_250Ma.nc",
    300: "Map57_PALEOMAP_1deg_Late_Pennsylvanian_300Ma.nc",
    330: "Map62_PALEOMAP_1deg_Late_Mississippian_330Ma.nc",
    410: "Map71_PALEOMAP_1deg_Early_Devonian_410Ma.nc",
}

# Same age ladder used across Notebooks 1, 3, 5 (0 Ma = today).
AGES_MA = [0, 50, 100, 150, 200, 250, 300]

# A small, geographically spread set of Australian places for Notebook 5.
# Add your own here and re-run this script to make them selectable.
TOWNS = {
    "Sydney":      (-33.8688, 151.2093),
    "Austinmer":   (-34.2967, 150.9280),
    "Melbourne":   (-37.8136, 144.9631),
    "Brisbane":    (-27.4698, 153.0251),
    "Perth":       (-31.9523, 115.8613),
    "Adelaide":    (-34.9285, 138.6007),
    "Darwin":      (-12.4634, 130.8456),
    "Hobart":      (-42.8821, 147.3272),
    "Cairns":      (-16.9203, 145.7710),
    "Alice Springs": (-23.6980, 133.8807),
    "Canberra":    (-35.2809, 149.1300),
}

ANCHOR_PLATE_ID = 0  # mantle reference frame — matches T01/T02, used by Notebooks 1-5

# --- Notebook 6 ("Fossil Climate Detectives") config -----------------------
# Revision note (v1.2): this used to reconstruct fossil points with
# Zahirovic2022 in the African-plate paleomagnetic frame (anchor 701701) --
# the frame the main suite's T62 notebook establishes as the approved choice
# for standalone paleoclimate work. That's a legitimate scientific choice on
# its own, but it does NOT match the plate model this notebook's own
# basemap is drawn from (scotese_and_wright2018, forced by needing to match
# the real PaleoDEM raster -- see MODEL_NAME_SW above). Two independently-
# built plate models don't agree pixel-for-pixel on where a coastline sits
# in deep time, and confirmed directly: at 410 Ma, points reconstructed with
# Zahirovic2022+701701 and then checked against the SW2018 continents drawn
# on the shared basemap landed inside those continents only 21/76 times --
# i.e. "most data ends up over the ocean", exactly the reported bug. Anchor
# plate 701701 doesn't even exist in scotese_and_wright2018's own rotation
# hierarchy (confirmed directly), so there's no way to reuse it there.
# scotese_and_wright2018 (PALEOMAP) is itself built as an absolute/
# paleomagnetically-referenced reconstruction -- that's what makes a
# PaleoDEM product possible at all -- so its own default frame (anchor 0,
# the SAME frame build_sw_reconstruction() already uses for every other
# notebook) already gives geologically sane absolute paleolatitudes, without
# needing a separate climate-specific anchor. Reconstructing with SW2018+
# anchor 0 instead fixed the containment check to 76/76 at 410 Ma, so
# export_fossils() below now reuses the SAME model/reconstruction as the
# basemap it's displayed on, dropping the separate Zahirovic-based pathway.
BOUCOT_DIR = _SIBLING_REPO / "data" / "Boucot2013_Lithology_Data_Tables"

# Six ages spanning a good climate story, chosen to (a) be real Boucot 2013
# map ages (so "15 Ma" etc. is the actual age of the data, not a rounded
# target) and (b) have an exact matching PaleoDEM file (see PALEODEM_FILES).
# Story arc: first forests -> coal swamps -> Triassic hothouse -> dinosaur
# era warmth -> late dinosaur era -> a cooling, more modern-ish world.
FOSSIL_AGES_MA = [410, 330, 240, 155, 80, 15]
BOUCOT_MAP_FOR_AGE = {
    410: "Map06 LDevon v5.csv",
    330: "Map11 Serpuk v4.csv",
    240: "Map17 MTrias v4.csv",
    155: "Map20 UJuras v4.csv",
    80:  "Map23 ConiacCampMaas v5.csv",
    15:  "Map28 Miocene v4.csv",
}
FOSSIL_AGE_LABEL = {
    410: "Devonian — the first forests",
    330: "Carboniferous — the great coal swamps",
    240: "Triassic — a hot world after Earth's worst extinction",
    155: "Jurassic — age of the dinosaurs",
    80:  "Cretaceous — the last age of the dinosaurs",
    15:  "Miocene — a cooling, more familiar world",
}

# Boucot, Xu & Scotese (2013) lithology code -> (name, climate bin). This is
# the FULL published key (15 codes / 5 bins) even though Notebook 6 only
# ever shows the 5 bins as kid-friendly icons — kept in full here so the
# per-lithology name is available if a future notebook wants it.
LITHO_KEY = {
    "T": ("Tillites", "cold"), "D": ("Dropstones", "cold"),
    "G": ("Glendonites", "cold"), "I": ("Ice crystals", "cold"),
    "C": ("Coals", "wet_humid"),
    "B": ("Bauxites", "warm_humid"), "L": ("Laterites", "warm_humid"),
    "K": ("Kaolinites", "warm_humid"), "O": ("Oolitic ironstones", "warm_humid"),
    "PA": ("Palms", "warm_temp"), "M": ("Mangroves / lat. Mn", "warm_temp"),
    "CR": ("Crocodilians", "warm_temp"), "LF": ("Lungfish burrows", "warm_temp"),
    "E": ("Evaporites", "arid"), "CA": ("Calcretes", "arid"),
}
# NOTE for whoever reads this next: Boucot's published categories do NOT
# include a literal "coral / reef" bin — "warm_temp" (palms / mangroves /
# crocodilians / lungfish) is the closest real category to "warm and wet",
# and is what Notebook 6 uses for its crocodile icon. Real coral/reef
# occurrence data exists in the suite (see T57_Reef_Builders_Paleolatitude
# and T60_PBDB_Paleobiogeography, both PBDB-sourced) but reconstructing it
# for a kid-friendly notebook is future work, not done here.

# ---------------------------------------------------------------------------
# Map projections (used by render_basemap_* and every *_robinson export)
# ---------------------------------------------------------------------------
ROBINSON = ccrs.Robinson(central_longitude=0)
PLATE_CARREE = ccrs.PlateCarree()

# The Southern Ocean regional crop spans 240 degrees of longitude (-40 to
# 200), which straddles the +-180 seam of a standard central_longitude=0
# PlateCarree -- cartopy can't represent that as one flat rectangle and
# silently falls back to showing the WHOLE globe's longitude range instead
# (confirmed directly: ax.set_extent((-40,200,-90,-20)) on a standard
# PlateCarree leaves ax.get_xlim() at (-180, 180), not (-40, 200)). Using a
# PlateCarree recentred on the middle of that range avoids the seam
# entirely, so the crop actually shows just the intended region.
SOUTHERN_OCEAN_CENTRAL_LON = 80.0
SOUTHERN_OCEAN_PROJECTION = ccrs.PlateCarree(central_longitude=SOUTHERN_OCEAN_CENTRAL_LON)

# ---------------------------------------------------------------------------
# Fixed-crop calibration (bug fix, v1.2)
# ---------------------------------------------------------------------------
# Every render_* function below used to save with bbox_inches="tight", which
# crops each PNG by a DIFFERENT amount depending on what's actually drawn on
# it (gridline number labels only appear on the left/bottom edges, and their
# exact width varies with the numbers shown at that particular age/region).
# That made the crop CONTENT-DEPENDENT, so a single fixed extent constant
# used everywhere for overlay placement (ax.imshow(img, extent=...)) did NOT
# actually match every image's true pixel-to-data-coordinate mapping --
# towns, earthquakes, and fossil points would then land in the wrong place
# relative to the basemap under them (confirmed directly: a zoomed-in check
# showed Melbourne/Hobart landing in open ocean, and Adelaide's postcard
# marker landing near Hobart instead of Adelaide -- this, not a plate-ID
# bug, was the actual cause of that misalignment).
#
# The fix: every render_* function below places its axes at a FIXED box
# (AX_POS / REGIONAL_AX_POS, as a fraction of the figure) and saves with NO
# tight-crop, so the full saved PNG always maps to the exact same data
# extent. That true extent is computed once here via a throwaway
# calibration pass -- cartopy auto-adjusts (shrinks/recentres) the
# requested axes box to preserve the projection's true aspect ratio, so the
# ACTUAL post-draw position has to be read back (fig.canvas.draw() then
# ax.get_position()) rather than trusting the request, then the full-image
# data extent is linearly extrapolated from the axes' known inner data
# bounds (ax.get_xlim()/get_ylim(), also read post-draw) and its fractional
# position within the figure. Verified deterministic (identical figsize +
# axes request always reproduces the exact same true position) and verified
# visually (known reference towns/cities land exactly on their real
# coastline when overlaid using these extents).
AX_POS = (0.09, 0.09, 0.885, 0.86)          # left, bottom, width, height -- global Robinson maps
REGIONAL_AX_POS = (0.10, 0.12, 0.88, 0.85)  # left, bottom, width, height -- regional PlateCarree maps
ROBINSON_FIGSIZE = (10, 5.5)
ATLANTIC_FIGSIZE = (10, 5.5)
SOUTHERN_OCEAN_FIGSIZE = (11, 3.3)          # wide/short -- matches this crop's own ~5:1 aspect ratio,
                                             # which keeps cartopy's aspect-preserving auto-shrink small
                                             # (a badly-mismatched figsize amplifies extrapolation error)
ATLANTIC_EXTENT = (-90, 60, -60, 20)          # lon_min, lon_max, lat_min, lat_max -- Notebook 2
SOUTHERN_OCEAN_EXTENT = (-40, 200, -90, -20)  # lon_min, lon_max, lat_min, lat_max -- Notebook 4


def _calibrate_full_extent(figsize, ax_pos, projection, set_extent=None):
    """Return the TRUE full-image data extent for a figure built with
    fig.add_axes(ax_pos, projection=projection), ax.set_global() (if
    set_extent is None) or ax.set_extent(set_extent, crs=PLATE_CARREE)
    otherwise, and saved with NO crop. See the big comment above."""
    fig = plt.figure(figsize=figsize)
    ax = fig.add_axes(ax_pos, projection=projection)
    if set_extent is None:
        ax.set_global()
    else:
        ax.set_extent(set_extent, crs=PLATE_CARREE)
    fig.canvas.draw()
    ix0, ix1 = ax.get_xlim()
    iy0, iy1 = ax.get_ylim()
    pos = ax.get_position()
    plt.close(fig)
    x0, y0, x1, y1 = pos.x0, pos.y0, pos.x1, pos.y1
    per_x = (ix1 - ix0) / (x1 - x0)
    per_y = (iy1 - iy0) / (y1 - y0)
    return (
        ix0 - x0 * per_x,
        ix1 + (1 - x1) * per_x,
        iy0 - y0 * per_y,
        iy1 + (1 - y1) * per_y,
    )


# A full-globe Robinson map's data extent is a fixed constant -- it does not
# depend on what's plotted. Every notebook that loads a Robinson basemap PNG
# uses this exact tuple to place it with plain matplotlib imshow(extent=...).
ROBINSON_EXTENT = _calibrate_full_extent(ROBINSON_FIGSIZE, AX_POS, ROBINSON)

# Same idea for the two regional (PlateCarree) crops. build_dte_v2.py reads
# these two constants at BUILD time (not runtime) and bakes the numbers
# straight into the relevant notebook cells, so the shipped notebooks can
# never drift out of sync with what this script actually rendered.
ATLANTIC_FULL_EXTENT = _calibrate_full_extent(
    ATLANTIC_FIGSIZE, REGIONAL_AX_POS, PLATE_CARREE, set_extent=ATLANTIC_EXTENT)
SOUTHERN_OCEAN_FULL_EXTENT = _calibrate_full_extent(
    SOUTHERN_OCEAN_FIGSIZE, REGIONAL_AX_POS, SOUTHERN_OCEAN_PROJECTION, set_extent=SOUTHERN_OCEAN_EXTENT)

# A real bathymetry+topography colour scheme, in the spirit of this suite's
# own house convention (T43_Geochem_Corrected_Paleo_Elevation.ipynb uses
# GMT's built-in "earth" cpt, range -4000..4000, for exactly this purpose).
# matplotlib has no GMT cpt loader, so these stops approximate the classic
# earth/geo hypsometric-bathymetric scheme by hand: full ocean-depth range
# in blues (deep navy -> pale shelf blue) and full land-elevation range in
# green -> tan -> brown -> white, so mid-ocean ridges, trenches, and real
# mountain building are all visible on the map itself, not just implied.
_earth_stops = [
    (-8000, "#0a1a4a"), (-6000, "#0f2f6e"), (-4000, "#1c5599"),
    (-2000, "#3f7cb8"), (-1000, "#6ea8d0"), (-200, "#a9cbe0"),
    (0,     "#cdeab0"),
    (200,   "#8fbf5a"), (600, "#c9c56a"), (1200, "#d9b073"),
    (2000,  "#b98a5c"), (3000, "#8f6a4a"), (4000, "#5a4636"),
    (5500,  "#e8e8e8"), (7000, "#ffffff"),
]
EARTH_VMIN, EARTH_VMAX = -8000, 7000
_earth_nodes = [(v - EARTH_VMIN) / (EARTH_VMAX - EARTH_VMIN) for v, _ in _earth_stops]
_earth_colors = [c for _, c in _earth_stops]
EARTH_CMAP = mcolors.LinearSegmentedColormap.from_list("dte_earth", list(zip(_earth_nodes, _earth_colors)))

# Plate-velocity vector map settings (Notebook 1's second map). Tuned by eye
# against a real render at 0/50/300 Ma: `regrid_shape` (cartopy's automatic
# vector-field regridding onto the map projection) produced a chaotic mess
# of oversized, crossing arrows -- almost certainly interpolation blowing up
# across plate-ID discontinuities -- so it's deliberately left off; the raw
# spacingX/spacingY mesh plots cleanly. `scale` is fixed (not left to
# matplotlib's auto-scaling) and used identically at every age, so arrow
# length is directly comparable across the whole slider -- a kid can ask
# "were the plates moving faster back then?" and actually read the answer
# off arrow length, not just direction.
VELOCITY_QUIVER_SPACING = 15
VELOCITY_QUIVER_SCALE = 2500
VELOCITY_REF_MM_PER_YEAR = 50  # the reference arrow drawn in the map corner


def project_to_robinson(lons, lats):
    """Project arrays of longitude/latitude into Robinson x/y (metres), using
    the SAME projection object used for the basemap PNGs, so overlays drawn
    from the returned x/y always line up with a data/basemap_<age>Ma.png
    loaded via imshow(extent=ROBINSON_EXTENT)."""
    lons = np.asarray(lons, dtype=float)
    lats = np.asarray(lats, dtype=float)
    xy = np.array([ROBINSON.transform_point(lo, la, PLATE_CARREE) for lo, la in zip(lons, lats)])
    if len(xy) == 0:
        return np.array([]), np.array([])
    return xy[:, 0], xy[:, 1]


def project_to_southern_x(lons):
    """Convert true longitudes into the Southern Ocean regional map's own
    display-x coordinate (degrees from SOUTHERN_OCEAN_CENTRAL_LON, wrapped
    to (-180, 180]) -- so overlays line up with a basemap_southern_ocean_
    <age>Ma.png loaded via imshow(extent=SOUTHERN_OCEAN_FULL_EXTENT). Needed
    because that basemap is drawn on a recentred PlateCarree (see the
    SOUTHERN_OCEAN_CENTRAL_LON comment above) -- plain lon/lat would not
    line up with it directly the way it does for the Atlantic crop."""
    lons = np.asarray(lons, dtype=float)
    return ((lons - SOUTHERN_OCEAN_CENTRAL_LON + 180) % 360) - 180


def _require_paleodem(age):
    if age not in PALEODEM_FILES:
        raise KeyError(f"No PaleoDEM file registered for {age} Ma in PALEODEM_FILES.")
    path = PALEODEM_DIR / PALEODEM_FILES[age]
    if not path.exists():
        raise FileNotFoundError(
            f"PaleoDEM grid not found: {path}\n"
            "This script expects the Scotese & Wright (2018) PaleoDEM archive "
            "unzipped at ../GPlately-pyGMT_tutorials/zenodo_data/paleoDEM_ScoteseWright2018/ "
            "(see this repo's README for where that large-data archive comes from)."
        )
    return path


def _plot_plate_boundaries(ax, gplot):
    """Draw real plate boundaries on a cartopy axes, typed by kind -- the
    exact pattern demonstrated in the main suite's own T01_Hello_Deep_Time
    notebook (Cell 5, its Cartopy comparison render), reusing gplately's
    native PlotTopologies methods instead of a hand-rolled generic line.
    Ridges (red) and subduction zones are usually visible as real
    bathymetric features in the elevation raster underneath, which is part
    of the point of keeping full bathymetry rather than flattening the
    ocean to one colour.

    Revision note (v1.3): this used to call `gplot.plot_subduction_teeth()`
    for the subduction line, which draws little directional triangles --
    but only when the underlying topological features carry a resolved
    subduction *polarity* (which plate is overriding which). Checked
    directly: for this model (`scotese_and_wright2018`), `gplot.trenches`
    resolves 36 real subduction-zone sections, but `gplot.trench_left` /
    `gplot.trench_right` (what `plot_subduction_teeth` actually reads) come
    back empty at every age tried -- this model's topology doesn't carry
    that polarity attribute, so the teeth were silently never drawing
    anything, on every basemap in this whole suite, since the very first
    version. Switched to `gplot.plot_trenches()` instead, which only needs
    the (present) subduction-zone geometry, not polarity -- verified this
    correctly traces a real, recognisable Ring-of-Fire pattern (Andes,
    Aleutians, Japan, Indonesia, Himalaya collision front). Drawn as a
    visibly thicker line than the ridge/transform lines so it still reads
    as "a different, more important kind of line" without needing teeth."""
    gplot.plot_all_topological_sections(ax, color="0.75", linewidth=0.3)  # fills network gaps, kept faint
    gplot.plot_ridges(ax, color="red", linewidth=1.1)
    gplot.plot_transforms(ax, color="orange", linewidth=0.9)
    gplot.plot_trenches(ax, color="darkblue", linewidth=1.8)


def render_basemap_robinson(age, reconstruction, model):
    """Real bathymetry+topography, full-globe Robinson projection + lat/lon
    graticule, with real plate boundaries (ridges/transforms/subduction
    zones) reconstructed to this exact age drawn on top -> data/basemap_
    <age>Ma.png. Used by Notebooks 1, 3, 5, 6.

    `reconstruction`/`model` must be the Scotese & Wright (2018) model
    (build_sw_reconstruction()), NOT Zahirovic2022 -- see the comment by
    MODEL_NAME_SW above for why. This model has no separate "coastlines"
    layer, so the continent polygons' own edge doubles as the coastline.
    Boundary lines are only drawn for ages <= BOUNDARY_MAX_AGE_SW, since
    this model's topology doesn't resolve beyond that."""
    nc_path = _require_paleodem(age)
    ds = xr.open_dataset(nc_path)
    z = ds["z"].values
    lons, lats = ds["lon"].values, ds["lat"].values

    gplot = gplately.PlotTopologies(
        plate_reconstruction=reconstruction,
        continents=model.get_continental_polygons(),
        COBs=model.get_COBs(),
        time=float(age),
    )

    fig = plt.figure(figsize=ROBINSON_FIGSIZE)
    ax = fig.add_axes(AX_POS, projection=ROBINSON)
    ax.set_global()
    ax.pcolormesh(lons, lats, z, transform=PLATE_CARREE, cmap=EARTH_CMAP,
                  vmin=EARTH_VMIN, vmax=EARTH_VMAX, shading="auto")
    gplot.plot_continents(ax, facecolor="none", edgecolor="0.15", linewidth=0.35)
    if age <= BOUNDARY_MAX_AGE_SW:
        _plot_plate_boundaries(ax, gplot)
    else:
        print(f"    (no plate-boundary topology beyond {BOUNDARY_MAX_AGE_SW} Ma in this model -- "
              f"coastline only at {age} Ma)")
    gl = ax.gridlines(draw_labels=True, linewidth=0.4, color="black", alpha=0.35, linestyle="--")
    gl.top_labels = False
    gl.right_labels = False
    out_path = OUT_DIR / f"basemap_{age}Ma.png"
    # NO bbox_inches="tight" -- a fixed axes box (AX_POS) + full, uncropped
    # save is what makes ROBINSON_EXTENT a valid constant for every image.
    # See the "Fixed-crop calibration" comment near ROBINSON_EXTENT above.
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    print(f"  wrote {out_path.name}")


def render_basemap_subduction_only(age, reconstruction, model):
    """Same real bathymetry+topography Robinson map as render_basemap_robinson
    -- same figure size, same fixed AX_POS, same uncropped save -- but with
    ONLY the subduction-zone (trench) line drawn on top, no ridges and no
    transforms -> data/basemap_subduction_<age>Ma.png.

    Revision note (v1.3): added for Notebook 3, after the user asked for the
    earthquake map to be paired with "the same map but with subduction zones
    overlain, so kids can see their association." The existing basemap PNGs
    already have all three boundary types (ridges/transforms/subduction)
    baked into the raster together, so there's no way to selectively hide
    two of them from an already-rendered image -- this renders a second,
    genuinely separate basemap with only `gplot.plot_trenches` called, so
    the two backgrounds can sit side by side and isolate exactly one
    variable (which boundary type is shown) while everything else about
    the map -- bathymetry, continents, projection, extent -- stays identical.
    (`plot_trenches` rather than `plot_subduction_teeth` -- see the revision
    note on `_plot_plate_boundaries` above for why the teeth version turned
    out to silently draw nothing for this plate model.) Because it shares
    the exact same AX_POS/figsize/save settings as render_basemap_robinson,
    it also shares the same calibrated ROBINSON_EXTENT, so the existing
    earthquake robinson_x/y columns overlay on it correctly with no extra
    computation.

    `reconstruction`/`model` must be the Scotese & Wright (2018) model, same
    reasoning as render_basemap_robinson."""
    nc_path = _require_paleodem(age)
    ds = xr.open_dataset(nc_path)
    z = ds["z"].values
    lons, lats = ds["lon"].values, ds["lat"].values

    gplot = gplately.PlotTopologies(
        plate_reconstruction=reconstruction,
        continents=model.get_continental_polygons(),
        COBs=model.get_COBs(),
        time=float(age),
    )

    fig = plt.figure(figsize=ROBINSON_FIGSIZE)
    ax = fig.add_axes(AX_POS, projection=ROBINSON)
    ax.set_global()
    ax.pcolormesh(lons, lats, z, transform=PLATE_CARREE, cmap=EARTH_CMAP,
                  vmin=EARTH_VMIN, vmax=EARTH_VMAX, shading="auto")
    gplot.plot_continents(ax, facecolor="none", edgecolor="0.15", linewidth=0.35)
    if age <= BOUNDARY_MAX_AGE_SW:
        gplot.plot_trenches(ax, color="darkblue", linewidth=1.8)
    else:
        print(f"    (no plate-boundary topology beyond {BOUNDARY_MAX_AGE_SW} Ma in this model -- "
              f"coastline only at {age} Ma)")
    gl = ax.gridlines(draw_labels=True, linewidth=0.4, color="black", alpha=0.35, linestyle="--")
    gl.top_labels = False
    gl.right_labels = False
    out_path = OUT_DIR / f"basemap_subduction_{age}Ma.png"
    # NO bbox_inches="tight" -- see the comment in render_basemap_robinson.
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    print(f"  wrote {out_path.name}")


def render_velocity_robinson(age, reconstruction, model):
    """Real plate-motion velocity field (direction + speed) at this exact
    age -> data/velocity_<age>Ma.png. Used by Notebook 1's second map, so
    kids can see which plates are moving fast or slowly, and which way.

    Draws on a plain continents/coastlines/plate-boundary background rather
    than the full bathymetry raster -- deliberately, so the arrows (which
    need to be the visual focus) don't fight the elevation colour scheme
    for attention. Boundaries are kept so the same colour legend from the
    first map still applies (ridges push plates apart, subduction pulls
    them together).

    The arrows themselves come straight from gplately's own
    PlotTopologies.plot_plate_motion_vectors -- the exact method
    demonstrated in gplately's own official example notebook
    (04-VelocityBasics.ipynb on the GPlately GitHub) -- not a hand-rolled
    velocity calculation."""
    gplot = gplately.PlotTopologies(
        plate_reconstruction=reconstruction,
        coastlines=model.get_coastlines(),
        continents=model.get_continental_polygons(),
        COBs=model.get_COBs(),
        time=float(age),
    )

    fig = plt.figure(figsize=ROBINSON_FIGSIZE)
    ax = fig.add_axes(AX_POS, projection=ROBINSON)
    ax.set_global()
    ax.set_facecolor("#dceaf5")  # plain ocean tint -- no bathymetry raster on this map, on purpose
    gplot.plot_continents(ax, facecolor="#e8e2c8", edgecolor="none")
    gplot.plot_coastlines(ax, color="0.35", linewidth=0.4)
    _plot_plate_boundaries(ax, gplot)
    quiver = gplot.plot_plate_motion_vectors(
        ax, spacingX=VELOCITY_QUIVER_SPACING, spacingY=VELOCITY_QUIVER_SPACING,
        color="darkgreen", scale=VELOCITY_QUIVER_SCALE, width=0.0035, zorder=5,
    )
    ax.quiverkey(
        quiver, X=0.83, Y=-0.05, U=VELOCITY_REF_MM_PER_YEAR, coordinates="axes",
        label=f"{VELOCITY_REF_MM_PER_YEAR} mm/year ({VELOCITY_REF_MM_PER_YEAR / 10:.0f} cm/year) — a fast-moving plate",
        labelpos="E", fontproperties={"size": 9},
    )
    gl = ax.gridlines(draw_labels=True, linewidth=0.4, color="black", alpha=0.35, linestyle="--")
    gl.top_labels = False
    gl.right_labels = False
    out_path = OUT_DIR / f"velocity_{age}Ma.png"
    # NO bbox_inches="tight" -- see the comment in render_basemap_robinson.
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    print(f"  wrote {out_path.name}")


def render_basemap_regional(age, extent, out_name, reconstruction, model, figsize, projection):
    """Real bathymetry+topography, simple equirectangular crop, with real
    plate boundaries reconstructed to this exact age -> data/<out_name>.
    `extent` is (lon_min, lon_max, lat_min, lat_max), always given in TRUE
    (unrotated) longitude/latitude. `projection` is the axes' own PlateCarree
    (PLATE_CARREE for the Atlantic crop, SOUTHERN_OCEAN_PROJECTION for the
    Southern Ocean crop -- see the comment by SOUTHERN_OCEAN_CENTRAL_LON for
    why that one needs recentring). Used by Notebooks 2 and 4.

    `reconstruction`/`model` must be the Scotese & Wright (2018) model, same
    reasoning as render_basemap_robinson above."""
    nc_path = _require_paleodem(age)
    ds = xr.open_dataset(nc_path)
    z = ds["z"].values
    lons, lats = ds["lon"].values, ds["lat"].values

    gplot = gplately.PlotTopologies(
        plate_reconstruction=reconstruction,
        continents=model.get_continental_polygons(),
        COBs=model.get_COBs(),
        time=float(age),
    )

    fig = plt.figure(figsize=figsize)
    ax = fig.add_axes(REGIONAL_AX_POS, projection=projection)
    ax.set_extent(extent, crs=PLATE_CARREE)
    ax.pcolormesh(lons, lats, z, transform=PLATE_CARREE, cmap=EARTH_CMAP,
                  vmin=EARTH_VMIN, vmax=EARTH_VMAX, shading="auto")
    gplot.plot_continents(ax, facecolor="none", edgecolor="0.15", linewidth=0.35)
    if age <= BOUNDARY_MAX_AGE_SW:
        _plot_plate_boundaries(ax, gplot)
    else:
        print(f"    (no plate-boundary topology beyond {BOUNDARY_MAX_AGE_SW} Ma in this model -- "
              f"coastline only at {age} Ma)")
    gl = ax.gridlines(draw_labels=True, linewidth=0.4, color="black", alpha=0.35, linestyle="--")
    gl.top_labels = False
    gl.right_labels = False
    out_path = OUT_DIR / out_name
    # NO bbox_inches="tight" -- see the comment in render_basemap_robinson.
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    print(f"  wrote {out_path.name}")


def build_reconstruction(anchor_plate_id=ANCHOR_PLATE_ID):
    print(f"Loading {MODEL_NAME} (cached under {MODEL_DATA_DIR}), anchor plate {anchor_plate_id} ...")
    pmm = PlateModelManager()
    model = pmm.get_model(MODEL_NAME, data_dir=str(MODEL_DATA_DIR))
    reconstruction = gplately.PlateReconstruction(
        rotation_model=model.get_rotation_model(),
        topology_features=model.get_topologies(),
        static_polygons=model.get_static_polygons(),
        anchor_plate_id=anchor_plate_id,
    )
    return model, reconstruction


def build_sw_reconstruction():
    """The Scotese & Wright (2018) PALEOMAP plate model -- see the
    MODEL_NAME_SW comment above for why this exists as a second model
    alongside Zahirovic2022. Used for render_basemap_robinson/
    render_basemap_regional's continents+boundaries, AND for anything else
    whose reconstructed position is displayed directly on top of one of
    those basemaps (towns, fossils) -- see the "same plate model as what's
    drawn under it" revision notes by export_towns() and BOUCOT_DIR below.
    Only earthquakes (present-day positions only, no reconstruction) and the
    velocity map (deliberately Zahirovic2022, for its topology coverage
    beyond 100 Ma) still use build_reconstruction() instead."""
    print(f"Loading {MODEL_NAME_SW} (cached under {MODEL_DATA_DIR_SW}) ...")
    pmm = PlateModelManager()
    model = pmm.get_model(MODEL_NAME_SW, data_dir=str(MODEL_DATA_DIR_SW))
    reconstruction = gplately.PlateReconstruction(
        rotation_model=model.get_rotation_model(),
        topology_features=model.get_topologies(),
        static_polygons=model.get_static_polygons(),
    )
    return model, reconstruction


def export_land_polygons(model, reconstruction):
    """One simplified filled-land GeoJSON per age. Kept for Notebook 2's
    zoomed-in jigsaw comparison and as a lightweight fallback; Notebooks 1,
    3, 5, 6 now use the real-elevation basemap PNGs instead."""
    for age in AGES_MA:
        gplot = gplately.PlotTopologies(
            plate_reconstruction=reconstruction,
            coastlines=model.get_coastlines(),
            continents=model.get_continental_polygons(),
            COBs=model.get_COBs(),
            time=age,
        )
        continents_gdf = gplot.get_continents()
        continents_gdf = continents_gdf.copy()
        continents_gdf["geometry"] = continents_gdf.geometry.simplify(
            0.2, preserve_topology=True
        )
        out_path = OUT_DIR / f"land_{age}Ma.geojson"
        continents_gdf.to_file(out_path, driver="GeoJSON")
        print(f"  wrote {out_path.name}  ({len(continents_gdf)} polygons)")


def export_towns(reconstruction_sw):
    """Reconstructed positions of every TOWNS entry, at every age, for
    Notebook 5 — lat/lon plus pre-projected Robinson x/y.

    Revision note (v1.2): this used to take the Zahirovic2022
    `reconstruction` instead. Same bug class as the fossils fix below —
    Notebook 5's postcard is drawn on the Scotese & Wright (2018) basemap,
    but the town's own rigid-rotation history came from a *different* plate
    model. Both models happen to assign Adelaide the same plate ID (801,
    confirmed directly — so this was never a plate-ID *assignment* bug), but
    each model's own reconstructed rotation for that plate disagrees with
    the other's, and in deep time that disagreement is large: checked
    directly across every age this notebook uses, Zahirovic2022 vs.
    scotese_and_wright2018 put Adelaide up to ~43 degrees of longitude and
    ~19 degrees of latitude apart from each other at 150-200 Ma. Confirmed
    that's the actual cause of "Adelaide doesn't move correctly with the
    continent" — reconstructing with SW2018 instead (using its own
    continental polygons, per gplately.Points' point-in-polygon plate-ID
    lookup, exactly as requested) puts the star back on the correct plate
    history for the continent actually drawn underneath it."""
    names = list(TOWNS.keys())
    lats = np.array([TOWNS[n][0] for n in names])
    lons = np.array([TOWNS[n][1] for n in names])
    pts = gplately.Points(reconstruction_sw, lons, lats, anchor_plate_id=ANCHOR_PLATE_ID)

    rows = []
    for age in AGES_MA:
        rlons, rlats = pts.reconstruct(
            float(age), return_array=True, anchor_plate_id=ANCHOR_PLATE_ID
        )
        rx, ry = project_to_robinson(rlons, rlats)
        for name, rlon, rlat, x, y in zip(names, rlons, rlats, rx, ry):
            rows.append({"town": name, "age_ma": age, "lat": rlat, "lon": rlon,
                         "robinson_x": x, "robinson_y": y})

    out_path = OUT_DIR / "towns_through_time.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"  wrote {out_path.name}  ({len(rows)} rows, {len(names)} towns)")


# A small, real, well-documented fallback list — used only if the live USGS
# fetch below fails (e.g. no internet when this script is run). Magnitudes
# and locations are widely reported historical values.
FALLBACK_QUAKES = [
    (38.297, 142.373, 9.1, "Tohoku, Japan", 2011),
    (3.316, 95.854, 9.1, "Sumatra-Andaman", 2004),
    (-38.29, -73.05, 9.5, "Valdivia, Chile", 1960),
    (61.02, -147.65, 9.2, "Prince William Sound, Alaska", 1964),
    (-36.12, -72.90, 8.8, "Maule, Chile", 2010),
    (31.02, 103.37, 7.9, "Sichuan, China", 2008),
    (28.23, 84.73, 7.8, "Gorkha, Nepal", 2015),
    (18.46, -72.53, 7.0, "Haiti", 2010),
    (37.75, -122.55, 7.9, "San Francisco, USA", 1906),
    (37.17, 37.03, 7.8, "Turkey-Syria border", 2023),
]


def export_earthquakes():
    """Notable earthquakes (M >= 7.5 since 1970) from the public USGS
    catalogue, for Notebook 3 — lat/lon plus pre-projected Robinson x/y.
    Falls back to a small static list if there's no internet connection
    when this script is run."""
    url = (
        "https://earthquake.usgs.gov/fdsnws/event/1/query"
        "?format=csv&starttime=1970-01-01&minmagnitude=7.5&orderby=time"
    )
    rows = []
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            text = resp.read().decode("utf-8")
        reader = csv.DictReader(text.splitlines())
        for r in reader:
            rows.append({
                "lat": float(r["latitude"]),
                "lon": float(r["longitude"]),
                "mag": float(r["mag"]),
                "place": r["place"],
                "year": r["time"][:4],
            })
        print(f"  fetched {len(rows)} earthquakes from USGS")
    except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as e:
        print(f"  USGS fetch failed ({e}) — using {len(FALLBACK_QUAKES)}-quake fallback list")
        rows = [
            {"lat": lat, "lon": lon, "mag": mag, "place": place, "year": year}
            for lat, lon, mag, place, year in FALLBACK_QUAKES
        ]

    lats = np.array([r["lat"] for r in rows])
    lons = np.array([r["lon"] for r in rows])
    rx, ry = project_to_robinson(lons, lats)
    for r, x, y in zip(rows, rx, ry):
        r["robinson_x"], r["robinson_y"] = x, y

    out_path = OUT_DIR / "notable_earthquakes.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"  wrote {out_path.name}  ({len(rows)} rows)")


def _boundary_line_rows(gdf):
    """Shared helper: flatten a gplately boundary GeoDataFrame (ridges,
    trenches, ...) into (segment_id, lon, lat, robinson_x, robinson_y) rows
    -- handles both LineString and MultiLineString geometries, and each
    disconnected line gets its own segment_id so plotting code can draw
    them as separate lines instead of one path with stray connectors
    jumping between unrelated segments. Shared by export_subduction_zones
    and export_ridges below."""
    rows = []
    seg_id = 0
    for geom in gdf.geometry:
        lines = geom.geoms if geom.geom_type == "MultiLineString" else [geom]
        for line in lines:
            lons, lats = zip(*line.coords)
            rx, ry = project_to_robinson(lons, lats)
            for lo, la, x, y in zip(lons, lats, rx, ry):
                rows.append({"segment_id": seg_id, "lon": lo, "lat": la,
                             "robinson_x": x, "robinson_y": y})
            seg_id += 1
    return rows, seg_id


def export_subduction_zones(age, reconstruction, model):
    """Real subduction-zone (trench) line geometry at a given age, as plain
    lon/lat plus pre-projected Robinson x/y, one row per vertex, grouped by
    `segment_id` (trenches are a set of disconnected lines, not one
    continuous path) -> data/subduction_zones_<age>Ma.csv.

    Revision note (v1.5): added for Notebook 3, after the user reported the
    subduction-zone line was "not visible at all" in the earthquake/
    subduction comparison -- the line is baked into the basemap PNG raster,
    UNDER the earthquake dots, and earthquakes genuinely cluster right on
    top of real subduction zones (that's the whole point of the notebook!),
    so wherever the line mattered most it was getting completely covered.
    A raster background can never be redrawn "in front of" markers added
    later in the notebook. Kids notebooks don't have gplately to redraw the
    real boundary geometry themselves, so this precomputes it here and
    ships it as a flat CSV (same pattern as duck_path.csv) -- the notebook
    plots it as its own line, LAST, on top of the earthquake scatter."""
    gplot = gplately.PlotTopologies(
        plate_reconstruction=reconstruction,
        continents=model.get_continental_polygons(),
        COBs=model.get_COBs(),
        time=float(age),
    )
    rows, seg_id = _boundary_line_rows(gplot.get_trenches())
    out_path = OUT_DIR / f"subduction_zones_{age}Ma.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"  wrote {out_path.name}  ({seg_id} segments, {len(rows)} points)")


def export_ridges(age, reconstruction, model):
    """Real mid-ocean-ridge (spreading boundary) line geometry at a given
    age, same shape as export_subduction_zones above -> data/ridges_<age>Ma.csv.

    Revision note (v1.6): added after the user pointed out Notebook 3's
    separate "All plate boundaries" comparison panel was unnecessary --
    Step 1 and Step 2 already show every boundary type on the shared
    basemap, so re-showing them a third time in Step 3 was redundant.
    Simplified Step 3 down to a single map, and this export makes sure
    ridges (MORs) are still part of that one remaining map: drawn as their
    own vector layer, same "plot it last, on top of the earthquake dots"
    reasoning as the subduction line above, since ridges are seismically
    active too and would be just as easy to bury under a dot."""
    gplot = gplately.PlotTopologies(
        plate_reconstruction=reconstruction,
        continents=model.get_continental_polygons(),
        COBs=model.get_COBs(),
        time=float(age),
    )
    rows, seg_id = _boundary_line_rows(gplot.get_ridges())
    out_path = OUT_DIR / f"ridges_{age}Ma.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"  wrote {out_path.name}  ({seg_id} segments, {len(rows)} points)")


# ---------------------------------------------------------------------------
# Notebook 6 — Fossil Climate Detectives
# ---------------------------------------------------------------------------

def _parse_signed(value, hemi, positive):
    if pd.isna(value):
        return np.nan
    try:
        v = float(value)
    except (TypeError, ValueError):
        return np.nan
    if pd.isna(hemi):
        return v
    h = str(hemi).strip().upper()
    if h == positive:
        return abs(v)
    if h == ("S" if positive == "N" else "W"):
        return -abs(v)
    return v


def _canonical_columns(df):
    cols = {c.strip(): c for c in df.columns}
    def pick(*cands):
        for cand in cands:
            for k, v in cols.items():
                if k.lower() == cand.lower():
                    return v
        return None
    return {"code": pick("LithologyCode"), "lat": pick("LAT"), "ns": pick("NS"),
            "lon": pick("LONG"), "ew": pick("EW")}


def _load_boucot_csv(path):
    """Load one Boucot 2013 Map CSV, keeping only rows with a recognised
    lithology code, with signed present-day coordinates parsed out. Same
    schema-normalising approach as the main suite's T62 notebook."""
    df = pd.read_csv(path, encoding="latin-1", on_bad_lines="skip")
    cmap = _canonical_columns(df)
    out = pd.DataFrame({
        "code": df[cmap["code"]].astype(str).str.strip(),
        "present_lat": [_parse_signed(la, ns, "N") for la, ns in
                         zip(df[cmap["lat"]], df[cmap["ns"]] if cmap["ns"] else [None] * len(df))],
        "present_lon": [_parse_signed(lo, ew, "E") for lo, ew in
                         zip(df[cmap["lon"]], df[cmap["ew"]] if cmap["ew"] else [None] * len(df))],
    })
    out = out[out["code"].isin(LITHO_KEY.keys())].copy()
    out["bin"] = out["code"].map(lambda c: LITHO_KEY[c][1])
    out = out.dropna(subset=["present_lat", "present_lon"]).reset_index(drop=True)
    return out


def export_fossils(reconstruction_sw, model_sw):
    """Reconstruct Boucot 2013 climate-sensitive-lithology points at each of
    FOSSIL_AGES_MA, using the SAME Scotese & Wright (2018) model/anchor as
    the basemap this notebook displays them on (see the revision note by
    BOUCOT_DIR above for why), drop any that land outside the reconstructed
    continents (almost always a genuine plate-model mismatch, not a real
    open-ocean lithology), and write one CSV with lat/lon, Robinson x/y, and
    climate bin, for Notebook 6."""
    if not BOUCOT_DIR.exists():
        raise FileNotFoundError(
            f"Boucot 2013 data tables not found at {BOUCOT_DIR} — see this "
            "repo's README for where that data comes from."
        )

    from shapely.geometry import Point as _Point
    from shapely.ops import unary_union as _unary_union
    from shapely.prepared import prep as _prep

    all_rows = []
    for age in FOSSIL_AGES_MA:
        csv_path = BOUCOT_DIR / BOUCOT_MAP_FOR_AGE[age]
        df = _load_boucot_csv(csv_path)

        pts = gplately.Points(reconstruction_sw, df["present_lon"].values, df["present_lat"].values,
                               anchor_plate_id=ANCHOR_PLATE_ID)
        rlon, rlat = pts.reconstruct(float(age), anchor_plate_id=ANCHOR_PLATE_ID, return_array=True)
        df = df.iloc[:len(rlon)].copy()
        df["paleo_lon"], df["paleo_lat"] = rlon, rlat
        df = df.dropna(subset=["paleo_lon", "paleo_lat"]).reset_index(drop=True)

        gplot = gplately.PlotTopologies(
            plate_reconstruction=reconstruction_sw,
            continents=model_sw.get_continental_polygons(),
            COBs=model_sw.get_COBs(),
            time=float(age),
        )
        cont_gdf = gplot.get_continents()
        if cont_gdf is not None and len(cont_gdf) > 0:
            uni = _prep(_unary_union(list(cont_gdf.geometry)))
            inside = np.fromiter(
                (uni.contains(_Point(lo, la)) for lo, la in zip(df["paleo_lon"], df["paleo_lat"])),
                dtype=bool, count=len(df),
            )
            n_before = len(df)
            df = df.loc[inside].reset_index(drop=True)
            print(f"  {age} Ma: kept {len(df)}/{n_before} points inside reconstructed continents")

        rx, ry = project_to_robinson(df["paleo_lon"].values, df["paleo_lat"].values)
        df["robinson_x"], df["robinson_y"] = rx, ry
        df["age_ma"] = age
        all_rows.append(df[["age_ma", "code", "bin", "paleo_lon", "paleo_lat", "robinson_x", "robinson_y"]])

    out = pd.concat(all_rows, ignore_index=True)
    out_path = OUT_DIR / "fossils_through_time.csv"
    out.to_csv(out_path, index=False)
    print(f"  wrote {out_path.name}  ({len(out)} rows across {len(FOSSIL_AGES_MA)} ages)")


# ---------------------------------------------------------------------------
# Notebook 4 — Follow the Duck through Deep Time
# ---------------------------------------------------------------------------
# Revision note (v1.2): the duck's path used to be pure hand-drawn arithmetic
# (a constant eastward drift, deflected north by an arbitrary hard-coded
# rectangle when "closed") with no knowledge of where the real land was —
# confirmed as the reported bug, the path ran straight over continents.
# This still isn't a physical ocean-current model (the notebook is honest
# about that), but it now uses the SAME real PaleoDEM elevation grid as the
# basemap it's drawn on to guarantee the path never crosses land: a
# shortest-path search over the ocean-only grid cells (elevation < 0),
# lightly biased to prefer a constant "preferred" latitude (mimicking a
# current that would rather flow straight around the globe) and only pay a
# cost to detour when real land is actually in the way. At 0 Ma that lets it
# sail straight across; at 50 Ma, with Australia and Antarctica still joined
# across the whole Tasmanian Gateway region in this model, it's forced on a
# long detour up and over the top of Australia instead — the "gateway
# closed -> flow deflected" idea the notebook already told, now emerging
# from real geography instead of being asserted.
DUCK_PREFERRED_LAT = -50.0    # the latitude the "current" would rather stay at, if nothing blocks it
DUCK_LAT_PENALTY_WEIGHT = 3.0  # cost per degree south of that, per degree of longitude travelled
DUCK_START_LONLAT = (60.0, -55.0)    # Indian Ocean, south of Africa -- (60,-50) is
                                      # open ocean today but sits on a raised, then-
                                      # exposed piece of crust at 60 Ma (elevation
                                      # +600 m there, confirmed directly), so the
                                      # start point is pulled a bit further south to
                                      # stay in open ocean at every age this notebook uses
DUCK_END_LONLAT = (-170.0, -50.0)    # South Pacific, south of New Zealand
DUCK_AGES_MA = [60, 50, 40, 30, 20, 10, 0]  # widened from [60, 0] for the Mission 4 slider
# Revision note: originally 50 Ma. The user flagged that Scotese & Wright's
# own 50 Ma map already shows the Tasmanian Gateway just starting to open,
# which undercuts a "mostly closed" story at that age. 60 Ma (Map15,
# "Paleocene" -- not in this repo's original PaleoDEM subset, fetched
# separately from the Zenodo archive and added to PALEODEM_FILES above) is
# comfortably before that opening and gives a real Zahirovic-style land
# connection across the gateway -- confirmed directly with the same
# ocean-only pathfinding below, not just assumed.


def _duck_ocean_grid(age, lon_margin=(-130.0, 130.0)):
    """The Southern Ocean region's elevation grid at this age, reindexed
    into SOUTHERN_OCEAN_PROJECTION's own rotated longitude (so it can be
    searched without the +-180 antimeridian getting in the way — see the
    SOUTHERN_OCEAN_CENTRAL_LON comment above)."""
    nc_path = _require_paleodem(age)
    ds = xr.open_dataset(nc_path)
    z = ds["z"].sel(lat=slice(-90, -10))
    lon = z.lon.values
    rot_lon = ((lon - SOUTHERN_OCEAN_CENTRAL_LON + 180) % 360) - 180
    order = np.argsort(rot_lon)
    rot_lon_sorted = rot_lon[order]
    grid = z.values[:, order]
    mask = (rot_lon_sorted >= lon_margin[0]) & (rot_lon_sorted <= lon_margin[1])
    return grid[:, mask], rot_lon_sorted[mask], z.lat.values


def _duck_true_to_rot(lon):
    return ((np.asarray(lon, dtype=float) - SOUTHERN_OCEAN_CENTRAL_LON + 180) % 360) - 180


def _duck_ocean_path(grid, rot_lons, lats, start_true_lonlat, end_true_lonlat):
    """Cheapest ocean-only route from start to end across an elevation grid
    (elevation < 0 = passable), using Dijkstra with 8-connectivity. Cost per
    step is real angular distance plus a penalty for being south of
    DUCK_PREFERRED_LAT, so the path only detours around land it actually has
    to. Returns a list of (display_x, lat) points in the SAME rotated
    coordinate space as SOUTHERN_OCEAN_FULL_EXTENT, or None if no all-ocean
    route exists at all within this grid."""
    import heapq
    ny, nx = grid.shape
    is_ocean = grid < 0

    def nearest_idx(vals, target):
        return int(np.argmin(np.abs(vals - target)))

    sx, ex = _duck_true_to_rot(start_true_lonlat[0]), _duck_true_to_rot(end_true_lonlat[0])
    si, sj = nearest_idx(lats, start_true_lonlat[1]), nearest_idx(rot_lons, sx)
    ei, ej = nearest_idx(lats, end_true_lonlat[1]), nearest_idx(rot_lons, ex)
    if not is_ocean[si, sj]:
        raise ValueError(f"duck start point is on land (elevation={grid[si, sj]:.0f} m)")
    if not is_ocean[ei, ej]:
        raise ValueError(f"duck end point is on land (elevation={grid[ei, ej]:.0f} m)")

    dist = np.full((ny, nx), np.inf)
    dist[si, sj] = 0.0
    prev = {}
    visited = np.zeros((ny, nx), dtype=bool)
    heap = [(0.0, si, sj)]
    neighbours = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    found = False
    while heap:
        d, i, j = heapq.heappop(heap)
        if visited[i, j]:
            continue
        visited[i, j] = True
        if (i, j) == (ei, ej):
            found = True
            break
        for di, dj in neighbours:
            ni, nj = i + di, j + dj
            if 0 <= ni < ny and 0 <= nj < nx and is_ocean[ni, nj] and not visited[ni, nj]:
                lat_mid = np.deg2rad((lats[i] + lats[ni]) / 2)
                lon_step = abs(rot_lons[nj] - rot_lons[j])
                base = np.hypot(lats[ni] - lats[i], lon_step * np.cos(lat_mid))
                penalty = DUCK_LAT_PENALTY_WEIGHT * max(0.0, DUCK_PREFERRED_LAT - lats[ni]) * max(lon_step, 1.0)
                nd = d + base + penalty
                if nd < dist[ni, nj]:
                    dist[ni, nj] = nd
                    prev[(ni, nj)] = (i, j)
                    heapq.heappush(heap, (nd, ni, nj))
    if not found:
        return None

    idx_path = [(ei, ej)]
    cur = (ei, ej)
    while cur != (si, sj):
        cur = prev[cur]
        idx_path.append(cur)
    idx_path.reverse()
    return [(rot_lons[j], lats[i]) for i, j in idx_path]


def export_duck_path():
    """Precompute the duck's ocean-only path at each of DUCK_AGES_MA ->
    data/duck_path.csv, for Notebook 4. See the revision note above."""
    rows = []
    for age in DUCK_AGES_MA:
        grid, rot_lons, lats = _duck_ocean_grid(age)
        path = _duck_ocean_path(grid, rot_lons, lats, DUCK_START_LONLAT, DUCK_END_LONLAT)
        if path is None:
            raise RuntimeError(
                f"No all-ocean route found for the duck at {age} Ma between "
                f"{DUCK_START_LONLAT} and {DUCK_END_LONLAT} — pick different "
                "start/end points or widen the search margin in _duck_ocean_grid."
            )
        for step, (display_x, lat) in enumerate(path):
            rows.append({"age_ma": age, "step": step, "display_x": display_x, "lat": lat})
        print(f"  {age} Ma: duck path found, {len(path)} steps, "
              f"latitude range {min(p[1] for p in path):.1f} to {max(p[1] for p in path):.1f}")

    out_path = OUT_DIR / "duck_path.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"  wrote {out_path.name}  ({len(rows)} rows across {len(DUCK_AGES_MA)} ages)")


def main():
    print(f"gplately {gplately.__version__}\n")
    model, reconstruction = build_reconstruction()
    model_sw, reconstruction_sw = build_sw_reconstruction()

    print("\nExporting land polygons ...")
    export_land_polygons(model, reconstruction)

    print("\nExporting town positions through time ...")
    export_towns(reconstruction_sw)

    print("\nExporting notable earthquakes ...")
    export_earthquakes()

    print("\nExporting subduction-zone and ridge line geometry for Notebook 3 ...")
    export_subduction_zones(0, reconstruction_sw, model_sw)
    export_ridges(0, reconstruction_sw, model_sw)

    print("\nRendering Robinson basemaps (real bathymetry+topography, real plate boundaries, "
          "Scotese & Wright 2018 continents -- matches the DEM's own plate model) ...")
    for age in AGES_MA:
        render_basemap_robinson(age, reconstruction_sw, model_sw)
    for age in FOSSIL_AGES_MA:
        render_basemap_robinson(age, reconstruction_sw, model_sw)

    print("\nRendering the subduction-zones-only basemap for Notebook 3 ...")
    render_basemap_subduction_only(0, reconstruction_sw, model_sw)

    print("\nRendering plate-velocity vector maps for Notebook 1 (Zahirovic2022 -- needs topology "
          "coverage the Scotese & Wright model doesn't have beyond 100 Ma) ...")
    for age in AGES_MA:
        render_velocity_robinson(age, reconstruction, model)

    print("\nRendering regional basemaps for Notebooks 2 and 4 ...")
    # Widened from a 2-state (0/300 Ma) toggle to a full 7-age slider for
    # Mission 2, matching the AGES_VELOCITY cadence used elsewhere.
    for age in (0, 50, 100, 150, 200, 250, 300):
        render_basemap_regional(age, ATLANTIC_EXTENT, f"basemap_atlantic_{age}Ma.png", reconstruction_sw, model_sw,
                                 ATLANTIC_FIGSIZE, PLATE_CARREE)
    # Widened from a 2-state (0/60 Ma) toggle to a full slider for Mission 4,
    # at the same 10 Ma cadence as DUCK_AGES_MA below.
    for age in (0, 10, 20, 30, 40, 50, 60):
        render_basemap_regional(age, SOUTHERN_OCEAN_EXTENT, f"basemap_southern_ocean_{age}Ma.png", reconstruction_sw, model_sw,
                                 SOUTHERN_OCEAN_FIGSIZE, SOUTHERN_OCEAN_PROJECTION)

    print("\nExporting the duck's ocean-only path (real elevation data, never crosses land) ...")
    export_duck_path()

    print("\nExporting fossil climate indicators (Boucot 2013) ...")
    export_fossils(reconstruction_sw, model_sw)

    print(f"\nDone. All files written to {OUT_DIR}")


if __name__ == "__main__":
    main()
