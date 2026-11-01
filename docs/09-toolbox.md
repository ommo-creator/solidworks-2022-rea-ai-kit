# Toolbox 表库：任意标准、任意孔的默认值从哪来、怎么查

适用范围：**所有标准**（GB / ISO / DIN / JIS / ANSI Inch / ANSI Metric / BSI / KS / AS / IS / PCS / DME /
HASCO / PEM…）与**所有孔型**（光孔、沉头、锥沉、螺纹、管螺纹、销孔、底孔）。不记录任何具体数值——
数值随标准与规格变化，一律现场查。

---

## 1. 为什么必须查表

孔向导的默认尺寸**不是硬编码、也不是 API 入参**：

- `IWizardHoleFeatureData2` 的 `ThruHoleDiameter / CounterBoreDiameter / CounterSinkDiameter /
  ThreadDiameter / TapDrillDiameter …` 在 `InitializeHole` 之后**自动有值**；
- 这些值来自 Toolbox 的数据库表（实现层可见 SQL：`SELECT * FROM [%s] ORDER BY CDbl(DIAMETER) DESC`、
  `DISTINCT CDBL(DIAMETER),[SIZE],HEAD_DIA,HEAD_ANG,...`，错误串
  `Error occurred retrieving counterbore diameter from table '%s'`）；
- 因此 `HoleWizard5` 的 `Value1..Value12` 是**旧 COM 表面的遗留槽位**，现代 UI 与实现层都不使用它们
  （二进制里连字面量都搜不到）。想改尺寸就改命名属性，想改默认值就改表。

---

## 2. 表库位置与格式（通用）

| 位置 | 内容 | 表名模式 |
|---|---|---|
| `<SW>\Toolbox\data utilities\lang\English\swbrowser.sldedb` | Toolbox 主目录（约 19 MB，5,000+ 表） | `<STD>_DATA_HW_<类别>` |
| `<SW>\Toolbox\lang\<lang>\<std>.sldedb` | 每个标准一套（iso / din / jis / ansiinch / ansimtrc / bsi / pcs / dme / hasco-metric …） | `HOLE` / `TAP` / `PTAP` / `btap` / `fHole` / `Lhole` |
| `<SW>\Toolbox\lang\<lang>\cisc.sldedb` 等 | 结构型材库 | 型材表（`CC`/`MC`/`HS`/`Lc`…），**不含孔表** |

全部是标准 **SQLite 3**（文件头 `SQLite format 3\x00`），只读连接即可，**不需要** SolidWorks 运行或 ODBC 驱动。

替代做法（不需要碰文件）：用 API 直接问——
`sw.GetHoleStandardsData(holeType)` → `IHoleStandardsData.GetFastenerTableTypes / GetFastenerTable`。
两者内容同源，但读 SQLite 更快、能一次看清全部标准。

---

## 3. 三步定位（换成任何标准都一样）

```python
import sqlite3
db = r'<SW>\Toolbox\data utilities\lang\English\swbrowser.sldedb'
con = sqlite3.connect('file:%s?mode=ro' % db.replace('\\', '/'), uri=True)
cur = con.cursor()

# 1) 该标准有哪些孔表
for (t,) in cur.execute("select name from sqlite_master where type='table' and name like ?",
                        ('GB_DATA_HW_%',)):
    print(t)

# 2) 表结构：找 SIZE 与尺寸列
print([c[1] for c in cur.execute('pragma table_info("GB_DATA_HW_ScrewClearances")')])

# 3) 按 SIZE 取行（SIZE 是字符串：'M12' / '#10-24' / '1/4' / 'M48'）
print(list(cur.execute('select * from "GB_DATA_HW_ScrewClearances" where SIZE = ?', ('M12',))))
```

判断表是否"对"的技巧：先 `select * limit 1` 看列名里有没有你要的量
（`DIAMETER / DEPTH / TAP_DRILL / HEAD_DIA / HEAD_HT / CLOSE_FIT / CounterSink…`），
再按 `SIZE` 过滤；表里往往是**毫米字符串**，写进 API 前统一 ×0.001。

---

## 4. 配合/公差档位是通用概念

间隙类表通常一行多档：`CLOSE_FIT / Normal_Fit / Loose_Fit`（ANSI 侧同样三档），
销孔类还有 `NOMINAL_FIT / CLEARANCE_FIT / PRESS_FIT / TRANSITIONAL_FIT`。

同一个 `SSize` 走不同 API 路线（`HoleWizard5` vs `CreateDefinition+InitializeHole`）**可能默认取到不同档**，
于是同一个 M12 会得到 13 或 13.5 这样的差异。这是设计如此，不是 API bug：

- 要确定性：显式写命名属性（`CounterBoreDiameter`、`ThruHoleDiameter`…）；
- 要"按标准来"：先用 `GetFastenerTable` / SQLite 取行值，再写入属性。

---

## 5. 两条正规改法

| 目标 | 做法 | 影响面 |
|---|---|---|
| 改这个孔的尺寸 | 路线 B/C 写命名属性后 `CreateFeature` / `ModifyDefinition` | 单特征 |
| 改默认值/加自定义标准 | 改 Toolbox 表（Toolbox 配置或直接用标准表文件） | 之后所有新孔 |

⚠️ 改 Toolbox 表前先备份对应 `.sldedb`；表是**用户级共享数据**，改错会影响所有文档。

---

## 6. 与 API 的关系（避免重复劳动）

- 标准列表：`GetHoleStandards()` 的返回**顺序 ≠ 枚举顺序**，必须按名字匹配；
- 紧固件列表：`GetFastenerTypes(stdName)` **必须先调 `GetHoleStandards()` 热身**，否则恒返回 `(None,None,False)`；
- 表数据：`GetFastenerTable(stdName, fastenerID, tableID)` 返回的行才是权威值；
- 头径/头高等"看起来没生效"的量，多半是表里本来就取了某个小值（例如极薄的沉台），
  先查表再判断实现是否有问题。

---

## 7. 相关脚本

| 脚本 | 作用 |
|---|---|
| `probe_db.py` | 判断 `.sldedb` 真实格式（SQLite / Jet） |
| `db_tables.py` / `db_dump1.py` | 列某个库的表清单、表结构与元数据表 |
| `db_find_hole.py` | 扫全部 `.sldedb`，按表名找出含孔表的库 |
| `db_gb_hw.py` / `db_gb_sc.py` | 列出某标准的 `<STD>_DATA_HW_*` 表、按 SIZE 取行（把 GB 换成任意标准即可） |
| `dump_gb_tables.py` | 按标准批量导出表结构与样例行（可改成任意标准） |
