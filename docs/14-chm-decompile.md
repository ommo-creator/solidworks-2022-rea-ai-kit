# 官方资料的打开方式（CHM / 日志 / 示例）

## 1. CHM 反编译

```powershell
# 目录必须先建，否则 hh.exe 退出码 0 但一个文件都不出（实测踩过）
$out = 'D:\...\chm-api-en'
New-Item -ItemType Directory -Force -Path $out | Out-Null
Start-Process hh.exe -ArgumentList @('-decompile', $out, '<SW_INSTALL>\api\sldworksapi.chm') -Wait
```

本机实测结果：

| CHM | 大小 | 产出页数 | 内容 |
|---|---|---|---|
| `sldworksapi.chm` | 31.8 MB | **17,170** | 全部方法参考 + 2,828 个可运行示例 |
| `API_GB.chm` | 4.9 MB | 2,587 | 中文 API 手册（方法说明为简版） |
| `sldworksapiprogguide.chm` | 0.4 MB | 170 | 编程指南（工作流、概念） |
| `swconst.chm` | 5.8 MB | 1,311 | 全部枚举的成员说明 |
| `swcommands.chm` | 0.2 MB | 74 | 命令行/命令 ID |

方法页命名：`SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.<接口>~<方法>.html`
示例页命名：`<操作>_Example_VB.htm` / `_CSharp.htm` / `_VBNET.htm` / `_CPlusPlus_COM.htm`

### 页面里的结构（解析用）

```html
<!-- 参数声明 -->
<a class="parameter" id="Sd" href="#">Sd</a> As System.Boolean
<!-- 参数说明（浮动气泡） -->
<div id="Sd_box" class="dxpopupbubble">
  <DL><DT class="popupbubble"><I>Sd</I></DT>
      <DD class="popupbubble"><P>True for single ended, false for double ended</P></DD></DL>
</div>
```

正则可直接抄 `scripts/chm_index.py`：参数名锚点是 `class="parameter" id="NAME"`，说明锚点是 `id="NAME_box"`。

## 2. 会话日志 swxJRNL.swj —— SolidWorks 自己写的"宏录制"

位置：`%APPDATA%\SolidWorks\SOLIDWORKS 2022\swxJRNL.swj`（覆盖写，每次退出/启动刷新；同目录还有 `swxJRNL.BAK`）。

它不是流水账，而是一份**能直接运行的 VBA 宏**：开头 `Sub main()`，结尾 `End Sub`，变量声明齐全，枚举用真实名字（`swWindowState_e.swWindowMaximized`、`swUserPreferenceToggle_e.swSketchAddConstToRectEntity`）。

本机一次 1,071 行的日志统计（37 种调用，584 次调用行）：

| 调用 | 次数 | 含义 |
|---|---|---|
| `Part.ClearSelection2` | 112 | 几乎所有特征操作前都先清选择 |
| `Part.ActiveView.FrameState/Left/Top` | 119 | 每次激活文档都重设窗口 |
| `swApp.ActivateDoc2` | 39 | 多文档切换 |
| `swApp.NewDocument` | 35 | 建文档（日志里就是官方写法） |
| `swApp.CloseDoc` | 34 | 关文档 |
| `Part.Save3` | 16 | 保存，带 errors/warnings 两个 Long |
| `Part.ShowNamedView2("*Isometric", 7)` | 14 | 视角复位 |
| `Part.EditRebuild3` | 9 | 重建 |

### 三个可以直接抄的"习惯"

1. **进草图前先关掉两个吸附开关**（否则矩形自动带构造线/中点关系，后续选轮廓会多选）：
   ```vb
   Part.Extension.SetUserPreferenceToggle swUserPreferenceToggle_e.swSketchAddConstToRectEntity, _
        swUserPreferenceOption_e.swDetailingNoOptionSpecified, False
   Part.Extension.SetUserPreferenceToggle swUserPreferenceToggle_e.swSketchAddConstLineDiagonalType, _
        swUserPreferenceOption_e.swDetailingNoOptionSpecified, True
   ```
2. **每步之间 `ClearSelection2 True`**，不要指望上一步的选择还干净。
3. **画完立刻 `InsertSketch True` 退出草图**，再选轮廓做特征 —— 日志里从不"在草图里直接建特征"。

### 最有价值的一条：特征数据对象

日志把我调的 `FeatureLinearPattern5(3, 0.025, ...)` 重写成了：

```vb
Set swFeatMgr = Part.FeatureManager
Set swFeatData = swFeatMgr.CreateDefinition(swFeatureNameID_e.swFmLPattern)
swFeatData.D1EndCondition = 0
swFeatData.D1ReverseDirection = False
swFeatData.D1Spacing = 0.025
swFeatData.D1TotalInstances = 3
swFeatData.D2EndCondition = 0
swFeatData.D2PatternSeedOnly = False
swFeatData.D2ReverseDirection = False
swFeatData.D2Spacing = 0
swFeatData.D2TotalInstances = 1
swFeatData.GeometryPattern = False
swFeatData.VarySketch = False
Set swFeat = swFeatMgr.CreateFeature(swFeatData)
```

圆周阵列对应 `swFmCirPattern`(=5)，属性是 `TotalInstances / Spacing(弧度) / EqualSpacing / ReverseDirection / Direction2`。

**Python/comtypes 里必须补一步**：`CreateDefinition` 返回的是无类型 `_Dispatch`，直接 `CreateFeature` 会抛
`ctypes.ArgumentError: COMError: (-2147352570, '未知名称。', (None, None, None, 0, None))`。
先 `fd = fd.QueryInterface(SldWorks.ILinearPatternFeatureData)`（圆周用 `ICircularPatternFeatureData`），
17 个属性全部可写，`CreateFeature(fd)` 返回 `IFeature`，特征树出现 `阵列(线性)1`。

## 3. 示例库

`data/examples-index.json`：`{文件名: {op, lang, title, code, file}}`，2,828 条。

按主题挑 VB6 示例（最接近 comtypes 的调用形态）：

```python
import json
ex = json.load(open("examples-index.json", encoding="utf-8-sig"))
for fn, e in ex.items():
    if e["lang"] == "VB" and "Mate" in e["op"]:
        print(e["op"], len(e["code"]))
```

高价值主题与数量：装配/配合 167、工程图 197、草图/线段 169、选择/射线 68、质量属性 46、阵列/镜像 41、
拉伸/切除 34、保存/导出 33、圆角/倒角 12、旋转 5。
