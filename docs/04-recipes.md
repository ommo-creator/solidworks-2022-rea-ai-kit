# 可运行配方（Python + comtypes）

前提：`scripts/swe.py` 在同目录（或用 `SKILL_DIR/scripts` 加 `sys.path`）。

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
import swe
```

`sw = swe.connect()` 连上 SolidWorks；`md = swe.new_part(sw)` 新建零件并强类型化；`swe.P(obj, "Method", ...)` 绕开 `_Dispatch` 不可调用问题。

---

## R1 板 + 通孔 + 线性/圆周阵列

```python
sw = swe.connect()
swe.quiet(sw)                    # 关掉尺寸输入框与过定义提示
md = swe.new_part(sw)

# 主体 100×60×20
sk = md.SketchManager
sk.InsertSketch(True)
sk.CreateCornerRectangle(0, 0, 0, 0.10, 0.06, 0)
sk.InsertSketch(True)
md.ClearSelection2(True)
feat = swe.feature_profile(md)                  # 选 ProfileFeature
sw_feat = md.FeatureManager.FeatureExtrusion2(
    True, False, False, 0, 0, 0.020, 0.010,
    False, False, False, False,
    0.0174532925199433, 0.0174532925199433,
    False, False, False, False,
    True, True, True, 0, 0.0, False)
assert sw_feat is not None

# 顶面 D12 通孔：必须画在被切的那个面上
md.ClearSelection2(True)
assert md.Extension.SelectByRay(0.05, 0.03, 0.020, 0, 0, 1, 0.001, 2, False, 0, 0)
sk.InsertSketch(True)
sk.CreateCircleByRadius(0.02, 0.02, 0, 0.006)
sk.InsertSketch(True)
md.ClearSelection2(True)
swe.feature_profile(md)
cut = md.FeatureManager.FeatureCut4(
    True, False, False, 1, 0, 0.0, 0.0,
    False, False, False, False, 0.0, 0.0,
    False, False, False, False, False,
    True, True, False, False, False,
    0.0, 0.0, False, False)
assert cut is not None
# 判据：体积 ≈ 1.17738e-4

# 线性阵列 3×，间距 25 mm：特征 mark 4 + 方向参考 mark 1
md.ClearSelection2(True)
cut.Select2(False, 4)
assert md.Extension.SelectByID2("右视基准面", "DATUMPLANE", 0, 0, 0, True, 1, None, 0)
md.FeatureManager.FeatureLinearPattern5(
    3, 0.025, 1, 0.0, False, False, "", "",
    False, False, False, False, True,
    False, False, False, False, False, 0.0, 0.0, False, False)
# 判据：体积 ≈ 1.132142e-4

# 圆周阵列：轴 = 外侧圆柱面（射线打侧面），mark 1；特征 mark 4
md.ClearSelection2(True)
md.Extension.SelectByRay(0.300, 0, 0.040, -1, 0, 0, 0.001, 2, True, 1, 0)
md.Extension.SelectByID2("", "FACE", 0, 0, 0, True, 4, None, 0)  # 或 cut.Select2(True,4)
md.FeatureManager.FeatureCircularPattern4(
    6, 6.283185307179586, False, "", False, True, False)
```

---

## R2 装配

```python
sw = swe.connect()
asm = sw.INewAssembly()
asm.SaveAs(r"...\re2_asm.SLDASM")

sw.OpenDoc6(plate_path, 1, 1, "", 0, 0)   # 先 preload，否则 AddComponent5 失败
sw.OpenDoc6(cube_path, 1, 1, "", 0, 0)
asm.AddComponent5(plate_path, 0, "", False, "", 0.0, 0.0, 0.0)   # 8 参
asm.AddComponent5(cube_path, 0, "", False, "", 0.15, 0.03, 0.05)
comps = asm.GetComponents(False)          # 2

# 注意：坐标是「包围盒中心」，不是几何原点
# 配合：末位 ErrorStatus 被 comtypes 摘掉 → 14 参
asm.AddMate5(0, 0, False, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0, False, False)
# 判据：目标组件 GetXform() 平移发生变化；特征树出现 MateGroup
asm.SaveAs(r"...\re2_asm.SLDASM")
```

`asm.GetMates` 在本版本不存在，别调。

---

## R3 工程图

```python
sw = swe.connect()
drw = sw.INewDrawing(6)                                    # A4
drw.CreateDrawViewFromModelView3(part_path, "*前视", 0.10, 0.15, 0.0)
drw.Create3rdAngleViews2(part_path)                        # 总数 1 → 5
# 遍历：GetFirstView() 返回的是「图纸」，子视图靠 GetNextView 迭代
v, n = drw.GetFirstView(), 1
while v is not None:
    v = swe.P(v, "GetNextView"); n += v is not None
drw.SaveAs(r"...\re3_drawing.SLDDRW")
```

`P(v,"GetNextView")` 必须包：裸调 `v.GetNextView()` 会 `TypeError: '_Dispatch' object is not callable`。

---

## R4 尺寸驱动

```python
sw = swe.connect()
swe.quiet(sw)                              # 关键：否则弹「修改」框挂死
md = swe.new_part(sw)
sk = md.SketchManager

sk.InsertSketch(True)
sk.CreateCornerRectangle(0, 0, 0, 0.10, 0.06, 0)
seg = swe.segments(sk)[0]                  # 已 QueryInterface，可直接 Select2
seg.Select2(False, 0)
md.AddDimension2(0.05, 0.075, 0)
dim = swe.P(md, "Parameter", "D1@草图1@零件1.Part")
dim.SystemValue = 0.080                     # 米
md.EditRebuild3()

md.ClearSelection2(True)                           # 关键：清残留选择
sk.InsertSketch(True)
md.FeatureManager.FeatureExtrusion2(... 23 参 ...)
# 判据：80mm → 9.6e-5；50mm → 6e-5；120mm → 1.44e-4
```

尺寸全名形如 `D1@草图1@零件3.Part`。

---

## R5 质量与体数

```python
md = ...
status, arr = md.Extension.GetMassProperties2(1, False)     # 2 实参
Vol, Area, Mass = arr[3], arr[4], arr[5]                    # 米³ / 米² / kg
part = md
n = swe.bodies_count(md)                                     # 1
bbox = swe.bbox(md)                                          # 毫米 [0,0,0,100,60,20]
```

`CreateMassProperty()` 在没有材质时 `Density=1.0`、`Mass=Volume`，只能看体积趋势，不能当质量。

---

## R6 回转（球头 / 半圆球）

```python
md = swe.new_part(sw)
sk = md.SketchManager
md.Extension.SelectByID2("前视基准面", "DATUMPLANE", 0, 0, 0, False, 0, None, 0)
sk.InsertSketch(True)
# 半圆弧
sk.CreateArc(0, 0, 0, 0, 0.05, 0, 0, -0.05, 0, 1)
# 构造轴线（必须设 ConstructionGeometry 否则回转找不到轴）
axis = sk.CreateLine(0, -0.06, 0, 0, 0.06, 0)
axis.ConstructionGeometry = True          # 在 segment 上！
sk.InsertSketch(True)
md.ClearSelection2(True)
swe.feature_profile(md)
md.FeatureManager.FeatureRevolve2(
    True, True, False, False, False, False,
    0, 0, 6.283185307179586, 0.0,
    False, False, 0.0, 0.0, 0, 0.0, 0.0,
    True, True, True)
```

⚠️ 只画「半圆弧 + 构造轴线」。若再画一条与轴重合的直线去闭合轮廓 → 轮廓退化，`FeatureRevolve2` 返回 `None`。

---

## R10 圆角 `FeatureFillet3`（14 参，✅ 体积精确到 1e-20）

原理：先射线选中一条**棱边**（`SelectByRay(..., TypeWanted=1, ...)`），再调 `FeatureFillet3`。**Options 必须是 `2`（swFeatureFilletUniformRadius）**，否则 R1 不生效。

```python
md, fm = swe.new_part(sw), None
fm = md.FeatureManager
# ... 先建 100x60x20 板（体积 1.2e-4）
swe.clear(md)
ok = md.Extension.SelectByRay(0.16, 0.12, 0.010, -0.7071, -0.7071, 0.0, 0.0004, 1, False, 0, 0)
assert md.SelectionManager.GetSelectedObjectCount2(-1) >= 1     # 不要用 GetSelectedObjectType3 判断类型
f = fm.FeatureFillet3(2, 0.005, 0.0, 0.0, 0, 0, 0,
                      None, None, None, None, None, None, None)
```

- 参数序：`(Options, R1, R2, Rho, Ftyp, OverflowType, ConicRhoType, Radii, Dist2Arr, RhoArr, SetBackDistances, PointRadiusArray, PointDist2Array, PointRhoArray)`
- `Ftyp = 0` 简单圆角（`VariableRadius=1 / Face=2 / FullRound=3`）；`OverflowType = 0`（`KeepEdge=1 / KeepSurface=2`）；`ConicRhoType = 0`（`Circular`）。
- 实测：r=5 mm 单条竖棱 → 特征 `圆角1`，体积 `1.2e-4 → 1.198927e-4`，去料 `1.0730091830e-7`，与理论 `(1-π/4)·r²·L = 1.07300918296e-7` **完全一致**。
- 变量半径 / 面圆角 / 非对称要把 `Radii` / `Dist2Arr` 传数组（每选中对象一项），本机未跑。

## R11 倒角 `InsertFeatureChamfer`（8 参，✅）

```python
c = fm.InsertFeatureChamfer(0, 1, 0.003, 0.7853981633974483, 0.003, 0.0, 0.0, 0.0)
# 参数：(Options, ChamferType, Width, Angle, OtherDist, VertexDist1, VertexDist2, VertexDist3)
```

- `Options`：`swFeatureChamferOption_e` = `FlipDirection=1 / KeepFeature=2 / TangentPropagation=4 / PropagateFeatToParts=8`（0 = 默认）。
- `ChamferType`：`swChamferType_e` = `AngleDistance=1 / DistanceDistance=2 / Vertex=3 / EqualDistance=16`。
- 实测（先选同一条棱边，`AngleDistance`、3 mm、45°）→ 特征 `倒角1`，体积 `1.2e-4 → 1.1991e-4`，去料 `9.0e-8` = `0.5·w²·L` 精确。

## R12 抽壳 `IModelDoc2.InsertFeatureShell`（2 参，✅）

```python
md.ClearSelection2(True)                 # 不选面 = 闭合壳
md.InsertFeatureShell(0.002, False)      # (Thickness, Outward)；返回 Void
```

- **开口壳**：先用 `swe.select_face(md, 0.05, 0.03, 0.020, 0, 0, -1)` 选中要开口的面，再调；被选中的面即"移除面"。
- 实测（100×60×20 板、t=2 mm）：闭合壳体积 `3.39840e-5`（理论 `1.2e-4 - 0.096·0.056·0.016`，误差 1.4e-20）；开口壳 `2.32320e-5`（理论 `1.2e-4 - 0.096·0.056·0.018`，误差 6.8e-21）；特征名都是 `抽壳1`。
- 多厚度 / 指定移除面集合：改用 `IShellFeatureData`（`Thickness`、`FacesRemoved`、`Direction`、`AccessSelections`），本机未跑。

## R14 配合读回（装配）

```python
asm = qi(swe.new_assembly(sw), SW.IAssemblyDoc)      # 注意分层 QI
md  = qi(asm, SW.IModelDoc2)
asm.AddComponent5(part, 0, "", False, "", x, y, z)   # 零件须先 OpenDoc6 预加载
md.Extension.SelectByRay(...)                        # 选两个面，TypeWanted=2
r = asm.AddMate5(5, 2, False, 0.010, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, False, False, 0)
# r == (1, POINTER(IMate2))  -> 状态 + 配合对象

f = qi(md.FirstFeature(), SW.IFeature)
while f:
    if f.GetTypeName2() == 'MateGroup':                       # 名「配合」
        sub = qi(f.GetFirstSubFeature(), SW.IFeature)         # 类型 MateDistanceDim，名「距离1」
        spec = qi(sub.GetSpecificFeature2(), SW.IMate2)
        spec.Type, spec.Alignment, spec.GetMateEntityCount()
        ent = qi(spec.MateEntity(0), SW.IMateEntity2)
        dd  = qi(spec.DisplayDimension, SW.IDisplayDimension)
        d   = qi(dd.GetDimension(), SW.IDimension)            # D1@距离1@xxx.Assembly
    f = qi(swe.P(f, 'GetNextFeature'), SW.IFeature)
```

- 实测（板顶面 + 立方体底面、距离 10 mm）：`Type=5`（距离）、`Alignment=1`（ANTI_ALIGNED）、
  `GetMateEntityCount()=2`、`MateEntity(0).ReferenceType=3`（面）、
  `EntityParams=[-0.05,-0.03,0.01,0,0,1,0,0]` 与 `[0.14,0.02,0.02,0,0,-1,0,0]`（点 xyz + 法向 xyz + 2），
  `DisplayDimension.GetNameForSelection()='D1@距离1'`、`Value=10.0`(mm) / `SystemValue=0.01`(m)。
- `swMateType_e`：COINCIDENT 0 / CONCENTRIC 1 / PERPENDICULAR 2 / PARALLEL 3 / TANGENT 4 /
  **DISTANCE 5** / ANGLE 6 / UNKNOWN 7 / SYMMETRIC 8 / CAMFOLLOWER 9 / GEAR 10 / WIDTH 11 / LOCK 16 / SCREW 17。
- `swMateAlign_e`：ALIGNED 0 / ANTI_ALIGNED 1 / CLOSEST 2。
- 读不出配合的原因几乎总是 QI 层级不对，不是 API 缺失（`GetMates` 在本版本确实不存在）。

## R15 保存 / 导出与错误码

```python
# IModelDoc2.SaveAs4(Name, Version, Options)   [out] 参数不要传
err, warn, ok = md.SaveAs4(r"D:\out\a.SLDPRT", 0, 1)      # 0=当前版本, 1=覆盖+静默

# 带 ExportData（STEP 用 214；实测不带也能导出）
exp = sw.GetExportFileData(214)
err, warn, ok = md.Extension.SaveAs(r"D:\out\a.STEP", 0, 1, exp)

# 老接口直接返回错误码（int，不分离 warn）
code = md.SaveAs3(path, 0, 1)      # 0=成功
code = md.SaveAs2(path, 0, True, True)
```

实测对照（100×60×20 板，本机 SW 2022 SP5）：

| 场景 | ok | errors | warnings |
| --- | --- | --- | --- |
| 新建 / 覆盖（options=0 或 1） | True | 0 | 0 |
| 非法盘符 `Z:\nope\x` | False | **1** `swGenericSaveError` | 0 |
| 目标目录不存在 | False | **1** | 0 |
| 文件名含 `<` `>` | False | **1** | 0 |
| 目标文件只读 | False | **1**（**不是** 2 `swReadOnlySaveError`） | 0 |
| 空文件名 `""` | False | **256** `swFileSaveAsInvalidFileExtension` | 0 |
| 未知扩展名 `.UNKNOWNEXT` | False | **256** | 0 |
| STEP 导出（带/不带 ExportData） | True | 0 | 0 |
| `SaveAs3` / `SaveAs2` 非法盘符 | — | 返回 **1** | — |

- `swSaveAsOptions_e` 位掩码：Silent 1 / Copy 2 / SaveReferenced 4 / AvoidRebuildOnSave 8 /
  UpdateInactiveViews 16 / OverrideSaveEmodel 32 / SaveEmodelData 64 / DetachedDrawing 128 /
  IgnoreBiography 256 / CopyAndOpen 512 / IncludeVirtualSubAsmComps 1024。
- `swFileSaveError_e`（14 项）：Generic 1 / ReadOnly 2 / FileNameEmpty 4 / ContainsAtSign 8 /
  FileLock 16 / FormatNotAvailable 32 / WithRebuild 64 / DoNotOverwrite 128 / InvalidFileExtension 256 /
  NoSelection 512 / BadEDrawingsVersion 1024 / NameExceedsMaxPathLength 2048 / NotSupported 4096 /
  RequiresSavingReferences 8192（**是累加位，不是序号**）。
- `swSaveAsVersion_e`：CurrentVersion 0 / SW98plus 1 / FormatProE 2 / StandardDrawing 3 / DetachedDrawing 4。

---

## R16 孔向导：CreateDefinition → InitializeHole → 命名属性 → CreateFeature

```python
md.ClearSelection2(True)
swe.select_face(md, 0.05, 0.03, 0.020, 0, 0, 1, 0)      # 只选面，别预建草图
fd = md.FeatureManager.CreateDefinition(25)             # 25 = swFmHoleWzd
fd = fd.QueryInterface(SW.IWizardHoleFeatureData2)      # 不 QI -> 0x80020006
fd.InitializeHole(0, 13, 376, 'M12', 1)                 # 沉头孔 / GB / 六角头 / M12 / 贯穿
fd.CounterBoreDiameter = 0.024
fd.CounterBoreDepth    = 0.008
feat = md.FeatureManager.CreateFeature(fd)
md.EditRebuild3()
```

判据：板 1.2e-4 → 去料 `5.336781e-6`；理论 `π(0.0135/2)²·0.02 + π((0.024/2)²-(0.0135/2)²)·0.008 = 5.33672e-6`。
`Value1..Value12` 在本路线里根本不存在——它们是 `HoleWizard5` 的旧覆盖槽。

## R17 改已有孔：AccessSelections + ModifyDefinition

```python
feat = hole.QueryInterface(SW.IFeature)
fd = feat.GetDefinition().QueryInterface(SW.IWizardHoleFeatureData2)
fd.AccessSelections(md, None)      # ★ 不调用的话属性会变、几何不变
fd.CounterBoreDiameter = 0.022
fd.CounterBoreDepth    = 0.006
feat.ModifyDefinition(fd, md, None)
md.EditRebuild3()
```

判据：去料 `4.139048e-6`，理论 `4.139048e-6`，偏差 `2.0e-20`。
改盲孔：`fd.EndCondition = 0`、`fd.ThruHoleDepth = 0.012` → 去料 `3.0772e-6`。

### 孔向导前置数据（必须运行时查）

```python
hs = sw.GetHoleStandardsData(0).QueryInterface(SW.IHoleStandardsData)  # 0 = CounterBore
hs.GetHoleStandards()                       # ★ 热身，否则下一行返回 (None,None,False)
idx, names, ok = hs.GetFastenerTypes('GB')  # 名字按返回的 names 取，别硬编码
# GB / CounterBore: 376 379 377 378 361 364 375 374
# GB / Hole:        708 357 356 355
# GB / CounterSink: 363 362 369 373 368 372 367 371 365 366 370
# GB / Tap:         358 360 359
```

## R18 钣金基体法兰（FeatureData 路线，✅ 实测 6.0000e-06）

```python
md.Extension.SelectByID2('上视基准面', 'PLANE', 0, 0, 0, False, 0, None, 0)
md.SketchManager.InsertSketch(True)
md.SketchManager.CreateCornerRectangle(0, 0, 0, 0.10, 0.06, 0)
md.SketchManager.InsertSketch(True)
fd = md.FeatureManager.CreateDefinition(34)       # swFmBaseFlange
q = fd.QueryInterface(SW.IBaseFlangeFeatureData)
q.Thickness = 0.001        # 板厚（米）
q.BendRadius = 0.001       # 折弯半径
f = md.FeatureManager.CreateFeature(fd)           # 传未 QI 的 fd
md.EditRebuild3()
```

- 特征名 `基体-法兰1`，类型 `SMBaseFlange`；判据：体积 = 长×宽×厚 = 6e-06（100×60×1mm）。
- `q.AccessSelections()` 会报"服务器出现意外情况"，**可以忽略**，不要因此重试或重启实例。
- 反面记录：`InsertSheetMetalBaseFlange2`(19 参) 四种组合全 False，不要再试。

## R20 图纸 BOM 表（✅ 实测）

```python
import swe
from swe import SW, P

sw = swe.connect(); swe.quiet(sw)
d  = swe.new_drawing(sw, 6)                  # 6 = A4
dm = swe.md2(d)
drw = dm.QueryInterface(SW.IDrawingDoc)
sheet = P(drw, 'GetFirstView')               # 返回的是图纸(图纸1)
P(drw, 'CreateDrawViewFromModelView3', part_path, '*前视', 0.10, 0.15, 0.0)
dm.EditRebuild3()
view = P(sheet, 'GetNextView')               # 工程图视图1

TPL = r'<SW_INSTALL>\lang\chinese-simplified\bom-standard.sldbomtbt'
t = P(view, 'InsertBomTable2', False, 0.20, 0.25, 1, 1, '默认', TPL)
print(P(sheet, 'GetTableAnnotationCount'))   # -> 1
```

- 模板目录查法：`sw.GetUserPreferenceStringValue(22)`（`swFileLocationsBOMTemplates`）→ 本机 `<SW_INSTALL>\lang\chinese-simplified`，内含 11 个 `.sldbomtbt`。
- `AnchorType`：1 = 左上；`BomType`：**1 = PartsOnly（可用）**、0 在本机返回 None。
- 表挂在**图纸**上，不在视图上：判据看 `sheet.GetTableAnnotationCount()`，`view.GetTableAnnotationCount()` 恒 0。
- 注意：`IModelDocExtension.InsertBomTable` 是"零件/装配体"那个，传图纸会返回 None；**图纸侧必须用 `IView.InsertBomTable*`**。

## R21 爆炸视图（⚠️ 半通：视图与步骤能建，距离写不进）

```python
ad = asm.QueryInterface(SW.IAssemblyDoc)
am = asm.QueryInterface(SW.IModelDoc2)
ad.AddComponent5(p1, 0, '', False, '', 0, 0, 0)      # 必须先 preload 零件
ad.AddComponent5(p2, 0, '', False, '', 0.04, 0.02, 0.035)
am.EditRebuild3()

print(P(ad, 'CreateExplodedView'))            # True
print(P(ad, 'GetExplodedViewNames2', ''))     # ('爆炸视图1',)
cfg = am.ConfigurationManager.ActiveConfiguration
print(P(cfg, 'GetNumberOfExplodeSteps'))      # 1
st = P(cfg, 'GetExplodeStep', 0)              # 链1，GetNumOfComponents()=2
st.ExplodeDistance = 0.05                     # ← 写入被忽略，回读仍 0.0
print(P(ad, 'ShowExploded2', True, '爆炸视图1'))   # True（两个参数！）
```

- 实测结论：`CreateExplodedView()` → True、`GetExplodedViewNames2('')` → `('爆炸视图1',)`、步骤容器 `链1` 自动带 2 个组件；
  但 `ExplodeDistance` 赋值后回读恒 0.0，`AddExplodeStep2(...)` 恒返回 `(3, None)`（`swCreateExplodeStepError_NoComponents`，即便两个组件都已 `Select4(False/True, 0, False)` 选中），`IExplodeStep.SetComponents` 抛 `COMError -2147417851 '服务器出现意外情况。'`。
- 判据：能通过的只有"爆炸视图 + 步骤对象存在"；**组件位移拿不到**（`IComponent2.GetXform` 返回 tuple，`IMathTransform.ArrayData` 在本机不可读，见坑 39）。
- 剩余杠杆：GUI 里点"爆炸步骤"（本机 COM 实例没有可用窗口，见坑 57；需交互实例）；或改用 `SetExplodeDirection` + 手工设置每个组件的变换（未验）。

## R22 镜像（❌ 本机 API 全 False，九种组合已穷举）

```python
# 统一前置：板 100×60×20 + 一个 Ø12 通孔（体积 1.17738e-4）
m.ClearSelection2(True)
m.Extension.SelectByID2('右视基准面', 'PLANE', 0, 0, 0, False, <plane_mark>, None, 0)
m.Extension.SelectByID2('切除-拉伸1', 'BODYFEATURE', 0, 0, 0, True, <feat_mark>, None, 0)
r = m.FeatureManager.InsertMirrorFeature2(<mirror_body>, False, True, False, 0)   # 恒 False
```

| 组合 | 选中数 | 结果 | 体积 |
|---|---|---|---|
| feature mark0 + plane mark1 | 2 | False | 不变 1.17738e-4 |
| feature mark4 + plane mark1 | 2 | False | 不变 |
| feature mark0 + plane mark2 | 2 | False | 不变 |
| feature mark0 + face mark2 | 1 | False | 不变 |
| SOLIDBODY mark0 + plane mark1（mirrorBody=True/False） | 1 | False | 不变 |
| plane 先选（mark 0/1/4）+ feature 后选 | 2 | False | 不变 |
| `IPartDoc.InsertMirrorFeature(True)` / `(False)` | 2 | False | 不变 |
| 面 → `IEntity.GetBody()` → `IBody2.Select2` 后镜像 | 1 | False | 不变 |

- 结论：本机 30.5.0 下镜像**所有已确认入口都返回 False**（不是参数错，是功能面不通）。
- 三条出口：① GUI（`swCommands_` 里有镜像命令，需交互实例）；② 直接建对称几何（左右各画一遍，最稳）；③ `IMirrorSolidFeatureData` + `swFmMirrorSolid=4`（未验）。
- 判据若走通：体积应为原来的 2 倍去料（如 1.17738e-4 → 1.13214e-4 再降一个孔的量），特征树出现 `镜像1`。

## R23 抽壳多厚度（❌ 属性写入抛 COM 错误）

```python
m.ClearSelection2(True)
P(m, 'InsertFeatureShell', 0.002, False)      # 闭合壳：3.3984e-05
m.EditRebuild3()
swe.select_face(md, 0.05, 0.03, 0.02, 0, 0, 1, 0)   # 选要不同厚度的面
fd = P(shell_feature, 'GetDefinition').QueryInterface(SW.IShellFeatureData)
P(fd, 'AccessSelections', m, None)            # True
fd.MultipleThicknessFaces = faces             # ← 抛 COMError -2147417851
```

- 四种赋值写法全败：list / tuple / 单个 `IFace2` / `comtypes.automation.VARIANT(VT_DISPATCH)` —— 全报 `COMError (-2147417851, '服务器出现意外情况。')`。
- `m.InsertFeatureShellAddThickness(0.004)`（官方 1 参 Sub）返回 0，体积不变（闭合壳仍 3.3984e-05），`GetMultipleThicknessFacesCount()` 仍 0。
- `IShellFeatureData` 走 `ModifyDefinition` 也不收（坑 47：`'类型不匹配。'`，`IWizardHoleFeatureData2` 同路却成功）。
- 出口：GUI 抽壳对话框的"多厚度设定"；或用"抽壳 2mm + 局部加厚面单独做偏移曲面/薄壁拉伸"的组合几何替代。判据参考：闭合壳 3.3984e-05、开口壳（移除顶面）2.3232e-05。

## R24 边界凸台等价（放样 + 引导线）✅ 实测精确

> 结论先行：SolidWorks 2022 的 API **没有边界凸台入口**（`swFeatureNameID_e` 121 个 ID 全试，0 个能 QI 成 `IBoundaryBossFeatureData`；`sldmodu.dll` 里也没有边界凸台特征类）。
> 但"两个方向受控"的工程效果可以用 `InsertProtrusionBlend2` + 引导线完整复现，且体积能与解析公式对上 1e-10 级。

```python
# 剖面1：前视基准面（法向 +Z），40×40 居中
m.Extension.SelectByID2('前视基准面', 'PLANE', 0, 0, 0, False, 0, None, 0)
sk.InsertSketch(True); sk.CreateCornerRectangle(-0.02, -0.02, 0, 0.02, 0.02, 0); sk.InsertSketch(True)

# 剖面2：前视基准面偏移 0.05（沿 +Z），20×20 居中
P(m, 'CreatePlaneAtOffset3', 0.05, False, True)
m.Extension.SelectByID2('基准面1', 'PLANE', 0, 0, 0, False, 0, None, 0)
sk.InsertSketch(True); sk.CreateCornerRectangle(-0.01, -0.01, 0, 0.01, 0.01, 0); sk.InsertSketch(True)

# 引导线：3D 草图里 4 条线，连接对应角点 (x,y,0) -> (x/2,y/2,0.05)
sk.Insert3DSketch(True)
for (x, y) in [(0.02,0.02), (-0.02,0.02), (-0.02,-0.02), (0.02,-0.02)]:
    sk.CreateLine(x, y, 0.0, x/2, y/2, 0.05)
sk.Insert3DSketch(True)

# 选中：两个剖面 mark=1 + 4 条引导线逐段 mark=1
m.ClearSelection2(True)
m.Extension.SelectByID2('草图1', 'SKETCH', 0,0,0, False, 1, None, 0)
m.Extension.SelectByID2('草图2', 'SKETCH', 0,0,0, True,  1, None, 0)
for i in range(1, 5):
    m.Extension.SelectByID2('Line%d@3D草图1' % i, 'EXTSKETCHSEGMENT', 0,0,0, True, 1, None, 0)

r = m.FeatureManager.InsertProtrusionBlend2(False, False, False, 1.0, 0, 0, 0.0, 0.0,
                                            False, False, False, 0.0, 0.0, 0, True, True, True, 0)
m.EditRebuild3()   # -> True，特征 Blend，体积 4.666666667e-05，bbox [-20,-20,0, 20,20,50]
```

- 判据：`(h/3)(A₁+A₂+√(A₁A₂)) = (0.05/3)(0.0016+0.0004+0.0008) = **4.666666667e-05**`，实测完全一致；`GetPartBox(False)` 回 `[-20,-20,0, 20,20,50]` 毫米。
- **引导线的 mark 只认 0 或 1**：mark=1 成功（体积精确）；mark=0 也成功；mark=2 与 mark=4 **都返回 False**（选中的确实是 6 个对象）。
- 必须**逐段**选（`EXTSKETCHSEGMENT`，名字 `Line1@3D草图1`）；把整张 `3D草图1` 当一个对象选（`SKETCH`，mark=4）→ False。
- 引导线要与剖面**同向**：剖面必须放在法向与引导线方向一致的那个基准面上（本次用前视 = +Z）。放到上视基准面上就会错（见坑 66）。
- 体积范围：几何对不上时 `InsertProtrusionBlend2` 仍可能返回 True，但体积会离谱（例如 2.1333333e-05）——一定用体积 + bbox 双判据。

## R25. 能力自检（13 项端到端回归）

脚本：`<REPO_ROOT>/examples\sw_audit.py`（32 秒跑完，13/13 通过）。用法：

```powershell
Get-Process SLDWORKS -ErrorAction SilentlyContinue | Stop-Process -Force; Start-Sleep 4
$env:PYTHONIOENCODING='utf-8'; $env:PYTHONUTF8='1'
& "python" "<REPO_ROOT>/examples\sw_audit.py"
```

| 项 | 判据（实测值） |
|---|---|
| 拉伸+切除 | vol = 1.177380533e-04（100×60×20 挖 Ø12） |
| 回转 | vol = 4.712388980e-05 = π(R²−r²)h |
| 扫描 | vol = 1.570796327e-05 = πr²L |
| 放样+引导线 | vol = 4.666666667e-05 = (h/3)(A₁+A₂+√(A₁A₂)) |
| 圆角 | 去料 1.073009183e-07 = (1−π/4)r²L |
| 倒角 | 去料 9.000000e-08 = 0.5w²L |
| 抽壳(单厚度) | vol = 3.398400e-05（闭合壳 t=2mm） |
| 孔向导 M48 | 去料 3.926990817e-05 = π·0.025²·0.02 |
| 钣金基体法兰 | vol = 6.000000e-06（100×60×1mm） |
| 曲面拉伸 | sheet body = 1 |
| 配置驱动 | BIG 8.4e-04 / 默认 1.2e-04 |
| 材质写入 | mass = 0.936000 kg（普通碳钢 7800） |
| 导出 STEP | ret=[0,0,True]，文件 ~15.8 KB |

要点：① 每项独立 try/except，单项失败不影响其它项；② 判据全部是"体积/质量与解析式对账"，不是"返回非 None"；
③ 跑前先杀进程，避免上一次 wedge 的实例污染结果；④ 本轮修好的三处坑：回转的局部 z（坑 69）、钣金 CreateFeature 收 QI 对象（坑 67）、配置返回值不可信（坑 68）。

## R26 端到端案例：法兰盘（圆柱→中心孔→螺栓孔+圆周阵列→圆角→倒角→材质→工程图含剖视→STEP）

完整可跑脚本：`<REPO_ROOT>/examples\p36_case_flange.py`，单次 14.1 s。

| 步骤 | 调用 | 实测体积 (m³) | 解析式 | 偏差 |
|---|---|---|---|---|
| 1 圆柱 Ø120×60 | `FeatureExtrusion2` 23 参 | 6.785840131754e-04 | π·0.06²·0.06 | 0 |
| 2 中心孔 Ø60 贯穿 | `FeatureCut4` 27 参（T1=1） | 5.089380098815e-04 | 上步 − π·0.03²·0.06 | 0 |
| 3 单孔 Ø11 @R45 | `FeatureCut4` | 5.032360192153e-04 | 上步 − π·0.0055²·0.06 | 0 |
| 4 圆周阵列 4 | `FeatureCircularPattern4(4, 2π, False, '', False, True, False)` | 4.861300472165e-04 | 上步 − 4×单孔 | 0 |
| 5 顶外圆角 r3 | `FeatureFillet3(2, 0.003, ...)` | 4.854100523489e-04 | 去料 7.199949e-07 vs 修正式 7.203140e-07 | 0.04% |
| 6 内孔口倒角 2 mm | `InsertFeatureChamfer(0,1,0.002,π/4,...)` | 4.850246836501e-04 | 去料 3.853687e-07 vs `0.5w²·2π(R+w/2)` | 1.1% |
| 7 材质 普通碳钢 | `IPartDoc.SetMaterialPropertyName2('默认','solidworks materials.sldmat','普通碳钢')` | — | 质量 3.783193 kg = 7800×V | 0 |
| 8 导出 | `SaveAs` .SLDPRT 186,733 B + STEP 46,005 B | — | — | — |
| 9 工程图 | A4 → `*前视` → `.SLDDRW`（**剖视见坑 74：法兰属圆形轮廓，剖视返回 None**） | 视图数 1→2 | — | — |

关键实现点（每一步都踩过坑，见坑 70~73）：
1. 拉伸/切除前 `swe.feature_profile(md)` 必须选**最后一张**草图；
2. 面用射线选（`select_face`），薄壁环带上打点要在环带中径上；
3. 圆周阵列的轴 = 外圆柱面（`mark=1`），特征按名字 `BODYFEATURE`（`mark=4`），选中数应为 2；
4. 工程图先 `swe.drw()` 再建视图，存盘 `swe.save(swe.md2(d), p)`；
5. 每步 `EditRebuild3()` 后再读体积，`swe.mass2(md)` 返回 `(status, arr)`，体积在 `arr[3]`。

失败信号对照：`feat=False` 且体积不变 = 轮廓没选上（不是参数错）；`sav ok=False` 但文件存在且大小合理 = 目标已存在的假失败。

## R27 一键函数（`swe.py`，10 个，均已回归）

新增在 `<REPO_ROOT>/examples\swe.py` 末尾，公开可调用对象 54 个；回归脚本 `p37_api_regress.py`。

| 函数 | 作用 | 关键点 |
|---|---|---|
| `solid_rect(md, w, h, depth, plane, cx, cy)` | 矩形拉伸 | 内部取**最后一张**草图（坑 70） |
| `solid_circle(md, r, depth, plane, cx, cy)` | 圆拉伸 | 圆柱/圆盘 |
| `cut_circle(md, x,y,z, dx,dy,dz, r, cx, cy)` | 面上画圆切除 | 射线选面（面必须是被切的那个，坑 5） |
| `cut_rect(md, ...)` | 面上画矩形切除 | 同上，27 参 `CUT27` |
| `pattern_circular(md, count, axis, feature_name)` | 圆周阵列 | 轴=外圆柱面 `mark=1`，特征按名字 `mark=4`（坑 72） |
| `pattern_linear(md, count, spacing, plane, ...)` | 线性阵列 | 22 参，方向用基准面 `mark=1` |
| `apply_material(md, name, database, config)` | 写材质 | 入口 `IPartDoc.SetMaterialPropertyName2` |
| `measure(md)` | 体积/面积/质量/包围盒/实体数/特征名 | `mass2` 返回 `(status, arr)`，体积 `arr[3]` |
| `flange(sw, ...)` | 法兰端到端（圆柱→中心孔→螺栓孔→圆周阵列→圆角→倒角→材质） | 6 步体积逐位对上（见下） |
| `drawing_front_section(sw, part, out)` | A4 图 → 标准视图 → 剖视 → 存盘 | 复用视图（`make_view=False`，坑 75） |

`flange()` 回归（与 R26 案例逐位一致，相对偏差 ≤ 1e-13）：
圆柱 `6.785840131754e-04` → 中心孔 `5.089380098815e-04` → 单孔 `5.032360192153e-04` → 圆周阵列 `4.861300472165e-04` → 圆角 `4.854100523489e-04` → 倒角 `4.850246836501e-04` → 质量 `3.783193 kg`；`bbox [-60,-60,0,60,60,60]` 毫米、1 个实体、27 个特征、零件 226,526 B。

线性阵列回归：板 200×60×20 `2.4e-04` → 切 20×20 `2.32e-04` → 线阵 3 件 `2.16e-04`（偏差 0）。


## R28. 国标法兰族（GB/T 9124.1-2019 表驱动）

```python
import sys; sys.path.insert(0, r"<REPO_ROOT>/examples\standards")
import swe, gb9124_2019 as GB
d = GB.get(100, "PN16", 1)      # 返回米制几何：r_out / h / r_bore / r_hole / pcd / n
md, r = swe.flange(sw, r_out=d["r_out"], h=d["h"], r_bore=d["r_bore"],
                   r_hole=d["r_hole"], pcd=d["pcd"], n_hole=d["n"],
                   fillet_r=0, chamfer_w=0, material="普通碳钢", save_path=part)
swe.drawing_front_section(sw, part, drw)     # 前视 + 剖视 A
```

- 尺寸表 `standards/gb9124_2019.py`：DN50/65/80/100/125/150/200，PN10/PN16，系列 I/II 内径可选。
- 实测（PN16 系列 I，不加工艺圆角/倒角）：DN50 3.4788e-04、DN80 4.5895e-04、DN100 5.5900e-04、DN150 9.1011e-04 m³，
  与 `π(R²−r_b²)C − n·π·r_h²·C` **偏差 0.0000%**。
- 加圆角/倒角后偏差为负（DN50 −0.26%），残差可用 `(1−π/4)r²·2π(R−r(1−π/4))` 与 `0.5w²·2π(r_b+w/2)` 精确解释。

## R29. 法兰 + 垫片 + 螺栓 总装（含干涉与 BOM）

```python
for p in (P_FLA, P_GAS, P_BOLT):
    sw.OpenDoc6(p, 1, 1, "", 0, 0)          # ★ 坑 76：必须先预加载
asm = swe.new_assembly(sw)                     # 再 QI 成 IAssemblyDoc：
A = asm.QueryInterface(SW.IAssemblyDoc)        # from comtypes.gen import SldWorks as SW
A.AddComponent5(P_FLA, 0, "", False, "", 0, 0, C/2)          # 下法兰
A.AddComponent5(P_GAS, 0, "", False, "", 0, 0, C + t/2)      # 垫片
A.AddComponent5(P_FLA, 0, "", False, "", 0, 0, C + t + C/2)  # 上法兰
# 螺栓按 2πk/n 均布，半径 = K/2
idm = A.InterferenceDetectionManager
idm.TreatCoincidenceAsInterference = False
n_i = idm.GetInterferenceCount()                              # 期望 0
```

- `AddComponent5` 的位置是**包围盒中心**（坑 21），不是原点。
- 装配工程图里 `IView.InsertBomTable2(False, X, Y, 1, 1, "默认", BOM模板)` 可插入 BOM（`BomType=1` 只列零件）。
- 爆炸步骤仍不可编程（坑 63）：`AddExplodeStep2` 恒返回 `(3, None)`。

## R30 读 BOM 表（行/列/文字）

```python
# 前提：装配体已在会话里打开；工程图 + 视图已建
d  = swe.drw(swe.new_drawing(sw))
dm = swe.md2(d)
d.CreateDrawViewFromModelView3(asm_path, "*前视", 0.10, 0.15, 0.0)
v  = swe.P(d, "GetFirstView")
while v is not None and swe.P(v, "Type") != 7:      # 跳过图纸本体
    v = swe.P(v, "GetNextView")
TPL = r"<SW_INSTALL>\lang\chinese-simplified\bom-standard.sldbomtbt"
swe.P(v, "InsertBomTable2", False, 0.20, 0.06, 1, 1, "默认", TPL)
rows, titles = swe.bom_table(d)      # 二维字符串 + 列标题，标签已剥掉
```

判据：`swe.bom_table()` 的 `rows[0]` 等于列标题、行数 = 零件种类数 + 1；PL50 总装实测 `4×4`、数量列 `2/1/4`。
坑：见 77（`ITableAnnotation` 才是数据接口、`GetBomTable` 只写）。

## R31 装配体剖视图（实测可用）

```python
# 装配体先在会话里打开（预加载，坑 76）
d  = swe.drw(swe.new_drawing(sw))
dm = swe.md2(d)
d.CreateDrawViewFromModelView3(asm_path, "*前视", 0.10, 0.15, 0.0)
info = swe.section_view(d, asm_path, view_name="*前视", view_at=(0.10, 0.15),
                        label="A", section_at=(0.10, 0.19), scale=2.0, pad=0.0035,
                        make_view=False)          # 复用上面已建的视图
```

判据：视图数 2→3 且新视图 `Type==2`、`swe.P(v, "GetSection")` 能读到 `GetLabel()='A'`、
`GetName()='剖切线1'`、`GetLineInfo()` 四点坐标。实测 PL50 总装：`剖面视图 A-A`、
label=A、SLDDRW 134,139 B；换竖向剖切线（xd=0.10, y≈0.02）同样成功。

注意：`v.GetSection` 直接调用会抛 `TypeError: '_Dispatch' object is not callable`，
必须 `swe.P(v, "GetSection")`（与坑 63 同源）。装配剖视不需要额外开关，
`CutSurfaceBodies`/`DisplaySurfaceBodies` 默认即可。

## R32 BOM 行 → 组件 → 零件 → 材料/重量汇总

```python
rows, titles = swe.bom_table(d)                      # R30
table = swe.P(swe.P(d, "GetFirstView"), "GetTableAnnotations")[0]
total = 0.0
for r in range(1, len(rows)):                        # 0 行是表头
    qty  = int(rows[r][-1]) if rows[r][-1].isdigit() else 1
    comps = swe.bom_components(table, r)             # IBomTableAnnotation.GetComponents
    path  = swe.comp_path(comps[0])                  # 组件自身的路径
    doc   = sw.OpenDoc6(path, 1, 1, "", 0, 0)[-1]    # 零件
    pd    = doc.QueryInterface(SW.IPartDoc)
    mat   = swe.P(pd, "GetMaterialPropertyName2", "默认")[1] or "未指定"
    st, a = swe.mass2(doc)                           # a[3]=体积 a[5]=质量
    total += a[5] * qty
swe.P(asm_doc, "EditRebuild3")                       # 坑 78：材质变了要重建
print(total, swe.mass2(asm_doc)[1][5])               # 两者应一致
```

判据：逐行合计 == 装配体质量。PL50 总装实测 `5.955886 kg` vs `5.955886 kg`，差 8.9e-16 kg。

## R33 剖视图上定位每个零件（图纸坐标）

```python
sec = <剖面视图 IView>
for name, comp in swe.view_components(sec):          # 坑 79②
    tr = swe.P(comp, "GetXform"); a = list(swe.P(tr, "ArrayData"))
    origin = (a[3], a[7], a[11])                     # 组件在模型空间的原点
    xy = swe.model_to_view(sec, origin, c_model)     # c_model = 装配包围盒中心
    print(name, [round(v, 4) for v in xy])
```

判据：能看到 5 个组件；但 **PL50 总装实测只有两法兰的原点落在 outline 内**，3 个螺栓原点在框外（螺栓轴线 y=±62.5 mm，剖切面只切 y=0 截面）。
→ 组件原点只适合"居中类零件"；要精确给每个零件挂引线，改用该零件在视图内的可见边/面取锚点（见坑 79 ⑥）。

R33 的实测边界：`c_model` 用装配包围盒中心；`GetVisibleComponents` 枚举与原点投影可用，但不保证落在框内。

## R34 剖视图自动气球

```python
dm.Extension.SelectByID2(secname, "DRAWINGVIEW", 0, 0, 0, False, 0, None, 0)
swe.P(sec, "InsertBomTable2", False, 0.22, 0.06, 1, 1, "默认", TPL)   # 气球需要 BOM
balls = swe.auto_balloon(d, layout=1, ignore_multiple=False)          # 坑 79③
```

判据：返回非 None 列表（实测 3 个）、`sheet.GetNoteCount()` 增加、`.SLDDRW` 明显变大（95,790 → 151,891 B）。


## R35 线稿附图三件套（图序/剖切符号/导出）

见 `docs/06-line-art-figures.md` §4 工作流；核心三点：图序坐标夹进 `0..GetSize()`、剖切符号读 `parent_view.GetSectionLineInfo2()` 自检、导出优先 DXF（`[0,0,True]`），PDF 返回 `[1,0,False]` 需人工核。


## R36 线稿附图（A4 无图框 + 单图单页 + 编号引线 + 图序）

**判据**：`GetSize()` = `[0.297, 0.21, 6]`；`GetTemplateName()` = `''`；每张图纸只剩 1 个视图（剖视为 `Type=2`）；每个编号的箭头尖落在视图 `GetOutline()` 内；PDF `/MediaBox` = `841.89×595.276`。

```python
W, H = 0.297, 0.210
d  = swe.new_drawing(sw); dd = d.QueryInterface(SW.IDrawingDoc)
dd.SetupSheet5('图1', 6, 13, 1, 1, True, '', W, H, '', False)   # 6=A4, 13=None(无模板=无图框)
sh = swe.P(dd, 'GetCurrentSheet').QueryInterface(SW.ISheet)
assert swe.P(sh, 'GetSize') == [0.297, 0.21, 6]

fv = dd.CreateDrawViewFromModelView3(ASM, '*前视', 0.15, 0.115, 0.0).QueryInterface(SW.IView)
scale = min((W-0.028)/mw, (H-0.028)/mh)
fv.ScaleDecimal = scale; swe.P(swe.md2(dd), 'EditRebuild3')      # 出框就 *0.82 再 rebuild
# 剖切线（图纸层草图）→ 剖视
sk = swe.P(swe.md2(dd), 'SketchManager'); swe.P(sk, 'InsertSketch', True)
seg = swe.P(sk, 'CreateLine', 0.15, 0.050, 0, 0.15, 0.180, 0).QueryInterface(SW.ISketchSegment)
swe.P(seg, 'Select2', False, 0); swe.P(dd, 'MakeSectionLine'); swe.P(sk, 'InsertSketch', True)
sec = swe.P(dd, 'CreateSectionViewAt5', 0.15, 0.115, 0, 'A', 0, None, 0).QueryInterface(SW.IView)
sec.ScaleDecimal = scale; sec.ScaleHatchPattern = 0.4
# 删前视，只留剖视
md2 = swe.md2(dd)
if md2.Extension.SelectByID2(swe.P(fv,'GetName2'), 'DRAWINGVIEW', 0,0,0, False, 0, None, 0):
    md2.EditDelete()
# 编号 + 引线
note = swe.P(md2, 'InsertNote', '1')            # 只有 InsertNote 返回 INote
ann  = swe.P(note, 'GetAnnotation')
ann.SetPosition(x_label, y_label, 0.0)          # 3 个 double
ann.SetLeader2(True, 0, True, True, False, False)
ann.SetLeaderAttachmentPointAtIndex(0, x_tip, y_tip, 0.0)
ann.SetArrowHeadStyleAtIndex(0, 3)
ann.SetArrowHeadSizeAtIndex(0, True, 0.0025, 0.0012, 0.0012)
# 第二张图：无图框 A4 + 轴测
dd.NewSheet('图2', 6, 13, 1, 1)                  # 5 参
# 导出：逐页 ActivateSheet + SaveAs4（目标文件先删）
```

实测（PL50 法兰总装）：图1 剖视 `[0.1169,0.0362,0.1831,0.1938]`、4 个编号箭头尖全部在框内；图2 轴测 `[0.0858,0.0192,0.2142,0.1968]`；两张 PDF 12,772 / 12,770 B，MD5 不同，MediaBox 均 A4。

### R37 补充：父视图要"隐藏"，不能删

```python
fv  = dd.CreateDrawViewFromModelView3(ASM, '*前视', 0.15, 0.115, 0.0).QueryInterface(SW.IView)
# … 画剖切线 → MakeSectionLine → CreateSectionViewAt5 …
sec = swe.P(dd, 'CreateSectionViewAt5', 0.15, 0.115, 0, 'A', 0, None, 0).QueryInterface(SW.IView)
fv.SetVisible(False, False)          # 关键：不要 EditDelete
print(fv.GetVisible(), sec.GetVisible())   # 期望 False / True
```
多图纸时 PDF 逐页导出不可靠（坑 97），线稿附图按"一图一文件"生成。
