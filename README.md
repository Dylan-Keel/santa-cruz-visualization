# Santa Cruz Visualization

Registered aerial image time series ("flipbooks") for watersheds in Santa Cruz County, California, grouped by drainage. Each flipbook puts every date on one map grid so that flipping between years shows change in place.

## Flipbooks

| Drainage | Flipbook | Watersheds | Dates |
|---|---|---|---|
| Scott Creek | [Scott Creek watersheds](scott-creek/watersheds/) | Upper Scott Creek, Mill Creek, Big Creek, Little Creek | 1941 to 2025 |

## What the flipbook shows

- A 2D view of all four watersheds and fixed-camera 3D views draped on the 10 m elevation model
- Overlays: watershed divides, start point and confluences, streams, CAL FIRE historical fire perimeters
- Optional layers, off by default with an opacity slider: LiDAR canopy height, tall trees (LiDAR tops at least 200 ft tall with a full crown), and Topographic Wetness Index
- Play, pause, zoom, and save any frame as a still
- No parcel view, and no road or stream crossing layers

## Layout

```
scott-creek/watersheds/     viewer, frames, code
shared/                     page template, builder, layer and LiDAR code
```

In the flipbook folder, `index.html` is the viewer, the `.jpg` files are frames, the `.webp` files are the canopy and wetness layers, `tall_trees.csv` lists the flagged tree tops (UTM zone 10N, NAD83), the `.geojson` files are the watershed outlines, and `code/` holds the scripts that located, orthorectified and assembled the imagery.

## Sources

- Historic frames, 1941 to 1998: UCSB Library FrameFinder scans
- 2003, 2007, 2025: Santa Cruz County orthophotos (county image service)
- 2012 to 2022: USDA National Agriculture Imagery Program
- LiDAR: USGS 3DEP, Santa Cruz County, April 2020. Elevation: USGS 3DEP 10 m
- Streams: National Hydrography Dataset. Fire perimeters: CAL FIRE

## Caveats

Historic frames were orthorectified for this project. Measured offsets between adjacent dates are typically 4 to 10 m, more on steep ground. Watershed divides and stream lines are not a survey. The LiDAR survey predates the August 2020 CZU Lightning Complex, so canopy height and tall trees show the pre-fire forest. The tall tree layer is a LiDAR screen, not a timber cruise. The wetness index comes from a 10 m elevation model and shows where terrain concentrates drainage, not measured soil moisture.

This repo follows the same structure as `humboldt-visualization`. The tall tree threshold here is 200 ft where the Humboldt flipbooks use 131 ft, because 131 ft is an ordinary canopy height in this forest.
