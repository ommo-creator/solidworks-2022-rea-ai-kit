# 19 · 大装配批量改型：位姿 / 配合 / 删除 / 保存 / 崩溃

> 这一篇解决的是"零件都能建，但一进几百个组件的装配就出怪事"：
> 位姿**静默错乱**、配合报**"无法找到解"**、删件**删不动**、保存**返回 True 但盘上没变**、长循环跑到一半**进程消失**。
>
> 实测环境：SolidWorks 2022 SP5.0（30.5.0.0049）+ Windows + Python 3.13 + comtypes 1.4.17；
> 装配规模 300–400 组件，单轮改型涉及 60–130 个零件文件，连续跑两周。
> 下文数字与现象来自这次真实改型（零件名已匿名），凡标 ❌ 的都是踩过并复现的。
>
> 分档沿用全仓约定：✅ 本机跑通并量化验证｜⚠️ 有条件可用｜❌ 本机证伪

## 19.0 一句话结论

改装配不是"多调几个方法"，而是**必须自己造三件东西**，缺一件就会"返回成功、结果错、还不报错"：

| # | 必须自建 | 为什么 | 位置 |
|---|---|---|---|
| 1 | 位姿的 **写 → 读回 → 几何复测** 闭环 | `Transform2` 写错不报错，129 个件能全部叠到同一点 | §19.1 / §19.9 |
| 2 | 保存的 **落盘证据链**（字节数 + 重开 + 体积回读） | `SaveAs` 对占用文件返回 `True`，盘上却没变；`Save()` 会弹模态永久阻塞 COM | §19.5 |
| 3 | 会话的 **寿命预算**（≤45 件/会话） | 超出后 `OpenDoc7` 静默返回 `None`，再往后进程直接消失 | §19.6 |

## 19.1 位姿：`IMathTransform` 那 16 个 double 到底怎么排

### 布局（✅ 实测，2022 SP5）

```python
# [0..8]  旋转 3×3（按行取：R 的第 0/1/2 行）
# [9..11] 平移（单位：米）
# [12]    = 1.0
# [13..15]= 0.0
ad = [R00, R01, R02,
      R10, R11, R12,
      R20, R21, R22,
      tx,  ty,  tz,
      1.0, 0.0, 0.0, 0.0]
```

读回换算（**零件局部坐标是毫米，平移是米**）：

```python
a = [float(v) for v in comp.GetTotalTransform(True).ArrayData]
R = (a[0:3], a[3:6], a[6:9])
def to_asm(p_mm):                      # p_mm = 零件局部坐标(mm)
    return tuple(sum(R[i][j] * p_mm[j] for j in range(3)) + a[9 + i] * 1000.0
                 for i in range(3))
```

### 写位姿（✅ 配方见 `docs/04-recipes.md` R37）

```python
from array import array
mu = sw.GetMathUtility().QueryInterface(SWT.IMathUtility)
mt = mu.CreateTransform(array('d', ad)).QueryInterface(SWT.IMathTransform)   # 必须传 array('d')
try:
    cc.Transform2 = mt
except Exception:
    cc._IComponent2__com__set_Transform2(mt)     # 极少见：老路径 property 赋值不通时的私有 setter
```

### 四个已知陷阱

| 陷阱 | 现象 | 修法 |
|---|---|---|
| ❌ 把平移塞进第 4 列（`[m00,m01,m02,tx, m10,…]`） | 不报错、`AddComponent5` 成功、`Transform2` 赋值成功，但**整装配位姿错乱**（实测 129 个碟簧全叠到球心、衬块跑到北极） | 平移只在 `[9..11]`；写完**立刻读回**逐件比对 |
| ❌ 末尾四位凭记忆写 | 有时能跑，有时位姿怪，难定位 | 以"读回一致"为准；本章写法 `[…,1.0,0.0,0.0,0.0]` 已在多轮实测通过 |
| ❌ `CreateTransform` 直接赋值 | `CreateTransform` 返回裸 `_Dispatch`，属性赋值报错 | 先 `QueryInterface(SWT.IMathTransform)` |
| ❌ 用变换矩阵反推方位 | 同一份文件里两个件读出来是 `112°+45k` 和 `114°+45k`，而几何真值都是 `113°+45k` | 方位一律取**几何**（扇段两侧竖直面法向的角平分线 / 面质心 `atan2`），不读矩阵列 |

> ⚠️ **旋转方向必须逐批复测**。实测反例：对某族件按"直觉正方向"施加 `+2°`，几何方位反而从 `336°` 变 `334°`
> （即实际是 `−2°`）；改 `−4°` 才到 `338°`。不同来源件的矩阵右乘顺序可能相反——**改完立刻用几何法复测**，
> 不要以"我写的是 +2°"当结论。

## 19.2 插入组件：`AddComponent5` 的三个前提

```python
c = A.AddComponent5(path, 0, '', False, '', 0.0, 0.0, 0.0)   # 0/''/False/'' = 用默认配置、原点定位
if c is None:
    raise RuntimeError('插入失败(part 不在内存?)')
cc = c.QueryInterface(SWT.IComponent2)
cc.Transform2 = mt                                            # 位姿单独设，别指望 x/y/z 参数
```

1. ✅ **零件必须已在内存**：未 `OpenDoc6/OpenDoc7` 打开过 → 静默返回 `None`（无异常）。
2. ✅ **一次会话别开太多**：累计打开约 **45 个零件**之后，`OpenDoc7` 开始返回 `None`；零件用完立刻 `SW.CloseDoc(title)`。
3. ✅ 返回的是装配侧的 `IComponent2` 派发指针，读名字/路径/包围盒前先 QI（`GetPathName` / `Name2` / `GetBox`）。

> 删件、改件、再重插是**破坏引用**的操作。已有配合和引用要先评估：覆盖同名零件文件 + `EditRebuild3` + `Save`
> 往往比"删组件重插"安全（见 §19.5 第 4 条）。

## 19.3 配合：`AddMate5` 只在**活动文档**生效，且"无法找到解"多半是自找的

### ✅ 正确姿势

```python
sw.ActivateDoc3(md.GetTitle(), False, 0, 0)      # 先激活
md = sw.ActiveDoc.QueryInterface(SWT.IModelDoc2) # 再取（不是之前抓的那个对象）
A  = md.QueryInterface(SWT.IAssemblyDoc)
err, mate = A.AddMate5(5, 2, False, 0.043, 0.047, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                       False, False, 0, out)     # 距离配合 + 限位
```

- ❌ 对**非活动文档**调用：仍返回一个指针，`ErrorStatus≠0`，配合**根本没建**。历史上一整个装配"一条配合都没有"就是踩这条。
- ⚠️ `ErrorStatus≠0` **不等于失败**，也别把它当唯一判据；真正的判据是**重建后几何有没有被求解器搬动**。

### ❌ 致命用法：短行程用"距离限位"表达

实测事故：在两个**法向相反**的面之间加"距离限位 43~47 mm"（一个面法向 `−X`，另一个也朝 `−X`）：

1. `Flip=False` / `True` 都解不出 `43 mm`；
2. 求解器把两个件甩到 **2.1~2.2 m** 外；
3. `EditDelete` 删掉配合后，**位移仍留在文件里**，装配永久错位；
4. 只能按基线逐件 `Transform2` 恢复（`a7_repair.py` 式：按 `Name2` 匹配基线位姿再写回）。

**结论（结构口径，不是 API 口径）**：0~4 mm 的短行程**不要用自动距离限位**。它在结构上由
`Ø220/Ø221 导向副 + 挡圈防脱 + 碟簧组装配高` 三处几何保证；要演示运动学，用"限制角度配合"或手工路径配合。

## 19.4 批量删件：`IComponent2.Select4` 走不通

| 通道 | 实测 | 结论 |
|---|---|---|
| `IComponent2.Select4(...)` | 472 件目标，实删 **0** | ❌ 对装配组件不可靠 |
| `Extension.SelectByID2(name,'COMPONENT',0,0,0,append,0,None,0)` + `EditDelete` | 472 件全删 | ✅ |

- 第 8 参是 `Callout`，**必须传 `None`**（传 `0` 有时也过，但会随机失手）。
- 返回值**不可信**（常返回 `False` 但已选中）→ 用 `SelectionManager.GetSelectedObjectCount2(-1)` 数。
- 每批 **25 个**，批间 `md.ClearSelection2(True)`；删完 `EditRebuild3`。
- 名称匹配要算 `Name2` 前缀（`N64_xxx-1` / `N64_xxx<1>` 两种后缀都见过），别用精确等号。

## 19.5 保存：`Save()` 会阻塞，`SaveAs` 会撒谎

| 用法 | 结论 |
|---|---|
| `md.Save()` | ❌ 会弹「另存为」模态框 → **永久阻塞 COM**，脚本挂死 |
| `md.SaveAs2(tmp, 0, True, True)` | ✅ 正常返回 `0`；`True/True` = 静默 + 保存到临时路径 |
| `md.SaveAs(path)`（Extension 路径） | ⚠️ 能落盘，但目标已存在时返回 `False`（坑 15）；`IModelDocExtension.SaveAs4` 本机**不存在** |
| 零件被别的会话占用 | ⚠️ 返回 `True`，**盘上文件没变** |

### ✅ 落盘证据链（唯一可信判据）

```python
md.SaveAs2(tmp, 0, True, True)
SW.CloseDoc(md.GetTitle())
assert os.path.getsize(tmp) > 100_000          # ① 字节数
os.replace(tmp, final)                         # ② 原子替换
d2, _ = open_doc(final, ro=True, silent=True)  # ③ 重开
assert len(A2.GetComponents(True) or []) == n  # ④ 结构回读
assert abs(vol(d2) - expect) < 1e-6            # ⑤ 体积回读
```

- 体积回读要**用米**对米（`GetMassProperties2()[3]`），别和 `mm³` 混（漏 `×1e9` 会得到 `−100%` 的假结论）。
- 改完体积变化必须能和**解析值**对账：`ΔV = π(r₁²−r₂²)·h` 之类；实测例子：`16.160763270 → 16.133559000 m³`，
  差 `−0.027204270 m³` = 8 件 × `3,400,533.75 mm³`，与该次两步切除的解析和**逐位吻合**。
- ✅ **保住装配引用 + 配合**的做法：把新版零件**覆盖同名文件**，再 `EditRebuild3` + `Save`；
  比"删组件 → 插新件 → 重建配合"稳得多（后者会把既有配合全部作废）。

## 19.6 会话卫生与崩溃归因（这条不遵守，长循环必死）

### 现象

| 报错原文 | 含义 |
|---|---|
| `COMError(-2147023170, '远程过程调用失败。')` | 进程已经没了（RPC 目标消失） |
| `COMError(-2147417848, '被调用的对象已与其客户端断开连接。')` | 对象存活、连接断了：SW 侧已重置会话 |
| `COMError(-2147417851, '服务器出现意外情况')` | 常见于**文档里留着一张没退出的草图**：`NewDocument` / `CreateLine` 全线报错 |

### ✅ 已定位的真因（`%TEMP%\swxJRNL.swj` 栈）

```
uiTreeCtrlView_c::OnInitialBkMdComptUpdate   ← 崩在这里
  ← uiBaseFeatureFilter_c::Create / CreateFeatureFilter
```

FeatureManager 特征树在"长时间开文档 / 关文档"的循环里**异步刷新**，撞上刚被关闭的文档 → 访问违例 → 进程死亡。
Windows 应用日志里**没有** Application Error 记录（别去那里找）。

### ✅ 规避（已固化进驱动脚本）

1. 每个会话 **≤45 个零件**；
2. **每件处理完立刻 `SW.CloseDoc(title)`**（注意是 `CloseDoc(title())`，漏括号 = 文档不关 + 文件被锁 `PermissionError[5]`）；
3. 每件把结果写 **json 断点**，崩了能续跑；
4. 批间重启 SW：`Stop-Process` → `Start-Process <SW_INSTALL>\SLDWORKS.exe` → 等 **65–90 s**；
5. 遇到 `-2147417851`：先 `SW.CloseAllDocuments(True)`（把残留草图清掉），再继续——不要重试原调用。

## 19.7 干涉：只有"对数下降"等于没查

### ✅ 完整开关 + 读数（403 件全装配约 2.7 s）

```python
idm = asm.InterferenceDetectionManager
idm.TreatCoincidenceAsInterference = False   # 只贴合、零体积接触不算
idm.IncludeMultibodyPartInterferences = False
idm.TreatSubAssembliesAsComponents = False
idm.ShowIgnoredInterferences = False
idm.IgnoreHiddenBodies = True
cnt = idm.GetInterferenceCount()
for it0 in (idm.GetInterferences() or []):
    it = it0.QueryInterface(SWT.IInterference)
    v_mm3 = it.Volume * 1e9                              # Volume 是 m³
    names = [c.QueryInterface(SWT.IComponent2).Name2 for c in (it.Components or [])]
```

### 三条方法论（比 API 更重要）

1. ❌ **"主要干涉已清零"这种汇总句会漏真事故**：某轮报"P03 相关全部清零"，而真实互穿
   `上压靴 × 下压靴 = 2.82e6 mm³ × 8 对` 一直存在，只是不在被检查的那张清单里。
2. ✅ **先问"重叠落在哪个面上"，再问"重叠多少"**：总体积相同可能是完全不同的两件事
   （刻意焊接互埋 vs 装配占位错）。
3. ⚠️ **条件**：装配要 `ForceRebuild3` 过、在干净会话里读；刚做完大量删除/插入直接读，结果不可信。
   历史脚本里"本机返回不可信"的结论，多半是条件不满足，而不是 API 不通。

## 19.8 半剖与"看得见的证据"

### ✅ 装配级半剖（在临时副本上切，不动本体）

```python
md = open_copy_to_temp(asm_path)                  # 永远别切原文件
md.Extension.SelectByID2('右视基准面', 'PLANE', 0, 0, 0, False, 0, None, 0)
md.InsertSketch(True)
s = md.SketchManager
for a, b in [((-3, -3), (3, -3)), ((3, -3), (3, 3)), ((3, 3), (-3, 3)), ((-3, 3), (-3, -3))]:
    s.CreateLine(a[0], a[1], 0.0, b[0], b[1], 0.0)      # 3 m 见方
md.ClearSelection2(True)
f = md.FeatureManager.FeatureCut4(
    True, False, True,                                  # Sd, Flip, Dir
    0, 0, 3.0, 0.0,                                     # T1,T2=0 盲切；D1=3.0 m
    False, False, False, False,
    0.0, 0.0,
    False, False, False, False,
    False,
    True, True,                                         # UseFeatScope, UseAutoSelect
    True, True, True,                                   # AssemblyFeatureScope, AutoSelectComponents, PropagateFeatureToParts
    0.0, 0.0, False, False)
```

- ✅ 一次切掉 `x>0` 半空间，**所有零件的剖切面同时出现**，比"隐藏一半零件"真实。
- ❌ `IModelViewManager.CreateSectionViewData()` 的 `FirstPlane` 赋值在本机报 `COMError(-2147352570,'未知名称')`
  → 3D 剖视这条线没通；要剖面直接走上面的装配级切除（或工程图剖视，见 `docs/05-sections.md`）。
- ❌ 别"删历史特征"来改外形：某壳体删掉 `MCP_*` 特征后，体积反而 `+0.117 m³`，`bbox` 从 `±1847.8` 变 `±2100`
  —— 那些特征里混着壁内油道，删一个带走一片壁。

## 19.9 改型的复测纪律（翻车最多的五条）

1. **判据要两头查**：判"半件"只查 `abs(zmax)<=2` 会漏（该件 `zmin=0 / zmax=160`，其实做了半边）；`zmin`/`zmax` 都要看。
2. **筛选会漏翻向件**：按 `abs(phi)<0.5` 筛某工位时，翻向实例（`Ry(β+180)`）局部 `+X` 指向反方向被滤掉，
   于是只看得到一半碟簧，得出"预紧链有 4.78 mm 空档"的**假结论**。筛选后必须交叉核对实例数。
3. **体积/质检只看总量会自欺**：`nBody` 变了必须解释（本该 1 体的件变 4 体 = 切断了）；
   `ΔV` 必须落在解析值 ±30% 内，并且**符号**别写反（`EXP` 为负时 `-EXP*1.3 <= dV <= -EXP*0.7` 恒 `False`）。
4. **同一件事别让"改"和"审"并发**：审查期间必须**冻结写入**（实测审查中途文件被改，已测数据全部作废）。
5. **每次改完都留一份"可回滚基线 + 备份目录"**：备份命名 `_bak_x<n>`，与版本号一一对应；
   回滚判据 = 字节数 + 重开组件数 + 体积，三件对齐才算回滚成功。

## 19.10 本章对应的问题清单（速查）

| 症状 | 先看 |
|---|---|
| 装配里所有件位置都不对 | §19.1 布局 / 读回复核 |
| `AddComponent5` 返回 `None` | §19.2 零件未在内存 |
| 配合建不上 / 件被甩出几米 | §19.3 活动文档 + 距离限位 |
| 删件 0 个 | §19.4 换 `SelectByID2 + EditDelete` |
| `SaveAs` 返回 `True` 但盘上没变 | §19.5 证据链 |
| 跑到一半进程消失 | §19.6 ≤45 件 / 重启 |
| 干涉数字和眼看的对不对 | §19.7 条件与口径 |
| 剖视图建不出 | §19.8 装配级 `FeatureCut4` |
| "改完更糟" | §19.9 复测纪律 |
