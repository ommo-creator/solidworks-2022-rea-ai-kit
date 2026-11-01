# 通用特征参数对照表（SolidWorks 2022 COM 实测）

一页纸回答三个问题：**哪个方法、几个参数、怎么验证对不对**。所有"实参个数"都是 comtypes
`argtypes` 长度减 1（去掉 `this`）后的**实际传参个数**；所有判据都用"体积变化 vs 闭式解"核对过。

先读 §1 的五条铁律，再查 §2 主表，需要抄代码看 §3，验证公式看 §4。

---

## 1. 五条铁律（跨特征通用）

1. **单位**：API 长度一律**米**、角度一律**弧度**；`GetPartBox()` 返回**毫米**；
   `IDimension.Value` 是**毫米**、`IDimension.SystemValue` 是**米**。
2. **选对象，不是选名字**：中文界面下草图叫「草图1」不可硬编码；用
   `SelectByRay(x,y,z, dx,dy,dz, radius, TypeWanted, append, mark, option)`（**11 参**），
   其中 `TypeWanted`：`1`=棱边、`2`=面。无视图的后台会话里 `SelectByID2("", "FACE", …)` 常失败。
3. **先 QI 再调用**：`CreateDefinition` / `GetOpenDocSpec` / `GetDefinition` 返回无类型 `_Dispatch`，
   必须 `obj = obj.QueryInterface(SW.Ixxx)` 才能读到成员；否则 `COMError: (-2147352570, '未知名称。')`
   （`0x80020006 DISP_E_UNKNOWNNAME`）。
4. **判据用体积**：每次特征后 `GetMassProperties2(1, False)` 取数组**索引 3 = 体积（m³）**，
   与闭式解比；`SetSystemValue2` / `ModifyDefinition` 的返回值都不可信。
5. **特征要重建**：改尺寸/改定义后 `EditRebuild3()`，否则读回的几何是旧的。

---

## 2. 主表

| 特征 | 入口方法（接口） | 实参 | 关键参数位 | 判据 |
|---|---|---|---|---|
| 拉伸 | `FeatureExtrusion2`（`IFeatureManager`） | **23** | `D1`（深度）、`T1`（终止条件）、`Sd`（单向） | 体积 + 截面积×深度 |
| 拉伸（新） | `FeatureExtrusion3`（`IFeatureManager`） | 23 | 同 2，尾部 3 个 bool 控制薄壁/方向 | 同上 |
| 切除 | `FeatureCut4`（`IFeatureManager`） | **27** | `T1`（`1`=`ThroughAll`）、`D1` | 体积 − 孔体积 |
| 旋转 | `FeatureRevolve2`（`IFeatureManager`） | **20** | `Dir1Angle`（弧度，全周 `6.283185307179586`）、`IsCut` | 体积 = 截面积×2πR（Pappus） |
| 线性阵列 | `FeatureLinearPattern5`（`IFeatureManager`） | **22** | 前 4 位：实例数1, 间距1, 实例数2, 间距2 | 体积 = 单件×(有效件数) |
| 圆周阵列 | `FeatureCircularPattern4`（`IFeatureManager`） | **7** | `(Num, Spacing弧度, FlipDirection, DName, GeometryPattern, EqualSpacing, VaryInstance)` | 体积 = 单件×Num |
| 圆角 | `FeatureFillet3`（`IFeatureManager`） | **14** | `R1`、`Ftyp`、**`Options` 必须含 `2`(UniformRadius)** | 去料 = `(1−π/4)·r²·L` |
| 倒角 | `InsertFeatureChamfer`（`IFeatureManager`） | **8** | `(Option, Type, Width, Angle, OtherDist, …)`，`Type=1`=角度距离 | 去料 = `0.5·w²·L` |
| 抽壳 | **`InsertFeatureShell`（`IModelDoc2`）** | **2** | `(Thickness, Outward)`；不选面=闭合壳 | 去料 = 内腔体积 |
| 孔（快捷） | `HoleWizard5`（`IFeatureManager`） | **27** | 第 6/7/8 = `Diameter/Depth/Length` **覆盖值** | 体积 − πr²t（按表取值） |
| 孔（可控） | `CreateDefinition(25)` → `InitializeHole` | **1** / **5** | `(GenericHoleType, StdIndex, FastenerType, SSize, EndType)` | 同上，命名属性可逐项覆写 |
| 孔（改已有） | `IFeature.GetDefinition` → `ModifyDefinition` | **0** / **3** | 改前必须 `AccessSelections(topDoc, comp)`（2 参） | 体积随属性线性变 |
| 配合 | `AddMate5`（`IAssemblyDoc`） | **14** | `(Type, Align, Flip, Distance, …)`；返回 `(status, IMate2)` | 组件 `GetXform()` 平移量 |
| 工程图标注 | `InsertModelAnnotations`（`IDrawingDoc`） | **4** | `(Option, Types, AllViews, DuplicateDims)`，`Types=8` 尺寸 | 注记数 / 显示尺寸数 |
| 剖视图 | `CreateSectionViewAt5`（`IDrawingDoc`） | **7** | `(X, Y, Z, Label, Options, ExcludedComponents, SectionDepth)` | 视图数 +1、视图名含标签 |
| 尺寸驱动 | `AddDimension2` → `IDimension.SystemValue` | **3** | `(x, y, z)` 标注位置；`SetSystemValue2(v, 1)` | 体积 = a×b×t |
| 保存 | `SaveAs4` / `Extension.SaveAs` | **3** / **4** | `(Name, Version, Options[, ExportData])` | 返回 `[errors, warnings, ok]` |
| 静默打开 | `GetOpenDocSpec` → `OpenDoc7` | **1** / **1** | `spec.Silent/LightWeight/IgnoreHiddenComponents` | 0.99 s、无弹窗 |

---

## 3. 参数语义与可抄调用串

### 3.1 拉伸 `FeatureExtrusion2`（23）

```
FeatureExtrusion2(Sd, Flip, Dir, T1, T2, D1, D2, Dchk1, Dchk2, Ddir1, Ddir2,
                  Dang1, Dang2, OffsetReverse1, OffsetReverse2,
                  TranslateSurface1, TranslateSurface2, Merge, UseFeatScope,
                  UseAutoSelect, T0, StartOffset, FlipStartOffset)
```

已验证可用的最小集：

```python
fm.FeatureExtrusion2(True, False, False, 0, 0, 0.020, 0.010,
                     False, False, False, False,
                     0.0174532925199433, 0.0174532925199433,
                     False, False, False, False,
                     True, True, True, 0, 0, False)
```

- `T1/T2` 取 `swEndConditions_e`：`Blind 0 / ThroughAll 1 / ThroughNext 2 / UpToVertex 3 /
  UpToSurface 4 / OffsetFromSurface 5 / MidPlane 6 / UpToBody 7 / ThroughAllBoth 9 /
  UpToSelection 10 / UpToNext 11`（**8 空缺**，不要按顺序猜）。
- `D1` 是米；`Dang1/Dang2` 是弧度（1° = 0.0174532925199433）。
- 调用前必须选中**轮廓**（`GetTypeName2() == "ProfileFeature"` 的特征），选基准面会返回 `None`。

### 3.2 切除 `FeatureCut4`（27）

```
FeatureCut4(Sd, Flip, Dir, T1, T2, D1, D2, Dchk1, Dchk2, Ddir1, Ddir2, Dang1, Dang2,
            OffsetReverse1, OffsetReverse2, TranslateSurface1, TranslateSurface2,
            NormalCut, UseFeatScope, UseAutoSelect, AssemblyFeatureScope,
            AutoSelectComponents, PropagateFeatureToParts, OptimizeGeometry,
            T0, StartOffset, FlipStartOffset)
```

- **完全贯穿**：`T1 = 1`；传 `0` 且 `D1=0` 会切出空特征（返回 `None`，体积不变）。
- 草图必须画在**被切的那个面**上（`SelectByRay` 取面再 `InsertSketch(True)`）；
  画在基准面上 `FeatureCut4` 返回 `None`（这是最常见的"切除没反应"）。

### 3.3 旋转 `FeatureRevolve2`（20）

```
FeatureRevolve2(SingleDir, IsSolid, IsThin, IsCut, ReverseDir, BothDirectionUpToSameEntity,
                Dir1Type, Dir2Type, Dir1Angle, Dir2Angle, OffsetReverse1, OffsetReverse2,
                OffsetDistance1, OffsetDistance2, ThinType, ThinThickness1,
                ThinThickness2, Merge, UseFeatScope, UseAutoSelect)
```

```python
fm.FeatureRevolve2(True, True, False, False, False, False, 0, 0,
                   6.283185307179586, 0, False, False, 0, 0, 0, 0, 0, True, True, True)
```

- 全周 = `2π`；`IsCut=True` 即旋转切除。
- 必须有**构造线**做轴：`Set seg = sk.CreateLine(...) : seg.ConstructionGeometry = True`
  （属性在 `ISketchSegment` 上，不在 `ISketchManager` 上）。
- 半圆截面做球时**只画半圆弧 + 构造轴**；多画一条与轴重合的闭合直线会让特征返回 `None`。

### 3.4 阵列

线性（22）：

```python
fm.FeatureLinearPattern5(3, 0.025, 1, 0.0, False, False, "", "",
                         False, False, False, False, True, False, False, False,
                         False, False, 0.0, 0.0, False, False)
```

- 前四位 = 方向1(实例数, 间距 m) + 方向2(实例数, 间距 m)；两个 `""` 是方向参考名（留空即按已选方向）。
- 选特征用 `mark=4`，选方向参考（基准面/棱边）用 `mark=1`。

圆周（7）：

```python
fm.FeatureCircularPattern4(6, 6.283185307179586, False, "", False, True, False)
```

- 轴必须是已选的**圆柱面或棱边**（`mark=1`），被阵列特征 `mark=4`。
- **判据陷阱**：直线阵列若最后一件跨出实体边界，有效件数会少于 `Num`，体积按有效件数算
  （实测 3 件里只有 2.5 个孔在板内）。

### 3.5 圆角 / 倒角 / 抽壳

```python
fm.FeatureFillet3(2, 0.005, 0.0, 0.0, 0, 0, 0, None, None, None, None, None, None, None)
fm.InsertFeatureChamfer(0, 1, 0.003, 0.7853981633974483, 0.003, 0.0, 0.0, 0.0)
md.InsertFeatureShell(0.002, False)          # 注意：IModelDoc2，不是 IFeatureManager
```

- 圆角第 1 参是半径 R1（米），第 5 参 `Options` 位掩码**必须含 `2`**，否则 R1 不生效。
  `swFeatureFilletOptions_e`：`Propagate 1 / UniformRadius 2 / VarRadiusType 4 / UseHelpPoint 8 /
  UseTangentHoldLine 16 / CornerType 32 / AttachEdges 64 / KeepFeatures 128 / CurvatureContinuous 256 /
  ConstantWidth 512 / NoTrimNoAttached 1024 / ReverseFace1Dir 2048 / ReverseFace2Dir 4096 /
  PropagateFeatToParts 8192 / Asymmetric 16384`。
- `swFeatureFilletType_e`：`Simple 0 / VariableRadius 1 / Face 2 / FullRound 3`。
- 倒角 `Type`：`swChamferType_e` `AngleDistance 1 / DistanceDistance 2 / Vertex 3 / EqualDistance 16`；
  `Option`：`FlipDirection 1 / KeepFeature 2 / TangentPropagation 4 / PropagateFeatToParts 8`。
- 抽壳：不选面 = 闭合壳；选中面 = 开口壳（面 `mark=0`）；多厚度用 `IShellFeatureData`。

### 3.6 孔（三种路线，详见 `docs/08-hole-wizard.md`）

```python
# 只选面（选中数必须=1，不要预建草图）
md.FeatureManager.HoleWizard5(2, 13, 356, "M48", 1, 0.0, 0.0, 0.0,
                              0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                              "", False, False, True, False, True, False)
```

- `GenericHoleType`：`CounterBore 0 / CounterSink 1 / Hole 2 / PipeTap 3 / Tap 4 / Legacy 5`。
- `StandardIndex` **按名字查**（`GetHoleStandards()` 返回顺序 ≠ 枚举顺序），且必须先热身。
- 命名属性优先于 `Value1..Value12`（那 12 个槽位现代 UI 不使用）。

### 3.7 配合 / 标注 / 剖视 / 尺寸 / 保存

```python
st, mate = asm.AddMate5(5, 2, False, 0.010, 0,0,0,0,0,0,0, False, False, 0)  # 14 参
d.InsertModelAnnotations(0, 8, False, False)                                # 4 参，Types=8=尺寸
d.CreateSectionViewAt5(0.10, 0.19, 0.0, "A", 0, None, 0)                    # 7 参
md.AddDimension2(0.05, 0.075, 0.0)                                          # 3 参
md.SaveAs4(name, 0, 1)                                                      # -> [err, warn, ok]
```

- 配合：`swMateType_e` `COINCIDENT 0 / CONCENTRIC 1 / TANGENT 4 / DISTANCE 5 / ANGLE 6 / …`；
  `Align`：`ALIGNED 0 / ANTI_ALIGNED 1 / CLOSEST 2`。`GetMates()` 在本版本不存在，扫特征树找 `MateGroup`。
- 标注**两个必要条件**：视图被选中（`SelectByID2(view,"DRAWINGVIEW",…)`）**且**视图引用的模型
  已在会话中打开（`OpenDoc6`）；缺一个就"返回 True 但注记 0"。
- 剖视：先在**图纸层**开草图 `CreateLine` → `seg.Select2(False,0)` → `MakeSectionLine()` →
  `CreateSectionViewAt5(...)`；`ActivateView` 后建的线 `CreateLine` 会返回 `None`。
- 尺寸：切配置后 `IDimension` 的 RCW **缓存了配置上下文**，必须重新 `md.Parameter(...)` 再 QI。
- 保存：`SaveAs4` / `Extension.SaveAs` 返回 `[errors, warnings, ok]`；`errors` 是位标志且粒度粗
  （只读文件也只报 `1`），**必须**配合落盘大小复核。`swFileSaveError_e`：`Generic 1 / ReadOnly 2 /
  FileNameEmpty 4 / FileLock 16 / InvalidFileExtension 256 / RequiresSavingReferences 8192 / …`。

---

## 4. 判据公式速查

| 特征 | 闭式解（去料为正） |
|---|---|
| 拉伸/切除 | `面积 × 深度` |
| 圆柱孔 | `π·r²·t` |
| 沉头孔 | `π·r_thru²·t + π·(R_cb² − r_thru²)·h_cb` |
| 锥沉孔 | 通孔 + 锥台 `(π·h/3)(R² + Rr + r²)` |
| 旋转（Pappus） | `截面积 × 2π × 形心半径` |
| 球 | `(4/3)πR³` |
| 圆角（棱边长 L） | `(1 − π/4)·r²·L` |
| 倒角（宽 w，棱边长 L） | `0.5·w²·L` |
| 抽壳（开口） | `外体积 − 内腔体积` |

核对精度：以上尺寸正确时误差可低至 `1e-20` 量级；若偏差 > `1e-6` 相对值，先怀疑**选错对象**或**没重建**。

---

## 5. 失败模式速查（现象 → 首查项）

| 现象 | 首查 |
|---|---|
| 特征方法返回 `None`，体积不变 | 轮廓/面选错（`GetSelectedObjectCount2(-1)` 是否 ≥1；是否 `==` 期望值） |
| `COMError -2147352570 未知名称` | 没 QI（`CreateDefinition`/`GetDefinition`/`GetOpenDocSpec`） |
| 属性设了但几何不变 | 没 `AccessSelections` 或没 `ModifyDefinition` / `EditRebuild3` |
| 尺寸写到别的配置 | `IDimension` RCW 未重新获取（配置缓存） |
| 注记返回 True 但数量 0 | 模型没在会话里打开，或视图没被选中 |
| 保存 `errors=1` 但文件其实写成了 | `errors` 粒度粗；用文件大小复核 |
| 阵列件数对不上 | 有实例跨出实体边界，按有效件数算 |
| 脚本卡在对话框 | `SetUserPreferenceToggle(10, False)`（尺寸输入）与 `(100, False)`；`InteractiveAdvancedOpen=False` |

### 补充行（P0/P1/P2 实测，2026-10-29）

| 能力 | 入口 | 实参 | 状态 | 要点 |
|---|---|---|---|---|
| 扫描 | InsertProtrusionSwept4 | 20 | ✅ 实测 1.57079633e-05 = πr²L | SelectByID2 草图名：轮廓 mark=1、路径 mark=4 |
| 放样 | InsertProtrusionBlend2 | 18 | 📄 参数已核未跑 | 两轮廓草图 + GuideCurveInfluence |
| 边界凸台 | IBoundaryBossFeatureData + CreateFeature | 1 | 📄 未跑 | Direction1/2 + CurveSet |
| 抽壳(多厚度) | IShellFeatureData.SetMultipleThicknessAtIndex | 2 | ⚠️ 数据类可读，多厚度未跑 | 先 AccessSelections，再写面集 |
| 镜像 | InsertMirrorFeature2 | 5 | ⚠️ 返回 None，未通 | 特征 mark=4 + 基准面 mark=1 |
| 拔模 | InsertMultiFaceDraft / IBody2.DraftBody2 | 6 / 6 | 📄 参数已核 | CreateDefinition(3) 返回 None，别走那条 |
| 材质 | IPartDoc.SetMaterialPropertyName2 | 3 | ✅ 0.936 / 0.924 kg 精确 | 第 1 参是配置名，第 2 参库 basename |
| 自定义属性 | ICustomPropertyManager.Add3 / Get6 / GetAll3 | 4 / 2 / 0 | ✅ 跨保存持久化 | Get6 返回 5 元组，第 1 个才是值 |
| 干涉 | IAssemblyDoc.InterferenceDetectionManager | 0 | ✅ 6.000000000000002e-06 精确 | 先设 TreatCoincidenceAsInterference |
| 爆炸视图 | CreateExplodedView / IConfiguration.AddExplodeStep2 | 0 / 8 | ⚠️ 视图可建，步返回 3(NoComponents) | 需在爆炸视图激活态选中组件 |
| BOM 表 | IModelDocExtension.InsertBomTable | 5 | 📄 参数已核未跑 | 模板 .sldbomtbt 本机未找到 |

### 导出格式矩阵（纯 `SaveAs`，板 100×60×20）

| 扩展名 | 结果 | 体积 | 说明 |
|---|---|---|---|
| `.STEP` / `.STP` | ✅ | 15,766 / 15,780 B | AP203 |
| `.IGS` | ✅ | 22,386 B | **必须 `.igs`，写 `.IGES` 返回 False** |
| `.X_T` | ✅ | 6,295 B | Parasolid |
| `.SAT` | ✅ | 5,852 B | ACIS |
| `.STL` | ✅ | 684 B | 12 三角面 |
| `.WRL` | ✅ | 795 B | VRML |
| `.3DXML` | ✅ | 2,724 B | — |
| `.IFC` | ✅ | 8,810 B | — |
| `.PDF` | ✅ | 174,832 B | 3D PDF |
| `.DXF` / `.DWG` | ❌ | 0 | 零件不支持，走工程图/展开图 |

### 放样 / 拔模 / 镜像 / 抽壳多厚度（第 2 轮实测）

| 能力 | 入口 | 实参 | 状态 | 要点 |
|---|---|---|---|---|
| 放样 | `IFeatureManager.InsertProtrusionBlend2` | 18 | ✅ 8.24656237e-05（理论 8.24668072e-05，偏差 1.2e-9） | 两轮廓草图**都 mark=1**；平行面用 `CreatePlaneAtOffset3` |
| 平行基准面 | `IModelDoc2.CreatePlaneAtOffset3` | 3 | ✅ 生成 `基准面1` | 先选中基准面，再 `(距离, FlipDir, AutoSize)` |
| 拔模 | `IFeatureManager.InsertMultiFaceDraft` | 6 | ✅ 去料 3.61205e-06 | 面 **mark=2**、中性面 **mark=1**；传播范围未定（见坑 45） |
| 镜像实体 | `IFeatureManager.InsertMirrorFeature2` | 5 | ❌ 未通 | SOLIDBODY/PLANE 四种 mark 组合全 None；`IBody2.Select2` 报错 |
| 抽壳加厚 | `IModelDoc2.InsertFeatureShellAddThickness` | 0 | ❌ 无效 | argtypes 只有 this，传厚度被忽略、体积不变 |
| 边界凸台 | `IBoundaryBossFeatureData` | — | ⚠️ 未跑 | 需 CurveSet/Direction 组合 |

放样可抄调用串：

```python
md.Extension.SelectByID2(草图1, 'SKETCH', 0, 0, 0, False, 1, None, 0)
md.Extension.SelectByID2(草图2, 'SKETCH', 0, 0, 0, True, 1, None, 0)
fm.InsertProtrusionBlend2(False, True, True, 1.0, 0, 0, 0.0, 0.0, False, False,
                          False, 0.0, 0.0, 0, True, True, True, 0)
```

### 第 3 轮（负面结论，同样要记）

| 能力 | 入口 | 结论 | 证据 |
|---|---|---|---|
| 镜像实体/特征 | `InsertMirrorFeature2` | ❌ 三种选法全 None | 体积 1.68e-4 前后不变 |
| 实体选择 | `IBody2.Select2` | ❌ comtypes 拒收第 2 参 | `AttributeError: 'int' object has no attribute` |
| 抽壳改厚度 | `IFeature.ModifyDefinition` | ❌ Parameter 1 类型不匹配 | QI 版与 raw `_Dispatch` 版同错 |
| 抽壳多厚度 | `SetMultipleThicknessAtIndex` | ❌ 同上，无法提交 | 未到提交就失败 |
| 钣金基体法兰 | `CreateDefinition(34)` + `CreateFeature` | 0+1 | ✅ 体积 6.0000e-06（100×60×1mm） | 快捷方法 `InsertSheetMetalBaseFlange2` 全 False，别用 |

### 第 5 轮：圆角变体（同一棱边、0.004 m、板 100×60×20）

| Options | 变体 | 去料体积 | 判据 |
|---|---|---|---|
| 2 | 常量半径 | 6.867259e-08 | = (1−π/4)r²L |
| 258 | 曲率连续 | 4.231377e-08 | 约 0.616× 常量半径，不能照搬公式 |
| 514 | 恒定宽度 | 6.867259e-08 | 不退化为半径的前提是传 Width |
| 3 | 传播 | 6.867259e-08 | 单棱边无相邻面时与基础一致 |

### 第 6 轮：曲面拉伸 ✅（`FeatureExtruRefSurface` 21 参）

| 项 | 值 |
|---|---|
| 方法 | `IFeatureManager.FeatureExtruRefSurface`（21 参，Sub） |
| 选中 | 只选开放轮廓草图（`last_profile`） |
| 结果 | 特征 `曲面-拉伸1` / `ExtruRefSurface` |
| 判据 | `GetBodies2(1,False)` = 1 个 sheet body；体积 0、面积 = 0.05×0.03 = 1.5e-3 |

### 第 7 轮：BOM / 爆炸 / 边界凸台

| 能力 | 结论 | 判据 / 关键事实 |
|---|---|---|
| BOM 模板 | ✅ 找到 | `GetUserPreferenceStringValue(22)` → lang 目录，11 个 `.sldbomtbt` |
| 图纸插 BOM | ❌ API 不对 | `Extension.InsertBomTable` 只用于零件/装配；图纸侧实现要 model doc |
| 爆炸视图 | ✅ 已创建 | `CreateExplodedView()` → `GetExplodedViewNames2` = ['爆炸视图1'] |
| 爆炸步 | ❌ 恒 3 | 入口在 `IConfiguration.AddExplodeStep2`；错误 3=NoComponents |
| 边界凸台 | ❌ 无入口 | `swFeatureNameID_e` 无 Boundary；改用 `InsertProtrusionBlend2` |
- 图纸 BOM 补充：`RunCommand(88, "")` 返回 True 但只在 GUI 里打开 PMP，不落表（坑 56）。

### 第 10 轮：工程图公差 + 子装配

| 能力 | 入口 | 实测 |
|---|---|---|
| 尺寸公差 | `md.Parameter('D1@凸台-拉伸1')` → QI `IDimension` → `SetToleranceType(2)` + `SetToleranceValues(0.0002, -0.0001)` | 回读 `GetToleranceType()=2`、`GetToleranceValues()=[0.0002, -0.0001]`，`FullName='D1@凸台-拉伸1@零件1.Part'`、`Value=20.0`（mm） |
| 子装配 | 先 `IAssemblyDoc.AddComponent5(子装配路径,...)` 再往顶层装 | 子装配 `GetComponents(False)`=2；顶层装入「子装配 + 零件」后 `GetComponents(False)`=**4**（会递归摊平）；子装配组件名 `p18_sub-1`、`GetChildren()`=**2** |

调用串：
```python
dim = md.Parameter('D1@凸台-拉伸1').QueryInterface(SW.IDimension)
dim.SetToleranceType(2)                 # 2 = 双向
dim.SetToleranceValues(0.0002, -0.0001)
top = swe.new_assembly(sw).QueryInterface(SW.IAssemblyDoc)   # 必须先 QI
top.AddComponent5(sub_path, 0, "", False, "", 0.0, 0.0, 0.0)
```
