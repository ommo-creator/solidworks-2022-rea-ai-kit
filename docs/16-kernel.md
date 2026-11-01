# 几何内核与 `IModeler`（P3-2 实测）

> 环境：SolidWorks 2022 SP5 / 30.5.0.0049。状态：✅ 实测出数 / 📄 元数据已核 / ⚠️ 未通。

## 0 一句话结论

SolidWorks 的几何内核是 **Parasolid**（`pskernel.dll`，版本 **33.01.260**），另带 **ACIS**（`spaacis.dll`，**20171.0.2**）用于兼容旧格式/导入；
内核级 API 面是 `ISldWorks.GetModeler()` → `IModeler`（**135 个成员**，必须 `QueryInterface(SW.IModeler)` 才能 `dir()` 出来），
但**直接造体（CreateBodyFromBox 系列）在 Python/VBS 侧被 SAFEARRAY 封送卡住**，日常建模应继续用特征 API。

## 1 内核身份（✅ 文件元数据）

| 文件 | 大小 | FileVersion | 说明 |
|---|---|---|---|
| `pskernel.dll` | 61,672,000 B | **33.01.260** | Parasolid V33.1 内核 |
| `spaacis.dll` | 58,350,408 B | **20171.0.2.17062** | ACIS 2017.1（历史/导入兼容） |
| `sldmodu.dll` | 49,587,864 B | 30.5.0.0049 | 建模模块（特征类 `mo*_c` 都在这里） |

旁证：`sldmodu.dll` 的导入表里能看到 Parasolid 符号（`PK_*`），`FeatureExtrusion2` 等特征最终都落到 `pskernel` 的布尔/扫掠例程。

## 2 `IModeler` 能干什么（📄 反射 + 实测）

- 取法：`mdl = sw.GetModeler()`（返回 `_Dispatch`）→ `mdl.QueryInterface(SW.IModeler)` → **135 个成员**可枚举。
- 构造类：`CreateBodyFromBox` / `CreateBodyFromBox3` / `ICreateBodyFromBox` / `ICreateBodyFromBox2` /
  `CreateBodyFromCyl` / `ICreateBodyFromCyl2` / `CreateBodyFromCone` / `ICreateBodyFromCone2` /
  `CreateCylindricalSurface` / `CreateCylindricalSurface2` …
- 曲面类：`CreatePlanarSurface`、`ICreateBsplineSurface`、`CreateSheetFromSurface` 等。
- 曲线类：`ICreateLine`、`CreateArc`、`ICreateBsplineCurve`、`CreateTrimmedCurve` 等。
- 官方签名（CHM）：`Body2 CreateBodyFromBox3(ByVal BoxDimArray As System.Object)`；
  `Body ICreateBodyFromBox2(ByRef BoxDimArray As System.Double)`（数组）。
- 把造好的体塞进零件：`IPartDoc.CreateFeatureFromBody3(Body, MakeRefSurface As Boolean, Options As Integer)`（3 参）。

## 3 造体这一步为什么没通（⚠️ 实测记录）

| 通道 | 调用 | 结果 |
|---|---|---|
| comtypes | `CreateBodyFromBox3([0,0,0,0.1,0.2,0.3])` | `COMError -2147352563 '内存已锁定。'`（列表/元组/`array('d')` 全一样） |
| comtypes | `ICreateBodyFromBox2(c_double*6)` | `ArgumentError: expected LP_c_double instance instead of list` |
| comtypes | `ICreateBodyFromBox2(数组)` | 返回 `None` |
| VBScript | `mdl.ICreateBodyFromBox2(a)`（VBS 原生 SAFEARRAY） | `err 13 类型不匹配`，`body=Empty` |

结论：`ByRef BoxDimArray As System.Double` 这个"数组 byref"在 pywin32/comtypes 与 VBS 两条晚期绑定通道上都封送不进去；
要用内核直造，应从 **C# / VBA**（有原生 SAFEARRAY 与类型库早绑定）侧做，或退回特征 API（拉伸/旋转照样走内核）。

## 4 判据

- 内核是否真在干活：任何特征（拉伸/旋转/抽壳）成功且体积与解析公式吻合到 1e-16 级，就已经证明 Parasolid 在算，不必非要直调 `IModeler`。
- 曲面体判据走 `GetBodies2(1, False)` 计数（见 `docs/05-sections.md` §3），实体走 `GetBodies2(0, False)`。
