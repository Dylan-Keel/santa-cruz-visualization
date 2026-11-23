# Shared code

- `page.tpl`: the viewer page template
- `build.py`: assembles a flipbook site from orthorectified mosaics (run from a site folder holding `cfg.py`, `cams.py`, `frames.json`, `site.json`)
- `layers.py`: Topographic Wetness Index, canopy height coloring, tall tree detection
- `overlays.py`: writes the canopy and wetness layers and the tree list for a site
- `lidar_copc.py`: builds 1 m surface and ground grids from USGS 3DEP LiDAR, reading COPC tiles to 1 m spacing
- `stage.py`: makes the flat hosted copy of a site

Python 3 with numpy, scipy, matplotlib, opencv, rasterio, geopandas, shapely, pysheds, laspy (with lazrs), pystac-client, planetary-computer and Pillow.
