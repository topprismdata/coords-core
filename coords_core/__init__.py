"""coords-core: single source of truth for China coordinate conversions.

Compatibility exports (the three consumer families):
- Territory-IR / SRAF names: wgs2gcj, gcj2wgs, out_of_china, convert,
  A, EE, PI
- spatial-ca names: gcj02_to_wgs84_closed_form, bd09_to_gcj02, bd09_to_wgs84
- canonical names: wgs84_to_gcj02, gcj02_to_wgs84 (iterative), ...
Frame discipline lives in coords_core.frames.
"""
from coords_core.kernels import A, EE, PI
from coords_core.convert import (
    Point,
    bd09_to_gcj02,
    bd09_to_wgs84,
    convert,
    gcj02_to_bd09,
    gcj02_to_wgs84,
    gcj02_to_wgs84_closed_form,
    haversine_m,
    out_of_china,
    wgs84_to_bd09,
    wgs84_to_gcj02,
)
from coords_core.frames import (
    CRS,
    MIXED_FRAME_GUANGZHOU_M,
    FrameError,
    mixed_frame_offset_m,
    require_declared,
    to_wgs84,
)

__version__ = "0.1.0"

# family-compat aliases
wgs2gcj = wgs84_to_gcj02
gcj2wgs = gcj02_to_wgs84

__all__ = [
    "A", "EE", "PI", "Point",
    "bd09_to_gcj02", "bd09_to_wgs84", "convert",
    "gcj02_to_bd09", "gcj02_to_wgs84", "gcj02_to_wgs84_closed_form",
    "haversine_m", "out_of_china", "wgs84_to_bd09", "wgs84_to_gcj02",
    "wgs2gcj", "gcj2wgs",
    "CRS", "MIXED_FRAME_GUANGZHOU_M", "FrameError",
    "mixed_frame_offset_m", "require_declared", "to_wgs84",
    "__version__",
]
