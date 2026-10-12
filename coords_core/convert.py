"""Scalar conversions. Two accuracy tiers, both canonical:

- gcj02_to_wgs84 / wgs84_to_gcj02: 6-round fixed-point iteration
  (sub-millimetre round-trip; bit-for-bit compatible with the
  Territory-IR / SRAF production family).
- gcj02_to_wgs84_closed_form: one-step de-bias (max ~3 m in-China vs
  iterative, see tests/golden_vectors.json). Kept because spatial-ca
  publishes it as its public API; provided for compatibility, NOT for
  new callers.

BD-09 chain matches spatial_ca/geometry.py.
"""
from __future__ import annotations

import math
from typing import Tuple

from coords_core.kernels import A, EE, PI, _tl, _to

Point = Tuple[float, float]

_X_PI = math.pi * 3000.0 / 180.0


def out_of_china(lon: float, lat: float) -> bool:
    return not (72.0 <= lon <= 137.8 and 0.8 <= lat <= 55.8)


def wgs84_to_gcj02(lon: float, lat: float) -> Point:
    """WGS-84 -> GCJ-02. Points outside China pass through unchanged."""
    if out_of_china(lon, lat):
        return lon, lat
    rl = lat / 180.0 * PI
    magic = 1.0 - EE * math.sin(rl) ** 2
    sm = math.sqrt(magic)
    dlat = _tl(lon - 105.0, lat - 35.0)
    dlat = (dlat * 180.0) / ((A * (1.0 - EE)) / (magic * sm) * PI)
    dlon = _to(lon - 105.0, lat - 35.0)
    dlon = (dlon * 180.0) / (A / sm * math.cos(rl) * PI)
    return lon + dlon, lat + dlat


def gcj02_to_wgs84(lon: float, lat: float, rounds: int = 6) -> Point:
    """GCJ-02 -> WGS-84, 6-round fixed-point iteration (canonical tier)."""
    if out_of_china(lon, lat):
        return lon, lat
    w_lon, w_lat = lon, lat
    for _ in range(rounds):
        g_lon, g_lat = wgs84_to_gcj02(w_lon, w_lat)
        w_lon = lon + w_lon - g_lon
        w_lat = lat + w_lat - g_lat
    return w_lon, w_lat


def gcj02_to_wgs84_closed_form(lon: float, lat: float) -> Point:
    """GCJ-02 -> WGS-84, one-step closed form (compat tier, <=3 m in-China).

    Same function spatial-ca exposes as gcj02_to_wgs84. New callers should
    prefer the iterative gcj02_to_wgs84.
    """
    if out_of_china(lon, lat):
        return lon, lat
    d_lat = _tl(lon - 105.0, lat - 35.0)
    d_lng = _to(lon - 105.0, lat - 35.0)
    rad_lat = lat / 180.0 * PI
    magic = math.sin(rad_lat)
    magic = 1 - EE * magic * magic
    sqrt_magic = math.sqrt(magic)
    d_lat = (d_lat * 180.0) / ((A * (1 - EE)) / (magic * sqrt_magic) * PI)
    d_lng = (d_lng * 180.0) / (A / sqrt_magic * math.cos(rad_lat) * PI)
    return lon - d_lng, lat - d_lat


def bd09_to_gcj02(lon: float, lat: float) -> Point:
    x = abs(lon - 0.0065)
    y = abs(lat - 0.006)
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * _X_PI)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * _X_PI)
    return z * math.cos(theta), z * math.sin(theta)


def gcj02_to_bd09(lon: float, lat: float) -> Point:
    z = math.sqrt(lon * lon + lat * lat) + 0.00002 * math.sin(lat * _X_PI)
    theta = math.atan2(lat, lon) + 0.000003 * math.cos(lon * _X_PI)
    return z * math.cos(theta) + 0.0065, z * math.sin(theta) + 0.006


def bd09_to_wgs84(lon: float, lat: float) -> Point:
    gl, ga = bd09_to_gcj02(lon, lat)
    return gcj02_to_wgs84(gl, ga)


def wgs84_to_bd09(lon: float, lat: float) -> Point:
    gl, ga = wgs84_to_gcj02(lon, lat)
    return gcj02_to_bd09(gl, ga)


def convert(pt: Point, to_wgs: bool) -> Point:
    """Auto-direction single-point GCJ<->WGS; outside-China passes through.

    Compat API of the Territory-IR / SRAF family.
    """
    lon, lat = pt[0], pt[1]
    if out_of_china(lon, lat):
        return lon, lat
    return gcj02_to_wgs84(lon, lat) if to_wgs else wgs84_to_gcj02(lon, lat)


def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Great-circle distance in metres (frame-discipline diagnostics)."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# ---- compat aliases (Territory-IR / SRAF family names) ----
wgs2gcj = wgs84_to_gcj02
gcj2wgs = gcj02_to_wgs84
