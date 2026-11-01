# 技术插图附图：剖视 + 标注的可行路径（本机实测）

> 分档：✅ 实测通过｜⚠️ 部分可用（有条件）｜❌ 本机不可用（有证据）

## 0. 结论先说

| 需求 | 状态 | 一句话结论 |
|---|---|---|
| 装配剖视图 | ✅ | `swe.section_view()`；判据「新视图 `Type==2` 且能读到 label」 |
| 剖视图读零件清单 | ✅ | `IView.GetVisibleComponents()`（元素要 QI `IComponent2`） |
| 零件在图纸上的坐标 | ⚠️ | 普通视图用 `ModelToViewTransform.ArrayData`；**剖视图该矩阵退化，不能用** |
| 注释（球标）创建 | ✅ | `NewNote(text,h)` 返回 int → `GetNotes()` → `INote` → `GetAnnotation()` |
| 箭头精确落点 | ✅ | `SetLeaderAttachmentPointAtIndex(0,x,y,z)`，回读误差 0.00000 |
| 编号顺序 | ✅ | 纯代码：按图纸 y 降序（从上到下）或极角（从外到内）排序后编号 |
| 箭头样式/字号 | ✅ | `SetArrowHeadStyleAtIndex` + `SetArrowHeadSizeAtIndex` + `ITextFormat` |
| 自动气球（装配） | ✅ | 先插 BOM → 选中视图 → `AutoBalloon2(1, False)` → 3 个球标 |
| 自动气球（零件剖视） | ❌ | `AutoBalloon2` 返回单对象但注记数不变；`AutoBalloon5` 返回 None |
| 从可见边反推锚点 | ❌ | `GetVisibleEntities2` 需传 `RootDrawingComponent`，且只吐 2 条边/1 个剪影 |

## 1. 注释与引线的正确调用链

```python
d.NewNote("1", 0.003)                        # 返回 int（不是 INote）
sheet = d.GetFirstView()                     # 图纸（不是 IDrawingDoc）
note  = list(sheet.GetNotes())[-1].QueryInterface(SW.INote)
ann   = note.GetAnnotation()                 # 唯一桥
ann.SetPosition(x + 0.030, y, 0.0)           # 气泡位置
ann.SetLeader2(True, 0, True, True, False, False)
ann.SetLeaderAttachmentPointAtIndex(0, x, y, 0.0)   # ← 箭头尖精确落点
ann.SetArrowHeadStyleAtIndex(0, 3)           # swArrowStyle_e
ann.SetArrowHeadSizeAtIndex(0, True, 0.0025, 0.0012, 0.0012)
```

回读校验（**必须看末点**）：

```python
pts = list(ann.GetLeaderPointsAtIndex(0))    # 3 个点
tip = (pts[-3], pts[-2], pts[-1])            # 注释端 → 拐点 → 箭头尖
```

实测：指定 (0.0460, 0.1500) → 末点 (0.046, 0.150, 0.0)，`dx=dy=0.00000`；指定 (0.0900, 0.1500) → (0.090, 0.150)，同样 0 误差。首点恒在气泡侧，**拿首点当箭头是错的**。

## 2. 坐标换算（只对普通视图成立）

`IView.ModelToViewTransform.ArrayData` 是 **16 个 double**：

```
[0..2] xAxis  [3..5] yAxis  [6..8] zAxis  [9..11] 平移  [12] 比例  [13..15] 0
```

`p_sheet = trans + scale · R · (p_model − c_model)`，`c_model` 取视图中心。
100×60×20 板、2:1：(0,0,0)→(0.000,0.090)、(0.10,0.06,0.02)→(0.200,0.210)，与 `GetOutline()` 外扩 4.2 mm 吻合。

**剖视图不适用**：两个不同模型点被投影到同一图纸点（基向量退化），所以剖视图只能用「已知图纸坐标 + 反读校验」或图形界面取点。

## 3. 编号顺序（技术插图惯例）

CNIPA 与代理机构通用要求：图序「图1、图2」标在图正下方；附图内标记用阿拉伯数字、与说明书一致；引出线为细实线、一端指向部件、不得交叉、不得穿透无关部件。顺序无强制条文，实务上**全篇统一**即可：

```python
pts.sort(key=lambda t: (-t["y"], t["x"]))   # 从上到下、同高从左到右
# 或极角：math.atan2(y - cy, x - cx) 降序 = 从外到内顺时针
```

## 4. 推荐工作流（当前能力下的最稳做法）

1. `swe.section_view()` 出剖视图，判据 Type==2 + label。
2. 装配件先 `InsertBomTable2`（序号来源）。
3. 气球二选一：
   - 装配：`AutoBalloon2(1, False)`（SW 自己把引线贴到真实轮廓，最省事）；
   - 零件/需要自定义顺序：`NewNote` + `SetLeaderAttachmentPointAtIndex`（落点可控到 0 误差）。
4. 回读每条注释的末点，落一张 `annot.csv`（文本/x/y/nLead）。
5. 人工在 SW 里核对箭头是否压在轮廓线上（本机自动化读不到剖视边，这一步暂时必须人看）。
6. 导出 PDF/PNG 交代理机构前，检查：图序文字、编号连续、引线不交叉。

## 5. 已知边界（别浪费时间的方向）

- `InsertNote` 不存在；`InsertNewNote2` 11 参无坐标。
- `AutoBalloon5` + `IAutoBalloonOptions` 设了参数仍返回 None。
- `GetVisibleEntities2(None, et)` 报 `TypeError: Parameter 2`（必须给组件）；给了 root 也只有 2 条边。
- 剖视图中 `GetVisibleComponents()` 的**组件原点**常落在 outline 外（螺栓轴线在剖切面之外），不能当锚点。
- `IAnnotation` 的 QI 在气球对象上失败（「不支持此接口」），必须经 `INote`。
