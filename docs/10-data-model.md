# 数据面：材料 / 自定义属性 / 质量与干涉 / 配置与设计表

实测环境：SolidWorks 2022 SP5（30.5.0）、Windows、comtypes 1.13+、Python 3.13。
本文件只写**已验证**的入口与判据；未验证的会标 ⚠️。

---

## 0 三条通用原则

1. **先拿到正确的接口**。同一能力常挂在奇怪的地方：材料在 `IPartDoc`，不在 `IModelDocExtension`；干涉在 `IAssemblyDoc`。
2. **写完必须 `EditRebuild3()` 再读质量/体积**，否则拿到重建前的旧值。
3. **判据用数字**（质量、体积、返回值码），不要用"没报错"当成功。

---

## 1 材料（密度 → 质量）

### 1.1 正确入口

```python
part = md.QueryInterface(SW.IPartDoc)          # 材料接口在 IPartDoc 上
part.SetMaterialPropertyName2('默认', 'solidworks materials.sldmat', '普通碳钢')  # 返回 0
md.EditRebuild3()
status, arr = md.Extension.GetMassProperties2(1, False)
mass = arr[5]                                   # 索引 5 = 质量
```

- 第 1 参是**配置名**（`'默认'`），不是空串。
- 第 2 参是材料库的 **basename**（`solidworks materials.sldmat`），传全路径也行。
- 第 3 参是库内材质名（中文版即中文名，如 `普通碳钢`、`合金钢`、`AISI 1020`）。

### 1.2 读回

```python
part.GetMaterialPropertyName2('默认')   # 只有 1 个实参 → ('solidworks materials', '合金钢')
md.MaterialIdName                       # 'solidworks materials|合金钢|9'
```

### 1.3 实测数字（板 100×60×20，体积 1.2e-4 m³）

| 材质 | 密度 kg/m³ | 质量 kg | 与 密度×体积 的偏差 |
|---|---|---|---|
| 普通碳钢 | 7800 | 0.936 | 0.0 |
| 合金钢 | 7700 | 0.924 | 1.11e-16 |

### 1.4 失败路径（别走）

| 写法 | 结果 |
|---|---|
| `md.Extension.SetMaterialPropertyName2(...)` | `AttributeError`（typelib 里没有） |
| `md.MaterialIdName = 'solidworks materials|普通碳钢'` | 写进去、能读回，**质量一点不变** |
| `md.MaterialUserName = '普通碳钢'` | 同上，只是显示名 |

### 1.5 材料库文件（免开 SW 就能查密度）

```python
dbs = sw.GetMaterialDatabases()     # 3 条路径，均在 …\lang\<语言>\sldmaterials\
```

- 文件是 **UTF-16 XML**，`<material name="普通碳钢" matid="9">` 内含 `<DENS displayname="密度" value="7800"/>`。
- `solidworks materials.sldmat` 有 269 个材质，钢类 29 个。
- 想批量建"材质-密度"表，直接解析这个 XML 比逐个调 API 快两个数量级。

---

## 2 自定义属性

```python
cpm = md.Extension.CustomPropertyManager('默认').QueryInterface(SW.ICustomPropertyManager)
cpm.Add3('图号', 30, 'QJT-001', True)      # 30=文本，3=数字，最后一位=已存在则覆盖
cpm.GetNames()                              # 名字列表
cpm.Get6('图号', False)                     # 2 个实参 → (值, 解析值, 是否解析, 是否链接, 结果码)
cpm.GetAll3()                               # 0 个实参 → [名字, 类型, 值, 结果, 链接, 数量]
```

- `Get6` 返回 5 元组，第一个才是值；`GetAll3` 返回 6 个平行数组。
- 持久化已验证：写 3 条 → 保存 → 关闭 → `OpenDoc6` 重开 → 名字、值、材质全部保留（`probe-output\p0_mat_prop.SLDPRT` 128,248 B）。

---

## 3 质量 / 包围盒 / 干涉

```python
# 质量（推荐：一次拿全）
st, arr = md.Extension.GetMassProperties2(1, False)   # arr[3]=体积 arr[4]=表面积 arr[5]=质量
# 包围盒（毫米！）
bbox = md.QueryInterface(SW.IPartDoc).GetPartBox(False)   # [x0,y0,z0,x1,y1,z1] 单位 mm
# 装配干涉
idm = asm.InterferenceDetectionManager          # IAssemblyDoc 上的 0 参调用
idm.TreatCoincidenceAsInterference = False
idm.IncludeMultibodyPartInterferences = True
idm.GetInterferenceCount()
for it in idm.GetInterferences():
    it.Volume()                                  # m³
    it.IsPossibleInterference()
```

干涉实测：板 100×60×20 + 20 mm 立方体（`AddComponent5` 按**包围盒中心**落位 `(0.04,0.02,0.005)`）→ `Volume() = 6.000000000000002e-06`，与 0.02×0.02×0.015 精确一致。

---

## 4 配置与设计表

### 4.1 配置（不需要 Excel，推荐）

```python
md.AddConfiguration3('D80', '80mm 版', '', 0)
md.EditRebuild3()
md.ShowConfiguration2('D80')          # 必须先重建，否则返回 False 且不切换
md.EditRebuild3()
dim = md.Parameter('D1@草图1').QueryInterface(SW.IDimension)   # ★ 切配置后必须重新取对象
dim.SetSystemValue2(0.08, 1)          # 1 = swInConfigurationOpts_e.ThisConfiguration
md.EditRebuild3()
dim.GetSystemValue2('D80')            # 只返回该配置的覆盖值，无覆盖时是 0.0
```

- `SetSystemValue2` **返回 0 也算成功**，不要用返回值判失败。
- ⚠️ 拿旧 `IDimension` 对象写新配置 → 会写到**上一个**活动配置（坑 26）。

### 4.2 设计表：本机无 Excel，不可用

| 尝试 | 结果 |
|---|---|
| `InsertFamilyTableNew()` | 返回 0，`GetDesignTable()` 有对象、`Attach()` True，但 `Updatable` False、`GetTotalRowCount()` = **-2** |
| `SetEntryText(row,col,text)` 全填 | 全返回 0，`UpdateTable(...)` True，配置仍只有 `['默认']` |
| `InsertFamilyTableOpen(GBK 制表符 .txt)` | **False** |
| `InsertFamilyTableOpen(openpyxl 造的 .xlsx)` | **True**，但随后 `LastError` 抛 `COMError (-2147417851, '服务器出现意外情况。')`，行数 -2 |

根因：机器上没有 Excel（`C:\Program Files*\Microsoft Office\root\Office*\EXCEL.EXE` 不存在），SW 的嵌入式工作表引擎也没起来。
**结论**：需要多规格就用 4.1 的配置路线；真要设计表，先装 Excel 或改用"配方 + 参数文件"批量建模。

---

## 5 判据速查

| 能力 | 通过判据 |
|---|---|
| 材料 | 质量 = 密度 × 体积，偏差 < 1e-12 |
| 自定义属性 | 保存→关闭→重开，`Get6` 值不变 |
| 质量属性 | `arr[3]` 与几何体积一致；`GetPartBox` 是**毫米** |
| 干涉 | `Volume()` 等于手工算的重叠体积 |
| 配置 | 每个配置的 `GetSystemValue2(cfg)` 与体积都对得上 |
| 设计表 | 无 Excel 时：`Updatable=False` + 行数 -2 就是不可用信号 |
