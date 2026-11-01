# 剖视图、截面读取与"读现有模型"

**分档约定**：✅ = 本机跑通并量化验证；📄 = 官方 CHM 参数已核对（参数个数、名称、类型），运行时未跑；⚠️ = 推断，需实测。

---

## 0. 实测配方：工程图剖视图（✅ 2026-10-29 跑通）

关键前提：SolidWorks 的剖视图不是"传坐标就出图"，而是**先把一条已选中的直线变成剖切线（`MakeSectionLine`），再调用 `CreateSectionViewAt5`**。少了 `MakeSectionLine`，`CreateSectionViewAt5` 一律返回 `None`（本机连试 3 种写法都是 `None`，加上它立刻就出图）。

```python
dm = swe.new_drawing(sw, 6)                       # A4
d  = swe.drw(dm)
v  = d.CreateDrawViewFromModelView3(part, "*前视", 0.10, 0.15, 0.0)   # 视图数 1 -> 2
sk = dm.SketchManager
sk.InsertSketch(True)                             # 图纸层开草图，不要 ActivateView
seg = sk.CreateLine(0.10, 0.125, 0, 0.10, 0.180, 0)   # 竖直剖切线，穿过视图
seg.Select2(False, 0)                             # 必须选中（选中数 = 1）
d.MakeSectionLine()                               # 缺这一步必失败
sec = d.CreateSectionViewAt5(0.10, 0.19, 0.0, "A", 0, None, 0)
sk.InsertSketch(True)                             # 退草图
```

实测结果：视图数 **2 → 3**，新视图名 `剖面视图 A-A`，`IView.Type = 2`（基础模型视图是 7）；落盘 `probe-output\sec3_drawing.SLDDRW` **71,596 B**。

读回剖视图（晚绑定即可，`GetSection()` 返回无类型 `_Dispatch`）：

```python
sec = view.GetSection()
sec.GetLabel()      # 'A'
sec.GetName()       # '剖切线1'
sec.GetArrowInfo()  # 12 个 double：两条箭头的起止点（图纸坐标，米）
sec.GetLineInfo()   # 6 个 double：剖切线端点（视图局部坐标，竖直方向是 ±0.025）
sec.GetAutoHatch()  # False
```

三条实测结论（与旧版本文档冲突时以本节为准）：

1. **不需要 `ActivateView`**。在图纸层 `InsertSketch` 后 `CreateLine` 返回 True；反过来"先 `ActivateView` 再 `InsertSketch`"，`CreateLine` 返回 `None`（线根本没建出来）。
2. `SelectByRay` **打不到视图里的模型边**（返回 `False`），剖切线只能用草图直线 + `Select2`。
3. `CreateSectionView()`（0 参）在同一条已选剖切线上**同样能出图**（视图数 2 → 3），可作为 `CreateSectionViewAt5` 的备选。

---

## 1. 工程图剖视图（Drawing section view）

### 1.1 五个重载，别乱选

| 方法 | 参数 | 说明 |
|---|---|---|
| `IDrawingDoc.CreateSectionViewAt5` | **7** | `(X, Y, Z, SectionLabel, Options, ExcludedComponents, SectionDepth)` ← **实测跑通，推荐** ✅ |
| `CreateSectionViewAt4` | 6 | 同上但**没有** `SectionDepth` |
| `CreateSectionViewAt3` | 11 | `(X, Y, Z, NotAligned, IsOffsetSection, Label, Chgdirection, Scwithmodel, Partial, Dispsurfcut, ExcludedComponents)` |
| `CreateSectionViewAt2` | 10 | 同 At3 去掉 `ExcludedComponents` |
| `CreateSectionView` | 0 | 旧式，靠已选对象 |

参数语义（官方原文，📄）：

- `X/Y/Z`：剖视图在**图纸上**的中心位置，单位**米**（与全文单位律一致，A4 图纸约 0.297×0.210）。
- `SectionLabel`：剖面字母，`"A"`。同一张图纸连续剖切要换字母。
- `Options`：`swCreateSectionViewAtOptions_e` 位掩码（实测真值）：`NotAligned=1`、`OffsetSection=2`、`ChangeDirection=4`、`ScaleWithModel=8`、`Partial=16`、`DisplaySurfaceCut=32`、`ExcludeFasteners=64`、`CutSurfaceBodies=128`；普通剖视传 `0`。
- `ExcludedComponents`：装配体要排除的零部件数组，传 `None`（VBS 传 `Nothing`）。
- `SectionDepth`：从所选剖切线起算的**剖切深度**（米）。`0` 通常按"完全贯穿"处理 ⚠️。

### 1.2 正确调用顺序（📄 文档要求 + 前序步骤已 ✅）

```
drw = swe.new_drawing(sw, paper=swe.PAPER_A4)                    # ✅ A4 图纸
view = swe.P(drw, 'CreateDrawViewFromModelView3', part, '*前视', 0.10, 0.15, 0.0)   # ✅
# 1) 先在视图里选一条线当剖切线（草图线段或模型边）
md.Extension.SelectByID2('Line1', 'SKETCHSEGMENT', 0, 0, 0, False, 0, None, 0)     # 📄
# 2) 再建剖视图，位置放在原视图右侧
sec = swe.P(drw, 'CreateSectionViewAt5', 0.20, 0.15, 0.0, 'A', 0, None, 0.0)       # 📄
```

**必须先有剖切线被选中**，否则返回 `None` 且不出视图——这与"拉伸前必须选中轮廓"是同一类前置条件（坑 23）。

### 1.3 读回剖面属性

`IDrSection`（由视图取得：`view.GetSection()` / `drw` 侧 `IDrSection.GetView()`、`GetSectionView()`，📄）共 26 项，常用：

| 成员 | 用途 |
|---|---|
| `GetLabel()` / `GetName()` | 剖面字母 / 内部名 |
| `GetLineInfo()` / `GetArrowInfo()` | 剖切线位置与箭头方向 |
| `GetAutoHatch()` | 是否自动剖面线 |
| `CutSurfaceBodies` / `DisplaySurfaceBodies` | 是否剖切/显示曲面体 |
| `EnumExcludedComponents()` / `GetExcludedComponents()` / `ExcludeFasteners` | 排除件（**装配剖视最常用**） |
| `GetDisplayOnlySpeedPakBodies()` / `GetDontCutAllInstances()` | 轻化与实例控制 |

---

## 2. 零件/装配内的三维剖面（3D section）

| 方法 | 参数 | 用途 |
|---|---|---|
| `IModelViewManager.CreateSectionView` | 1 | 建三维剖面视图（参数为 `ISectionViewData`，📄） |
| `IModelViewManager.CreateSectionViewData()` | 0 | 先拿数据对象，再填属性（与 FeatureData 同套路，**记得 QI**，见坑 21） |
| `IModelViewManager.GetSectionViewData` | 1 | 按索引取回 |
| `IModelViewManager.RemoveSectionView` | 0 | 删除 |
| `IPartDoc.GetSectionedBody(Boolean)` | 1 | **得到被剖切后的体**（用于测量/导出剖切结果）✅ 存在 |
| `IComponent2.GetSectionedBodies` | 1 | 装配组件同上 |
| `IModelDocExtension.GetSectionProperties` / `GetSectionProperties2` | 1 | 读剖面属性 |

---

## 3. 读现有模型（全部 ✅ 本机跑通）

```python
sw  = swe.connect()
md  = swe.md2(sw.OpenDoc7(typed_spec))        # 0.99 s，静默（见 silence.md）
```

| 要什么 | 怎么读 | 单位/形状 |
|---|---|---|
| 体积/面积/质量/质心/惯性矩 | `md.Extension.GetMassProperties2(1, False)` | 返回 `(status, arr13)`，索引 3=体积、4=面积、5=质量 |
| 包围盒 | `md.GetPartBox(False)` | **毫米**，`[x1,y1,z1,x2,y2,z2]` |
| 实体个数 | `md.EnumBodies3(0, True)` 或 `BodyFolder.GetBodies()` | 数组 |
| 单个实体质量 | `body.GetMassProperties(0.0)` | 索引 3=体积（索引 1 是 y 质心，别读错） |
| 特征树 | `md.FirstFeature()` → `GetNextFeature()` + `GetTypeName2()` | 跳过 16 个固定文件夹（见 ui-strings.md） |
| 特征尺寸 | `feat.GetFirstDisplayDimension()` → `GetNextDisplayDimension()` → `dim.SystemValue`（米） | 与 R4 同路 |
| 材质 | `body.GetMaterialPropertyName(2 params)`、`md.Extension.GetMaterialPropertyName` 📄 | 返回库文件名 + 材质名 |
| 工程图视图 | `drw.GetFirstView()` 是**图纸**，`P(v,'GetNextView')` 迭代子视图 | 图纸 → 视图1..N |
| 图纸名/比例 | `drw.GetCurrentSheet()` 📄 | 用户项目里此法"行为特殊"，以 `GetFirstView().GetName2()` 兜底 |

**只读巡检标准动作**：`Silent=True` + `ReadOnly=True` + `AddToRecentDocumentList=False` 打开 → 读体积/包围盒/特征数 → `CloseDoc`。不会改文件、不污染最近列表。

---

## 4. 其它建模入口的参数个数（📄 已核，未逐个跑）

| 工具 | 方法 | 参数 |
|---|---|---|
| 圆角 | `IFeatureManager.FeatureFillet3` | **14**（`Options, R1, R2, Rho, Ftyp, OverflowType, ConicRhoType, Radii, Dist2Arr, RhoArr, SetBackDistances, PointRadiusArray, PointDist2Array, PointRhoArray`） |
| 倒角 | `IFeatureManager.InsertFeatureChamfer` | **8**（`Options, ChamferType, Width, Angle, OtherDist, VertexChamDist1..3`） |
| 拔模 | `IDraftFeatureData2`（FeatureData 路线） | `Angle`（弧度）、`FacesToDraft`、`DirectionPull`、`FacePropagation`、`AllowReducedAngle` |
| 抽壳 | 需在 `IFeatureManager` 上按名字找（`FeatureShell` 未在索引命中） | ⚠️ 待查，别猜参数 |
| 实体级倒圆 | `IBody2.AddConstantFillets(2)` | 2 |
| 实体级拔模 | `IBody2.DraftBody(5)` / `DraftBody2(6)` | 5 / 6 |

**圆角/倒角必须先选中边**（`edge.Select2(False, mark)` 或 `SelectByRay` 的 `TypeWanted=1`），与草图轮廓同一逻辑。

---

## 5. 剖视图三条铁律

1. **先选剖切线再调用**——没有选中对象时 `CreateSectionViewAt5` 静默返回 `None`。
2. **位置是图纸坐标（米）且不能压在已有视图上**，A4 横向建议 `x ∈ [0.02, 0.28]`、`y ∈ [0.02, 0.19]`。
3. **装配剖视要显式排除件**（`ExcludedComponents`），否则标准件/紧固件会把剖面糊死；`IDrSection.ExcludeFasteners = True` 是更省事的替代。
