"""WP03 conformance tests.

Golden vectors generated 2026-10-12 from the four pre-existing
implementations before they are switched to coords-core:
- iterative family: Territory-IR/territory_ir/coords.py == SRAF
  intelligence/coords.py (bit-for-bit identical 6-round fixed-point)
- closed form: spatial-ca-benchmark spatial_ca/geometry.py
Sources of truth recorded in tests/golden_vectors.json.
"""
import json
import math
from pathlib import Path

import pytest

from coords_core import (
    A, EE, PI,
    CRS, FrameError, MIXED_FRAME_GUANGZHOU_M,
    bd09_to_gcj02, bd09_to_wgs84, convert, gcj02_to_bd09,
    gcj02_to_wgs84, gcj02_to_wgs84_closed_form, haversine_m,
    out_of_china, require_declared, to_wgs84, wgs84_to_bd09, wgs84_to_gcj02,
)

GOLDEN = json.loads(
    (Path(__file__).parent / "golden_vectors.json").read_text(encoding="utf-8"))


def test_in_china_iterative_matches_golden_bitwise():
    """coords-core must reproduce the production iterative family exactly."""
    for v in GOLDEN["vectors"]:
        if v["out_of_china"]:
            continue
        assert wgs84_to_gcj02(*v["wgs_input"]) == tuple(v["gcj"]), v["city"]
        assert gcj02_to_wgs84(*v["gcj"]) == tuple(v["wgs_roundtrip_iterative"]), v["city"]


def test_closed_form_matches_golden():
    for v in GOLDEN["vectors"]:
        if v["out_of_china"]:
            continue
        assert gcj02_to_wgs84_closed_form(*v["gcj"]) == tuple(v["wgs_closed_form"]), v["city"]


def test_closed_form_within_5m_of_iterative_in_china():
    for v in GOLDEN["vectors"]:
        if v["out_of_china"]:
            continue
        it = v["wgs_roundtrip_iterative"]
        cf = v["wgs_closed_form"]
        d = haversine_m(it[0], it[1], cf[0], cf[1])
        assert d <= 5.0, (v["city"], d)


def test_roundtrip_residual_submillimetre():
    for v in GOLDEN["vectors"]:
        if v["out_of_china"]:
            continue
        it = v["wgs_roundtrip_iterative"]
        d = haversine_m(v["wgs_input"][0], v["wgs_input"][1], it[0], it[1])
        assert d < 0.001, (v["city"], d)


def test_out_of_china_passthrough_all_tiers():
    for v in GOLDEN["vectors"]:
        if not v["out_of_china"]:
            continue
        lon, lat = v["wgs_input"]
        assert gcj02_to_wgs84(lon, lat) == (lon, lat)
        assert gcj02_to_wgs84_closed_form(lon, lat) == (lon, lat)
        assert wgs84_to_gcj02(lon, lat) == (lon, lat)


def test_guangzhou_mixed_frame_offset_near_623m():
    """SRAF documented case: reading GCJ-02 as WGS-84 (no conversion) shifted
    everything ~623 m (E-549/N+293). Golden point reproduces the magnitude and
    direction (sign convention: as_wgs = gcj treated as wgs)."""
    v = next(v for v in GOLDEN["vectors"] if v["city"] == "guangzhou")
    lon, lat = v["wgs_input"]
    gcj = v["gcj"]
    east_m = (gcj[0] - lon) * 111320.0 * math.cos(math.radians(lat))
    north_m = (gcj[1] - lat) * 111320.0
    offset = math.hypot(east_m, north_m)
    assert abs(offset - MIXED_FRAME_GUANGZHOU_M) <= 5.0
    # direction: gcj point sits E/N of truth here; reading gcj-as-wgs shifts
    # positions by -(east, north). SRAF's documented E-549/N+293 is that
    # negation of this vector (convention difference, same physical case).
    assert east_m > 0 and north_m < 0
    gf = GOLDEN["guangzhou_mixed_frame"]
    assert abs(gf["offset_m"] - MIXED_FRAME_GUANGZHOU_M) <= 5.0


def test_bd09_chain_matches_golden():
    # golden example used the closed-form tier (spatial-ca provenance);
    # coords_core.bd09_to_wgs84 is the iterative canonical tier: <=5 m apart
    wl, wa = bd09_to_wgs84(113.30, 23.10)
    ge, ga = GOLDEN["bd09_example"]
    assert haversine_m(wl, wa, ge, ga) <= 5.0
    # bd09 roundtrip
    gl, ga = bd09_to_gcj02(113.30, 23.10)
    bl, ba = gcj02_to_bd09(gl, ga)
    # BD-09 encode/decode is an approximate inverse pair (~1e-5 deg)
    assert abs(bl - 113.30) < 2e-5 and abs(ba - 23.10) < 2e-5
    # wgs->bd09 must land within ~3 m of the reverse-only example
    wl, wa = wgs84_to_bd09(*GOLDEN["bd09_example"])
    d = haversine_m(wl, wa, 113.30, 23.10)
    assert d < 5.0, d


def test_constants_match_legacy_modules():
    # Territory-IR / SRAF / spatial_ca constants
    assert A == 6378245.0
    assert EE == 0.00669342162296594323


def test_frame_discipline_rejects_unknown():
    with pytest.raises(FrameError):
        require_declared("UNKNOWN")
    assert require_declared("GCJ02") == CRS.GCJ02
    lon, lat = 118.3766, 31.3340
    assert to_wgs84(lon, lat, "WGS84") == (lon, lat)
    back = to_wgs84(*wgs84_to_gcj02(lon, lat), "GCJ02")
    # GCJ->WGS is a fixed-point inverse: sub-millimetre, not bit-exact
    assert haversine_m(back[0], back[1], lon, lat) < 0.001


def test_convert_auto_direction():
    v = next(v for v in GOLDEN["vectors"] if v["city"] == "beijing")
    lon, lat = v["wgs_input"]
    assert convert((lon, lat), to_wgs=False) == tuple(v["gcj"])
    assert convert(v["gcj"], to_wgs=True) == tuple(v["wgs_roundtrip_iterative"])
