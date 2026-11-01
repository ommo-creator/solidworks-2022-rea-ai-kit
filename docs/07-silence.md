# 静默与无人值守（SolidWorks 2022 SP5 实测）

目的：让脚本跑起来不弹框、不抢焦点、不等用户点"确定"。这里区分三件容易混淆的事：
**① 命令行开关 ② 打开文档时的静默 ③ 运行期对话框抑制**。

---

## 0. 结论先行

| 问题 | 结论 | 证据 |
|---|---|---|
| SolidWorks 有 `/silent` 之类的命令行开关吗 | **官方 API 文档里没有任何 CLI 开关**（19,578 个 CHM 页面搜 `command-line switch/option` = 0 命中） | `cli-recon.json` |
| 那怎么静默 | 走 API 两条：`IDocumentSpecification.Silent` 打开 + `SetUserPreferenceToggle` 抑制对话框 | 本文 §2 §3 |
| 静默打开能省掉什么 | 不弹对话框、不做即时图形刷新，本机 `OpenDoc7` 0.99 s 完成；`OpenDoc6` 对照 0.78 s（**不静默**），所以静默不是提速手段，是"不打扰人" | `p1_silent2.py` |
| 已经踩过的坑 | `GetOpenDocSpec` 返回 `_Dispatch`，直接丢给 `OpenDoc7` 会 `0x80020006 DISP_E_UNKNOWNNAME` | 见 §2 与 pitfalls 第 24 条 |

---

## 1. 命令行

`startup_ParseCmdLine` 确实存在于 `SLDWORKS.exe`（导入表可见），说明它有解析命令行参数的分支，但：

- `sldworksapi.chm`（17,170 页）、`API_GB.chm`（2,587 页）、`sldworksapiprogguide.chm`（170 页）、`swcommands.chm`（74 页）四处全扫，**没有一页描述开关名和语义**；
- 猜测性开关（`/r`、`/m`、`/silent`、`-batch`）没有官方依据，属"试了才知道"，不建议在对客脚本里依赖。

**如果你要无人值守，正确做法是：进程由 `CreateObject("SldWorks.Application")` 拉起（不需要用户点图标），然后全部靠 API 静默，而不是靠命令行。** 详见 `SKILL.md` §1 通道矩阵。

---

## 2. 静默 / 轻量打开（推荐入口）

```
import comtypes.gen.SldWorks as SW        # 必须：类型库已生成

spec = sw.GetOpenDocSpec(path)            # -> _Dispatch（无类型）
spec = spec.QueryInterface(SW.IDocumentSpecification)   # ← 关键，必须重新绑定
spec.Silent = True
spec.LightWeight = True
spec.IgnoreHiddenComponents = True
doc  = sw.OpenDoc7(spec)                  # -> IModelDoc2
```

实测（`re5_mass.SLDPRT`，本机）：

```
before QI : _Dispatch
after  QI : POINTER(IDocumentSpecification)
flags     : True True True
OpenDoc7  -> POINTER(IModelDoc2) in 0.99s  title=re5_mass
mass      : volume=1.1773805328941534e-04
close     : 0
```

对比 `OpenDoc6(path, 1, 1, '', 0, 0)`：0.78 s，`ret[2]` 才是模型对象。两者都能用，**批量开图纸/装配时用 `OpenDoc7` + `Silent`**，因为它同时能给 `ReadOnly` / `ViewOnly` / `ConfigurationName` / `SheetName`，且不弹"轻化/还原"提示。

### 2.1 `IDocumentSpecification` 全部 26 个属性（官方文档索引，逐个可用）

| 属性 | 用途 |
|---|---|
| `FileName` | 目标文件（`GetOpenDocSpec` 已经填好） |
| `Silent` | **静默打开**，不弹框不刷新图形 |
| `LightWeight` / `UseLightWeightDefault` | 轻化打开 |
| `IgnoreHiddenComponents` | 装配里跳过隐藏零部件 |
| `ReadOnly` / `ViewOnly` | 只读 / 仅供查看 |
| `ConfigurationName` | 指定配置 |
| `SheetName` | 工程图指定图纸 |
| `DisplayState` | 显示状态 |
| `DetailingMode` | 工程图详图模式（大装配图纸提速） |
| `UseSpeedPak` | SpeedPak |
| `LoadExternalReferencesInMemory` | 外部参考是否载入 |
| `LoadModel` | 是否加载模型 |
| `AutoRepair` / `CriticalDataRepair` | 自动修复 / 关键数据修复 |
| `InteractiveAdvancedOpen` / `InteractiveComponentSelection` | 交互式高级打开（**自动化里要设 False**，否则等于弹向导） |
| `Selective` / `ComponentList` | 选择性打开指定零部件 |
| `PLMObjectSpecification` | PDM 侧对象 |
| `DocumentType` / `Query` / `AddToRecentDocumentList` | 类型 / 查询 / 是否加入最近列表（**批处理记得设 False**，别污染用户最近文件） |
| `Error` / `Warning` | **打开后读回**的错误与警告码（替代 `OpenDoc6` 的 out 参数） |

> `InteractiveAdvancedOpen = True` 是最常见的"脚本卡住"来源：它会弹出高级打开向导等人点。批处理里显式设 `False`。

---

## 3. 运行期对话框抑制（`SetUserPreferenceToggle`）

读写都只有 1 个实参，回读验证过：
`sw.GetUserPreferenceToggle(id)` / `sw.SetUserPreferenceToggle(id, False)`。

### 3.1 建模/草图相关（最常拦路）

| ID | 枚举 | 本机默认 | 建议 |
|---|---|---|---|
| 10 | `swInputDimValOnCreate` | True | **必须设 False**，否则 `AddDimension2` 弹「修改」对话框直接挂死（实测踩过） |
| 100 | `swSketchOverdefiningDimsPromptToSetState` | False | 设 False |
| 96 | `swSketchPromptToCloseSketch` | True | 关对话框时设 False |
| 122 | `swEnableConfirmationCorner` | — | 角点确认 |
| 368 | `swPromptForAutoMateFlip` | — | 自动配合翻转提示 |
| 540 | `swWarnStartingSketchInContextAssembly` | — | 装配内建草图警告 |
| 578 | `swShowMateReferenceErrors` | — | 配合参考错误 |

### 3.2 打开/保存/引用相关

| ID | 枚举 | 本机默认 | 建议 |
|---|---|---|---|
| 15 | `swExtRefNoPromptOrSave` | False | 外部参考不提示不保存（批处理推荐 True） |
| 227 | `swCollabTopDocsNoPromptOrSave` | — | 协作顶层文档 |
| 329 | `swWarnSaveUpdateErrors` | — | 保存更新错误 |
| 334 | `swWarnSavingReferencedDoc` | — | 保存参考件警告 |
| 564 | `swWhileOpeningAssembliesAutoDismissMessages` | True | 装配打开消息自动消失（已经是 True） |
| 77 | `swShowErrorsEveryRebuild` | True | **重建报错弹窗**，批处理设 False |
| 347 | `swViewShowAnnotationLinkErrors` | — | 注解链接错误 |
| 353 | `swDrawingShowSheetFormatDialog` | — | 工程图图纸格式对话框 |
| 453 | `swDXFExportHiddenLayersWarnIsOn` | — | DXF 隐藏层警告 |
| 619 | `swMakeFirstSelectionTransparentInMateDialog` | — | 配合对话框首选项透明（视觉干扰） |
| 651 | `swDetailingRadialDimsDisplayNearSideMessages` | — | 径向尺寸提示 |

写入/回读实测（`p1_silent2.py`）：

```
 564 swWhileOpeningAssembliesAutoDismissMessages   True -> False=False -> restore True
  77 swShowErrorsEveryRebuild                      True -> False=False -> restore True
```

### 3.3 整型偏好（`swUserPreferenceIntegerValue_e`）

| ID | 枚举 | 用途 |
|---|---|---|
| 306 | `swRebuildErrorAction` | 重建出错时的动作（0 停止 / 1 继续） |
| 271 | `swFeatureManagerDisplayWarnings` | 特征树警告显示 |
| 519 | `swAssemblyOpenMessagesDismissTime` | 装配消息自动消失毫秒数（调小=更少打扰） |
| 294 / 388 / 389 | `swPropertyManagerColorImportantMessage` / `swSystemColorsMateCalloutWarning` / `swSystemColorsMateCalloutError` | 只是配色，不影响阻塞 |
| 469 / 475 | `swShowEquationCircularReferencesMessage` / `…PotentialCircularReferencesMessage` | 方程式循环引用提示 |

---

## 4. 推荐的开场三行

```
sw = swe.connect(visible=True)   # 或 visible=False，完全后台
swe.quiet(sw)                    # SetUserPreferenceToggle(10|100, False)
sw.SetUserPreferenceToggle(77, False)    # 重建错误不弹窗
sw.SetUserPreferenceToggle(564, False)   # 装配消息不打断
```

`visible=False` 的实例仍然能建特征、能保存，只是没有窗口——但**没有视图时 `SelectByID2("", "FACE", …)` 会失败**，必须改用 `SelectByRay`（坑 11）。这是"后台跑"和"能选面"的取舍点，批量无选择操作的任务才用 `visible=False`。

---

## 5. 与坑清单的对应

- 坑 24（本文新增）：`GetOpenDocSpec` 返回 `_Dispatch`，不 QI 就 `OpenDoc7` → `0x80020006 DISP_E_UNKNOWNNAME`；与坑 21（`CreateDefinition` 同一个病）同源。
- 坑 10：`AddDimension2` 弹「修改」框挂死 → 用 `SetUserPreferenceToggle(10, False)` 解决（本文 §3.1）。
