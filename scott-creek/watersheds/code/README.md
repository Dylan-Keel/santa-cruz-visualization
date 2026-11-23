# Code

Scripts that located, orthorectified and assembled the imagery for this flipbook. They were run in order by hand and are kept as a record of method. Shared page, layer and LiDAR code is in `/shared`.

Order: `dl.py` (scans), `modern.py` (NAIP and county orthophotos), `chain.py` (which calls `fitall.py`, `refine.py` and `mos2.py`, working backward in time), `lidar_copc.py` and `ov_big.py` (canopy, tall trees, wetness index), `mkframes.py` (frame list and page text), then `build.py` and `stage.py` from `/shared`. `county_reuse.py` was a stand-in used while the county image service was down.

The first build covered Upper Scott Creek alone on a grid 4 km to the west. Its camera fits were carried over, which is why `cfg.py` keeps the original pose origin.
