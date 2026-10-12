"""Frame discipline: declared-CRS rule and mixed-frame diagnostics.

Contract (SRAF data convention, org-wide since WP03):
- business packs default crs=GCJ-02 (AMap/ Tencent map frame);
- OSM landmarks / OSM tiles / storage = WGS-84;
- internal geometry = WGS-84 only; conversions happen once at the boundary.
Mixing frames without conversion produced a measured ~623 m systematic offset
in Guangzhou (see MIXED_FRAME_GUANGZHOU_M and tests/golden_vectors.json).
"""
from __future__ import annotations

from enum import Enum

from coords_core.convert import haversine_m, wgs84_to_gcj02


class CRS(str, Enum):
    WGS84 = "WGS84"
    GCJ02 = "GCJ02"
    BD09 = "BD09"
    UNKNOWN = "UNKNOWN"


class FrameError(ValueError):
    """Raised when a frame-discipline rule is violated."""


def require_declared(crs: CRS | str) -> CRS:
    """Reject UNKNOWN frames at boundaries (fail-closed)."""
    crs = CRS(crs)
    if crs is CRS.UNKNOWN:
        raise FrameError(
            "CRS_UNKNOWN: frame must be declared (WGS84/GCJ02/BD09); "
            "mixed frames caused a measured ~623 m offset in Guangzhou")
    return crs


def to_wgs84(lon: float, lat: float, crs: CRS | str) -> tuple[float, float]:
    """Single entry point for boundary conversion into the WGS-84 frame."""
    crs = require_declared(crs)
    if crs is CRS.WGS84:
        return lon, lat
    if crs is CRS.GCJ02:
        from coords_core.convert import gcj02_to_wgs84
        return gcj02_to_wgs84(lon, lat)
    if crs is CRS.BD09:
        from coords_core.convert import bd09_to_wgs84
        return bd09_to_wgs84(lon, lat)
    raise FrameError(f"unhandled CRS {crs}")


# Guangzhou case (SRAF docs + tests/golden_vectors.json): magnitude of the
# apparent offset when GCJ-02 coordinates are read as WGS-84 (or vice versa).
MIXED_FRAME_GUANGZHOU_M = 623.0


def mixed_frame_offset_m(lon: float, lat: float) -> float:
    """Metre-scale magnitude of treating WGS-84 as GCJ-02 at this point.

    Diagnostic only: quantifies how wrong an undeclared frame can be.
    """
    gl, ga = wgs84_to_gcj02(lon, lat)
    return haversine_m(lon, lat, gl, ga)
