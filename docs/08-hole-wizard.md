# 孔向导（Hole Wizard）参数语义：`Value1..Value12` 到底是什么

本文是 2026-10-29 在 SolidWorks 2022 SP5 / COM 上实测的结论，不是文档转述。
判据全部是"造完孔用体积核对"，理论值按 `πr²h` 与锥台公式手算，偏差量级写在各节。

---

## 0. 一句话结论

`HoleWizard5` 的 `Value1..Value12` **不是**"12 个尺寸"，而是旧版留下的**用户覆盖槽**；
用标准表（GB/ISO/DIN…）造孔时它们应当留 `0.0`，真正决定几何的是
**`IWizardHoleFeatureData2` 上一批有名字的属性**：

| 想要什么 | 属性名 | 单位 |
|---|---|---|
| 通孔直径 / 深度 | `ThruHoleDiameter` / `ThruHoleDepth` | 米 |
| 沉台直径 / 深度 | `CounterBoreDiameter` / `CounterBoreDepth` | 米 |
| 锥沉孔直径 / 角度 | `CounterSinkDiameter` / `CounterSinkAngle` | 米 / **度** |
| 螺纹公称直径 / 螺纹深度 | `ThreadDiameter` / `ThreadDepth` | 米 |
| 底孔直径 / 底孔深度 | `TapDrillDiameter` / `TapDrillDepth` | 米 |
| 终止条件 | `EndCondition` | `swEndConditions_e`（0 盲孔 / 1 完全贯穿） |
| 标准 / 紧固件 / 规格 | `Standard` / `FastenerType2` / `FastenerSize` | 字符串 / int / 字符串 |

所以**不要猜 Value 槽**，改几何请走下面 §2 的三条路之一。

---

## 1. 标准与紧固件索引：必须运行时查（且要先热身）

```python
hs = sw.GetHoleStandardsData(genericHoleType).QueryInterface(SW.IHoleStandardsData)
hs.GetHoleStandards()                      # ★ 必须先调一次，否则下面返回 (None,None,False)
idx, names, ok = hs.GetFastenerTypes('GB') # ★ 名字来自 GetHoleStandards 的返回值，别硬编码
```

- `GetHoleStandardsData(HoleTypeID)`：`HoleTypeID` 用 `swWzdGeneralHoleTypes_e`
  （`CounterBore 0` / `CounterSink 1` / `Hole 2` / `PipeTap 3` / `Tap 4` / `Legacy 5` …）；
  `Legacy(5)` 返回 **None**。
- **索引顺序 ≠ 枚举顺序**，必须按名字取。`GetHoleStandards()` 在本机返回
  `((0,1,16,2,4,13,15,8,9,14,3,5,10,11,12), ('ANSI Inch','ANSI Metric','AS','BSI','DIN','GB','IS','ISO','JIS','KS','DME','HASCO Metric','PCS','Progressive','Superior'), True)`。
- 不同孔型的标准清单长度不同（`Hole` 有 17 项，含 `PEM® Inch/Metric`）。
- 各孔型的 GB 紧固件实测：

| 孔型 | GB 紧固件索引 | 名称 |
|---|---|---|
| `Hole(2)` | 708 / 357 / 356 / 355 | 暗销孔 / 螺纹钻孔 / **螺钉间隙** / 钻孔大小 |
| `CounterBore(0)` | 376 379 377 378 361 364 375 374 | 六角头螺栓 GB/T5782 / 5780 / 5781 / 5783、内六角 GB/T70.1 等 |
| `CounterSink(1)` | 363 / 362 …（共 11 个） | 内六角花形半沉头 GB/T2674 / 沉头 GB/T2673、木螺钉、自攻螺钉 |
| `Tap(4)` | 358 / 360 / 359 | 底部螺纹孔 / 直管螺纹孔 / **螺纹孔** |

- `GetFastenerTableTypes(标准, 紧固件ID)` / `GetFastenerTable(...)` 只对部分紧固件有表；
  「钻孔大小(355)」这类返回 `(None, False)`，尺寸由 `SSize` 字符串决定。

---

## 2. 三条可用的造孔路线

### 路线 B（推荐）：`CreateDefinition → InitializeHole → 命名属性 → CreateFeature`

```python
md.ClearSelection2(True)
swe.select_face(md, 0.05, 0.03, 0.020, 0, 0, 1, 0)   # 只选面，别预建草图
fd = md.FeatureManager.CreateDefinition(25)          # 25 = swFeatureNameID_e.swFmHoleWzd
fd = fd.QueryInterface(SW.IWizardHoleFeatureData2)   # ★ 不 QI 会 DISP_E_UNKNOWNNAME
fd.InitializeHole(0, 13, 376, 'M12', 1)              # 沉头孔 / GB / 六角头 / M12 / 贯穿
fd.CounterBoreDiameter = 0.024                       # 显式覆写
fd.CounterBoreDepth    = 0.008
feat = md.FeatureManager.CreateFeature(fd)           # 返回 IFeature 或 None
md.EditRebuild3()
```

实测（板 100×60×20，去料 = 体积差）：
`5.336781e-6`，理论 `π(0.0135/2)²·0.02 + π((0.024/2)²-(0.0135/2)²)·0.008 = 5.33672e-6`。

> 注意 `InitializeHole` 之后 `ThruHoleDiameter` 是 **0.0135**（Ø13.5），
> 而 `HoleWizard5` 同样参数得到的是 **0.013**（Ø13）。两条路的默认表行不完全一致。

### 路线 C：改已有孔特征

```python
feat = holeFeature.QueryInterface(SW.IFeature)
fd = feat.GetDefinition().QueryInterface(SW.IWizardHoleFeatureData2)
fd.AccessSelections(md, None)          # 不调用也能写属性，但几何不会变
fd.CounterBoreDiameter = 0.022
fd.CounterBoreDepth    = 0.006
feat.ModifyDefinition(fd, md, None)    # ★ 提交在 IFeature 上，IWizardHoleFeatureData2 没有 ModifyDefinition
md.EditRebuild3()
```

实测：去料 `4.139048e-6`，理论 `4.139048e-6`，偏差 `2.0e-20`。
`EndCondition=0 + ThruHoleDepth=0.012` 同样生效（去料 `3.0772e-6`，理论一致）。

### 路线 A：直接 `HoleWizard5`（快捷，参数要摆对）

```python
md.FeatureManager.HoleWizard5(
    genericHoleType, standardIndex, fastenerTypeIndex, 'M48', endType,
    0.0, 0.0, 0.0,                 # ★ Diameter / Depth / Length —— 是"覆盖值"，不是孔深
    *([0.0]*12),                   # ★ Value1..Value12 留 0
    '', False, False, True, False, True, False)
```

第 6/7/8 参是 `Diameter / Depth / Length` 覆盖值。把 0.025 传进 `Diameter` 就会得到
"洗一个大坑"的怪几何（本次实测等效 Ø50.8）。

---

## 3. 四类孔的实测表（GB / M12 / 贯穿 20 mm 板）

| 孔型 | 特征名 | 关键属性 | 去料 | 理论 | 偏差 |
|---|---|---|---|---|---|
| 光孔 `Hole(2)/356` | `M12 间隙孔1` | `ThruHoleDiameter=0.013` | `2.654646e-6` | `π·0.0065²·0.02` | 0 |
| 沉头孔 `CounterBore(0)/376` | `M12 六角头螺栓的柱形沉头孔1` | `Thru=0.013` `CB=0.026` `CBD=0.0005` | `2.853744e-6` | `2.654646e-6 + 1.990984e-7` | 0 |
| 锥沉孔 `CounterSink(1)/363` | `M12 内六角花形半沉头螺钉的锥形沉头孔1` | `Thru=0.0135` `CS=0.027?` `CSA=90` | `3.356291e-6` | 通孔 `2.862776e-6` + 浅锥台 | 见下 |
| 螺纹孔 `Tap(4)/359` | `M12 螺纹孔1` | `ThreadDiameter=0.012` `ThreadDepth=0` | 退化解见坑 §4.3 | — | — |

- **沉头孔默认 `CounterBoreDepth = 0.0005`（0.5 mm）**，所以"看不到沉台"是正常的，
  不是没生效——把它设成 0.006 立刻可见（路线 C 已验证）。
- 锥沉孔的 `CounterSinkAngle` 读回来是 **90**，按"度"理解（若当弧度会得到 5157°）；
  锥台体积与实测差 `4.8e-7`，说明默认锥角/直径还有表驱动的细节未完全对上，
  精度要求高的场合请以"生成后用体积复核 + 图纸标注"为准。

---

## 4. 坑

1. **`GetFastenerTypes` 必须先 `GetHoleStandards()` 热身**：否则一律 `(None, None, False)`，
   看起来像"该标准不支持这个孔型"。这个坑让我误判过"GB 没有锥沉孔"。
2. **索引不能硬编码**：`swWzdHoleStandards_e.GB = 13` 是对的，但 `GetHoleStandards()` 返回的
   **顺序**是 `(0,1,16,2,4,13,…)`，用位置推会全线错位。
3. **`Tap` 全零参数会退化成大坑**：`HoleWizard5(4,13,359,'M12',…)` 造出的特征去料
   `4.05366e-5`（等效 Ø50.8 贯穿）。要螺纹孔请用路线 B/C 显式写
   `ThreadDiameter/ThreadDepth/TapDrillDiameter`。
4. **`ThruHoleDepth` 有时读回 `AttributeError`**（`CreateDefinition` 路线刚 `InitializeHole`
   之后）。要么先 `CreateFeature` 再从特征 `GetDefinition` 读，要么直接用 `EndCondition` 判断。
5. **只选面，不要预建草图**：面 + 草图 = 选中数 2 时 `HoleWizard5` 返回 `None` 且不去料。
6. **`IWizardHoleFeatureData2` 没有 `ModifyDefinition`**：提交必须走 `IFeature.ModifyDefinition`；
   只写属性不提交，属性值会变、几何不变。
7. **木螺钉/自攻螺钉类紧固件没有 M12 规格**：`CreateFeature` 直接返回 `None`，不是接口坏了。

---

## 5. 相关脚本

| 脚本 | 作用 |
|---|---|
| `r16_whfd.py` | 造沉头孔 → 读 `IWizardHoleFeatureData2` 全部命名属性 |
| `r17_whfd2.py` | `AccessSelections + ModifyDefinition` 改沉台，体积对账 |
| `r18_holemap.py` | 四类孔首次对照（暴露 Diameter/Depth 参数位错） |
| `r20_holeq.py` | `GetHoleStandards` / `GetFastenerTypes` 调用形态试验 |
| `r21_holemap3.py` | 锥沉孔/螺纹孔全零参数行为 |
| `r22_hwdef.py` | 路线 B 首次跑通（`CreateDefinition(25)`） |
| `r24_csink2.py` | 遍历 15 套标准，确认 GB 其实有 11 个锥沉孔紧固件 |
| `r25_csink3.py` | GB 锥沉孔逐个紧固件试 M12，2 个可用、9 个因规格缺失失败 |
| `strings_hwiz.py` | 扫 `sldhwizuiu.dll`：关键词计数 + 样本（含修饰名 getter） |
| `strings_hwiz2.py` | 扫 `Value1..Value12` 字面量与 SQL 语句 |
| `strings_cisc.py` | 扫 `cisc.sldedb`（GB 标准表）里可见的列名 |

---

## 6. 二进制与 Toolbox 证据（REA）

### 6.1 实现层是"命名 getter + 显示尺寸对象"，不是 12 个 Value 槽

目标 `<SW_INSTALL>\sldhwizuiu.dll`（7,209,112 B）。C++ 修饰名直接暴露了孔特征的取值接口形态：

```
?GetCounterBoreDiameter@moHoleWzd_c@@QEAANPEAPEAVmoDisplayDim_c@@@Z
?GetCounterBoreDepth@moHoleWzd_c@@QEAANPEAPEAVmoDisplayDim_c@@@Z
?GetCounterBoreDepthWithHC@moHoleWzd_c@@QEAANPEAPEAVmoDisplayDim_c@@@Z
?GetCounterSinkDiameter@moHoleWzd_c@@QEAANPEAPEAVmoDisplayDim_c@@@Z
?GetNearCounterSinkDiameter@…   ?GetMidCounterSinkDiameter@…   ?GetFarCounterSinkDiameter@…
?GetCounterSinkAngle@…          ?GetNearCounterSinkAngle@…
```

三件事因此确定：

1. 每个尺寸都是**独立命名 getter**，第二参是 `moDisplayDim_c**`（输出显示尺寸对象）——与
   `IWizardHoleFeatureData2` 的 `ThruHoleDiameter / CounterBoreDiameter / CounterSinkDiameter ...`
   一一对应，这就是权威尺寸模型。
2. 存在 `Near / Mid / Far` 三级变体 → 一个孔可以有多级锥沉，平铺的 12 个槽根本表达不了。
3. 全文件**没有 `Value1`…`Value12` 任何字面量** → 这 12 个参数是旧 COM 表面遗留，
   现代 UI 不暴露，靠它们猜语义必然失败。

补充（REA/Ghidra 确认的模块边界）：`sldhwizuiu.dll` 只是**导入**这些 getter，并不实现它们——
`EXTERNAL:0x4d1 → SLDMODU.DLL::moHoleWzd_c::GetCounterBoreDiameter`、
`EXTERNAL:0x4db → …::GetCounterBoreDepth`、`EXTERNAL:0x271 → …::GetCounterBoreDepthWithHC`（source=imported）。
要做函数级深挖，目标应是 `sldmodu.dll`（47 MB）；UI 层 DLL 只负责界面与表访问。

### 6.2 默认值来自 Toolbox 的 SQL 表，不是 API 入参

反编译出的查询语句：

```sql
DISTINCT CDBL(DIAMETER), [SIZE],HEAD_DIA,HEAD_ANG,DIAMETER,COUNTERSINK_DIAMETER,[Name To Match]
SELECT * FROM [%s] ORDER BY CDbl(DIAMETER) DESC
```

配套错误串：`Error occurred retrieving counterbore diameter from table '%s'`。

→ 沉头直径/角度是**查表**得到的。表库是 **SQLite**（不是 Jet/Access），分两类：

- `<SW_INSTALL>\Toolbox\data utilities\lang\English\swbrowser.sldedb`
  —— **19,045,376 B / 5,272 张表**，Toolbox 主目录；GB 的孔表全在这里，表名形如 `GB_DATA_HW_*`，
  实测 8 张：`BottomingTap` / `DowelHole` / `DrillSizes` / `PipeTapDrills` / `ScrewClearances` /
  `StraightPipeTap` / `TapDrills` / `TappedHole`。
- `<SW_INSTALL>\Toolbox\lang\<lang>\*.sldedb` —— 各标准库（`iso` 594,944 / `din` 606,208 /
  `jis` 726,016 / `ansiinch` 1,106,944 / `ansimtrc` 573,440 / `bsi` / `pcs` / `superior` / `dme` / `hasco-metric` …），
  每库表名是 `HOLE` / `TAP` / `PTAP` / `btap` / `fHole` / `Lhole` 这类。

> ⚠️ **一处早前判断的更正**：曾把 `cisc.sldedb`（141,312 B）当成 GB 孔表，其实它是
> **CISC 钢结构型材库**（17 张表 `CC/MC/SC/WC/LC/HS/Ts1c…`，列是
> `DESIGNATIO/WEIGHT/AREA/DEPTH/TW/BF/TF/RI/RA/RT/IX/SX/RX`）。
> `HEAD_DIA` 那些字段名来自库里的全局字段字典 `fields`（165 行 `field_name/desc_english/...`），不是孔表数据。

这解释了此前两个疑问：

- **`HoleWizard5` 得 Ø13、`CreateDefinition` 路线得 Ø13.5**：GB 间隙表
  `GB_DATA_HW_ScrewClearances` 一行三种配合 —— M12 的 `CLOSE_FIT=13` / `Normal_Fit=13.5` / `Loose_Fit=15`，
  两条 API 路线默认取的行不同，不是谁算错了；
- 「钻孔大小」这一项的 `GetFastenerTableTypes` 返回 `(None, False)`——它本来就没有表行，
  尺寸只能靠 `SSize` 字符串解析。

沉头/锥沉的头径与头高同理来自表（或紧固件几何配置），**具体数值随标准、规格变化**，
不需要记住任何一档数字：孔的默认尺寸一律按 §7 的三步定位 + §5 的 API 交叉验证现场取。

### 6.3 实践含义

- 要改默认值：改 Toolbox 表（Toolbox 配置），或用路线 B/C 显式覆写命名属性。
- 不要再给 `Value1..Value12` 找语义——UI 与实现层都不使用它们。
- 需要多级锥沉（Near/Mid/Far）时 `HoleWizard5` 表达不了，只能走
  `IWizardHoleFeatureData2` 的 `CounterSinkDiameter` 族属性。

### 6.4 取证方式与限制

- 本节证据来自**直接二进制字符串提取**（脚本 `strings_hwiz.py` / `strings_hwiz2.py` / `strings_cisc.py`，
  纯 Python 读字节做 ASCII + UTF-16LE 扫描），**不依赖**函数级反编译。
- REA 的 Ghidra 支线：`rea analyze` 能正常启动 Ghidra 12.1.4（`Using Loader: Portable Executable (PE)`、
  `x86:LE:64:default:windows`），但 7.2 MB 目标的自动分析超过 CLI 默认 330 s 上限
  （`REA_GHIDRA_STARTUP_TIMEOUT_MS` 可调；MCP 侧 `update_analysis_settings` 只影响 MCP 进程，不影响 CLI）。
  函数级证据待该次分析跑完后补入，属于佐证而非结论前提。
- Ghidra 解析导入表时从 JDK 的 `bin` 目录找 `msvcp140.dll / vcruntime140.dll`，
  且 SolidWorks 内部依赖（`SLDAPPU/SLDMODU/SLDUIU/...`）全部 `Library not found`
  → **跨 DLL 交叉引用不可用**，本次结论不依赖函数级反编译，只依赖修饰名与 SQL 字面量。

---

## 7. 直接查 Toolbox 表（任意标准通用）

Toolbox 的 `.sldedb` 全是标准 SQLite 3 文件（文件头 `SQLite format 3\x00`），**只读打开即可查询**，
不需要 SolidWorks 运行、也不需要任何 ODBC 驱动。

```python
import sqlite3
db = r'<SW>\Toolbox\data utilities\lang\English\swbrowser.sldedb'
con = sqlite3.connect('file:%s?mode=ro' % db.replace('\\', '/'), uri=True)
cur = con.cursor()

# 第 1 步：这个标准有哪些孔表（把 GB 换成 ISO/DIN/JIS/ANSI METRIC...）
for (t,) in cur.execute("select name from sqlite_master where type='table' "
                        "and name like 'GB_DATA_HW_%'"):
    print(t)

# 第 2 步：看列，找 SIZE 与尺寸列
print([c[1] for c in cur.execute('pragma table_info("GB_DATA_HW_ScrewClearances")')])

# 第 3 步：按 SIZE 字符串取行（SIZE 可能是 'M12' / '#10-24' / '1/4'，一律字符串比较）
print(list(cur.execute('select * from "GB_DATA_HW_ScrewClearances" where SIZE = ?', ('M12',))))
```

要点（对所有标准成立）：

- 表名模式 `<STD>_DATA_HW_<类别>`，类别是 `ScrewClearances / TapDrills / TappedHole / DrillSizes /
  DowelHole / BottomingTap / PipeTapDrills / StraightPipeTap` 这类；标准多了 `PEMInch/PEMMetric`。
- 各标准另有一整套库在 `<SW>\Toolbox\lang\<lang>\<std>.sldedb`，表名是 `HOLE / TAP / PTAP / btap /
  fHole / Lhole`；结构型材库（如 `cisc`）只有型材表，没有孔表。
- 间隙类表通常一行三档配合（`CLOSE_FIT / Normal_Fit / Loose_Fit`，ANSI 侧同样三档）。
  同一 `SSize` 走不同 API 路线可能默认取不同档——这是**设计如此**，不是 API bug；
  需要确定档位时显式覆写命名属性，或直接用 `GetFastenerTable` 取行值。
- 表里是**毫米字符串**，写进 API 前统一换算成米。

完整方法论与"任意标准定位流程"见 `docs/09-toolbox.md`。
