# SolidWorks COM 坑清单（报错原文 → 根因 → 修法）

实测环境：SolidWorks Premium 2022 SP5.0（30.5.0.0049），Windows，Python 3.13.14 + comtypes 1.4.17。

---

## 1. PowerShell 连不上 / 能连上但文档对象全炸

**症状**

```
New-Object : 使用 CLSID {2f315be3-b0e2-4c87-b9f3-efa160fd4b66} 检索组件的 COM 类工厂失败，
原因是出现以下错误: 8002802B Element not found.
```

```
Exception from HRESULT: 0x8002000B (DISP_E_BADINDEX)   # Invalid index.
```

**根因**：`SldWorks.Application` 的 CLSID 没有 `ProxyStubClsid32`，PowerShell 的 IDispatch 绑定会退化成 `TYPE_E_ELEMENTNOTFOUND`；即使用 Interop RCW（`New-Object SolidWorks.Interop.sldworks.SldWorksClass`）连上，**强类型 vtable 调用**在文档对象上也会被 SolidWorks 拒绝（`DISP_E_BADINDEX`）。

**修法**：换通道。Python + comtypes、VBA 宏、VBScript（`cscript`）三条路都全通。PowerShell 只适合读 `RevisionNumber()`、`GetDocumentCount()` 这类 Application 级属性。

**已排除的方向**：`LoadTypeLibEx("sldworks.tlb", REGKIND_REGISTER)` 注册成功（981 个类型、`HKCR\Interface\{IID}` 出现 `ProxyStubClsid32`）**并不能**修复。不要再试。

---

## 2. `0x800401E3 操作不可用 (MK_E_UNAVAILABLE)` — GetActiveObject

**根因**：SolidWorks 没在运行，或运行实例在别的用户/会话里。`GetActiveObject` 不会帮你启动。

**修法**：必须用 `CreateObject`。Python comtypes 里 `comtypes.client.CreateObject("SldWorks.Application")`；用户既有脚本 `sw_earlybind.py` 也已经踩过并改成 CreateObject。

---

## 3. comtypes 连不上：`KeyError: 9` / `VT_DISPATCH`

**根因**：comtypes 的类型库映射缺 `VT_DISPATCH (9)`。

**修法**（在 `import comtypes.client` 之后、`CreateObject` 之前）：

```python
from ctypes import c_int
import comtypes, comtypes.automation as automation
try:
    automation.VT_DISPATCH  # 已存在
except AttributeError:
    automation.VT_DISPATCH = 9
```

另：类型库模块名是 **`SldWorks`**（不是 `SolidWorks`），`from comtypes.gen import SldWorks`。

---

## 4. `NewDocument(模板, 0, 0, 0)` 建出文档但报错

**症状**：VBS `err=61836 无法只写属性`；PowerShell `DISP_E_BADINDEX`；随后文档区多出一个"零件1"僵尸。

**根因**：模板路径年份/语言版本不匹配（`...\SOLIDWORKS 2020\templates\零件.prtdot` 这类硬编码必错）。且 VBA/VBS 里异常会中断，`If swModel Is Nothing` 的兜底根本执行不到。

**修法**：`sw.NewPart()`（返回 `Object`）或 `sw.INewPart()`（返回强类型 `PartDoc`）。装配用 `INewAssembly()`，工程图用 `INewDrawing(6)`（6 = `swDwgPaperA4size`）。
需要模板时查真值：`GetUserPreferenceStringValue(8/9/10)` → 零件/装配/工程图模板路径。

---

## 5. `FeatureCut4` 返回 `None`、不去料、特征数只 +1

**根因**：切草图建在 `前视基准面` 上，而要被切的是拉伸体的顶面。SolidWorks 不接受"草图平面不在目标实体上"的切除。

**修法**：先 `SelectByRay` 选中目标面（`TypeWanted=2`、`Mark=0`），再在该面上 `InsertSketch`，再切除。

```python
ok = md.Extension.SelectByRay(0.05, 0.03, 0.02, 0, 0, 1, 0.001, 2, False, 0, 0)
```

---

## 6. VBS：`类型不匹配: 'Extension.SelectByID2'`

**根因**：第 8 个参数是 `Object` 类型，传 `Empty` 不行。

**修法**：传 `Nothing`。C#/Python 传 `None` / `null`。

另：`doc.SelectByID2` 在 VBS 上"不支持此属性或方法" —— 该成员只在 `IModelDocExtension` 上，必须 `doc.Extension.SelectByID2(name, type, x, y, z, append, mark, Nothing, selectOption)`，共 9 参。

---

## 7. 中文名硬编码 → `SelectByID2` 返回 False

**根因**：中文版界面里草图叫 `草图1`，基准面叫 `前视基准面`；写 `"Sketch1"` / `"Front Plane"` 永远选不中。

**修法**（三选一，按稳健度递增）：

1. `ChrW` 拼名字（VBS）：`ChrW(21069)&ChrW(35270)&ChrW(22522)&ChrW(20934)&ChrW(38754)` = 前视基准面。
2. 用 `RefPlane` 序号：特征树里三个 `RefPlane` 依次是 前视 / 上视 / 右视。
3. **遍历特征树**取类型名：`GetTypeName2()=="ProfileFeature"` → `Select2(False,0)`。

---

## 8. `SelectByRay` 报 `类型不匹配`（错误 13）

**根因**：参数个数多了。实测 **11 参**。

**修法**：`(WorldX, WorldY, WorldZ, RayVecX, RayVecY, RayVecZ, RayRadius, TypeWanted, Append, Mark, Option)`。`TypeWanted=2` = 面，`4` = 边/线，`0` = 全部。

---

## 9. 加尺寸时 SolidWorks 假死 / 脚本无输出

**根因**：`AddDimension2` 触发「修改」输入对话框，模态阻塞，自动化会话没有 UI 可点。

**修法**：开局关掉两个开关（枚举真值来自 `enums.json`）：

```python
sw.SetUserPreferenceToggle(10, False)    # swInputDimValOnCreate
sw.SetUserPreferenceToggle(100, False)   # swSketchOverdefiningDimsPromptToSetState
```

---

## 10. 尺寸改完拉伸返回 `None`、体积 0

**根因**：加尺寸时线段被选中，退出草图时这份"选中"还在，`FeatureExtrusion2` 拿不到完整轮廓。

**修法**：`md.ClearSelection2(True)` → `md.InsertSketch(True)` → 再 `FeatureExtrusion2`。

---

## 11. 回转（半圆球）返回 `None`

**根因**：为了闭合轮廓，又在轴线上画了一条与构造轴线重合的直线 → 轮廓退化（零面积自交）。

**修法**：半圆回转只用「半圆弧 + 一条构造轴线」，`seg.ConstructionGeometry = True` 加在轴线那个 `SketchSegment` 上（**不是** `SketchManager` 的属性）。

---

## 12. `TypeError: '_Dispatch' object is not callable`

**根因**：comtypes 把无参方法当属性 get 了，返回 `_Dispatch` 而不是可调用对象。典型：`view.GetNextView`、`feature.GetNextFeature`、`part.GetBodies2`。

**修法**：统一包一层

```python
def P(obj, name, *args):
    v = getattr(obj, name)
    return v(*args) if callable(v) else v
```

---

## 13. `AttributeError: 'POINTER(IDispatch)' object has no attribute 'Select2'`

**根因**：`ISketchManager.GetSketchSegments` / `GetSketchSegments2` 返回的是裸接口指针，不是强类型对象。

**修法**：

```python
import comtypes.gen.SldWorks as SW
seg = seg.QueryInterface(SW.ISketchSegment)
seg.Select2(False, 0)
```

---

## 14. `[out]` 参数导致 `TypeError: call takes exactly N arguments`

**症状**

```
TypeError: GetMassProperties2() call takes exactly 3 arguments (4 given)
```

**根因**：comtypes 会把 `Int32&` 这类 [out] 参数从调用签名里摘掉。`GetMassProperties2(this, Config, UseSelected)` —— 实参只需 **2 个**：`(1, False)`，返回 `(status, arr)`。

同理 `AddMate5` 末位 `ErrorStatus` 被摘掉 → 只传 **14** 个参数，返回 `int`（拿不到 `Mate2`，但配合照样解算）。

---

## 15. `SaveAs` 返回 `False` 但其实写成功了

**根因**：目标文件已存在时 `IModelDoc2.SaveAs` 返回 `False`，但文件被覆盖写入。

**修法**：判据用「文件存在 + 体积 + 时间戳」，不要只看返回值。另：`IAssemblyDoc.GetMates` 在本版本**不存在**（`AttributeError: GetMates`），扫特征树找 `MateGroup`。

---

## 16. 特征树遍历跑飞

**根因**：特征树里有大量非特征节点（文件夹）。

**修法**：跳过 `Favorites / History / Selection Sets / 传感器 / 设计活页夹 / 注解 / Markups / 光源相机与布景 / 实体 / 曲面实体 / 备注 / 方程式 / 材质 / RefPlane×3 / 原点 / Tables`。用 `GetTypeName2()` 白名单反而更省事：`ProfileFeature / Extrusion / ICE / CirPattern / Reference / MateGroup`。

---

## 17. cscript 读 .vbs 报「无效字符」

**根因**：cscript 按 ANSI 读文件。用 UTF-8 **带 BOM** 保存 → 首字节被当非法字符；源码里写中文路径 → 按 GBK 误读，文件存到乱码目录（看似成功，实际找不到）。

**修法**：.vbs 源码保持**纯 ASCII 无 BOM**，路径从环境变量取：

```vbs
Set sh = CreateObject("WScript.Shell")
outdir = sh.ExpandEnvironmentStrings("%SW_OUT%")
```

注意 `Option Explicit` 下必须先 `Dim sh, outdir`。

---

## 18. 中文输出乱码

**修法**：`$env:PYTHONIOENCODING='utf-8'; $env:PYTHONUTF8='1'` 再跑 Python。

---

## 19. 两套 SolidWorks MCP 同挂一个实例 → 卡死

**根因**：两个 MCP 各自持有一个 COM 引用并争用 UI 线程。

**修法**：一次只挂一套；切换前 `CloseAllDocuments(True)` 并退出实例。

---

## 20. `GetSketchSegments` 拿不到线段（返回空）

**报错 / 现象**：`skm.GetSketchSegments` 或 `skm.GetSketchSegments2` 返回 `None`/空，或直接 `AttributeError: GetSketchSegments2`；`len(segments(sk)) == 0`。

**根因**（本机 30.5.0 实测）：
1. `GetSketchSegments` 挂在 **`ISketch`** 上，不在 `ISketchManager` 上 —— 必须先 `P(skm, "ActiveSketch")` 拿到活动草图。`GetSketchSegments2` 根本不存在。
2. 它返回的是**裸元组**（变体 out 数组，4 条线段 → 4 个 `POINTER(IDispatch)`），不是 `(retval, array)` 二元组。按 `(retval, array)` 去解会把数组当 `None` 丢掉。
3. 元组元素要先 `QueryInterface(ISketchSegment)` 才有 `Select2`。

**修法**：先试 `ActiveSketch`，同时接受「元组即数组」与「(retval, array)」两种形状：

```python
act = P(sk, "ActiveSketch")
v = act.GetSketchSegments()
segs = [x for x in v if not isinstance(x, (bool, int, float, str)) and x is not None]
seg = segs[0].QueryInterface(SldWorks.ISketchSegment)
seg.Select2(False, 0)
```

`swe.py` 的 `segments()` 已内置这套兜底。

## 21. `CreateFeature(fd)` 报「未知名称」`0x80020006`

**报错原文**：

```
ctypes.ArgumentError: argument 1: COMError: (-2147352570, '未知名称。', (None, None, None, 0, None))
```

（-2147352570 = `0x80020006` = `DISP_E_UNKNOWNNAME`）

**根因**：`IFeatureManager.CreateDefinition(id)` 返回的是**无类型 `_Dispatch`**。SolidWorks 的
`CreateFeature` 要求真正的 feature-data 接口指针；把裸 dispatch 递进去，它按名字去查成员，查不到就报未知名称。

**修法**（本机实测通过）：

```python
SWFM_LPATTERN, SWFM_CIRPATTERN = 6, 5          # swFeatureNameID_e
fd = md.FeatureManager.CreateDefinition(SWFM_LPATTERN)
fd = fd.QueryInterface(SldWorks.ILinearPatternFeatureData)     # 圆周用 ICircularPatternFeatureData
fd.D1Spacing = 0.025
fd.D1TotalInstances = 3
fd.D1EndCondition = 0
feat = md.FeatureManager.CreateFeature(fd)     # → IFeature，特征树出现「阵列(线性)1」
```

QI 之后 17 个属性全部可写（实测 0 失败）；线性阵列体积 1.2e-4 → 9.73805e-5。

## 22. comtypes `argtypes` 为空 ≠ 方法没有参数

**现象**：`len(getattr(SldWorks.IModelDoc2.ClearSelection2, "argtypes")) == 0`，看起来"参数被吃掉了"；
按 0 个参数调用却报参数错误。

**根因**：本机 30.5.0 的 typelib 里少数方法没有登记固定签名，comtypes 走 IDispatch 动态派发。
实测这 5 个：`ISldWorks.CloseDoc`、`IModelDoc2.InsertSketch`、`IModelDoc2.ClearSelection2`、
`IModelDoc2.ShowNamedView2`、`IModelDoc2.ViewZoomtofit2`；`ISketchManager.InsertSketch` 同理（声明 1 个、argtypes 0 个）。

**修法**：**按 CHM/官方声明传参**，不要按 `argtypes` 长度传。52 个方法核对下来，其余 46 个与官方声明完全一致。

## 23. 挤出前选了基准面 → `FeatureExtrusion2` 返回 `None`、体积读成 `None`

**现象**：`FeatureExtrusion2(...)` 不报错但返回 `None`；紧接着 `swe.mass2(md)` 抛
`TypeError: 'NoneType' object is not iterable`。

**根因**：挤出前选的是 `前视基准面`，SolidWorks 没有把"该面上的草图轮廓"当成有效轮廓。

**修法**：选**草图特征本身**，而不是基准面：

```python
assert swe.feature_profile(md) is True     # 选中 GetTypeName2()=="ProfileFeature" 的那个
md.FeatureManager.FeatureExtrusion2(...)   # 之后板体积 1.2e-4 正常
```

同一坑也解释了"为什么有时能挤、有时不能"：取决于上一次操作后选择集里残留的是什么。

---

## 24. `GetOpenDocSpec` 不 QI 就 `OpenDoc7` → `0x80020006 DISP_E_UNKNOWNNAME`

**报错原文**

```
ctypes.ArgumentError: argument 1: COMError: (-2147352570, '未知名称。', (None, None, None, 0, None))
```

**现象**：`spec = sw.GetOpenDocSpec(path)` 之后 `spec.Silent = True` 能设成功、回读也是 `True`，但一调 `sw.OpenDoc7(spec)` 就抛上面这个错。`type(spec).__name__` 是 `_Dispatch`。

**根因**：与第 14 条同一个病——comtypes 拿到的是**无类型 IDispatch**，属性读写走 `IDispatch::Invoke` 能成功，但把它当方法实参传给强类型 `OpenDoc7(Specification: Object)` 时，SolidWorks 侧的封送要求真实接口指针，于是"未知名称"。

**修法**：`QueryInterface` 之后**必须重新赋值**（就地调用不改原变量类型）：

```python
import comtypes.gen.SldWorks as SW
spec = sw.GetOpenDocSpec(path)
spec = spec.QueryInterface(SW.IDocumentSpecification)   # ← 重新赋值，这一步是关键
spec.Silent = True; spec.LightWeight = True
doc = sw.OpenDoc7(spec)                                  # -> POINTER(IModelDoc2)，0.99 s
```

**验证**：`before QI : _Dispatch` → `after QI : POINTER(IDocumentSpecification)` → `OpenDoc7 -> POINTER(IModelDoc2) in 0.99s title=re5_mass`。

---

## 25. `GetSelectedObjectType3` 恒返回 0，不能用它判断选中的是不是边/面

**报错/现象**：射线选边明明成功（`SelectByRay` 返回 `True`、`GetSelectedObjectCount2(-1)` 也 ≥ 1），但 `SelectionManager.GetSelectedObjectType3(0, -1)` 返回 `0`；按 `type == swSelEDGES(1)` 去判断就会误判成"没选中"而跳过特征。同一现象在草图线段上也出现（选中数 1、类型 0）。

**根因**：该接口在本机（30.5.0）对这两类对象不回真实 `swSelectType_e` 值，恒给 0。类型判定的可靠来源是选中对象本身（`ISelectionMgr.GetSelectedObject6` 再 `QueryInterface`），或干脆**用特征是否建成 + 体积变化**来证明。

**修法**：只用 `GetSelectedObjectCount2(-1) >= 1` 判定"选中了东西"，然后直接调特征 API；失败再看体积。

**验证**：`SelectByRay(0.16, 0.12, 0.01, -0.7071, -0.7071, 0, 0.0004, 1, False, 0, 0)` → `True / 选中数 1 / 类型 0`，随后 `FeatureFillet3` 建出 `圆角1` 且体积精确下降 `1.0730091830e-7`。

## 26. 工程图注记插不进去：两个必要条件（缺一个都"返回 True 但注记 0"）

**报错/现象**：选中工程图视图后调用

```python
d.InsertModelAnnotations3(0, 8 | 65536 | 131072, False, False, True, False)   # -> None
d.InsertModelAnnotations2(0, 8, False, False, True, False)                     # -> True
```

`IView.GetAnnotationCount()` 与 `GetDisplayDimensionCount()` 恒为 `0`。
即使换成 4 参旧版 `InsertModelAnnotations(0, 8, False, False)`，**只要被引用的零件没在会话里打开**，
依旧返回 `True` 而注记仍 0 —— 这是最容易误判成"成功"的假象。

**根因（两条，必须同时满足）**：

1. 本机（SW 2022 SP5 / 30.5.0）只有 **4 参旧版** 真正执行插入；`…2` / `…3` 静默不做事。
2. 工程图视图引用的**模型文档必须已经在当前会话里打开**（`sw.OpenDoc6(part, 1, 1, "", 0, 0)`），
   否则视图按需延迟加载，注记导入被静默跳过。

另外：用 `ActivateView` 代替选中视图，只会得到 1 条注记、0 个尺寸；必须
`SelectByID2(name, "DRAWINGVIEW", 0, 0, 0, False, 0, None, 0)`。

**修法**：

```python
sw.OpenDoc6(partPath, 1, 1, "", 0, 0)          # 必要条件 2：先让模型进入会话
dm = swe.new_drawing(sw)
d  = swe.drw(dm)
d.CreateDrawViewFromModelView3(partPath, "*前视", 0.10, 0.14, 0.0)
dm.Extension.SelectByID2(viewName, "DRAWINGVIEW", 0, 0, 0, False, 0, None, 0)
d.InsertModelAnnotations(0, 8, False, False)   # 必要条件 1：4 参旧版
dm.EditRebuild3()
```

**验证（三组对照，同一零件同一会话）**：

| 条件 | 返回 | 注记 | 尺寸 |
|---|---|---|---|
| 模型未打开 + 选中视图 | `True` | 0 | 0 |
| 模型未打开 + `ActivateView` | `True` | 0 | 0 |
| **模型已打开 + 选中视图** | `True` | **3** | **2** |
| 模型已打开 + `ActivateView` | `True` | 1 | 0 |

模型已打开时可读到 `D1@草图1@零件.Part = 100`（毫米）与 `通孔孔直径@草图2@零件.Part = 13`。

## 27. `IDimension.Value` 是毫米、`SystemValue` 是米

**报错/现象**：同一个尺寸，`dim.SystemValue` 读 `0.1`，`dim.Value` 读 `100`，容易以为单位被改坏。

**根因**：`Value` / `GetValue2` 返回**文档单位**（本机 mm），`SystemValue` / `GetSystemValue2` 返回**米**。

**修法**：脚本内部一律用 `SystemValue`（米）；给用户看数值时乘 1000，或直接读 `Value` 但注明单位。
`GetPartBox` 同理返回毫米，`GetMassProperties2` 的体积是立方米。

## 28. 装配里读不到配合 / AddComponent5 报 AttributeError

**报错**：`AttributeError: AddComponent5`、`AttributeError: FirstFeature`、`AttributeError: ClearSelection2`，
或 `md.GetMates()` → `AttributeError: GetMates`。

**根因**：`swe.new_assembly()` / `sw.NewAssembly()` 返回的是**无类型 `_Dispatch`**，不同成员挂在三个不同接口上；
把同一个对象当万能对象用，就会在"另一个接口的方法"上失败。`GetMates` 在本版本确实**不存在**（`IModelDoc2` 与
`IModelDocExtension` 都没有），配合只能从特征树读。

**修法**（分层 QI）：
```python
asm = qi(swe.new_assembly(sw), SW.IAssemblyDoc)   # AddComponent5 / AddMate5
md  = qi(asm, SW.IModelDoc2)                      # ClearSelection2 / Extension / EditRebuild3 / SaveAs / FirstFeature
f   = qi(md.FirstFeature(), SW.IFeature)          # GetFirstSubFeature / GetNextSubFeature / GetTypeName2
```

**验证**：分层后 `AddMate5` 返回 `(1, POINTER(IMate2))`；`MateGroup` 子特征 `MateDistanceDim`（「距离1」）可读
`Type=5`、`Alignment=1`、`GetMateEntityCount()=2`、`D1@距离1` = 10.0 mm。

## 29. 保存错误码粒度很粗，不能靠它区分失败原因

**现象**：目标文件只读时 `errors = 1`（`swGenericSaveError`），而不是 2（`swReadOnlySaveError`）；
空文件名与未知扩展名都报 256（`swFileSaveAsInvalidFileExtension`）；目录不存在、盘符非法、文件名含 `<>` 全是 1。

**根因**：`swFileSaveError_e` 是**位标志集合**（1/2/4/8/…/8192），SW 在很多失败分支只置 `swGenericSaveError(1)`，
细粒度码并没有被置位。另外 0 不是任何枚举成员，0 就表示"没有错误"。

**修法**：不要解析错误码来决定重试逻辑，改成**调用前预检**：
```python
assert not os.path.exists(path) or os.access(path, os.W_OK)   # 覆盖权限
assert os.path.isdir(os.path.dirname(path))                   # 目录存在
assert os.path.splitext(path)[1].lower() in {'.sldprt', '.sldasm', '.slddrw', '.step', '.stp', '.iges', '.x_t', '.stl', '.pdf', '.dxf', '.dwg'}
```
再用 `ok` 布尔 + 文件落盘（`os.path.getsize`）复核；错误码只用于写日志。

**验证**：非法盘符/无目录/只读/非法字符 → `errors=1, ok=False`；空名/未知扩展名 → `errors=256, ok=False`；
正常保存 → `errors=0, warnings=0, ok=True`；`SaveAs3`/`SaveAs2` 直接返回 `1` 而不带 warn。

## 30. 孔向导的 Value1..Value12 是"覆盖槽"，不是 12 个尺寸

**现象**：`HoleWizard5(..., 12 个 0.0, ...)` 造出的沉头孔看不到沉台、螺纹孔去料大得离谱（等效 Ø50.8）；
换成"自定义 12 个 Value"也猜不出对应关系，改一个值不知道动的是哪个尺寸。

**根因**：`Value1..Value12` 是旧版遗留的用户覆盖槽，标准表（GB/ISO/DIN）驱动时根本不参与；
真正的几何来自 `IWizardHoleFeatureData2` 的命名属性。另外 `HoleWizard5` 第 6/7/8 参是
`Diameter / Depth / Length` 覆盖值，把"孔深"传进 `Diameter` 会洗出一个大坑。

**修法**：别猜 Value。用命名属性：
```python
fd = md.FeatureManager.CreateDefinition(25).QueryInterface(SW.IWizardHoleFeatureData2)  # 25 = swFmHoleWzd
fd.InitializeHole(0, 13, 376, 'M12', 1)      # 沉头孔 / GB / 六角头 / M12 / 贯穿
fd.CounterBoreDiameter = 0.024              # 想改哪个就写哪个
fd.CounterBoreDepth    = 0.008
feat = md.FeatureManager.CreateFeature(fd)
```
改已有孔则 `fd.AccessSelections(md, None)` → 写属性 → `feat.ModifyDefinition(fd, md, None)`。

**验证**：路线 B 去料 `5.336781e-6` vs 理论 `5.33672e-6`；路线 C 去料 `4.139048e-6` vs 理论
`4.139048e-6`（偏差 `2.0e-20`）。详见 `docs/08-hole-wizard.md`。

## 31. GetFastenerTypes 不先 GetHoleStandards 就返回 (None,None,False)

**现象**：`hs = sw.GetHoleStandardsData(1).QueryInterface(SW.IHoleStandardsData)` 之后直接
`hs.GetFastenerTypes('GB')` → `(None, None, False)`，看起来像"GB 不支持锥沉孔"；
同一实例里先调一次 `hs.GetHoleStandards()` 再调，就正常返回 11 个紧固件。

**根因**：该接口内部表是惰性初始化的，第一次 `GetFastenerTypes` 在未初始化状态下失败并且**不报错**，
只把 ok 置 False。

**修法**：拿到 `IHoleStandardsData` 后先 `hs.GetHoleStandards()` 热身，再查紧固件；
并且**按返回的名字**取标准索引（顺序是 `(0,1,16,2,4,13,…)`，不是枚举顺序）。

**验证**：热身前后同一调用由 `(None,None,False)` 变为
`([363,362,369,373,…], ['内六角花形半沉头螺钉 GB/T2674-1986', …], True)`。

## 32. 只写属性不 AccessSelections，几何不会变

**现象**：`fd.CounterBoreDiameter = 0.03` 然后 `feat.ModifyDefinition(fd, md, None)` 返回 `True`、
属性回读也是 0.03，但体积一点没变。

**根因**：`IWizardHoleFeatureData2` 是**编辑器对象**，属性只写进编辑器；必须先
`AccessSelections(topDoc, component)` 把特征上下文挂上，`ModifyDefinition` 才会真正重建几何。

**修法**：`fd.AccessSelections(md, None)` → 写属性 → `feat.ModifyDefinition(fd, md, None)` → `md.EditRebuild3()`。
（`IWizardHoleFeatureData2` 本身没有 `ModifyDefinition`，提交在 `IFeature` 上。）

**验证**：不调用 `AccessSelections` 时体积不变；调用后去料 `4.139048e-6` 与理论完全一致。

## 33. 木螺钉/自攻螺钉类紧固件没有 M12 规格，CreateFeature 直接返回 None

**现象**：GB 锥沉孔 11 个紧固件里，`363/362`（内六角花形沉头/半沉头）能造出 M12，
其余 `369/373/368/372/367/371/365/366/370`（木螺钉、自攻螺钉）`CreateFeature` 全部返回 `None`。

**根因**：这些紧固件在 Toolbox 表里没有 M12 行，规格无效时 API 静默返回 None（不抛错）。

**修法**：造孔前先确认"标准 + 紧固件 + 规格"三元组在表里；
`GetFastenerTableTypes/GetFastenerTable` 能查的尽量先查，查不到就按候选逐个试并核对体积。

**验证**：`363` → `M12 内六角花形半沉头螺钉的锥形沉头孔1`，去料 `3.356291e-6`；
其余 9 个全部 `False`。

## 34. 导出 IGES 写 `.IGES` 返回 False

**现象**：`md.SaveAs(r'...\x.IGES')` 返回 `False`，文件 0 字节；同一模型写 `.igs` 成功 22,386 B。
**根因**：SolidWorks 的导出器按扩展名分派，`.IGES` 不在白名单。
**修法**：用 `.igs`（同理 `.stp`/`.x_t`/`.sat` 也可，但 `.STEP` 本身是有效的）。
**判据**：`ok=True` 且文件 > 1 KB。

## 35. 草图局部坐标系：前视基准面上"竖直"线不能用世界 Z 当 y

**现象**：在 `前视基准面` 上调 `CreateLine(0,0,0, 0,0,0.05)` 返回 `False`；草图随后从特征树里**消失**（空草图被自动删除）。
**根因**：`CreateLine(x1,y1,z1,x2,y2,z2)` 收的是**草图局部坐标**。前视基准面（XZ 平面）的局部 y 对应世界 **Z**，局部 z 指向面外。写世界 Z 到第 6 个参数 → 线垂直于草图平面 → 无效几何。
**修法**：前视面画竖直线写 `CreateLine(0,0,0, 0,0.05,0)`；或用 `CreateLine2(SketchPoint, SketchPoint, ...)`。
**判据**：返回值非 `None`，且草图名仍出现在 `FirstFeature/GetNextFeature` 遍历里。

## 36. 爆炸视图：`CreateExplodedView` 成功但 `AddExplodeStep2` 返回 3

**现象**：`asm.CreateExplodedView()` → `True`；`md.GetConfigurationNames()` 仍是 `['默认']`；随后 `cfg.AddExplodeStep2(0.03, 1, False, 0.0, 0, False, False, False)` 恒返回 `(3, None)`，组件位移不变。
**根因**：`swCreateExplodeStepError_e` 里 **3 = NoComponents**；本机无爆炸视图配置可激活，步骤拿不到可炸组件（GUI 里要"先选中组件再点爆炸步骤"）。
**修法**：本机纯 API 半通——视图对象能建、步加不上。要真正出爆炸图，用桌面自动化（wincu）在 GUI 里选组件→点爆炸步骤，或改用 `IConfiguration.AddExplodeStep` 旧重载。
**判据**：返回码 `0`（`swCreateExplodeStepError_Successful`）才算成功，`True` 不代表成功。

## 37. 没有实体时 `GetMassProperties2` 返回 None

**现象**：只建了两张草图就 `mass2(md)` → `TypeError: 'NoneType' object is not iterable`。
**根因**：`IModelDocExtension.GetMassProperties2` 在无实体文档上返回 `None`（不是空数组）。
**修法**：包一层 `volof()`，`None` 或长度不足时返回 `0.0`。
**判据**：读体积前先确认 `IPartDoc.EnumBodies3(0,True)` 至少 1 个。

## 38. 拔模不能走 `CreateDefinition(3)`

**现象**：`fm.CreateDefinition(3)`（`swFmDraft`）返回 `None`，随后 `.QueryInterface(...)` 报 `AttributeError: 'NoneType' object has no attribute 'QueryInterface'`。
**根因**：本版本拔模不支持 FeatureData 定义通道（与孔/阵列不同）。
**修法**：用 `fm.InsertMultiFaceDraft(6 参)` 或 `IBody2.DraftBody2(6 参)`；`IDraftFeatureData2` 只能从**已存在**的拔模特征 `GetDefinition()` 拿。
**判据**：体积/质量按 `tan(角)×侧面积` 变化。

## 39. `IMathTransform.ArrayData` 读不到

**现象**：`swe.P(component.GetXform(), 'ArrayData')` → `AttributeError`（或 `None`）。
**根因**：`ArrayData` 是 COM 属性但 comtypes 生成的描述符在这条路径上不可用；`GetData` 是 5 个 `[out]` 参数的 Sub。
**修法**：用 `xform.GetData(...)` 接 5 个返回值，或直接读 `IComponent2.Transform2`；要位移最简单是 `IComponent2.GetXform()` → `IMathTransform.GetData` 的第 4 个 out。
**判据**：位移分量与 `AddComponent5` 的中心定位规则一致（坑 21）。

## 40. 放样两份轮廓的 mark 必须都是 1

**现象**：`InsertProtrusionBlend2` 返回 `None`，或只出单面片。
**根因**：放样把**所有 mark=1 的草图**当作截面；写成 (1,2)/(2,1) 就只认到一份轮廓。
**修法**：`SelectByID2(草图1,'SKETCH',...,False,1,None,0)` + `SelectByID2(草图2,'SKETCH',...,True,1,None,0)`，再调 18 参。
**判据**：体积 ≈ 台锥公式 π/3·h·(R²+Rr+r²)；实测 8.24656237e-05 vs 理论 8.24668072e-05。

## 41. 平行基准面没有 `InsertRefPlane` 也很好造

**现象**：想在 z=50mm 处放第二个轮廓，`InsertRefPlane` 的约束枚举查不到、`CreatePlaneAtAngle*` 又不对。
**修法**：先选中参照面，再 `md.CreatePlaneAtOffset3(距离, FlipDir, AutoSize)` —— 3 个实参，返回 IFeature，特征名自动为 `基准面1`。
**判据**：特征树里出现新的 `RefPlane`。

## 42. 拔模：面 mark=2、中性面 mark=1

**现象**：面 mark=1 + 中性面 mark=2 → `InsertMultiFaceDraft` 返回 `None`，体积不变。
**修法**：选面时 mark 传 **2**，中性面（基准面）mark 传 **1**，再调 `(Angle, FlipDir, EdgeDraft, PropType, IsStepDraft, IsBodyDraft)`。
**判据**：0.1 rad、右侧面（60×20mm）实测去料 3.61205e-06；注意这个数比"单面楔形 1.2e-06"大约 3 倍，说明 `PropType=0` 连带了相邻面（见坑 45）。

## 43. 镜像实体这条路没走通

**现象**：`InsertMirrorFeature2(True, False, True, False, 0)` 在 `SOLIDBODY mark=4/1` × `PLANE mark=2/1` 四种组合下**全返回 None**；`IBody2.Select2(False, 4)` 报 `argument 2: AttributeError: 'int' object has no attribute ...`（comtypes 把第二个参数当接口指针）。
**当前结论**：本机 comtypes 下"镜像整个实体"未打通。可行出口：① 桌面自动化在 GUI 里点镜像；② 改镜像**特征**（先 `IFeature.Select2(False,4)` 选特征，镜像面 mark=1）待验；③ 直接建对称几何。
**判据**：镜像体后体积应翻倍（1.2e-4 → 2.4e-4）；没翻倍就是没成功。

## 44. `InsertFeatureShellAddThickness` 是空壳函数

**现象**：`argtypes` 长度只有 1（仅 this），传 `0.004` 后返回 0，抽壳体积一点不变（3.3984e-05）。
**当前结论**：这个入口在本机拿不到厚度参数。多厚度抽壳要走 `IShellFeatureData.MultipleThicknessFaces` + `SetMultipleThicknessAtIndex(i, t)` + `ModifyDefinition`，**未通**。
**判据**：闭合壳 3.39840e-05 / 开口壳 2.32320e-05 必须先复现，再谈多厚度。

## 45. 拔模 `PropType=0` 会连带相邻面

**现象**：只选一个 60×20mm 侧面拔模 0.1 rad，理论单面去料 1.2e-06，实测 3.61205e-06（约 3 倍）。
**根因**：`PropType`（传播类型）传 0 = 默认传播，SW 会把相切/相邻面一并拔模。
**修法**：要单面效果就换 `PropType`（查 `swDraftPropagationType_e`）或改用 `IBody2.DraftBody2` 显式给 FaceList。
**判据**：去料体积与 `0.5·h²·tan(α)·Σ面宽` 对得上；差一个整数倍就说明多面被带上。

## 46. 镜像：三种选法全失败（本机确认不可用）

**现象**：`InsertMirrorFeature2(False, True, True, False, 0)` 恒返回 `None`，体积完全不变（1.68e-4 前后一致）。
**试过的组合**（全部失败）：
1. `SOLIDBODY`（实体）`mark=4` + `PLANE mark=2`；
2. `SOLIDBODY mark=1` + `PLANE mark=1`；
3. 特征 `SelectByID2('凸台-拉伸2','BODYFEATURE',0,0,0,False,4,None,0)`（返回 True）+ `右视基准面 mark=1`；
4. `IBody2.Select2(False, 4)` → `argument 2: AttributeError: 'int' object has no attribute ...`（comtypes 把第二参当接口指针）。
**结论**：本机 comtypes 下镜像实体不可用，不要再试第 5 种 mark 组合。
**出口**：① 桌面自动化在 GUI 里点"镜像"（`mcp__wincu__*`）；② 直接建对称几何（两侧各画一次）；③ 用 `IMirrorSolidFeatureData` 的 `CreateDefinition` 路线（未验证，`swFeatureNameID_e` 里 `swFmMirrorSolid=4`）。
**判据**：成功后体积必须翻倍（1.2e-4 → 2.4e-4）；没翻倍就是没成功。

## 47. `ModifyDefinition` 不收 `IShellFeatureData`

**现象**：`sh.ModifyDefinition(fd, md, None)`（fd 已 `QueryInterface(SW.IShellFeatureData)` 并 `AccessSelections` 成功）报
`(-2147352571, '类型不匹配。', ('TypeError: Parameter 1', (<POINTER(IShellFeatureData) ...>, <POINTER(IModelDoc2) ...>, None)))`。
**试过**：传 QI 后的指针、传未 QI 的 `_Dispatch`（`GetDefinition()` 原对象）——两者都是同一个 "Parameter 1" 类型不匹配。
**对照**：同一台机器上 `IWizardHoleFeatureData2` 走 `ModifyDefinition` 是成功的（R17，误差 2.03e-20），所以不是 `ModifyDefinition` 本身坏，而是**抽壳定义的封送**不支持。
**结论**：抽壳只能建**单一厚度**（`InsertFeatureShell(Thickness, Outward)`），改厚度/多厚度需要 GUI。
**可用判据**：闭合壳 2 mm = 3.3984e-05（理论 1.2e-4 − 0.096·0.056·0.016）；开口壳（先选顶面）= 2.3232e-05。

## 48. 钣金基体法兰在本机返回 False（四种参数组合全试过）

**签名**（官方 19 参，已核对）：`InsertSheetMetalBaseFlange2(Thickness, ThickenDir, Radius, ExtrudeDist1, ExtrudeDist2, FlipExtruDir, EndCondition1, EndCondition2, DirToUse, PCBA, UseDefaultRelief, ReliefType, ReliefWidth, ReliefDepth, ReliefRatio, UseReliefRatio, Merge, UseFeatScope, UseAutoSelect)`。旧版 `InsertSheetMetalBaseFlange` 是 16 参（无后三个）。
**试过的组合**（全部 `feat=False`、草图仍在、无实体生成）：
1. 退出草图后 `SelectByID2('草图1','SKETCH',...,mark=0)` → False；
2. 草图编辑态直接调用 → False；
3. `CreateCustomBendAllowance()` 造出对象传 `PCBA`，`EndCondition1=1` → False；
4. `PCBA=None`、`EndCondition1=0/1` 交叉 → 全 False。
**结论（已被第 4 轮推翻，见下）**：`InsertSheetMetalBaseFlange2` 这条快捷门路不可用。出口：桌面自动化走 GUI（钣金工具栏两次点击即可），或改用"薄壁拉伸 + 圆角"近似建模。
**判据**：成功后体积应为 `长×宽×厚度`（100×60×1mm = 6e-06）；拿到别的数就是没建成。

## 49. 一次失败的 API 调用能把 SolidWorks 进程打挂

**现象**：`InsertSheetMetalBaseFlange2` 连续失败后，下一次 `sw.INewPart()` 直接抛 `(-2147417851, '服务器出现意外情况。')`，后续所有调用都失败（不是脚本问题）。
**修法**：`Get-Process SLDWORKS | Stop-Process -Force`，等 6 秒后重新 `connect()`。脚本要按"每个实验独立进程"设计，或至少在异常后重启实例。
**教训**：批量跑特征实验时，一次失败会污染整个会话；把每个能力写成独立脚本 + 失败即重启，比追上一条 try/except 更稳。

### 48 的更正（第 4 轮）：改走 FeatureData 就通了

REA 在 `sldmodu.dll` 的"特征名 → C++ 类"表里查到 `"Base-Flange" → moSMBaseFlange_c`，同时 `swFeatureNameID_e` 里有 `swFmBaseFlange = 34`，于是改走：

```python
md.Extension.SelectByID2('上视基准面', 'PLANE', 0, 0, 0, False, 0, None, 0)
md.SketchManager.InsertSketch(True)
md.SketchManager.CreateCornerRectangle(0, 0, 0, 0.10, 0.06, 0)
md.SketchManager.InsertSketch(True)
fd = md.FeatureManager.CreateDefinition(34)          # swFmBaseFlange
q = fd.QueryInterface(SW.IBaseFlangeFeatureData)
q.Thickness = 0.001
q.BendRadius = 0.001
f = md.FeatureManager.CreateFeature(q)               # 注意：传 fd，不要传 q
md.EditRebuild3()
```

实测：特征 `基体-法兰1`、`GetTypeName2()` = `SMBaseFlange`，体积 **6.0000e-06** = 100×60×1 mm 精确。文件 `probe-output\p4_sm_fd.SLDPRT` 74,937 B。

两个细节：① `q.AccessSelections(md, None)` 会抛 `(-2147417851, '服务器出现意外情况。')`，但**不影响** `CreateFeature`；② `CreateFeature` 要传**未 QI 的 `fd`**，之前传 QI 后的 `q` 在孔向导那条路上也是这么处理的。

## 50. 快捷方法返回 False 时，先找 `swFmXxx` 走 FeatureData

**模式**（已出现三次）：`InsertSheetMetalBaseFlange2`(19 参) 全 False → `CreateDefinition(34)+CreateFeature` 成功；`HoleWizard5` 需严格前置 → `CreateDefinition(25)` 一把过；`FeatureExtrusion2` 建不出曲面 → 曲面是**另一个特征类**（REA 查到 `"Surface-Extrude" → moExtruRefSurface_c`，而 Interop 里根本没有 `InsertSurfaceExtrude` 成员）。

**查法**：`enums.json` 里 `swFeatureNameID_e` 的 `swFm<名字>`；再到 DLL 里核对该名字的 C++ 类（`findstr /m /i /c:"Base-Flange" *.dll` 或字符串表）。**判据**：FeatureData 路线成功时特征名与体积都对得上，不是返回 True 就算。

## 51. 圆角变体：`Options` 位决定去料量，`ConstantWidth` 不给宽度就退化

**实测**（100×60×20 板，0.004 m 半径，去料 = 板前 − 板后）：

| Options | 含义 | 去料体积 | 与理论比 |
|---|---|---|---|
| 2 | UniformRadius | 6.867259e-08 | 1.0000（理论 6.86725877e-08） |
| 2\|256 = 258 | + CurvatureContinuous | 4.231377e-08 | 约 0.616 |
| 2\|512 = 514 | + ConstantWidth | 6.867259e-08 | 1.0000（**退化成半径**） |
| 2\|1 = 3 | + Propagate | 6.867259e-08 | 1.0000（单棱边无相邻面） |

**结论**：① 曲率连续圆角去料**明显更少**，判据不能沿用 `(1−π/4)r²L`；② `ConstantWidth` 必须把宽度传给第 3 个参数（`Width`），传 0.0 时会静默按半径算，看起来"没生效"；③ 单棱边场景 Propagate 与基础一致是正常的，别误判失败。

## 52. 曲面拉伸：REA 证实特征类存在，但 API 里找不到门

**证据**：`sldmodu.dll` 的特征名表里确有 `"Surface-Extrude" → moExtruRefSurface_c`（还有 `Surface-Knit → moSewRefSurface_c`、`Surface-Loft → moBlendRefSurface_c`、`Surface-Trim → moTrimRefSurface_c`），但**整个 Interop 程序集里搜不到 `InsertSurfaceExtrude` 或任何 `SurfaceExtrude` 成员**。
**已试**：`FeatureExtrusion2`（开放轮廓）→ False 且无实体；`CreateDefinition(62)` 与 `CreateDefinition(11)` → 都返回 None。
**下一步候选**：`IBody2.CreatePlanarTrimSurfaceDLL(2)` / `ICreatePlanarTrimSurfaceDLL(3)`（从曲线直接造平面修剪曲面）、`IFeatureManager.InsertSewRefSurface(5)`（缝合成曲面体，但要有源曲面）、`InsertRuledSurface`（直纹面）。
**判据**：曲面体的 `GetMassProperties` 体积=0、面积>0（`swBodyType_e.swSheetBody = 1`）。

### 52 的更正（第 6 轮，REA 定位到真入口）

**真正的入口是 `IFeatureManager.FeatureExtruRefSurface`（21 参）**，不是"没有入口"。之前搜 `SurfaceExtrude` 搜不到，是因为它叫 `FeatureExtruRefSurface`：

- `sldworks.tlb` 字符串表里紧邻 `FeatureExtrusion` 处有 **`FeatureExtruRefSurface`**；
- `sldapiu.dll` 里有实现名 `auFeatureManager_c::FeatureExtruRefSurface3`；
- `slduiu.dll` 里有 `auModelDoc_c::XDispatch2::FeatureExtruRefSurface`；
- `sldmodu.dll` 里有特征类 `moExtruRefSurface_c`（方法 `checkSketch`、`assignTrackingIdsToExtruFaces`、`getFaceArray`）。

**可抄调用**（开放轮廓：上视基准面一条线，退出草图，选中该草图）：

```python
f = md.FeatureManager.FeatureExtruRefSurface(
    True, False, False,          # Sd, Flip, Dir
    0, 0, 0.03, 0.03,            # T1, T2, D1, D2（米）
    False, False, False, False,  # Dchk1, Dchk2, Ddir1, Ddir2
    0.0, 0.0,                    # Dang1, Dang2
    False, False,                # OffsetReverse1, OffsetReverse2
    False, False,                # TranslateSurface1, TranslateSurface2
    True, True, False, False)    # CapEnd1, CapEnd2, DeleteOriginalFace, KnitResult
```

实测：返回 1（Sub，无返回值），特征树出现 **`曲面-拉伸1` / `ExtruRefSurface`**，`GetBodies2(0, False)=0`（无实体）、**`GetBodies2(1, False)=1`**（曲面体）。

**三个连带事实**：① `swe.bodies()` 只数实体，曲面体必须 `GetBodies2(1, False)`（0.05×0.03 的拉伸曲面实测 sheet=1、solid=0）；② 返回的 `POINTER(IDispatch)` 要先 `.QueryInterface(SW.IBody2)` 才拿到方法；③ **曲面体上 `GetMassProperties(0.0)` 的槽位语义与实体不同**：索引 3 读到 0.0015（= 0.05×0.03 面积），索引 4 读到 0.16（疑为周长 2×(0.05+0.03)），所以曲面判据用「sheet 计数 = 1 且 solid 计数 = 0」，不要照搬实体那套 `arr[3]=体积`。

## 53. 图纸 BOM：`IModelDocExtension.InsertBomTable` 不是给工程图用的

**现象**：工程图里新建视图后，`md.Extension.InsertBomTable(模板, 60, 230, 0, '默认')` **恒返回 None**，不报错、不落表。试了 5 种组合全 None：选中视图 / 不选；`BomType` = 0 / 1 / 2；`ConfigurationName` = `'默认'` / `''`。

**证据**：① CHM 上这个方法自己的说明是 **"Inserts BOM in parts and assemblies"**——它是往零件/装配文档里插 BOM，不是往图纸插；② `slddrwu.dll`（工程图模块）里对应实现是 `?InsertNewBomTable@uiDrawingDoc_c@@UEAAXPEAVuiModelDoc_c@@@Z`，**入参是 model doc，没有模板与坐标**——说明图纸侧走的是另一条（UI 命令）路径。

**可用信息**：BOM 模板目录由 `sw.GetUserPreferenceStringValue(22)`（`swFileLocationsBOMTemplates`）给出，本机 = `<SW_INSTALL>\lang\chinese-simplified`，共 **11 个** `.sldbomtbt`（`bom-standard` / `bom-material` / `bom-costing` / `bom-all` / `bom-circuit-summary` / `bom-stock size` …）。**模板并不缺，缺的是图纸侧插入 API**。

**出口**：① `ISldWorks.RunCommand(<BOM 命令 id>, 0)`（命令 id 见 `commands.json`）；② 直接建不带表的 BOM 式表格（`ITableAnnotation`）自行填行；③ GUI。

## 54. 爆炸步：入口在 `IConfiguration`，但错误码 3 与选中无关

**入口纠正**：`AddExplodeStep2` **不在 `IAssemblyDoc`**（`dir(SW.IAssemblyDoc)` 无此成员，调用只会得到 AttributeError），在 **`IConfiguration`**：`md.ConfigurationManager.ActiveConfiguration.AddExplodeStep2(8 实参)`。

**实测**：`asm.CreateExplodedView()` → True，`asm.GetExplodedViewNames2('')` → `['爆炸视图1']`（爆炸视图确实建出来了）；但 `AddExplodeStep2(0.03, 1, False, 0.0, 0, False, False, False)` 恒返回 **`(3, None)`** = `swCreateExplodeStepError_NoComponents`，即使已用 `IComponent2.Select4/Select2` 选中组件（选中返回 True）。`GetNumberOfExplodeSteps()` 读到 1（计数不等于建成功）。

**错误码全表**：0 Successful / 1 Generic / 2 NoExplodeView / **3 NoComponents** / 4 InvalidRadialAxis / 5 OpenExplodePMP / 6 EditingComponentInContext。

**剩余杠杆**（未验）：`IExplodeStep.SetComponents(1 参)` 可在已有 step 上补组件；或先 `asm.ShowExploded2` 进入爆炸态再建步；或走 GUI（爆炸 PropertyManager 必须处于打开态，对应错误码 5）。

## 55. 边界凸台：2022 的 COM API 没有入口

`IFeatureManager` 里与 Boundary 相关的只有 `SetFreeformBoundaryContinuity`；`swFeatureNameID_e` 121 个成员里没有 Boundary；CHM 索引里 `InsertBoundaryBoss` 查无此方法。→ **本版本只能 GUI 或改用放样（`InsertProtrusionBlend2`，已验证 18 参）**。

## 56. 图纸 BOM 的 GUI 命令：`RunCommand(88, "")` 返回 True 但不落表

`sw.RunCommand` 的签名是 **(Int32 CommandID, String CommandString)**——第二个参数必须是字符串，传 `0` 会报 `argument 2: TypeError: unicode string expected instead of int instance`。

BOM 命令：`swCommands_BillOfMaterials = 88`（`commands.json` 里描述是 "valid for drawings; Table toolbar > Bill of Materials"）。实测：选中 `工程图视图1` 后 `RunCommand(88, "")` → **返回 True**，但 `GetTableAnnotationCount()` 仍为 **0**，图纸上没有任何表。

**原因**：这个命令只是"打开 BOM 插入的 PropertyManager"，真正的创建在那个人机界面里点确认（与爆炸的 `swCreateExplodeStepError_OpenExplodePMP = 5` 同类）。→ 纯 API 建图纸 BOM 走不通，必须 GUI 或自建 `ITableAnnotation`。

**顺带**：`IView.GetTableCount` / `GetTableAnnotationCount` 在本版本都不存在（`未知名称`），表格计数只能在图纸层或遍历注释。

## 57. 桌面自动化够不到 COM 拉起的 SW：窗口是个 160×28@-32000 的幻影

**现象**：`mcp__wincu__*` 想点"BOM PropertyManager 的确定"，却发现 `Get-Process SLDWORKS` 报的 `MainWindowHandle` 指向一个 **160×28、坐标 (-32000,-32000)** 的窗口；`printwindow` 截出来 510 字节空白图。`ShowWindow(SW_RESTORE/SW_SHOW)` + `SetWindowPos(0,0,1600,900)` 执行成功但 `GetWindowRect` 仍然返回 `(-32000,-32000)`。

**实测枚举**（`EnumWindows` 按 pid 过滤）：该进程共 **813 个顶层窗口，只有 1 个 visible**，标题正是 `SOLIDWORKS Premium 2022 SP5.0 - [p16_bom_gui - 图纸1]`，尺寸 160×28 —— 即"窗口对象存在但 UI 从未真正落地"。

**结论**：由 COM（`CreateObject`/`comtypes`）拉起的 SW 实例，**桌面自动化无法可靠驱动**。要走 GUI 验证那些"只能点 PropertyManager"的功能（图纸 BOM、爆炸步、镜像、抽壳多厚度），必须先用 `Start-Process <SW_INSTALL>\SLDWORKS.exe` 起一个**交互实例**并让它真正显示窗口，再用 `wincu` 操作。

**顺带**：`Get-Process.MainWindowHandle` 对这类进程不可靠，别拿它当 GUI 目标句柄；用 `EnumWindows` + `IsWindowVisible` + `GetWindowRect` 自己找。

### 57 的补充（第 9 轮：换成交互实例也不行）

`Start-Process <SW_INSTALL>\SLDWORKS.exe` 起交互实例后：
- 窗口枚举**确实拿到了真窗口**：`986800`，**2048×1152 @ (0,0)**，标题 `SOLIDWORKS Premium 2022 SP5.0` —— 与 COM 版那个 160×28 幻影不同。
- 但 `wincu` 用这个句柄截图仍只得到 **146×21 / 510 字节**空白（`bounds` 仍报 -32000）；**桌面级** `scope="desktop"` 截图（2560×1440）里根本看不到 SOLIDWORKS，只有别的程序。

**结论**：本会话进程所在的 Windows 会话与可见桌面不是同一个，SW 窗口虽然在窗口管理器里"存在且 visible"，但**没有被合成到可见桌面**，因此桌面自动化拿不到像素、也无处点击。→ 四项 GUI 专属（图纸 BOM 确认、爆炸步、镜像、抽壳多厚度）在本环境**只能记录为"API 不存在 + GUI 不可达"，无法取得定量判据**。

**但交互实例换来了一个重要事实**：`RunCommand(88, "")` 在交互实例上返回 True 且**确实弹出了 BOM 的 PropertyManager**（`GetActiveObject` 可用、`Visible=true`、`views=['工程图视图1']`、`GetViewCount=2`、`sel_count=1`），只是没人能点确定。所以"图纸 BOM 必须走 PMP"这条定性与 GUI 侧证据一致。

## 58. 尺寸公差：`Parameter` 只认特征名上的维度，草图形状没有 D1

`md.Parameter('D1@草图1')` 对 `CreateCornerRectangle` 画的矩形返回 **None** —— 矩形四条边不是"被标注的尺寸"，没有 `D1`。可用的是特征维度：`md.Parameter('D1@凸台-拉伸1')` 才有值（`FullName='D1@凸台-拉伸1@零件1.Part'`、`Value=20.0` mm）。
写法：`dim = md.Parameter('D1@凸台-拉伸1').QueryInterface(SW.IDimension)` → `SetToleranceType(2)`（2=双向）→ `SetToleranceValues(上限, 下限)`，回读 `GetToleranceType()`/`GetToleranceValues()` 一致（实测 `[0.0002, -0.0001]`）。
工程图里要改显示尺寸的公差，走 R13 的 `GetDisplayDimensions()` → `IDisplayDimension.GetDimension()` → 同一个 `IDimension`。

## 59. 子装配：`GetComponents(False)` 会递归摊平，`IsSubAssembly` 不是成员

往顶层装配装一个子装配后，`top.GetComponents(False)` 返回 **4**（子装配 + 其 2 个零件 + 另 1 个零件），不是 2 —— 不要拿它当"顶层件数"判据；要判断某个组件是不是子装配，用该组件的 `GetChildren()`（实测 2）或 `GetChildrenCount`，`IComponent2.IsSubAssembly` 在本版本**不存在**（`AttributeError`）。
另：`swe.new_assembly(sw)` 返回无类型指针，`AddComponent5` 会 `AttributeError`，必须先 `.QueryInterface(SW.IAssemblyDoc)`（与坑 19 同源）。

## 60. Motion 算例对象是无类型 `_Dispatch`，零参方法会退化成属性

- 现象：`mgr = md.Extension.GetMotionStudyManager()` 之后 `dir(mgr)` **只有 `QueryInterface`**；
  `mgr.GetMotionStudyCount()` 报 `TypeError: 'int' object is not callable`，`mgr.CreateMotionStudy()` 报 `'_Dispatch' object is not callable`。
- 根因：Motion 的管理器来自**独立程序集** `SolidWorks.Interop.swmotionstudy.dll`（42,648 B），主类型库里没有它，comtypes 只能走动态派发；
  动态派发把零参方法映射成属性取值。
- 修法：一律 `swe.P(mgr, '名字', *args)`；实测 `swe.P(mgr,'GetMotionStudyNames')` → `('运动算例 1',)`、
  `swe.P(mgr,'CreateMotionStudy')` → 新算例、`swe.P(stu,'Calculate')` → `True`。
- 别在 `comtypes.gen.SldWorks` 里找管理器：那里只有 20 个 motion 符号，全是 `ISimulation*FeatureData`。

## 61. `IAssemblyDoc.GetSimulation()` 返回 None 是"加载项没注册"，不是 API 问题

- 现象：`swe.P(asm,'GetSimulation')` → `None`；`sw.GetAddInObject('SldMotion.SldMotionAddin' | 'CosmosWorks.CosmosWorks' | 'SldWorks.Simulation')` 全 `None`。
- 取证：`HKLM\SOFTWARE\SolidWorks\Addins` 只有 Composer / XPS Driver / Presentation Manager for MBD 三项；Motion 与 Simulation **未注册**。
- 结论：Motion 的**算例管理**仍可用（主程序内置，`GetMotionStudyManager` 正常，实测 Calculate=True）；
  **Simulation（FEA）整体不可用**；Motion 的物理求解是否可用取决于该加载项是否启用。
- 判据：拿不到 `GetSimulation()` 时不要继续调 `ISimulation` 的方法，改为 `GetMotionStudyManager()` 走算例路线。

## 62. `IModeler` 造体：数组参数在 Python/VBS 都封送不进去

- 现象：`mdl.QueryInterface(SW.IModeler)` 后 135 个成员能列出来，但 `CreateBodyFromBox3([0,0,0,0.1,0.2,0.3])`
  报 `COMError (-2147352563, '内存已锁定。')`；`ICreateBodyFromBox2(c_double*6)` 报 `expected LP_c_double instance instead of list`；
  VBS 里 `mdl.ICreateBodyFromBox2(a)`（VBS 原生数组）报 `err 13 类型不匹配`，`body=Empty`。
- 根因：官方签名是 `ByRef BoxDimArray As System.Double`（数组 byref），comtypes 与 VBS 的晚绑定都无法把它封送成正确的 SAFEARRAY。
- 修法：内核直造改用 **C#/VBA 早绑定**；日常建模不直调 `IModeler`，继续走特征 API（拉伸/旋转/抽壳同样落到 Parasolid）。
- 旁证数据：`pskernel.dll` 61,672,000 B / **Parasolid 33.01.260**；`spaacis.dll` 58,350,408 B / ACIS 20171.0.2；详见 `docs/16-kernel.md`。

## 63. 爆炸步：`AddExplodeStep2` 恒返回 3，`ExplodeDistance` 写不进

- 现象：装配体两个组件、都已 `Select4(..., 0, False)` 选中（选中数 1~2），`cfg.AddExplodeStep2(0.03, 1, False, 0, 0, False, False, False)` 仍返回 `(3, None)` = `swCreateExplodeStepError_NoComponents`。
- `CreateExplodedView()` 反而成功，自动生成 `爆炸视图1` + 步骤 `链1`（`GetNumOfComponents()`=2），但 `st.ExplodeDistance = 0.05` 赋值后回读**仍是 0.0**，`SetComponents(names)` 抛 `COMError -2147417851 '服务器出现意外情况。'`。
- 修法：纯 API 只能拿到"爆炸视图 + 步骤容器"；真正摆位要在 GUI 里做（本机 COM 实例没有可用窗口，见坑 57，需交互实例）。
- 另记：`Select4` 是**三参** `(Append, Mark, ShowPopup)`，第二件要 `Append=True` 否则互相顶掉（现象：选中数恒 1）；`ShowExploded2` 是**两参** `(ShowIt, ExplodeViewName)`，只传一个报 `required argument 'ExplodeViewName' missing`。

## 64. 抽壳多厚度：`MultipleThicknessFaces` 赋值必抛服务器错误

- 现象：`IShellFeatureData.AccessSelections(md, None)` → True，接着 `fd.MultipleThicknessFaces = <面>` 无论传 list / tuple / 单个 `IFace2` / `comtypes.automation.VARIANT(VT_DISPATCH)`，一律 `COMError (-2147417851, '服务器出现意外情况。')`；`GetMultipleThicknessFacesCount()` 始终 0。
- `m.InsertFeatureShellAddThickness(0.004)`（官方 1 参 Sub）返回 0 但体积不变（闭合壳仍 3.3984e-05），是空壳调用。
- 修法：多厚度只能走 GUI；或几何替代（抽壳 + 局部薄壁拉伸/偏移面）。单厚度抽壳本身可用：闭合 3.3984e-05、开口 2.3232e-05。

## 65. 本机镜像（`InsertMirrorFeature2` / `IPartDoc.InsertMirrorFeature`）恒 False

- 九种组合全试：feature mark0/4 + plane mark1/2、feature + face、SOLIDBODY + plane（mirrorBody=True/False）、plane 先选、`IPartDoc.InsertMirrorFeature(True/False)`、面→实体→`IBody2.Select2` 后镜像。
- 全部返回 **False**，体积恒 1.17738e-4 不变，特征树不增加 `镜像1`。
- 修法：① GUI 命令；② 直接建对称几何（最稳）；③ `IMirrorSolidFeatureData` + `swFmMirrorSolid=4`（未验）。

## 66. 基准面法向搞错：上视基准面沿 +Y 偏移，不是 +Z

- 现象：在 `上视基准面` 上画 40×40 矩形，再 `CreatePlaneAtOffset3(0.05)` 画 20×20 矩形，用"沿 Z 连接角点"的 3D 引导线做放样 → `InsertProtrusionBlend2` 返回 **True**（不报错！），但 `GetPartBox(False)` 给出 `[-0.0001,-0.0001,-30.0001, 40.0001,50.0001,50.0]` 毫米 —— 实体跑到 y=50、z 还有 -30，体积 2.1333333e-05（理论应为 4.666666667e-05）。
- 根因：三个默认基准面的法向是 **前视 +Z、上视 +Y、右视 +X**；`CreatePlaneAtOffset3(d)` 沿**法向**偏移，所以在上视面上偏移 0.05 得到的是 y=50 的平面，而剖面矩形的局部坐标又映射到 X-Z。引导线沿世界 Z 画，根本连不到第二个剖面。
- 修法：让剖面所在的基准面法向 = 引导线/拉伸方向。要沿 Z 做，就用 **前视基准面** + 偏移；上视面只适合沿 Y 的造型。
- 判据：先用 `IPartDoc.GetPartBox(False)` 看 bbox 再谈体积；bbox 不对就说明基准面选错了（`GetPartBox` 返回毫米，顺序 `xmin,ymin,zmin,xmax,ymax,zmax`）。
- 另记：`EnumBodies3` 返回的是 `IEnumBodies2` 枚举器，**没有 len()**，要 `while True: b = e.Next(1)` 或直接用 `GetBodies2(0, False)` 拿元组。

## 67. 钣金：属性设在未 QI 的 fd 上，CreateFeature 却必须收 QI 后的对象

- 现象：`fd = fm.CreateDefinition(34)` → 设 `fd.Thickness/fd.BendRadius`（晚绑定，成功）→ `fm.CreateFeature(fd)` 抛
  `ArgumentError: argument 1: COMError: (-2147352570, '未知名称。', (None, None, None, 0, None))`；
  反过来只在 QI 得到的 `q = fd.QueryInterface(SW.IBaseFlangeFeatureData)` 上设属性又会抛 `(-2147352571, '类型不匹配。')`。
- 实测矩阵（`p35_sm_try.py`，5 组）：`c1` 原始 fd 设属性 + 传 fd → 失败；`c2` 在 q 上设属性 + 传 fd → 失败；`c3` 原始设属性不 AccessSelections + 传 fd → 失败；`c4` q 设属性 + 传 fd → 失败；**`c5` 原始 fd 设属性 + 传 q → 成功**（`SMBaseFlange` + `FlatPattern`，体积 6.0e-06）。
- 修法：
  ```python
  fd = m.FeatureManager.CreateDefinition(34)      # swFmBaseFlange
  fd.Thickness = 0.001; fd.BendRadius = 0.001     # 属性写在原始 _Dispatch 上
  q = fd.QueryInterface(SW.IBaseFlangeFeatureData)
  m.FeatureManager.CreateFeature(q)               # 交给 CreateFeature 的必须是 QI 后的壳
  ```
- 另记：`fd.AccessSelections(md, None)` 在本机抛 `类型不匹配`（原始对象）或"服务器出现意外情况"（QI 对象），**都不影响** c5 成功。
- 这条修正了 b47 里"传未 QI 的 fd 也能成功"的旧记录（当时实际拿到的是 QI 后的对象）。

## 68. ShowConfiguration2 的返回值不能当判据

- 现象：`AddConfiguration3('BIG', ...)` → `EditRebuild3()` → `ShowConfiguration2('BIG')` 返回 **False**，但 `ConfigurationManager.ActiveConfiguration.Name` 已经是 `BIG`，后续按配置写尺寸/读体积全部作用在 BIG 上。
- 根因：该方法的 BOOL 返回反映"是否需要重算/是否成功切换"的内部状态，不等于"有没有切过去"。
- 修法：判据用 `ActiveConfiguration.Name`；写尺寸前再 `EditRebuild3()` 一次，并按"每个配置各读一次体积"验证互不影响。
- 判据样例（`sw_audit.py`）：BIG 改厚度到 140mm → 8.4e-04，切回 `默认` → 1.2e-04。

## 69. 草图点必须落在草图面内：高度写在局部 y，不是局部 z

- 现象：`前视基准面` 上 `CreateCornerRectangle(0.01, 0, 0, 0.02, 0, 0.05)`（把 50mm 高度写进第 6 参=局部 z）→ 草图能建，但 `FeatureRevolve2` 返回 **False**、无实体、`mass2` 拿 None；特征树里只剩 `ProfileFeature`，看不出任何报错。
- 根因：草图是 2D 的，局部 z 必须恒为 0；写出面外的点让轮廓退化，SW 静默放弃。
- 修法：`CreateCornerRectangle(0.01, 0, 0, 0.02, 0.05, 0)`（高度进局部 y）。前视面局部 (x,y) = 世界 (X,Z)，上视面 = (X,Y)，右视面 = (Z,Y)。
- 判据：回转体积 π(R²−r²)h；本例 0.01~0.02 × 50mm → **4.712388980e-05**，偏差 0。

### 63 的第 12 轮补充：三条入口全试过，只有 SetComponents 在半步上可用

- `IConfiguration.AddExplodeStep(ExplDist, ReverseDir, RigidSubassembly, ExplodeRelated)`（**4 参**，无 out）→ 返回 `None`，`GetNumberOfExplodeSteps()` 仍是 1，组件不位移。
- `IConfiguration.AddRadialExplodeStep(ExplDist, ExplAng, DivergeFromAxis)`（**3 实参**，Error 为 out）→ `(3, None)`，**同样是 `swCreateExplodeStepError_e.NoComponents`**。
- **`IExplodeStep.SetComponents(list(comps))` 有效，但有前提**：必须在刚 `CreateExplodedView()` 的同一会话里调用 —— 返回 `None`、`GetNumOfComponents()` 从 0 变 **2**。传 `tuple` 抛 `COMError (-2147417851, '服务器出现意外情况。')`；传 `(POINTER(IComponent2)*n)()` 抛 `TypeError: Cannot put ... in VARIANT`。**保存后重开装配再调同一条，同样抛"服务器出现意外情况"**。
- `ExplodeDistance` 无论写在原始 `_Dispatch` 上还是 `QueryInterface(SW.IExplodeStep)` 上，**回读恒为 0.0**；`ShowExploded2(True, '爆炸视图1')` 返回 True、`ViewExplodeAssembly()` 返回 0、`IsExploded` 属性不存在 —— 组件始终不位移。
- 读取端可用：`IExplodeStep` 34 个成员含 `GetComponentXform(Index)` / `IGetComponentXform` / `GetSpecificComponentXForm` / `GetComponents` / `GetComponentName` / `GetSubAssemblyExplodeSteps`。
- `IMathTransform` 在本机只暴露 `count` / `index`，`ArrayData` 读不到（`AttributeError`），要 `GetData` 的 5 个 out 参数才行。
- `IAssemblyDoc.GetComponents(False)` 返回的元素是 `POINTER(IDispatch)`，用前必须 `QueryInterface(SW.IComponent2)`，否则 `AttributeError: 'POINTER(IDispatch)' object has no attribute 'Name2'`。
- 结论：爆炸步"创建 + 给距离"在本版本纯 API 走不通，能自动化的只有"建爆炸视图 + 把组件挂到步骤上"；位移幅度仍需 GUI 或直接在装配里改组件变换。

## 70. `feature_profile()` 取"第一张草图" → 二次特征全部失败
- 现象：圆柱做出后，切孔时 `FeatureCut4` 返回 `False`、体积不变、特征树只多一张空草图。
- 根因：遍历特征树取**第一个** `ProfileFeature`，那永远是最早的 `草图1`（已消费），而不是刚画的 `草图2`/`草图3`。
- 修法：取**最后一张**，或按名字 `SelectByID2('草图3','SKETCH',0,0,0,False,0,None,0)`。`swe.feature_profile(md, mark=0, last=True)` 已修为此行为。
- 判据：每步之后必须 `EditRebuild3()` 再读体积，体积按"上一步实测值 − 本步理论去料"对账。

## 71. `IDrawingDoc` 没有 `SaveAs` / `CreateDrawViewFromModelView3`
- 现象：`d.SaveAs(path)` / `d.CreateDrawViewFromModelView3(...)` 抛 `AttributeError: SaveAs` / `KeyError: 'createdrawviewfrommodelview3'`。
- 根因：`swe.new_drawing()` 返回的是未定型 `_Dispatch`；视图创建在 `IDrawingDoc` 上，存盘在 `IModelDoc2` 上，两个都要 QI。
- 修法：`d = swe.drw(swe.new_drawing(sw))` 再建视图；存盘用 `swe.save(swe.md2(d), path)`。
- 判据：`swe.view_count(d)` 从 1 → 2 → 3；`.SLDDRW` 落盘 90 KB 量级。

## 72. 圆周阵列的轴与特征都不吃"空名字"
- 现象：`SelectByID2('', 'BODYFEATURE', 0,0,0, True, 4, None, 0)` 之后 `FeatureCircularPattern4` 返回 `False`。
- 根因：特征必须按**名字**选；空名字等于没选（也不报错）。
- 修法：`name = [n for n, ty in swe.feature_names(md) if ty == 'ICE'][-1]` → `SelectByID2(name, 'BODYFEATURE', 0,0,0, True, 4, None, 0)`；轴用**外圆柱面** `select_face(..., mark=1)`（不要用基准轴名）。
- 判据：调用前 `GetSelectedObjectCount2(-1)` 应为 2；阵列后体积 = 上一步 − N×单孔。

## 73. 曲线边缘的圆角/倒角不能用直线公式
- 现象：Ø120 圆盘顶面 r3 圆角，实测去料 `7.199949e-07`，而 `(1−π/4)r²·2πR` 给 `7.281269e-07`（差 1.1%）；内孔口 2 mm 倒角实测 `3.853687e-07` vs `0.5w²·2πR` 的 `3.769911e-07`（差 2.2%）。
- 根因：圆角/倒角把圆环的**中性半径**改变了——外凸棱边要减、内凹孔口要加。
- 修法：外圆角用 `(1−π/4)r²·2π(R − r(1−π/4))`（→ 7.203140e-07，差 0.04%）；内孔口倒角用 `0.5w²·2π(R + w/2)`（→ 3.895575e-07，差 1.1%）。
- 结论：直线棱边用精确式判据；环形棱边只能用上述修正式，误差 0.04%~1%，够做回归阈值。

## 74. 剖视图对"前视是圆形轮廓"的零件恒返回 None
- 现象：同一套 `CreateLine → Select2 → MakeSectionLine → CreateSectionViewAt5`，对矩形板 **OK**（视图 2→3，新视图 `Type=2`、`GetSection().GetLabel()='A'`），对**圆柱/法兰** 恒返回 `None`、视图数停在 2、不报错。
- 已排除的因素（都试过，无效）：剖切线长短（0.002~0.055 m 四档）、位置（视图轮廓内/外各两处）、`Options=0/1`、先关草图再 `MakeSectionLine`、`EditSheet()`、清空选择、用 `Line1` 名字选段。
- 视图轮廓读数（`IView.GetOutline()`）：圆柱视图 `(0.0658, 0.1158, 0.1342, 0.1842)`，剖切线 x=0.10 完全落在其中，仍失败。
- 判定：这是**几何相关**的静默失败，不是调用顺序问题。板类（前视为矩形）稳定可用；圆柱/回转类零件请改用"全剖 + 隐藏线可见"或直接给侧视图（`*右视`/`*上视`）再做剖视。
- 判据：`CreateSectionViewAt5` 非 `None` 且视图数 +1、新视图 `Type==2`、`GetSection()` 有 `label`。三者缺一即视为失败，**不要**只看视图数（重复建视图也会让数字 +1，见坑 74 的姊妹条）。

## 75. 重复建视图会让视图数 +1，看起来像剖视成功
- 现象：调用 `section_view()` 前已经用 `CreateDrawViewFromModelView3` 建过一次视图，结果视图数从 2 变 3，误判剖视成功；实际多出来的是一张 `工程图视图2`（`Type=7`），`GetSection()` 为 `None`。
- 修法：`swe.section_view(..., make_view=False)` 复用一个已存在的视图；`swe.drawing_front_section()` 内部已按此实现。
- 判据：新视图必须是 `Type==2` 且能读到 `label`；`Type==7` 一律是普通视图。

### 74 的补充（第 14 轮：把"为什么失败"分离出来了）

同一段剖切线、同一套代码，只换零件与视图比例：

| 零件 | 视图比例 | 视图尺寸 | 线长 | 结果 |
|---|---|---|---|---|
| 板 100×60×20 | 自动(1.08) | 108×68 mm | 76 mm | **OK** |
| 板 100×60×60 | 自动(0.58) | 58×38 mm | 46 mm | None |
| 板 120×120×60 | 自动(0.57) | 68×68 mm | 76 mm | None |
| 板 140×140×60 | 强制 1:1 | 148×148 mm | 156 mm | **OK** |
| 板 100×60×60 | 强制 1:1（线外扩 30 mm） | 108×68 mm | 128 mm | None |
| 板 100×60×60 | 强制 1:1（线外扩 60 mm） | 108×68 mm | 188 mm | **OK** |
| 板 100×60×60 | 强制 1.2:1 | 88 mm 线 | 88 mm | None |
| 板 100×60×60 | 强制 1.5:1 | 106 mm 线 | 106 mm | **OK** |
| 板 100×60×60 | 强制 2:1 | 208×128 mm | 94 mm | **OK（连测 5/5 全过）** |
| 圆柱 Ø120×60 | 自动 | 68×68 mm | 76 mm | None |

- 已排除：线方向（横/竖）、视图（`*前视/*右视/*上视`）、`Options=0/1`、`EditSheet()`、先关草图、清空选择、`Line1` 名字选段、`MakeSectionLine` 是否调用。
- 不是随机：`1:1` 连测 **0/5**、`2:1` 连测 **5/5**。
- 也不能简单归给"线不够长"：`1:1 + 128 mm 线` 失败，而 `1.5:1 + 106 mm 线` 成功。
- **工程结论**：`CreateSectionViewAt5` 的成功与否取决于**视图比例 × 线长的组合**，阈值不公开。可靠做法是**固定一个较大的比例**（实测 `ScaleDecimal = 2.0` 最稳，5/5），再按 `GetOutline()` 外扩 3~4 mm 画线；不要依赖自动比例。
- 写法：`v = sheet.GetNextView()` 后直接 `v.ScaleDecimal = 2.0`，`dm.EditRebuild3()`，再读 `v.GetOutline()` 定线，最后 `MakeSectionLine()` + `CreateSectionViewAt5(...)`。

**第 14 轮末尾已修复**：`swe.section_view()` 改成默认 `ScaleDecimal = 2.0`、按 `IView.GetOutline()` 上下各外扩 3.5 mm 画线、失败时退回自动比例重试一次。
四件零件实测全部通过（视图 `(1,2,3)`、`section_label='A'`、SLDDRW 落盘）：法兰 Ø120×60 → 132,415 B；板 100×60×60 → 72,964 B；板 120×120×60 → 71,529 B；圆柱 Ø120×60 → 85,908 B。


## 76. `AddComponent5` 不预加载 = 静默装空（装配体、STEP、BOM 一起坏）

**现象**：`asm.AddComponent5(path, 0, "", False, "", x, y, z)` 返回 **None**（不是报错），
`asm.GetComponentCount(0)` 得 0，随后：
- `save(.SLDASM)` 仍报成功，文件只有 33 KB；
- `Extension.SaveAs(x.STEP, 0, 1, GetExportFileData(214))` 返回 `[0, 0, True]`，文件 **301 B**，内容是一份 `DATA;` 为空的合规 STEP 壳；
- 装配工程图里 `InsertBomTable2` 照常插入（表数 1），但**没有行**。

**根因**：组件的源零件必须先进入当前 SolidWorks 会话。与坑 26（工程图注记要先 `OpenDoc6`）同源。

**修法**：每个零件在 `AddComponent5` 之前 `sw.OpenDoc6(path, 1, 1, "", 0, 0)`（每种零件一次即可，重复装入不用重复开）。
修好后实测：`GetComponentCount(0)` = **7**、`SLDASM` 152,795 B、`STEP` **82,416 B**（真实几何）、装配图纸 95,497 B。

**判据**：装配体一定要读三条 —— 组件数、STEP 体积（> 几十 KB）、干涉检查耗时/结果；只看到 `SaveAs` 返回 True 会漏掉空的装配体。

---

## 77. BOM 表的行/列读不出来——查错接口了

**现象**：`IView.InsertBomTable2(...)` 返回 `_Dispatch`，表也插上了（`GetTableAnnotationCount()`=1），但对它 `QueryInterface(SW.IBomTableAnnotation)` 读 `RowCount/ColumnCount` 一律 `AttributeError`，看起来"表对象不可读"。

**根因**：行/列/单元格文字在 **`ITableAnnotation`** 上，不在 `IBomTableAnnotation` 上。`IBomTableAnnotation` 只有 BOM 语义（`GetComponents`、`GetModelPathNames`、`Collapse/Expand`、`SaveAsExcel`…），`RowCount`、`ColumnCount`、`DisplayedText`、`GetColumnTitle` 全是 `ITableAnnotation` 的成员。

**修法**：
```python
ret = P(view, "InsertBomTable2", False, 0.20, 0.06, 1, 1, "默认", TPL)
row = swe.table_rows(ret)                    # 内部 QI ITableAnnotation
rows, titles = swe.bom_table(drawing_doc)    # 走图纸 GetTableAnnotations()，最稳
```

**顺带的两个坑**：
- `IView.GetBomTable()` 返回 `None`；`IView.IGetBomTable()` 抛 `(-2147352567, '发生意外。', ('无法读只写属性。'))` —— 它是**只写**属性，别指望读。
- `DisplayedText(row, col)` 与 `GetColumnTitle(col)` 返回的字符串带格式标签，例如 `'<FONT size=3.5>数量'`，用前要 `re.sub(r"<[^>]+>", "", s)`。

**实测（PL50 法兰总装，`probe-output\bom_read.SLDDRW` 93,909 B）**：`RowCount=4`、`ColumnCount=4`，内容
`项目号 | 零件号 | 说明 | 数量` → `1|PL50| |2`、`2|GASKET| |1`、`3|BOLT| |4`，与装配组成完全一致。

---

## 78. BOM 行查不到零件文件 / 改了材质装配体重没变

**现象一**：`IBomTableAnnotation.GetModelPathNames(row, item, part)` 返回空元组，BOM 行拿不到零件路径。

**根因与修法**：这条接口依赖 BOM 属性（零件号列的来源），标准模板下常为空。改用组件自身：
```python
comps = swe.bom_components(table, row)        # 内部走 IBomTableAnnotation.GetComponents
path  = swe.comp_path(comps[0])               # GetPathName -> GetPathName2 兜底
```

**现象二**：给零件新设材质后，装配体质量属性不变（本例差 0.461 kg / 8.39%）。

**根因**：装配体的质量属性是**缓存值**，零件材质改了不会自动失效。
**修法**：`swe.P(asm_doc, "EditRebuild3")` 再读。修复后：

| 行 | 零件号 | 数量 | 零件文件 | 材料 | 小计 |
|---|---|---|---|---|---|
| 1 | PL50 | 2 | PL50.SLDPRT | 普通碳钢 | 5.426933 kg |
| 2 | GASKET | 1 | GASKET.SLDPRT | 普通碳钢 | 0.127472 kg |
| 3 | BOLT | 4 | BOLT.SLDPRT | 普通碳钢 | 0.401480 kg |

BOM 合计 5.955886 kg = 装配体 5.955886 kg，差 **8.882e-16 kg**（机器精度）。

---

## 79. 剖视图里定位零件、加气球：ArrayData 布局与 AutoBalloon 的坑

**① `IView.ModelToViewTransform` 的 ArrayData 不是 4×4 矩阵**
它返回 **16 个 double**，按 `[xAxis(0-2)][yAxis(3-5)][zAxis(6-8)][trans(9-11)][scale(12)][0,0,0]` 排列；`trans` 是**视图中心在图纸上的位置**，`scale` 是视图比例（1:1 → 1.0，2:1 → 2.0）。别按行主序 4×4 去乘，会全错。
换算公式（实测 100×60×20 板、2:1、视图在 (0.10,0.15)）：

```
p_sheet = trans + scale * ( R · (p_model − c_model) )      # R 由 xAxis/yAxis/zAxis 组成
```

`c_model` 是**视图在模型空间的中心**（该板 = (0.05,0.03,0.01)）。验证：模型 (0,0,0) → 图纸 (0.000,0.090)、(0.10,0.06,0.02) → (0.200,0.210)，与 `GetOutline()` 外扩 4.2 mm 的边界完全吻合。
装配体要自己算 `c_model`：用各组件 `GetXform` 平移 + 零件包围盒求并。

**② `IView.GetVisibleComponents()` 在剖视图上可用**
`剖面视图 A-A` 上数到 **5 个**可见组件（`PL50-1/PL50-2/BOLT-1/BOLT-2/BOLT-4`），返回 tuple，元素要 QI `IComponent2` 才有 `Name2`。

**③ 自动气球：`AutoBalloon2` 可用，`AutoBalloon5` 返回 None**
`IDrawingDoc.AutoBalloon2(Layout, IgnoreMultiple)` → 返回球标 tuple（实测 3 个），图纸注记 57 个、`GetNoteCount()`=56，存盘 151,891 B。`AutoBalloon5(IAutoBalloonOptions)` 即使设好 Layout/IgnoreMultiple 也返回 `None`（本机）。
前置：先 `SelectByID2(视图名, "DRAWINGVIEW", 0,0,0, False, 0, None, 0)` 选中视图，且图纸上已插 BOM 表。

**④ 想改引线/字号**
`IAnnotation.SetArrowHeadSizeAtIndex(Index, UseDoc, Length, Width, Height)`、`SetArrowHeadStyleAtIndex(Index, Style)`（`swArrowStyle_e`）、`LeaderThickness`/`BentLeaderLength`、`GetLeaderPointsAtIndex(Index)` 读回引线折点、`GetTextFormat(Index)` → `ITextFormat`（字号/字体/加粗）。

**⑤ 组件自身的 GetXform 与视图变换是两种格式**
`IComponent2.GetXform()` 返回 **12 个 double 的普通数组**（不是 IMathTransform、没有 `.ArrayData`）：`[R00,R01,R02, R10,R11,R12, R20,R21,R22, tx,ty,tz]`，平移在**索引 9/10/11**。实测 `PL50-2`=(0,0,0.022)、`BOLT-1`=(0.0625,0,-0.011)。
`IComponent2.GetBox` 需要**两个**参数（`GetBox(BOptions, IncludeSketches)`）。

**⑥ 剖视图里 visible 的组件 ≠ 原点落在视图内**
PL50 总装上 `GetVisibleComponents()` 给 5 个（两法兰 + 3 螺栓），但把组件原点投到图纸后，三个螺栓全在 `GetOutline()` 外面（x=0.0140 < 0.0318；y=0.0250/0.2750 出界）——因为螺栓轴线在 y=±62.5 mm，剖切面只切中间 y=0 的截面，可见的是被"切开/看见"的几何，不是原点。
**所以：`GetVisibleComponents()` 只能用来枚举"谁被这一刀涉及"；要在图上给某个零件挂引线，锚点必须取该零件在当前视图里的可见几何（可见边/面），或者用零件包围盒中心再验证是否落在 outline 内。**

**⑦ 两个必须 QI 的返回对象**
`OpenDoc6` 回来的装配 `_Dispatch` 上没有 `GetComponents`（`AttributeError`）→ 先 `QueryInterface(SW.IAssemblyDoc)`；零件 `GetPartBox` 同理要用 `swe.bbox(pd)`（内部 QI `IPartDoc`）。


## 80. `IView.GetVisibleEntities2` 必须给组件，元素是 `POINTER(IDispatch)`

现象：`view.GetVisibleEntities2(None, 1)` → `COMError (-2147352571, '类型不匹配。')`，报 `TypeError: Parameter 2`；就算传了组件，元素也没有 `GetStartVertex`。

根因/修法：

```python
root = view.RootDrawingComponent          # 唯一合法的组件参数（零件视图也是它）
ents = view.GetVisibleEntities2(root, 1)  # 1=Edge 2=Vertex 3=Face 4=Silhouette
for e in ents:
    edge = e.QueryInterface(SW.IEdge)     # 必须先 QI
    v = edge.GetStartVertex()
```

`swViewEntityType_e`：Edge 1 / Vertex 2 / Face 3 / SilhouetteEdge 4。
实测 Ø165 法兰剖视图：Edge=2 个、Vertex=0、Face=1 —— 数量太少，**不足以反推锚点**，所以"从可见边自动取锚点"这条路当前不通。

## 81. 自动气球：装配能出、零件剖视不出

- 装配（已插 BOM + 选中视图）：`AutoBalloon2(1, False)` → 返回 3 个对象、注记数 56→59、文件 95,790 → 151,891 B。
- 零件剖视图：同法返回**一个** `POINTER(IDispatch)`，但 `sheet.GetAnnotationCount()` 57→57 不变 → 实际没加气球。
- `AutoBalloon5(IAutoBalloonOptions)` 即使 `CreateAutoBalloonOptions()` 里设好 `Layout/IgnoreMultiple` 仍返回 `None`。
- `AutoBalloon3/4` 参数更多、未验证。做法：装配用 AutoBalloon2；零件用 `NewNote + SetLeaderAttachmentPointAtIndex`（落点可控）。

## 82. 剖视图的 `ModelToViewTransform` 不能用于坐标换算

普通视图：`ArrayData` 16 个 double = `[xAxis 0-2][yAxis 3-5][zAxis 6-8][trans 9-11][scale 12][0,0,0]`，`p_sheet = trans + scale·R·(p_model − c_model)` 可精确复现 outline（误差 < 0.1 mm）。

剖视图（`Type==2`）：该矩阵基向量退化——两个不同模型点（x=0.05 与 x=0.0825）被算到**同一图纸点** (0.046, 0.150)。→ 剖视图坐标只能取「已知图纸坐标 + `SetLeaderAttachmentPointAtIndex` + 回读末点校验」。


## 83. 图纸坐标可以为负：图序/视图必须夹进 `0 ~ GetSize()`

现象：A4 横向图纸上，`剖面视图 A-A` 的 `GetOutline()` 是 `(0.0658, -0.0192, 0.1142, 0.3092)`，y 有负值；照 outline 下方 13 mm 放"图1"，落点 `y = -0.0432`（图纸外），打印会被裁掉。

修法：

```python
sheet = d.GetCurrentSheet().QueryInterface(SW.ISheet)
w, h, paper = sheet.GetSize()          # A4 横向 -> [0.297, 0.21, 6]
cap_y = max(outline[1] - 0.013, 0.012) # 夹进纸内
```

图纸原点在**左下角**，可见区就是 `0..w` / `0..h`；出图前统一夹一次，视图本身也要按 outline 重新摆位（`IView.Position` / `SetPosition`）。

## 84. 工程图导出：DXF 可信、PDF 返回 `[1,0,False]`

同一张 A4 图纸（图框 + 前视 + 剖视 + "图1"）：

| 目标 | 调用 | 返回 | 文件 |
|---|---|---|---|
| `.DXF` | `md.SaveAs4(p, 0, 1)` | `[0, 0, True]` | 55,324 B ✅ |
| `.PDF` | 同上 | `[1, 0, False]` | 44,009 B ⚠️ |
| `.PDF` | `sw.GetExportFileData(1=swExportPdfData)` + `Extension.SaveAs(p,0,1,ed)` | `[1, 0, False]` | 44,009 B ⚠️ |

`swExportDataFileType_e` 只有一项 `swExportPdfData = 1`；`swSaveAsVersion_e` = Current 0 / SW98plus 1 / ProE 2 / StandardDrawing 3 / DetachedDrawing 4。
PDF 这条**文件确实写出来了但 error=1**，不能当成功判据；要么改用 DXF（已验证），要么在 GUI 里"另存为 PDF"核对页数/内容后再交付。

补充：图框相关成员可用 —— `ISheet.GetTemplateName()` 返回 `...\lang\chinese-simplified\sheetformat\a4 - landscape.slddrt`，另有 `SetSheetFormatName` / `SetTemplateName` / `SaveFormat` / `ReloadTemplate` / `SheetFormatVisible`，可做"批量换图框"。

## R35 线稿附图三件套（图序 + 剖切符号核验 + 导出）

```python
# 1) 图序：夹进纸内、居中于视图正下方
sheet = d.GetCurrentSheet().QueryInterface(SW.ISheet)
w, h, _ = sheet.GetSize()
o = [float(x) for x in sec.GetOutline()]
d.NewNote("图1", 0.0050)                      # 返回 int
nt = list(d.GetFirstView().GetNotes())[-1].QueryInterface(SW.INote)
ann = nt.GetAnnotation()
ann.SetPosition((o[0]+o[2])/2, max(o[1]-0.013, 0.012), 0.0)

# 2) 剖切符号由 SolidWorks 自动生成，父视图可回读（含箭头坐标）
info = parent_view.GetSectionLineInfo2()      # 33 个 double：标志位 + 箭头/交点 3D 点

# 3) 导出：DXF 可信；PDF 仅落盘、error=1 需人工核
md.SaveAs4(os.path.join(out, "fig1.dxf"), 0, 1)
```

判据：图序回读坐标 = 设定值、在 `0..h` 内；`GetSectionLineInfo2()` 非空；DXF 返回 `[0,0,True]`。


## 85. 移动工程图视图：`Position` 必须给 `array('d',[x,y])`；比例要先按纸选

现象：`v.Position = (cx, cy)`（tuple）赋值**不报错但视图纹丝不动**；换成 `from array import array; v.Position = array('d',[cx,cy])` 才真的移动。

实测（Ø165 法兰、A4 横向 0.297×0.21）：
- 前视 `工程图视图1` outline `y[0.0008,0.3392]` → `Position=array('d',[0.09,0.1812])` → `y[0.0120,0.3504]`（dy=+0.0112 精确）。
- `dir(view)` 里**没有** `GetPosition/SetPosition` 这类条目（动态派发看不到），只能靠赋值。

**更根本的一条**：`swe.section_view()` 写死 `scale=2.0`，Ø165 件在 2:1 下视图高 338 mm > 纸高 210 mm，怎么移都放不下（y 必出界）。
出图前必须先定比例：

```python
w, h, _ = sheet.GetSize()                 # 0.297, 0.21
m = 0.012                                  # 四周留白
scale = min((w - 2*m) / model_w, (h - 2*m) / model_h)   # 例：Ø165 -> 0.48 取 0.4
v.ScaleDecimal = scale
```

比例定了再摆位，最后放图序，三者顺序不能反。

## 86. 图纸幅面：SetupSheet5 的 TemplateIn 必须传 13（swDwgTemplateNone），传 0 会得到 Letter

**现象**：`SetupSheet5('图1', 6, 0, 1, 1, True, '', 0.297, 0.210, '', False)` 返回 True，`GetSize()` 却是 `[0.2794, 0.2159, 0]`（11×8.5 in），PDF 的 `/MediaBox` 是 `792×612 pt`。

**根因**：`PaperSize` 与 `TemplateIn` 是两个枚举。`swDwgTemplates_e` 里 `0 = swDwgTemplateAsize`（A 幅面模板），`0.297/0.210` 只在 `TemplateIn = swDwgTemplateNone(13)` 或 `swDwgPapersUserDefined(12)` 时才有意义；传 0 等于"用 A 幅面的默认模板"，实际落到 `a - landscape.slddrt` = Letter。

**修法**：`SetupSheet5(Name, 6, 13, 1, 1, True, '', 0.297, 0.210, '', False)` → `GetSize()` = `[0.297, 0.21, 6]`，`GetTemplateName()` = `''`（无模板 ⇒ 无图框、无标题栏），PDF `/MediaBox [0 0 841.89 595.276]` = A4 横向。

## 87. 取 ISheet 只能走 GetCurrentSheet()，GetFirstView() 的对象 QI 不过

**现象**：`sheet = dd.GetFirstView(); sheet.QueryInterface(SW.ISheet)` → `(-2147467262, '不支持此接口')`；同对象上的 `GetSize/SetSize/SheetFormatVisible` 全部 `未知名称`。

**修法**：`sheet = dd.GetCurrentSheet().QueryInterface(SW.ISheet)`（返回 `_Dispatch`，QI 后正常）。拿到后可 `SetSize(6, 0.297, 0.210)`、`SheetFormatVisible = False`、`SetProperties(PaperSz, Templ, Scale1, Scale2, FirstAngle, Width, Height)`。

## 88. SaveAs4 目标已存在 → 返回 [1,0,False]（文件其实写了）

**现象**：同路径第二次 `SaveAs4` 返回 `[1, 0, False]`，但文件大小正常；先 `os.remove()` 再存 → `[0, 0, True]`。

**另一坑**：正在 SolidWorks 里打开着的 `.SLDDRW` 删不掉（`PermissionError: [WinError 32]`）——批量出图时改用新文件名，或先关文档。

## 89. 多图纸导出 PDF：一次只导当前页

**现象**：两张图纸的 `.SLDDRW` 导出 PDF 只得到 1 页。

**试过无效**：`ed = sw.GetExportFileData(1); ed.SetSheets(1, None)` → **False**；直接把未 QI 的 `ed` 传给 `md.Extension.SaveAs(p, 0, 1, ed)` → `argument 4: COMError(-2147352570, '未知名称。')`。

**可用做法**：逐页 `dd.ActivateSheet(name)` 后 `md.SaveAs4(输出/name.pdf, 0, 0)`，每页一个 PDF（实测两张 MD5 不同、各 12.7 KB、MediaBox 均为 A4）。

## 90. NewSheet 是 5 参

`IDrawingDoc.NewSheet(Name, PaperSize, TemplateIn, Scale1, Scale2)`；按 NewSheet3 的 11 参写会报 `call takes exactly 6 arguments (11 given)`（含 this）。实测 `dd.NewSheet('图2', 6, 13, 1, 1)` → 0，`GetCurrentSheet().GetName()` = `图2`。

## 91. InsertNote 才是拿 INote 的正路

**现象**：`d.NewNote(text, 0.005)` 返回的是 **int**（成功码），随后 `sheet.GetNotes()[-1]` 拿到的是**旧**对象（图纸上注释数一直是 87，文本是空串），`SetPosition` 却"生效"——因为改的是别的注释。

**修法**：`note = swe.P(md2, 'InsertNote', text)`（`IModelDoc2.InsertNote(Text)` 直接返回 `INote`）→ `ann = note.GetAnnotation()` → `ann.SetPosition(x, y, 0)`（3 个 double，传 `array('d')` 报 `类型不匹配: Parameter 1`）。引线：`SetLeader2(True,0,True,True,False,False)` + `SetLeaderAttachmentPointAtIndex(0, x, y, 0)` + `SetArrowHeadStyleAtIndex(0,3)` + `SetArrowHeadSizeAtIndex(0,True,0.0025,0.0012,0.0012)`；`GetLeaderPointsAtIndex(0)` 末三点为「锚点→拐点→箭头尖」。

## 92. 剖视图里的编号锚点不能用组件原点

**现象**：`IComponent2.GetXform()` 的平移（索引 9/10/11）投影到图纸后，3 个 M16 螺栓全落在 `GetOutline()` 之外（螺栓轴线在 y=±62.5 mm，剖切面只切 y=0）。`GetVisibleComponents()` 只回答"这一刀看得见谁"，不等于"原点在框内"。

**可用做法**：按零件 z 区间做 `y = oy0 + (z - zmin)/(zmax - zmin) * (oy1 - oy0)` 线性映射到视图轮廓内，x 取 `ox0+0.004`（左侧件）或 `ox1-0.004`（右侧件）；实测 4 个编号箭头尖分别落在 `(0.12087,0.14208) / (0.12087,0.115) / (0.12087,0.08792) / (0.17913,0.115)`，全部在轮廓内。

## 93. 剖面线密度只能整视图调

`IView.ScaleHatchPattern = 0.4` 生效（0.4 = 更疏）；`IView.GetFaceHatchCount()` 恒 **0**、`GetFaceHatches()` 返回 None —— 剖视剖面线不是"面剖面线"对象，逐面 `IFaceHatch.Scale` 的办法对剖视图无效。

## 94. 删除父视图会连带删掉派生视图（剖视/局部放大）

**现象**：建好 `剖面视图 A-A` 后，为"只留剖视"而 `SelectByID2(前视名,'DRAWINGVIEW',...)` + `EditDelete()`，导出 PDF 里只剩图框、剖视消失；同一会话里对已删视图的代理对象 `GetOutline()` 仍能返回旧数据（看起来还在）。

**根因**：剖视图/局部放大是**派生视图**，父视图删除时 SolidWorks 把子树一起删掉；COM 代理对象在删除后仍持有缓存。

**修法**：不要删父视图，改成隐藏：`fv.SetVisible(False, False)`。判据三条：`fv.GetVisible() == False`、`sec.GetVisible() == True`、激活该图纸后 `GetFirstView()->GetNextView()` 能枚举到 2 个子视图（`工程图视图N` type=7 + `剖面视图 A-A` type=2）。

## 95. `SetVisible` 的第二个参数会连坐派生视图

`IView.SetVisible(Visible As Boolean, DependentsToo As Boolean)`：`DependentsToo=True` 会把该视图的派生视图一起隐藏（剖视也随之消失）。只想藏父视图时必须传 `False`。

## 96. `IDrawingDoc.GetViews()` 只给图纸视图，且元素是 1 元 tuple

`dd.GetViews()` 返回的每一项是 **1 元 tuple**，`e[0]` 才是 `IDispatch`（`e.QueryInterface` 会报 `'tuple' object has no attribute 'QueryInterface'`）；而且它**只包含各图纸的 sheet view**（`IView.Type == 1`，名字就是 `图1`/`图2`），模型视图/剖视图**不在其中**。

要枚举某张图上的模型视图：先 `dd.ActivateSheet('图1')`，用 `GetCurrentSheet().GetName()` 确认已切换，再 `GetFirstView()` → 循环 `P(v,'GetNextView')`。切换未生效（没确认名字）时会读到上一张图纸的子视图，是"视图丢失"假象的常见来源。

## 97. 多图纸逐页 PDF 不可靠 —— 线稿附图请"一图一文件"

`IExportPdfData.SetSheets(1, None)`（AllSheets）与 `SetSheets(3, ['图1'])`（指定图纸）**都返回 False**，`swExportDataSheetsToExport_e` 的枚举值不起作用；`SaveAs4(pdf)` 每次导出的都是**当前图纸**，两张图导出的 PDF 字节数几乎相同（12,772 / 12,770 B；40,228 / 40,229 B），无法据此区分内容。

**做法**：线稿附图按"一张图一个 SLDDRW"生成，各自 `SaveAs4` 出 PDF，需要合并时再拼 PDF。判据：两个 PDF 的 MD5 必须不同、页数各为 1、MediaBox 为 A4（841.89×595.276）。

## 98. `IDrawingDoc` 上没有 `Extension` 和 `CloseDoc`

`dd.Extension` → `AttributeError: Extension`；`dd.CloseDoc()` / `md2.CloseDoc()` → `AttributeError: CloseDoc`。
正确写法：`md2 = dd.QueryInterface(SW.IModelDoc2)`，`ext = md2.Extension` 调 `ext.SaveAs(...)`；关文档用 `sw.CloseDoc(str(P(md2,'GetTitle')))`。
