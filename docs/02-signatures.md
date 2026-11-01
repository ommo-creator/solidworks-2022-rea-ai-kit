# 实测签名对照（SolidWorks 2022 SP5 / Interop 30.5.0）

所有调用串都是本机真跑通过的原样记录。"实参"不含 `this`。

---

## 新建与打开

```python
sw.INewPart()                       # PartDoc，首选
sw.NewPart()                        # Object，VBS 用
sw.INewAssembly()                   # AssemblyDoc
sw.INewDrawing(6)                   # DrawingDoc；6 = swDwgPaperA4size
sw.OpenDoc6(path, 1, 1, "", 0, 0)   # 返回元组，取 r[-1] 才是 ModelDoc2
sw.ActivateDoc3(name, True, 0, 0)   # 同名多开时切换
sw.CloseAllDocuments(True)
sw.GetUserPreferenceStringValue(8)  # 8/9/10 = 零件/装配/工程图模板路径
```

Python + comtypes 下 `OpenDoc6` 返回 `(retval, errors, warnings, model)` 之类的元组，**取最后一个元素**才是模型（用户既有脚本里记的坑）。

---

## 选择

| 方法 | 实参 | 说明 |
|---|---|---|
| `Extension.SelectByID2` | **9** | `(name, type, x, y, z, append, mark, callout, selectOption)`；第 8 位 Object 传 `None`/`Nothing` |
| `Extension.SelectByRay` | **11** | `(x, y, z, dx, dy, dz, rayRadius, TypeWanted, append, mark, option)` |
| `ClearSelection2` | 1 | `True` = 也清子选择 |

`TypeWanted`：`0` 全部、`1` 边、`2` 面、`4` 顶点（按 ray 命中优先级用）。
`Mark`：同一选择集里区分用途。切割特征 `mark=4`、阵列方向 `mark=1`。

---

## 草图

| 方法 | 实参 | 备注 |
|---|---|---|
| `SketchManager.InsertSketch` | 1 | `True` = 进/出草图并重建 |
| `CreateLine` | 6 | `(x1,y1,z1,x2,y2,z2)` |
| `CreateCircle` | 6 | `(cx,cy,cz, px,py,pz)` 圆心 + 圆上一点 |
| `CreateCircleByRadius` | 4 | `(cx,cy,cz, radius)` |
| `CreateArc` | 10 | `(cx,cy,cz, sx,sy,sz, ex,ey,ez, Int16 Direction)` |
| `CreateCornerRectangle` | 6 | 对角两点 |
| `CreateCenterRectangle` | 6 | 中心 + 角点 |
| `AddDimension2` | 3 | `(x, y, z)` 标注放置点；**先 `SetUserPreferenceToggle(10,False)`** |

构造线：`SketchSegment.ConstructionGeometry = True`（在 **segment** 上，不是 SketchManager）。

---

## 特征

### FeatureExtrusion2 — 23 实参

```
(True, False, False,          # Sd(单向), Flip, Dir(反向)
 0, 0,                        # T1, T2 终止条件（0=盲孔, 1=完全贯穿, 2=下一面, 6=两侧对称）
 0.020, 0.010,                # D1, D2 深度（米）
 False, False, False, False,  # Dchk1, Dchk2, Ddir1, Ddir2
 0.0174532925199433, 0.0174532925199433,   # Dang1, Dang2（弧度，1°）
 False, False, False, False,  # OffsetReverse1/2, TranslateSurface1/2
 True, True, True,            # Merge, UseFeatScope, UseAutoSelect
 0, 0.0, False)               # T0, StartOffset, FlipStartOffset
```

### FeatureCut4 — 27 实参

前 17 位与拉伸同序，尾部为切除专有：

```
(True, False, False, 1, 0, 0.0, 0.0,          # Sd,Flip,Dir,T1=1(完全贯穿),T2,D1,D2
 False, False, False, False,                   # Dchk1,Dchk2,Ddir1,Ddir2
 0.0, 0.0,                                     # Dang1,Dang2
 False, False, False, False,                   # OffsetReverse1/2, TranslateSurface1/2
 False,                                        # NormalCut
 True, True,                                   # UseFeatScope, UseAutoSelect
 False, False, False,                          # AssemblyFeatureScope, AutoSelectComponents, PropagateFeatureToParts
 0.0, 0.0, False, False)                       # T0, StartOffset, FlipStartOffset, OptimizeGeometry
```

尾部三/四位语义以 `IFeatureManager` 元数据顺序为准；本串已实跑产出 `切除-拉伸1`。

### FeatureRevolve2 — 20 实参

```
(True, True, False, False, False, False,      # SingleDir, IsSolid, IsThin, IsCut, ReverseDir, BothDirectionUpToSameEntity
 0, 0,                                         # Dir1Type, Dir2Type（0=盲孔, 1=完全贯穿）
 6.283185307179586, 0.0,                       # Dir1Angle, Dir2Angle（弧度）
 False, False, 0.0, 0.0,                       # OffsetReverse1/2, OffsetDistance1/2
 0, 0.0, 0.0,                                  # ThinType, ThinThickness1/2
 True, True, True)                             # Merge, UseFeatScope, UseAutoSelect
```

切用 `IsCut=True`（**不要**用 `FeatureRevolveCut2`，本机参数数目不符）。

### FeatureLinearPattern5 — 22 实参

```
(3, 0.025, 1, 0.0,                # 实例数, 间距(米), 方向序号(1=X/2=Y/3=Z), 反向偏移
 False, False, "", "",            # FlipDirection, DName(方向名，空=按方向序号), ...
 False, False, False, False,      # 变体类开关
 True,                            # GeometryPattern
 False, False, False, False, False,
 0.0, 0.0, False, False)
```

### FeatureCircularPattern4 — 7 实参

```
(6, 6.283185307179586, False, "", False, True, False)
# 实例数, 总角度(弧度), FlipDirection, DName, GeometryPattern, EqualSpacing, VaryInstance
```

### 其余

| 方法 | 实参 | 备注 |
|---|---|---|
| `FeatureFillet3` | 多 | 需先选边；半径第一个 double |
| `Extension.CreateMassProperty` | 0 | `CreateMassProperty()` 返回对象，无材质时 Density=1.0、Mass=Volume（**不可信**） |
| `Extension.GetMassProperties2` | **2** | `(1, False)` → `(status, [Xc,Yc,Zc,Vol,Area,Mass,Ixx,Iyy,Izz,Ixy,Iyz,Ixz])` |
| `IPartDoc.EnumBodies3` | 2 | `(0, True)` → 实体枚举 |
| `IBody2.GetMassProperties` | 1 | `(0.0)` → `[Xc,Yc,Zc,Vol,Area,Mass,...]`，**索引 3 = 体积** |
| `IPartDoc.GetPartBox` | 1 | `(False)` → `[x1,y1,z1,x2,y2,z2]`，单位**毫米** |
| `IModelDoc2.SaveAs` | 1 | `(完整路径)`；目标已存在返回 `False` 但文件已写 |
| `IAssemblyDoc.AddComponent5` | **8** | `(路径, 0, "", False, "", x, y, z)`，按**包围盒中心**落位 |
| `IAssemblyDoc.AddMate5` | **14** | `ErrorStatus` 是 [out] 被摘掉；返回 int，配合仍解算 |
| `IDrawingDoc.CreateDrawViewFromModelView3` | 5 | `(模型路径, "*前视", x, y, z)` |
| `IDrawingDoc.Create3rdAngleViews2` | 1 | `(模型路径)` → 一次生成 4 视图 |
| `ISldWorks.SetUserPreferenceToggle` | 2 | `(10, False)` 关尺寸输入框；`(100, False)` 关过定义提示 |

---

## 关键枚举真实值（反射取得，非文档抄写）

```
swEndConditions_e:      Blind 0, ThroughAll 1, ThroughNext 2, UpToVertex 3, UpToSurface 4,
                        OffsetFromSurface 5, MidPlane 6, UpToBody 7, ThroughAllBoth 9,
                        UpToSelection 10, UpToNext 11          ← 8 空缺，别按顺序推
swDwgPaperSizes_e:      A4 = 6
swInputDimValOnCreate:  10
swSketchOverdefiningDimsPromptToSetState: 100
```

完整枚举表随仓库提供：`data/enums.json`（889 个 `swconst` 枚举 / 5,142 个数值，另有 113 个枚举的 2,599 个成员名；机器可读，可直接当查表用）。重建方法见 `scripts/extract_enums.py`。

> **为什么需要这个文件**：`comtypes.gen.SldWorks` 里没有任何 `sw*` 常量（`hasattr(SldWorks,"swDocPART")` = `False`），`data/docs-index.json` 也只有方法页没有枚举页。没有 `data/enums.json` 就只能把枚举值硬编码进脚本。

## 装配配合读回（R14 实测）

| 成员 | 参数数 | 说明 |
| --- | --- | --- |
| `IAssemblyDoc.AddMate5` | **14** | 末位 `Int32&` 被 comtypes 摘除；返回 `(status, IMate2)` 二元组 |
| `IMate2` | — | `Type` / `Alignment` / `Flipped` / `DisplayDimension` / `GetMateEntityCount()` / `MateEntity(i)` / `GetLinkedMate()` |
| `IMateEntity2` | — | `Reference`（面或边）/ `ReferenceType`（3=面）/ `EntityParams`（8 个 double：点 xyz + 法向 xyz + 2） |
| `IDisplayDimension` | — | `GetNameForSelection()` → `D1@距离1`；`GetDimension()` → `IDimension` |
| 特征树 | — | 配合位于 `MateGroup`（名「配合」）子特征：类型名 `MateDistanceDim`（距离）/ 其它配合同名规律 |
| 分层 QI | — | `new_assembly()` → `IAssemblyDoc`；`ClearSelection2/Extension/EditRebuild3/SaveAs/FirstFeature` 在 `IModelDoc2`；子树遍历在 `IFeature` |

## 保存 / 导出返回结构（R15 实测）

| 方法 | 实参个数 | 返回 |
| --- | --- | --- |
| `IModelDoc2.SaveAs(String NewName)` | 1 | `Boolean` |
| `IModelDoc2.SaveAs2(Name, Version, SaveAsCopy, SaveReferenced)` | 4 | `Int32` 错误码（0=成功） |
| `IModelDoc2.SaveAs3(Name, Version, Options)` | 3 | `Int32` 错误码 |
| `IModelDoc2.SaveAs4(Name, Version, Options)` | **3**（`Int32& Errors`、`Int32& Warnings` 是 [out]，不要传） | `[errors, warnings, ok]` |
| `IModelDocExtension.SaveAs(Name, Version, Options, ExportData)` | **4** | `[errors, warnings, ok]` |
| `ISldWorks.GetExportFileData(Int32 fileType)` | 1 | ExportData 对象（214=STEP；本机不带也能导 STEP） |

## 孔向导（Hole Wizard）

| 成员 | 实参 | 说明 |
|---|---|---|
| `IFeatureManager.HoleWizard5` | **27** | 快捷路线；第 6/7/8 参是 `Diameter/Depth/Length` 覆盖值（不是孔深），`Value1..Value12` 留 0 |
| `IFeatureManager.CreateDefinition` | **1** | 传 `swFeatureNameID_e.swFmHoleWzd = 25` |
| `IFeatureManager.CreateFeature` | **1** | 传 QI 后的 `IWizardHoleFeatureData2`；返回 `IFeature` 或 `None` |
| `IWizardHoleFeatureData2.InitializeHole` | **5** | `(GenericHoleType, StdIndex, FastnerType, SSize, EndType)` |
| `IWizardHoleFeatureData2.ChangeStandard` | **3** | `(Standard, FastenerType, SSize)` → bool |
| `IWizardHoleFeatureData2.AccessSelections` | **2** | `(TopDoc, Component)`；改已有孔前必须调用 |
| `IWizardHoleFeatureData2.ReleaseSelectionAccess` | **0** | 释放 |
| `IFeature.ModifyDefinition` | **3** | `(FeatureData, TopDoc, Component)` —— 提交在 IFeature 上，`IWizardHoleFeatureData2` 没有此方法 |
| `ISldWorks.GetHoleStandardsData` | **1** | 传 `swWzdGeneralHoleTypes_e`；`Legacy(5)` 返回 None |
| `IHoleStandardsData.GetHoleStandards` | **0** | ★ 先调它热身，否则 `GetFastenerTypes` 恒返回 `(None,None,False)` |
| `IHoleStandardsData.GetFastenerTypes` | **1** | 传标准名（从 `GetHoleStandards` 的返回值取），返回 `(索引元组, 名称元组, ok)` |
| `IHoleStandardsData.GetFastenerTableTypes` | **2** | `(标准名, 紧固件ID)` |
| `IHoleStandardsData.GetFastenerTable` | **3** | `(标准名, 紧固件ID, 表ID)` |

**`IWizardHoleFeatureData2` 关键命名属性**（全部 double，单位米；`EndCondition` 用 `swEndConditions_e`）：

`ThruHoleDiameter` `ThruHoleDepth` `CounterBoreDiameter` `CounterBoreDepth`
`CounterSinkDiameter` `CounterSinkAngle`(度) `ThreadDiameter` `ThreadDepth` `ThreadAngle`
`TapDrillDiameter` `TapDrillDepth` `HoleDiameter` `HoleDepth` `HeadClearance` `HeadClearanceType`
`DrillAngle` `CounterDrillDiameter/Depth/Angle` `FarCounterSinkDiameter/Angle` `CosmeticThreadType`
`Standard`(str) `FastenerType`(str) `FastenerType2`(int) `FastenerSize`(str) `EndCondition`(int)
`FeatureScope` `AutoSelect` `AssemblyFeatureScope` `HoleFit` `Diameter` `Depth`

**枚举真值**：`swWzdGeneralHoleTypes_e` CounterBore 0 / CounterSink 1 / Hole 2 / PipeTap 3 / Tap 4 / Legacy 5 / CounterBoreSlot 6 / CounterSinkSlot 7 / HoleSlot 8；
`swWzdHoleStandards_e` AnsiInch 0 / AnsiMetric 1 / BSI 2 / DME 3 / DIN 4 / Hasco 5 / HelicoilInch 6 / HelicoilMetric 7 / ISO 8 / JIS 9 / PCS 10 / Progressive 11 / Superior 12 / **GB 13** / KS 14 / IS 15 / AS 16 / PEMInch 17 / PEMMetric 18；
`swFeatureNameID_e.swFmHoleWzd = 25`、`swFmSketchHole = 24`、`swFmHoleTableFeature = 51`。
