# coords-core

中国坐标转换与帧纪律的唯一事实源（Module-1 数据管理整合计划 WP03 产物）。

## 背景

WP03 之前组织内有四套 GCJ-02 ⇄ WGS-84 实现：

| 来源 | 算法 | 状态 |
|---|---|---|
| Territory-IR `territory_ir/coords.py` | 6 轮定点迭代（亚毫米往返） | 与 SRAF 逐位一致 → **收敛为本库** |
| SRAF `intelligence/coords.py` | 同上（6 轮迭代）+ 数据包帧纪律 | 转换函数收敛；pack 级帧流程留在 SRAF |
| spatial-ca `spatial_ca/geometry.py` | 闭式一步 de-bias（境内 ≤3m）+ BD-09 链 | 收敛为 compat 层（新调用方请用迭代版） |
| geospatial-data-governance | 设计规范（无代码） | 规范语义由本库实现 |

金标向量与偏差实测见 `tests/golden_vectors.json`（2026-10-12 自四实现生成）：
迭代往返残差 <1e-14 度；闭式 vs 迭代境内最大 ~3.1m（漠河，高纬）；广州混帧表观
偏移 621.7m（方向 E-545.6/N+298.0，与 SRAF 记载 623m/E-549/N+293 吻合）。

## 帧纪律

- 数据包（门店/围栏/合同中心）默认 `GCJ-02`；OSM 地物/存储/内部几何 = `WGS-84`；
- 边界处用 `frames.to_wgs84(lon, lat, crs)` 一次转换；`UNKNOWN` 帧直接
  `FrameError`（fail-closed）；
- 混帧不转换 = 广州实测 ~623m 系统偏移（`MIXED_FRAME_GUANGZHOU_M`）。

## 用法

```python
from coords_core import gcj02_to_wgs84, wgs84_to_gcj02, to_wgs84, CRS

# 迭代版（规范层，新代码一律用这个）
wgs = gcj02_to_wgs84(113.2644, 23.1291)          # GCJ -> WGS
gcj = wgs84_to_gcj02(*wgs)                        # WGS -> GCJ

# 帧纪律入口
wgs = to_wgs84(113.2644, 23.1291, CRS.GCJ02)

# 兼容层（旧 API 名全部保留）
from coords_core import wgs2gcj, gcj2wgs, convert            # Territory-IR/SRAF 名
from coords_core import gcj02_to_wgs84_closed_form, bd09_to_wgs84  # spatial-ca 名

# 可选 numpy 批量
from coords_core.vector import wgs2gcj_vec, gcj2wgs_vec
```

## 迁移状态（各仓切换引用）

| 仓库 | 方式 | 状态 |
|---|---|---|
| spatial-ca-benchmark | `pyproject` git 依赖 + `geometry.py` 内部转发 | 见该仓 WP03 提交 |
| Territory-IR | `territory_ir/coords.py` 薄 shim 再导出 | 同上 |
| SRAF | `intelligence/coords.py` 薄 shim 再导出（pack 级流程保留） | 同上 |

依赖声明（PEP 508 direct reference，锁定 tag）：

```
coords-core @ git+https://github.com/topprismdata/coords-core.git@v0.1.0
```

## 规则

修改 `kernels.py` 常数/公式 = 跨仓破坏性变更：必须同步升级三个消费仓并重出
金标向量。`tests/test_conformance.py` 用 golden vectors 锁定位级一致。
