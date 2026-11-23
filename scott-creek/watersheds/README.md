# Scott Creek Watersheds Flipbook

A registered aerial image time series for four watersheds in the Scott Creek drainage, Santa Cruz County: Upper Scott Creek (5,644 ac, everything draining to 37.0804 N, 122.2469 W), Mill Creek (2,404 ac), Big Creek (7,183 ac) and Little Creek (1,335 ac). The three tributaries are each taken above their confluence with Scott Creek.

Open `index.html` to view it.

## What is in it

- Sixteen dates from March 1941 to 2025
- Four views: all four watersheds in plan, 3D Upper Scott Creek, 3D Big Creek, and 3D of all four from above the coast
- Optional layers: LiDAR canopy height and tall trees (April 2020, before the CZU Lightning Complex), Topographic Wetness Index, CAL FIRE perimeters
- Play, pause, zoom, and save any frame as a still

## Known gaps

- 1941 covers 95 percent of Upper Scott Creek, 51 percent of Mill Creek, 24 percent of Big Creek and 73 percent of Little Creek. Every later date covers all four.
- No scanned frames between 1963 and 1985.
- The county orthophotos (2003, 2007, 2025) carry a year but no flight date.

`basins.geojson` holds the four watershed polygons, `tall_trees.csv` the flagged LiDAR tops, and `code/` the scripts.
