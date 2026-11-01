---
name: sw-com-reversed
description: "SolidWorks 2022 COM 自动化的逆向实测结论：哪条通道能操作文档对象、每个特征方法的精确参数个数与顺序、官方 CHM 参数语义索引、会话日志里的真实调用形态、98 条必踩坑（R1~R34）与量化验证判据。写或调试 SolidWorks API 脚本、VBA 宏、MCP/插件工具前先读本技能，避免重复试错。"
metadata:
  category: engineering-cad
  version: 2.26.0
  verified_on: "SolidWorks Premium 2022 SP5.0 (30.5.0.0049) on Windows; Python 3.13.14 + comtypes 1.4.17"
  evidence: "REA 逆向 Interop 元数据 + 官方 CHM 反编译 + swxJRNL 会话日志 + 本机端到端实跑"
---

# SolidWorks COM 逆向实测
> 本文既是**仓库入口**，也可以直接作为一份 Agent Skill 放进 `skills/` 目录使用。
> 完整说明见 [`README.md`](README.md)；配套数据在 `data/`，可跑示例在 `examples/`。
> 全部结论实测于 **SolidWorks 2022 SP5.0 (30.5.0.0049)**。

本文**不是**建模教程。它只回答三类问题：

1. 为什么脚本报 `Invalid index` / `类型不匹配` / `返回 None` / `窗口假死`？
2. 这个特征方法**到底**该传几个参数、第几个是角度、哪个是 [out]？
3. 怎么用**数值**（体积/质量）证明脚本真的建了东西，而不是"看起来跑成功了"？

建模策略与设计审查不在本文范围；本文只负责"让代码真的动起来"。

## 1. 通道矩阵（第一个决策，选错会浪费几小时）
| 通道 | Application 级 | 文档对象（ModelDoc2/FeatureManager/SketchManager） | 判定 |
|---|---|---|---|
| Python + `comtypes`（早绑定/后期绑定均可） | ✅ | ✅ **全通** | **首选**，本技能以它为准 |
| VBA 宏（SolidWorks 内 `RunMacro`） | ✅ | ✅ 全通 | 可用；参数个数必须对 |
| VBScript（`cscript`，纯 IDispatch） | ✅ | ✅ 全通 | 可用；文件须 ANSI 无 BOM |
| PowerShell + Interop RCW（`New-Object SolidWorks.Interop.sldworks.SldWorksClass`） | ✅ | ❌ 一律 `0x8002000B DISP_E_BADINDEX` | **不可用于文档对象** |
| PowerShell 晚绑定（`New-Object -ComObject SldWorks.Application`） | ❌ `0x8002802B TYPE_E_ELEMENTNOTFOUND` | ❌ | 直接放弃 |
关键差别：SolidWorks 对**强类型 vtable 调用**返回 `DISP_E_BADINDEX`，只接受 **IDispatch 晚绑定**。所以"PowerShell 能连上、`RevisionNumber()` 能读、一到 `doc.GetTitle()` 就炸"不是配置问题，是通道不对。
> 注册 `sldworks.tlb`（`LoadTypeLibEx(..., REGKIND_REGISTER)`，981 个类型）**不能**修复此问题。别再往"补代理/修 ProxyStub"方向试。
Python 侧前置补丁（comtypes 老坑）：`comtypes` 的类型库可能缺 `VT_DISPATCH(9)` 映射，连不上时先注册补丁；`connect()` 必须 `CreateObject` 语义，**不要** `GetActiveObject`（`0x800401E3 操作不可用`）。

## 2. 六条铁律
1. **单位**：API 一律**米 / 弧度**。`0.1` = 100 mm，`360°` = `6.283185307179586`。唯一例外：`IPartDoc.GetPartBox()` 返回**毫米**。
2. **文档对象方法必须晚绑定**：见第 1 节。PS 脚本不要试图自动化建模。
3. **新建零件用 `NewPart()`，别用 `NewDocument(模板,...)`**：模板路径/年份稍不一致就会建出文档后抛错（VBS `61836 无法只写属性`、PS `DISP_E_BADINDEX`），留下"僵尸零件1"。
4. **切除的草图必须画在被切的面上**（先用 `SelectByRay` 选中该面）。画在 `前视基准面` 上，`FeatureCut4` 返回 `None`、不去料，特征数只 +1（空草图）。
5. **中文名不可硬编码**：草图是 `草图1` 不是 `Sketch1`；基准面名可用 `ChrW()` 拼；更稳的是遍历特征树取 `GetTypeName2()=="ProfileFeature"` 再 `Select2(False,0)`。
6. **别信"没报错"**：每次建模后读体积/质量，与理论值比对（第 6 节）。

## 3. 精确签名（含 this 的实测 argtypes 长度）
| 方法 | 实参个数 | 备注 |
|---|---|---|
| `FeatureExtrusion2` | **23** | `(Sd,Flip,Dir,T1,T2,D1,D2,Dchk1,Dchk2,Ddir1,Ddir2,Dang1,Dang2,OffsetRev1,OffsetRev2,TranslateSurf1,TranslateSurf2,Merge,UseFeatScope,UseAutoSelect,T0,StartOffset,FlipStartOffset)` |
| `FeatureCut4` | **27** | 同上再加 `(NormalCut,UseFeatScope,UseAutoSelect,AssemblyFeatureScope,AutoSelectComponents,OptimizeGeometry, ...)`；完全贯穿要 `T1=1` |
| `FeatureRevolve2` | **20** | 角度是弧度；切用 `IsCut=True`（不是 `FeatureRevolveCut2`） |
| `FeatureLinearPattern5` | **22** | 第 1 个实例数、第 2 个间距(m) |
| `FeatureCircularPattern4` | **7** | `(Number, Spacing(rad), FlipDirection, DName, GeometryPattern, EqualSpacing, VaryInstance)` |
| `IFeatureManager.CreateDefinition(ID)` | **1** | 返回**无类型 `_Dispatch`**，必须先 `QueryInterface(ILinearPatternFeatureData)` / `ICircularPatternFeatureData` |
| `IFeatureManager.CreateFeature(fd)` | **1** | 传 QI 后的数据对象；成功返回 `IFeature`，特征名 `阵列(线性)1` |
| `SelectByRay` | **11** | `(x,y,z, dx,dy,dz, rayRadius, TypeWanted, Append, Mark, Option)`，`TypeWanted=2` 是面 |
| `Extension.SelectByID2` | **9** | 第 8 个 Object 形参传 `Nothing`（VBS 里传 `Empty` 报类型不匹配） |
| `Extension.GetMassProperties2` | **2 实参** | `(1, False)`，返回 `(status, [Xc,Yc,Zc,Vol,Area,Mass,...])` |
| `AddComponent5` | **8** | `(路径, 0, "", False, "", x, y, z)`，按**包围盒中心**落位 |
| `AddMate5` | **14** | 末位 `ErrorStatus` 是 [out] 被摘掉；返回 int，但配合照样解算 |
| `FeatureFillet3` | **14** | `(Options,R1,R2,Rho,Ftyp,OverflowType,ConicRhoType,Radii,Dist2Arr,RhoArr,SetBackDistances,PointRadiusArray,PointDist2Array,PointRhoArray)`；`Options=2`(UniformRadius) 才生效，后 7 项传 `None` |
| `InsertFeatureChamfer` | **8** | `(Options,ChamferType,Width,Angle,OtherDist,VertexDist1..3)` |
| `InsertFeatureShell` | **2** | `IModelDoc2.InsertFeatureShell(Thickness, Outward)`，返回 `Void`；先选中面=开口壳 |
| `InsertModelAnnotations` | **4** | `IDrawingDoc.InsertModelAnnotations(Option, Types, AllViews, DuplicateDims)` → `Boolean`；**只有这个旧版能插入注记**，`…2`/`…3` 在本版本静默无动作（坑 19） |
| `IDrawingDoc.MakeSectionLine` | **0** | 把**已选中的草图直线**变成剖切线；不做这步 `CreateSectionViewAt5` 恒返回 `None` |
| `CreateSectionViewAt5` | **7** | `(X,Y,Z,Label,Options,ExcludedComponents,SectionDepth)`；`CreateSectionView()` 0 参亦可 |
| `SelectByRay` 的 `TypeWanted` | — | `1` = 棱边，`2` = 面；射线半径 0.0004 才打得到棱边 |
**参数个数不符的典型报错**：VBA 后期绑定 `"参数数目不对"` / `"无效参数"`；comtypes `TypeError: call takes exactly N arguments`。审计旧宏时先数参数。

## 4. 坑清单（压缩版，全文见 `docs/03-pitfalls.md`（77 条）
- R30 读 BOM 表：见 `docs/04-recipes.md`
- ~~`docs/03-pitfalls.md`~~）
1. 单位米/弧度；`GetPartBox` 毫米。
2. PS 不能操作文档对象（见 §1）。
3. `NewDocument` 模板陷阱 → `NewPart`。
4. 切除草图必须建在被切面（`SelectByRay`）。
5. `doc.SelectByID2` 不存在 → `doc.Extension.SelectByID2`（9 参）。
6. 草图/基准面中文名不可硬编码；`RefPlane` 1/2/3 = 前视/上视/右视。
7. `AddDimension2` 会弹「修改」对话框把进程挂死 → 开局 `SetUserPreferenceToggle(10,False)` + `(100,False)`。
8. 尺寸建完草图残留选中 → `ClearSelection2(True)` 再 `InsertSketch(True)`，否则拉伸拿不到轮廓。
9. 半圆回转只能"半圆弧 + 构造轴线"；多画一条与轴重合的直线 → 回转返回 `None`。
10. comtypes 把无参方法当属性 get 返回 `_Dispatch` → 统一用 `P(obj,"Method")` 包一层。
11. `GetSketchSegments` 返回 `POINTER(IDispatch)`，要 `.QueryInterface(ISketchSegment)` 才有 `Select2`。
12. `AddMate5` / `GetMassProperties2` 的 [out] 参数会被 comtypes 摘掉，位置计数要重算。
13. `SaveAs` 目标已存在返回 `False` 但**文件已写入**；`IAssemblyDoc.GetMates` 在本版本不存在 → 扫特征树找 `MateGroup`。
14. `CreateDefinition()` 返回无类型 `_Dispatch`：不先 `QueryInterface` 就 `CreateFeature` → `ctypes.ArgumentError: COMError: (-2147352570, '未知名称。', (None, None, None, 0, None))`（`0x80020006 DISP_E_UNKNOWNNAME`）。
15. comtypes 对少数方法**不登记固定 argtypes**（`CloseDoc` / `IModelDoc2.InsertSketch` / `ClearSelection2` / `ShowNamedView2` / `ViewZoomtofit2`），`len(argtypes)==0` 表示按 IDispatch 动态派发——仍按官方声明传参即可，不要以为"参数被吃掉了"。
16. 挤出前选**基准面**不可靠（`FeatureExtrusion2` 返回 `None`、体积读成 `None`）；必须用 `feature_profile()` 选中 `ProfileFeature` 草图轮廓。
17. `GetOpenDocSpec()` 返回无类型 `_Dispatch`，**必须** `spec = spec.QueryInterface(SW.IDocumentSpecification)` 再传 `OpenDoc7`，否则 `0x80020006 DISP_E_UNKNOWNNAME`（与坑 14 同源）。
20. 保存错误码 `swFileSaveError_e` 是位标志且粒度粗（只读也报 1，空名/坏扩展名都是 256），不要靠它判因，调用前预检目录/扩展名/写权限，用 `ok` + 落盘大小复核。
18. 装配对象要**分层 QI**：`IAssemblyDoc`（AddComponent5/AddMate5）、`IModelDoc2`（ClearSelection2/Extension/EditRebuild3/SaveAs/FirstFeature）、`IFeature`（子树遍历），否则 `AttributeError: AddComponent5` / `FirstFeature`。
19. 配合**不在** `GetMates`（本版本无此成员），而在特征树 `MateGroup`（名「配合」）的子特征里，类型名 `MateDistanceDim`；详见坑 28。
18. `SelectionManager.GetSelectedObjectType3` 恒返回 `0`（棱边/面/草图线段都一样），**不能用它判类型**；只认 `GetSelectedObjectCount2(-1) >= 1`，再用体积证明。
19. 工程图注记要同时满足两条：① 用 **4 参旧版** `InsertModelAnnotations(0, 8, False, False)`（`…3` 返回 `None`、`…2` 返回 `True`，两个都不做事）；② 视图引用的**模型必须已在会话里 `OpenDoc6` 打开**，否则同样返回 `True` 而注记恒 0。用 `ActivateView` 替代选中视图只会得到 1 注记 0 尺寸。
20. `IDimension.Value` 是**文档单位（毫米）**，`IDimension.SystemValue` 是**米**；同一尺寸 `Value=100` 对应 `SystemValue=0.1`，读标注时别混用。

## 5. 配方（可直接抄，见 `docs/04-recipes.md`）
| 编号 | 内容 | 现象级判据 |
|---|---|---|
| R1 | 板 + 通孔 + 线性/圆周阵列 | 1.2e-4 → 1.17738e-4 → 1.132142e-4 |
| R2 | 装配：`INewAssembly` + `AddComponent5` + `AddMate5` | 组件 xform 位移 -0.03 |
| R3 | 工程图：`INewDrawing(6)` + `CreateDrawViewFromModelView3` | 视图数 1 → 5 |
| R4 | 尺寸驱动：`AddDimension2` + `SystemValue` | 80mm→9.6e-5，50mm→6e-5 |
| R5 | 质量属性：`GetMassProperties2` / `EnumBodies3` | Vol=1.17738e-4 |
| R6 | 回转（球头类）：构造轴 + 半圆弧 | 5.022883 |
| R7 | FeatureData 路线：`CreateDefinition(6)` → QI → 置属性 → `CreateFeature` | `阵列(线性)1`，9.73805e-5 |
| R8 | 静默打开：`GetOpenDocSpec` → QI → `Silent` → `OpenDoc7` | 0.99 s、无弹框（详见 `docs/07-silence.md`） |
| R9 | **剖视图**：图纸草图直线 → `Select2` → `MakeSectionLine()` → `CreateSectionViewAt5` | 视图数 2→3，`剖面视图 A-A`，Type=2（详见 `docs/05-sections.md`） |
| R10 | **圆角**：射线选棱边(TypeWanted=1) → `FeatureFillet3(2,r,0,0,0,0,0,None×7)` | `圆角1`，去料 `1.0730091830e-7` = 理论精确 |
| R11 | **倒角**：`InsertFeatureChamfer(0,1,w,45°,w,0,0,0)` | `倒角1`，去料 `9.0e-8` = `0.5w²L` 精确 |
| R12 | **抽壳**：选面后 `InsertFeatureShell(t, False)` | 闭合 `3.3984e-5` / 开口 `2.3232e-5`，误差 <1e-19 |
| R13 | **工程图注记**：先 `OpenDoc6` 打开模型 → 建视图 → 选中视图 → `InsertModelAnnotations(0, 8, False, False)` → `EditRebuild3` | 注记 0→3、显示尺寸 0→2；读回 `D1@草图1`=100、`通孔孔直径`=13 |
| R14 | **配合读回**：`asm=qi(new_assembly,IAssemblyDoc)` + `md=qi(asm,IModelDoc2)` → `AddMate5(5,2,False,0.01,…)` → 走 `MateGroup` 子特征 → `GetSpecificFeature2` 取 `IMate2` | `(1, IMate2)`、`Type=5`、`Alignment=1`、实体 2 个、`D1@距离1`=10.0 mm |
| R15 | **保存/导出与错误码**：`SaveAs4(name,0,1)` 或 `Extension.SaveAs(name,0,1,exp)` → `(errors,warnings,ok)`；错误码是位标志，粒度很粗 | 正常 `0/0/True`；非法盘符/无目录/只读 → `1`；空名/坏扩展名 → `256`；STEP 带不带 ExportData 都成功 |

| 放样 | `InsertProtrusionBlend2` | 18 | 8.24656237e-05 |
| 拔模 | `InsertMultiFaceDraft` | 6 | 去料 3.61205e-06 |
| 镜像 | `InsertMirrorFeature2` | 5 | 未通（见坑 43） |
| 钣金 | `CreateDefinition(34)`+`CreateFeature` | 0+1 | 6.0000e-06 |
| R16 | **孔向导（推荐路线）**：选面 → `CreateDefinition(25)` → QI `IWizardHoleFeatureData2` → `InitializeHole(类型,标准,紧固件,'M12',终止)` → 写 `CounterBoreDiameter/Depth` 等命名属性 → `CreateFeature` | 去料 `5.336781e-6` = 理论 `5.33672e-6`；`Value1..Value12` 全程留 0（详见 `docs/08-hole-wizard.md
  - `docs/11-feature-matrix.md、`docs/10-data-model.md``：**通用特征参数对照表**（13 个特征的方法/参数个数/关键位/判据/失败模式）
  - `docs/09-toolbox.md`：Toolbox 表库通用查法（任意标准/任意孔的默认值从哪来、怎么查、怎么改）`） |
| R17 | **改已有孔**：`GetDefinition()` → QI → `AccessSelections(md,None)` → 写属性 → `IFeature.ModifyDefinition(fd,md,None)` | 沉台 22/6mm 去料 `4.139048e-6` = 理论精确；不 `AccessSelections` 则几何不变 |
## 6. 验证判据（证明"真建出来了"）
- `100×60×20` 板 = `1.2e-4` m³；加 1×D12 通孔 = `1.17738e-4`（单孔 `2.2619e-6`）；3 件阵列 = `1.132142e-4`。
- `D160×80` 圆柱 = `1.6084954e-3`；6×D12 @R50 阵列去料 `5.42867e-5`。
- 尺寸驱动：80 mm → `9.6e-5`；50 mm → `6e-5`；120 mm → `1.44e-4`。
- 特征树**必须跳过**的固定项：`Favorites / History / Selection Sets / 传感器 / 设计活页夹 / 注解 / Markups / 光源相机与布景 / 实体 / 曲面实体 / 备注 / 方程式 / 材质 / RefPlane×3 / 原点 / Tables`。
- 类型名对照：`ProfileFeature`（草图）、`Extrusion`（拉伸）、`ICE`（切除）、`CirPattern`（圆周阵列）、`Reference`（装配组件）、`MateGroup`（配合）。
- 圆角 r=5 mm 单棱 → 去料 `1.0730091830e-7`（`(1-π/4)r²L`）；倒角 3 mm/45° → `9.0e-8`（`0.5w²L`）。
- 抽壳 t=2 mm：闭合 `3.3984e-5`、开口 `2.3232e-5`；剖视图：视图数 +1、`IView.Type=2`、`IDrSection.GetLabel()=='A'`。
- 工程图注记：`IView.GetAnnotationCount()` 0→3、`GetDisplayDimensionCount()` 0→2；`ActivateView` 变体只有 1/0（说明必须选中视图）；模型未打开时两者都是 0（假成功）。

R36 线稿附图（A4 无图框 / 单图单页 / 编号引线 / 图序与逐页 PDF）

## 7. 文件
- `docs/17-motion.md` — Motion 算例：独立 interop 程序集、`IMotionStudyManager`/`IMotionStudy` 全成员、实测数字、驱动特征需预选。
- `docs/16-kernel.md` — 几何内核身份（Parasolid 33.01.260 / ACIS 20171.0.2）与 `IModeler` 135 成员、造体封送限制。
- `docs/15-gui-map.md` — 2,164 个 GUI 命令 vs API 成员的覆盖度对照（447 条弱映射）。
- `docs/03-pitfalls.md` — 76 条坑的报错原文与修法。
- `docs/02-signatures.md` — 方法/枚举完整对照。
- `docs/13-api-docs.md` — 34 个建模主链方法的**官方参数说明**（CHM 原文，含每个 bool 的含义）。
- `docs/14-chm-decompile.md` — 怎么把 31MB 的 `sldworksapi.chm` 变成可检索索引；`swxJRNL.swj` 日志怎么读。
- `docs/04-recipes.md` — R1~R29 可运行片段（R28 国标法兰族、R29 法兰总装）（R8 静默、R9 剖视的完整版另见 silence.md、sections.md）。
- `docs/12-commands.md` — **命令面**：2,164 条 `swCommands_e` 命令（2,154 条带数值 ID）+ 菜单路径，按 31 类分组。
- `docs/08-hole-wizard.md` — **孔向导**：`Value1..Value12` 的真实身份、`IWizardHoleFeatureData2` 命名属性全表、三条造孔路线、四类孔实测表、7 条坑。
- `docs/05-sections.md` — **剖视图/截面/读现有模型**：5 个 `CreateSectionViewAt*` 重载的精确参数、`IDrSection` 读回项、质量/包围盒/特征树/工程图读取配方。
- `docs/18-ui-strings.md` — **中文界面词汇实测表**（文档名/特征名/基准面名/必跳过的固定文件夹），并记录 `slduiu.dll` 明文扫描不可行的结论。
- `data/docs-index.json` — 12,127 个方法的参数/说明（6.6 MB，插件 `sw_api_doc` 直接查）。
- `data/examples-index.json` — 2,828 个官方示例（VB6/C#/VBNET）。
- `data/commands.json` — 命令面全量表（2,164 条，含 ID/菜单路径）。
- `data/features.json` — **特征参数表机器可读版**（19 条：实参个数/关键位/判据/可抄调用串），插件 `sw_feature_table` 直接查，可按关键词过滤。
- `scripts/swe.py` — harness v2（连接/静默/新建三类文档/选面/草图/特征树/质量/包围盒/落盘：`connect / quiet / new_part / new_assembly / new_drawing / md2 / P / sketch_on_plane / select_face / feature_profile / real_features / segments / mass / mass2 / bodies / bodies_count / body_mass / bbox / save / export_step`）。
- `scripts/preflight.py` — 环境自检（Python、comtypes、SW 版本、模板路径）。
- `scripts/chm_index.py` — CHM → 索引。

## 8. 可以继续补的方向（尚未实测）
`Configurations` 与 `DesignTable`、`SetMaterialPropertyName2` 带材质质量、工程图公差与 `InsertModelAnnotations4`、批量导出与错误码 `swFileSaveError_e`、`ICommandManager` 自建工具栏、`PropertyManagerPage`（不建议自动化）。另：**两套 SolidWorks MCP 不能同挂一个实例**，否则表现为卡死。

## 9. 官方资料三件套（本轮新增的证据源）
1. **CHM 反编译**：`hh.exe -decompile <目标目录> <chm>`，**目标目录必须先建好**，否则退出码 0 但产出 0 个文件（实测踩过）。`sldworksapi.chm`（31.8 MB）→ 17,170 页；`API_GB.chm`（中文，4.9 MB）→ 2,587 页；`swcommands.chm` → 命令行命令 ID。
2. **会话日志** `C:\Users\<用户>\AppData\Roaming\SolidWorks\SOLIDWORKS 2022\swxJRNL.swj`：SolidWorks 把整段会话写成一份**可复现的 VBA 宏**，这就是它自己认可的调用形态。实测它把我调的 `FeatureLinearPattern5(3,0.025,...)` 重写成了 `CreateDefinition(swFmLPattern)`＋属性赋值＋`CreateFeature` —— 由此确认 FeatureData 是内部正规形态。
3. **示例库** `data/examples-index.json`：2,828 个官方示例（装配 167、工程图 197、草图 169、选择 68、阵列 41、拉伸切除 34、保存导出 33、质量 46）。
查参数语义用 `sw_api_doc` 工具或 `docs/13-api-docs.md`；不要靠猜 bool 的含义。

## 10. 命令面（P2：`swCommands_e` 2,164 条）
`swcommands.chm` 反编译后能从 `swCommands_e` 枚举页抽到 **2,164 条命令、2,154 条带数值 ID**，每条都有「ID; 说明; 菜单路径」。用途：

- 想触发一个 UI 动作却没有 API 时，先查命令 ID，再 `sw.RunCommand(cmdID, 0)`（比模拟点菜单稳）。例：`swCommands_Open`=0、`swCommands_New`=1、`swCommands_Save`=2。
- 反向理解工作流：菜单路径直接告诉你这个动作在 GUI 里的位置，等于拿到了官方的功能地图。
- 分类规模（前几名）：`Insert` 88、`View` 78、`Edit` 71、`Tools` 31、`Sketch` 21；其余 1,775 条命名无统一前缀，归入「其他」，按 ID 升序可检索全量表 `data/commands.json`。
查法：`sw_reversed_guide('commands')`（分类节选）或直接读 `data/commands.json`（全量）。
> `swe.py` 已内置别名 `SW = SldWorks`，可直接写 `QueryInterface(SW.IDimension)` / `SW.ISketchSegment` / `SW.IDocumentSpecification`，不必自己 import comtypes.gen。
- 工程图注记 ✅ **已解决**（有前置条件）：模型必须先在会话里打开 + 用 4 参旧版 `InsertModelAnnotations`。孔向导专用位 `65536|131072` 是否额外带来尺寸待补（当前导入已含 `通孔孔直径`）。

## 11. 一键函数（`swe.py` 末尾，10 个）

`solid_rect / solid_circle / cut_circle / cut_rect / pattern_circular / pattern_linear / apply_material / measure / flange / drawing_front_section`

- 每个函数内部完成"选对象 → 建草图/特征 → `EditRebuild3`"，失败判据统一用体积对账。
- `flange()` 一次跑完法兰全流程（6 步体积精确、质量 3.783193 kg），`drawing_front_section()` 出 A4 图并尝试剖视。
- 回归：按本仓库 `examples/` 里的对照脚本逐条复跑（A/B/C 三组思路：连接与枚举、特征与体积对账、剖视与导出）。

## 12 随仓库提供的工具面

| 工具 | 用途 | 需要 |
|---|---|---|
| `docs/` | 本方法库的全部正文（坑清单、配方、签名、剖切、线稿附图…） | 无 |
| `data/commands.json` | 2,164 个 `swCommands_e` 命令号 → 菜单路径（`RunCommand` 用） | 无 |
| `data/docs-index.json` | 12,127 个官方方法页索引（签名 + 参数语义入口） | 无 |
| `data/examples-index.json` | 官方示例索引（C#/VB/C++ 示例正文片段） | 无 |
| `data/features.json` | 19 行特征参数表（方法/实参个数/判据/可抄调用串） | 无 |
| `data/enums.json` | **889 个 `swconst` 枚举 + 5,142 个数值**，另有 113 个枚举 2,599 个成员名 | 无 |
| `scripts/swe.py` | 连接/选择/特征/剖视/导出的一站式助手（含 10 个一键函数） | comtypes |
| `scripts/extract_enums.py` | 从反编译 CHM 重建 `data/enums.json` | 无 |
| `scripts/preflight.py` | 环境自检（python、comtypes、comtypes.gen、SLDWORKS 进程、模板） | comtypes |

`data/enums.json` 的意义：SolidWorks 2022 的 `comtypes.gen.SldWorks` **不含任何 `sw*` 常量**
（`hasattr(SldWorks, "swDocPART")` = `False`），所以"按名字设系统选项"在 Python 侧本来是无解的。
本仓库把 `swconst` 的枚举值抠出来，这条缺口才被补上，例如
`swViewDisplayMode_e: Wireframe=1 / HiddenLinesRemoved=2 / HiddenLinesGrayed=3 / Shaded=4 / ShadedWithEdges=5`。

配套 `swe.py` 里的读表助手：`bom_table(drawing)`（R30）、`bom_components(table,row)` + `comp_path(comp)`（R32）。
- R33 剖视图零件定位 / R34 自动气球：见 `docs/04-recipes.md`（坑 79 记录 ArrayData 布局与 AutoBalloon5 回 None）
