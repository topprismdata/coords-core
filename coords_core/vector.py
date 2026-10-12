"""Optional numpy-vectorized batch conversions (Territory-IR family API).

numpy is imported lazily inside each function; the rest of coords-core is
stdlib-only.
"""
from __future__ import annotations

from coords_core.kernels import A, EE, PI


def _tl_vec(x, y):
    import numpy as np
    r = -100.0 + 2.0*x + 3.0*y + 0.2*y*y + 0.1*x*y + 0.2*np.sqrt(np.abs(x))
    r += (20.0*np.sin(6.0*x*PI) + 20.0*np.sin(2.0*x*PI)) * 2.0/3.0
    r += (20.0*np.sin(y*PI) + 40.0*np.sin(y/3.0*PI)) * 2.0/3.0
    r += (160.0*np.sin(y/12.0*PI) + 320.0*np.sin(y*PI/30.0)) * 2.0/3.0
    return r


def _to_vec(x, y):
    import numpy as np
    r = 300.0 + x + 2.0*y + 0.1*x*x + 0.1*x*y + 0.1*np.sqrt(np.abs(x))
    r += (20.0*np.sin(6.0*x*PI) + 20.0*np.sin(2.0*x*PI)) * 2.0/3.0
    r += (20.0*np.sin(x*PI) + 40.0*np.sin(x/3.0*PI)) * 2.0/3.0
    r += (150.0*np.sin(x/12.0*PI) + 300.0*np.sin(x*PI/30.0)) * 2.0/3.0
    return r


def wgs2gcj_vec(lon, lat):
    """Vectorized WGS-84 -> GCJ-02."""
    import numpy as np
    lon = np.asarray(lon, dtype=float)
    lat = np.asarray(lat, dtype=float)
    rl = lat / 180.0 * PI
    magic = 1.0 - EE * np.sin(rl) ** 2
    sm = np.sqrt(magic)
    dlat = _tl_vec(lon - 105.0, lat - 35.0)
    dlat = (dlat * 180.0) / ((A * (1.0 - EE)) / (magic * sm) * PI)
    dlon = _to_vec(lon - 105.0, lat - 35.0)
    dlon = (dlon * 180.0) / (A / sm * np.cos(rl) * PI)
    return lon + dlon, lat + dlat


def gcj2wgs_vec(lon, lat, rounds: int = 6):
    """Vectorized GCJ-02 -> WGS-84 (fixed-point iteration, canonical tier)."""
    import numpy as np
    lon = np.asarray(lon, dtype=float)
    lat = np.asarray(lat, dtype=float)
    w_lon, w_lat = lon.copy(), lat.copy()
    for _ in range(rounds):
        g_lon, g_lat = wgs2gcj_vec(w_lon, w_lat)
        w_lon = lon + w_lon - g_lon
        w_lat = lat + w_lat - g_lat
    return w_lon, w_lat
