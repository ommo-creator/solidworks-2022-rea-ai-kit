# 01 · 通道矩阵与六条铁律

> 这一篇解决的是"为什么我的脚本连上了却什么都做不了"。
> 先选对通道，再谈方法签名；选错通道，后面所有努力都是浪费。

---

## 1. 通道矩阵（第一个决策）

| 通道 | Application 级 | 文档对象（`ModelDoc2` / `FeatureManager` / `SketchManager`） | 判定 |
|---|---|---|---|
| **Python + `comtypes`**（早绑定或后期绑定） | ✅ | ✅ **全通** | **首选**，本仓库以它为准 |
| VBA 宏（SolidWorks 内 `RunMacro`） | ✅ | ✅ 全通 | 可用；参数个数必须精确 |
| VBScript（`cscript`，纯 IDispatch） | ✅ | ✅ 全通 | 可用；文件须 **ANSI 无 BOM** |
| PowerShell + Interop RCW<br>`New-Object SolidWorks.Interop.sldworks.SldWorksClass` | ✅ | ❌ 一律 `0x8002000B DISP_E_BADINDEX` | **不可用于文档对象** |
| PowerShell 晚绑定<br>`New-Object -ComObject SldWorks.Application` | ❌ `0x8002802B TYPE_E_ELEMENTNOTFOUND` | ❌ | 直接放弃 |

### 为什么会这样

SolidWorks 对**强类型 vtable 调用**返回 `DISP_E_BADINDEX`，只接受 **IDispatch 晚绑定**。
所以"PowerShell 能连上、`RevisionNumber()` 能读、一到 `doc.GetTitle()` 就炸"
**不是配置问题，是通道不对**——别再花时间修 COM 注册。

### 已验证的无效补救手段（不要重复试）

| 尝试 | 结果 |
|---|---|
| 注册 `sldworks.tlb`（`LoadTypeLibEx(..., REGKIND_REGISTER)`，981 个类型） | **不能**修复；PowerShell 仍然 `DISP_E_BADINDEX` |
| 修 ProxyStub / 补代理层 | 无效 |
| 换成 `cscript` + `CreateObject` | **有效**（因为纯 IDispatch），但调试体验差 |
| 改成 Python + comtypes | **有效**，推荐 |

### Python 侧的两个前置条件

1. **`connect()` 必须是 `CreateObject` 语义，不要 `GetActiveObject` 语义。**
   后者在 SolidWorks 上常报 `0x800401E3 操作不可用`。
   本仓库 `scripts/swe.py` 的 `connect()` 已按前者实现。
2. **comtypes 老坑**：类型库可能缺 `VT_DISPATCH(9)` 映射，连不上时先注册补丁；
   首次 `GetModule` 会生成 `comtypes.gen.SldWorks`，这一步需要管理员权限写 site-packages。

---

## 2. 六条铁律

### 铁律 1 · 单位一律米 / 弧度

API 的**所有**长度是米、**所有**角度是弧度。

```python
0.1          # = 100 mm
6.283185307179586   # = 360°
```

**唯一例外：`IPartDoc.GetPartBox()` 返回毫米。**

写脚本时把单位换算集中在一个函数里，不要散落在各处——这是体积对账出错的第一大原因。

### 铁律 2 · 文档对象方法必须晚绑定

见上一节。PowerShell 脚本不要试图自动化建模；它能做的只有读 `Application` 级信息。

### 铁律 3 · 新建零件用 `NewPart()`，不要 `NewDocument(模板, ...)`

模板路径或年份稍有差异，就会**建出文档之后**再抛错，留下一个"僵尸零件1"：

| 通道 | 典型报错 |
|---|---|
| VBS | `61836 无法只写属性` |
| PowerShell | `DISP_E_BADINDEX` |

```python
# ✅
md = sw.NewPart()
# ❌ 模板不可靠
md = sw.NewDocument(template_path, 0, 0, 0)
```

### 铁律 4 · 切除的草图必须画在被切的面上

先用 `SelectByRay` 选中目标面，再在该面上建草图。

如果画在 `前视基准面` 上：`FeatureCut4` 返回 `None`、**不去料**、特征数只 +1（一张空草图）。
这就是"脚本没报错但模型没变"的典型形态。

```python
# TypeWanted: 1 = 棱边, 2 = 面; 射线半径 0.0004 才打得到棱边
md.Extension.SelectByRay(x, y, z, dx, dy, dz, 0.0004, 2, False, 0, 0)
```

### 铁律 5 · 中文名不可硬编码

草图是 `草图1` 而不是 `Sketch1`；`RefPlane` 1/2/3 分别是**前视/上视/右视**。

```python
# ✅ 稳的写法：遍历特征树按类型名找
for f in swe.features(md):
    if f.GetTypeName2() == "ProfileFeature":
        f.Select2(False, 0)
        break
```

基准面名字可以用 `ChrW()` 拼（VBA）或按 `GetTypeName2() == "RefPlane"` + 序号判断，
**不要**写死字符串。中英文界面字符串差异见 [`18-ui-strings.md`](18-ui-strings.md)。

### 铁律 6 · 别信"没报错"

每次建模后**读体积/质量并与理论值比对**。本版本上尤其要注意：

- `SelectionManager.GetSelectedObjectType3` **恒返回 `0`**（棱边/面/草图线段都一样），不能用于判类型；
  只认 `GetSelectedObjectCount2(-1) >= 1`。
- `IFeatureManager.FeatureCut4` 返回 `None` 但特征数 +1，是"空草图"。
- `SaveAs` 目标已存在时返回 `False`，**但文件其实已经写入了**。

体积判据表见 [`04-recipes.md`](04-recipes.md) 与 README 的"已验证的关键数字"。

---

## 3. 选择正确的层：`IAssemblyDoc` / `IModelDoc2` / `IFeature`

装配体对象必须**分层 QueryInterface**，否则会拿到 `AttributeError: AddComponent5` 之类的假象
（对象是对的，但接口指针层次不对）：

```python
import comtypes.gen.SldWorks as SW

asm = sw.ActiveDoc                          # 无类型中性指针
asm = asm.QueryInterface(SW.IAssemblyDoc)   # AddComponent5 / AddMate5
md  = asm.QueryInterface(SW.IModelDoc2)     # ClearSelection2 / Extension / EditRebuild3
feat = md.FirstFeature()                    # IFeature（子树遍历）
```

| 需要的能力 | 应该 QI 到的接口 |
|---|---|
| `AddComponent5` / `AddMate5` / `GetComponents` | `IAssemblyDoc` |
| `ClearSelection2` / `Extension` / `EditRebuild3` / `SaveAs` / `FirstFeature` | `IModelDoc2` |
| 子树遍历 / `GetTypeName2` / `Select2` | `IFeature` |
| 特征数据（阵列/孔/圆角…） | 对应 `I*FeatureData`，**必须先 QI** |

> 同类陷阱：`FeatureManager.CreateDefinition` 返回**无类型 `_Dispatch`**，
> 不先 `QueryInterface(ILinearPatternFeatureData)` 就 `CreateFeature`，会得到
> `COMError: (-2147352570, '未知名称。')`（`0x80020006 DISP_E_UNKNOWNNAME`）。
> `GetOpenDocSpec()` 也一样，必须先 QI 到 `IDocumentSpecification` 才能传给 `OpenDoc7`。

---

## 4. comtypes 的两个行为要记住

### 4.1 无参方法被当成属性

comtypes 有时把无参方法当属性 get 返回 `_Dispatch`，此时直接调用会报
`'builtin_function_or_method' object has no attribute 'Pointer'`。
统一用本仓库的包装：

```python
def P(obj, name, *args):
    """既支持属性也支持方法调用，绕开 comtypes 的这些坑"""
    return swe.P(obj, name, *args)

P(md, "GetTitle")
P(md, "ShowNamedView2", "", 7)      # 7 = 等轴测
```

### 4.2 `[out]` 参数会被摘掉

`AddMate5` 末尾的 `ErrorStatus`、`GetMassProperties2` 的返回数组，在 comtypes 里
**位置计数要重算**——官方签名有 N 个参数，实际调用可能只有 N-1 个。

```python
# 官方 14 参，实际 13 参（末位 [out] 被摘）
P(md, "AddMate5", 0, 1, False, 0, 0, 0, False, False, 0, 0, 0, 0, 0)
# GetMassProperties2 实际 2 参
P(ext, "GetMassProperties2", 1, False)   # -> (status, [Xc,Yc,Zc,Vol,Area,Mass,...])
```

> 少数方法 comtypes **不登记固定 argtypes**（`CloseDoc` / `InsertSketch` /
> `ClearSelection2` / `ShowNamedView2` / `ViewZoomtofit2`），此时 `len(argtypes) == 0`
> 表示走 IDispatch 动态派发，**仍按官方声明传参**，不要以为参数被吃掉了。

---

## 5. 相关文档

- 具体签名与参数个数 → [`02-signatures.md`](02-signatures.md)
- 踩过的坑（近 100 条）→ [`03-pitfalls.md`](03-pitfalls.md)
- 对象模型全貌 → [`10-data-model.md`](10-data-model.md)
- 用命令号驱动 UI 级操作 → [`12-commands.md`](12-commands.md)
