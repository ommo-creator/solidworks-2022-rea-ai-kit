# 可运行示例

五个脚本，从"能不能连上"一路走到"导出的图到底是不是空图"。
每个脚本都以**判据**结束，而不是以"没有报错"结束。

```bat
:: 前提：SolidWorks 2022 已运行、已打开一个零件或装配体
python scripts\preflight.py
python examples\01_connect.py
python examples\02_display_modes.py
python examples\03_display_mode_bands.py --out .\shots
python examples\04_section_and_export.py --out .\shots --hlr
python examples\05_readonly_audit.py --file "D:\models\demo.SLDASM"
```

| 脚本 | 验证什么 | 成功判据 |
|---|---|---|
| [`01_connect.py`](01_connect.py) | 通道是否可用 | 能打印 `RevisionNumber`（2022 SP5.0 → `30.5.0`）与已打开文档列表 |
| [`02_display_modes.py`](02_display_modes.py) | 显示模式怎么切才生效 | 写 `DisplayMode` 后回读**不变**（预期失败）；`RunCommand` 后回读**等于期望值** |
| [`03_display_mode_bands.py`](03_display_mode_bands.py) | 显示异常是模式问题还是渲染问题 | 各模式 `dark<128` 有明显差异；若全部为 0，说明导出链路坏了 |
| [`04_section_and_export.py`](04_section_and_export.py) | 剖切怎么建、导出怎么校验 | `CreateSectionView` 返回 `True`；导出图 `dark<128 ≥ 200` |
| [`05_readonly_audit.py`](05_readonly_audit.py) | 加载是否完整、品质是否够 | 组件全部参与、`suppressed/hidden = 0`、`rebuild_ok = True` |

---

## 依赖

| 层 | 需要 | 用途 |
|---|---|---|
| COM | `comtypes` | 连 SolidWorks（**唯一可用通道**） |
| 图像 | `Pillow`, `numpy` | 亮度统计、空帧校验 |
| 窗口 | `pywin32`（可选） | 把 SolidWorks 窗口恢复到前台；没有就手动点 |
| 环境 | `pywin32` 的 `pythoncom`（可选） | `scripts/preflight.py` 的宿主信息 |

```bat
pip install comtypes pillow numpy pywin32
```

---

## 三条纪律

1. **不保存文档。** 所有脚本只改视图状态。若标题出现 `*`（内存中已标脏），
   关闭时选「不保存」。
2. **不改系统选项。** 脚本里出现的都是视图级操作（显示模式、剖面视图、图像品质）。
   系统选项（背景色、抗锯齿、图形性能）请用界面改——理由见
   [`../troubleshooting/display-artifacts.md`](../troubleshooting/display-artifacts.md) 第 5 节。
3. **失败要报判据，不要只报异常。** 例如导出失败时报 `dark` 像素数，
   而不是只抛一个 `RuntimeError`。
