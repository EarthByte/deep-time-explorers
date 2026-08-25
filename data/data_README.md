# data/

This folder is populated by running `../export_data.py` once in the
`gplately` conda environment — see the main [README](../README.md#running-it).

It isn't populated yet in a fresh checkout. Expected contents once the
export script has been run:

- `basemap_<age>Ma.png` (×13 — full-globe Robinson projection, real bathymetry+topography, continents from the Scotese & Wright 2018 plate model to match the DEM, plate boundaries for ages ≤100 Ma)
- `basemap_subduction_0Ma.png` — same basemap/extent as `basemap_0Ma.png`, but with only the subduction-zone line drawn (no ridges/transforms), for Notebook 3's earthquake/boundary map
- `subduction_zones_0Ma.csv` — real subduction-zone line geometry (lon/lat + pre-projected Robinson x/y, grouped by `segment_id`), plotted on top of Notebook 3's earthquake dots so the line isn't buried underneath them
- `ridges_0Ma.csv` — real mid-ocean-ridge (spreading boundary) line geometry, same shape as `subduction_zones_0Ma.csv`, plotted alongside it on Notebook 3's earthquake map
- `velocity_<age>Ma.png` (×7 — real plate-velocity direction+speed arrows, for Notebook 1's second map)
- `basemap_atlantic_<age>Ma.png` (×2), `basemap_southern_ocean_<age>Ma.png` (×2, at 0 Ma and 60 Ma) — same, zoomed regional backgrounds
- `land_0Ma.geojson` … `land_300Ma.geojson` (7 files — kept for reference)
- `towns_through_time.csv`
- `notable_earthquakes.csv`
- `fossils_through_time.csv`
- `duck_path.csv` — the duck's real, land-avoiding sea route for Notebook 4, one row per step per age (see the "four more bug reports (v1.2)" addendum in STRATEGY_NOTES.md)
