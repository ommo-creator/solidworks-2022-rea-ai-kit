# 基于 REA 逆向解包 · 适用于 AI 的 SolidWorks 2022 方法库

> **REA = Reverse Engineered API.** 这个仓库不是建模教程，而是一份把 SolidWorks 的 COM
> 接口**逐条实测**过之后的结构化事实库：哪个通道真能操作文档对象、每个特征方法到底要几个
> 参数、第几个是角度、哪些"看起来成功"其实什么都没做、剖切与线稿导出该怎么写。
>
> 目标读者是**写代码的 AI / 脚本作者**，不是点鼠标的人。表里每一行都对应一次真实运行结果，
> 不是从文档抄来的。

[![SolidWorks](https://img.shields.io/badge/SolidWorks-2022%20SP5.0%20(30.5.0.0049)-red)](#-版本适用范围)
[![Python](https://img.shields.io/badge/Python-3.13%20%2B%20comtypes%201.4.17-blue)](#快速开始)
[![Methods](https://img.shields.io/badge/indexed%20methods-12%2C127-informational)](#仓库内容)
[![Enums](https://img.shields.io/badge/swconst%20enums-889%20%2F%205%2C142%20values-informational)](#仓库内容)

---

## ⚠️ 版本适用范围

**本仓库全部结论只在 SolidWorks 2022 上实测验证过**，具体版本
`SolidWorks Premium 2022 SP5.0, RevisionNumber 30.5.0.0049, Windows x64`。

| 项目 | 结论 |
|---|---|
| 验证版本 | **SolidWorks 2022 SP5.0 (30.5.0.0049)** |
| 可能同样适用 | 2022 全系列（SP0–SP5），2019–2021 大部分方法签名相同但**未逐条验证** |
| 明确未验证 | 2023 / 2024 / 2025 / 2026 —— 方法参数个数与枚举值都可能变 |
| 操作系统 | Windows 10 x64 实测；Windows 11 未验证 |
| 脚本栈 | Python 3.13.14 + `comtypes` 1.4.17（3.10+ 理论上可用） |

**参数个数是硬约束。** 例如 `FeatureExtrusion2` 在 2022 上是 23 个实参，在别的版本上少一个
就是 `TypeError: call takes exactly N arguments` 或 VBA 的"参数数目不对"。升级主版本前，
请用 `data/docs-index.json` 重新核对目标版本的签名，不要直接搬。

---

## 这个仓库解决什么问题

写 SolidWorks 自动化的真实痛点**不是**"不知道 API 名字"，而是：

1. **通道选错，浪费几小时。** PowerShell 用 Interop RCW 能连上、能读 `RevisionNumber()`，
   一到 `doc.GetTitle()` 就 `0x8002000B DISP_E_BADINDEX` —— 这不是配置问题，是通道不对。
   → [`docs/01-channel-and-rules.md`](docs/01-channel-and-rules.md)
2. **参数个数靠猜。** 官方文档写的是声明，不是实参个数；`[out]` 参数会被 comtypes 摘掉，
   位置计数要重算。→ [`docs/02-signatures.md`](docs/02-signatures.md)
3. **"没报错"等于没做事。** `FeatureCut4` 返回 `None`、特征数还 +1，实际是一张空草图。
   → 所以本仓库所有配方都带**体积对账**判据。→ [`docs/04-recipes.md`](docs/04-recipes.md)
4. **枚举值在 Python 侧拿不到。** `comtypes.gen.SldWorks` 里 `hasattr(...,"swDocPART")` 为 `False`。
   → 本仓库把 `swconst` 的 889 个枚举抠成 `data/enums.json`。
5. **剖切/线稿导出"看着对、导出是空图"。** → [`troubleshooting/display-artifacts.md`](troubleshooting/display-artifacts.md)

---

## 仓库内容

| 路径 | 内容 | 规模 |
|---|---|---|
| [`SKILL.md`](SKILL.md) | **AI 入口**：通道矩阵、六条铁律、签名速查、坑清单压缩版、配方表 | 176 行 |
| [`docs/01-channel-and-rules.md`](docs/01-channel-and-rules.md) | 通道矩阵 + 六条铁律（哪条路能走，为什么） | — |
| [`docs/02-signatures.md`](docs/02-signatures.md) | 精确签名：实参个数、`[out]` 位置、枚举值 | — |
| [`docs/03-pitfalls.md`](docs/03-pitfalls.md) | **完整坑清单**（近 100 条），每条含现象、原因、判据 | 82 KB / 783 行 |
| [`docs/04-recipes.md`](docs/04-recipes.md) | 可直接抄的配方 R1–R36（建模/装配/工程图/剖视/导出） | 38 KB / 600 行 |
| [`docs/05-sections.md`](docs/05-sections.md) | 剖视图：3D 剖切与 2D 工程图剖视两条路 | — |
| [`docs/06-line-art-figures.md`](docs/06-line-art-figures.md) | 纯线稿附图：A4 无图框、单图单页、编号引线、图序 | — |
| [`docs/07-silence.md`](docs/07-silence.md) | 静默打开：25 个对话框抑制开关与 `Silent` 配方 | — |
| [`docs/08-hole-wizard.md`](docs/08-hole-wizard.md) | 异型孔向导：`HoleWizard5` vs `IWizardHoleFeatureData2` | — |
| [`docs/09-toolbox.md`](docs/09-toolbox.md) | Toolbox 表库：任意标准/任意孔的默认值从哪来 | — |
| [`docs/10-data-model.md`](docs/10-data-model.md) | COM 对象模型：分层 QI、哪些成员本版本不存在 | — |
| [`docs/11-feature-matrix.md`](docs/11-feature-matrix.md) | 13 个特征的参数对照表（方法/参数数/关键位/失败模式） | — |
| [`docs/12-commands.md`](docs/12-commands.md) | `swCommands_e` 用法：菜单命令号驱动 UI 级操作 | — |
| [`docs/13-api-docs.md`](docs/13-api-docs.md) | 官方 CHM 的 12,127 个方法页怎么查、怎么反编译 | — |
| [`docs/14-chm-decompile.md`](docs/14-chm-decompile.md) | CHM 反编译与会话日志（`swxJRNL.swj`）读法 | — |
| [`docs/15-gui-map.md`](docs/15-gui-map.md) | 菜单/对话框 → 对应 API 或命令号的映射 | — |
| [`docs/16-kernel.md`](docs/16-kernel.md) | 内核（Parasolid）相关：容差、无效几何、干涉 | — |
| [`docs/17-motion.md`](docs/17-motion.md) | 运动算例 COM 面（`IMotionStudy*`） | — |
| [`docs/18-ui-strings.md`](docs/18-ui-strings.md) | 中英文界面字符串差异（别硬编码 `草图1`） | — |
| [`data/commands.json`](data/commands.json) | **2,164 个命令号** → 菜单路径（`RunCommand` 用） | 543 KB |
| [`data/docs-index.json`](data/docs-index.json) | **12,127 个方法页**索引 | 6.8 MB |
| [`data/examples-index.json`](data/examples-index.json) | 官方示例索引（C#/VB/C++ 正文片段） | 5.2 MB |
| [`data/features.json`](data/features.json) | 19 行特征参数表（可机读） | 8 KB |
| [`data/enums.json`](data/enums.json) | **889 个 `swconst` 枚举 / 5,142 个数值** + 113 个枚举 2,599 个成员名 | 317 KB |
| [`scripts/swe.py`](scripts/swe.py) | 一站式助手：连接、选择、特征、剖视、导出、体积对账 | 26 KB / 617 行 |
| [`scripts/extract_enums.py`](scripts/extract_enums.py) | 从反编译 CHM 重建 `data/enums.json` | — |
| [`scripts/preflight.py`](scripts/preflight.py) | 环境自检（python / comtypes / comtypes.gen / 进程 / 模板） | — |
| [`scripts/gb9124_2019.py`](scripts/gb9124_2019.py) | GB/T 9124.1-2019 板式平焊法兰尺寸表（示例数据） | — |
| [`examples/`](examples/) | 5 个可独立运行的脚本，每个都带"怎么算成功"的判据 | — |
| [`troubleshooting/`](troubleshooting/) | **显示/剖切/线稿导出异常的真实诊断记录与方法** | — |

---

## 快速开始

### 0. 环境自检

```bat
python scripts\preflight.py
```

它会告诉你：Python 版本、`comtypes` 是否可用、`comtypes.gen.SldWorks` 是否已生成、
`SLDWORKS.exe` 是否在跑、默认模板目录在哪。

### 1. 连接（唯一正确的通道）

```python
import sys; sys.path.insert(0, r"<REPO_ROOT>\scripts")
import swe

sw = swe.connect(visible=True)      # 内部用 CreateObject 语义，不要用 GetActiveObject
print(sw.RevisionNumber)            # 2022 SP5.0 -> "30.5.0"
```

> PowerShell 只能读 `Application` 级成员，**不能**操作文档对象。详见
> [`docs/01-channel-and-rules.md`](docs/01-channel-and-rules.md)。

### 2. 切显示模式：用 `RunCommand`，不要写 `DisplayMode`

这是一个真实踩坑：`IModelView.DisplayMode` 在本版本上**写入无效**（回读永远不变），
必须走菜单命令号：

```python
sw.RunCommand(335, "")      # 335 = swCommands_HiddenLinesRemoved（隐藏线消除 / HLR）
```

| 命令号 | 模式 | `swViewDisplayMode_e` |
|---|---|---|
| 334 | 线架图 | 1 `Wireframe` |
| **335** | **隐藏线消除（线稿）** | 2 `HiddenLinesRemoved` |
| 336 | 隐藏线可见 | 3 `HiddenLinesGrayed` |
| 337 | 着色 | 4 `Shaded` |
| 506 | 带边线上色 | 5 `ShadedWithEdges` |

（枚举值来自 `data/enums.json`，与实测回读一致）

### 3. 建 3D 剖切

```python
import swe
svd = swe.P(md.ModelViewManager, "CreateSectionViewData")
swe.P(svd, "FirstPlane", plane_dispatch)     # 必须用 setter 包装，直接赋值会 0x80020006
swe.P(svd, "FirstOffset", 0.0)
swe.P(svd, "ShowSectionCap", False)
swe.P(svd, "GraphicsOnlySection", True)
swe.P(svd, "Redraw")
md.ModelViewManager.CreateSectionView(svd)   # -> True
```

### 4. 导出一张图 —— 并且确认它不是空图

```python
ok = md.SaveBMP(r"out.png", 2560, 1440)
```

> **`SaveBMP` 读的是当前视口前缓冲，不是离屏渲染器。** 窗口最小化时它会把上一帧（甚至空白帧）
> 存下来，而且**返回 `True`**。导出后必须统计像素：`min(luma) < 128` 的像素数为 0 就说明
> 抓到的是空图。详见 [`troubleshooting/display-artifacts.md`](troubleshooting/display-artifacts.md)。

---

## 为 AI 准备的三张表

这套东西真正对模型有用的地方，是把"猜"变成"查"：

```python
import json
enums = json.load(open("data/enums.json", encoding="utf-8"))
enums["enums"]["swViewDisplayMode_e"]["swViewDisplayMode_HiddenLinesRemoved"]   # -> 2

cmds = json.load(open("data/commands.json", encoding="utf-8"))
# 找出所有和剖面/线稿相关的命令号
[r for r in cmds if "Section" in r.get("name", "")][:5]

docs = json.load(open("data/docs-index.json", encoding="utf-8"))
docs["IFeatureManager~FeatureExtrusion2.html"]     # -> 参数名、类型、官方语义
```

`data/*.json` 里**只有 API 元数据**：方法名、命令号、枚举值、参数语义。
没有任何模型文件、图纸、客户数据或机器指纹。

---

## 已验证的关键数字（用来判断"到底建成了没有"）

| 场景 | 体积判据 |
|---|---|
| `100×60×20` 板 | `1.2e-4` m³ |
| 同上 + 1×D12 通孔 | `1.17738e-4` m³（单孔 `2.2619e-6`） |
| 同上 + 3 件线性阵列 | `1.132142e-4` m³ |
| `D160×80` 圆柱 | `1.6084954e-3` m³ |
| 6×D12 @R50 圆周阵列 | 去料 `5.42867e-5` m³ |
| 尺寸驱动 80 / 50 / 120 mm | `9.6e-5` / `6e-5` / `1.44e-4` m³ |

**每次建模后读一次体积并比对**，这是唯一可靠的"真的做了"判据。
`SelectionManager.GetSelectedObjectType3` 在本版本恒返回 `0`，不能拿来判选中类型。

---

## 目录结构

```
solidworks-2022-rea-ai-kit/
├── SKILL.md                    # AI 入口（先读这个）
├── README.md
├── docs/                       # 18 篇正文
├── data/                       # 4 个索引表 + 1 个枚举表
├── scripts/                    # swe.py / preflight.py / extract_enums.py / gb9124_2019.py
├── examples/                   # 5 个可独立运行的对照脚本
└── troubleshooting/            # 显示与导出异常诊断
```

---

## 数据来源与方法

本仓库的结论来自四条互补的证据路径，**没有任何一条是"读文档猜的"**：

1. **REA 逆向 Interop 元数据** —— 解析 `sldworks.tlb` / `SolidWorks.Interop.*.dll`，
   得到真实的类型、成员、枚举，而不是文档里可能过时的声明。
2. **官方 CHM 反编译** —— `sldworksapi.chm` → 17,170 个 HTML → 12,127 个方法页索引
   （`data/docs-index.json`）+ `swconst` 枚举页（`data/enums.json`）。
3. **`swxJRNL.swj` 会话日志** —— SolidWorks 自己记录的调用序列，能看到 GUI 操作**真实**调用了
   哪个方法、传了什么参数（这是"官方文档没写、但软件确实这么做"的唯一来源）。
4. **端到端实跑** —— 每条配方都在 2022 SP5.0 上跑过，并留下体积/耗时/像素级判据。

---

## 许可与边界

- **代码**（`scripts/`、`examples/`）：MIT，见 [`LICENSE`](LICENSE)。
- **文档**（`docs/`、`README.md`、`SKILL.md`）：CC BY 4.0。
- **`data/*.json`**：API 元数据的结构化整理（方法名、命令号、枚举名字与数值、
  参数语义摘要）。这些是事实性接口数据，**不含**任何 SolidWorks 二进制、源码、
  帮助文档正文，也不含任何模型、图纸、客户或机器数据。
- SolidWorks / eDrawings / SolidWorks API 是 **Dassault Systèmes SolidWorks Corporation**
  的商标与版权财产。本仓库与其无隶属关系，未获其背书。
- 仓库**不提供**任何绕过许可、破解或逆向 SolidWorks 二进制的内容；"逆向"指的是
  对**公开的 API 元数据**（type library、随软件发布的帮助文件、软件自己的日志）
  做结构化整理。

如果你所在的组织对"API 元数据再发布"有额外限制，请在使用前自行评估；
`data/enums.json` 可以用 `scripts/extract_enums.py` 从**你自己机器上**的 CHM 重新生成。

---

## 贡献

见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。最需要的贡献是**在新版本上复跑并报告差异**
（2023/2024/2025 的参数个数变化、枚举值变化）。

## 英文摘要

*An AI-oriented, empirically verified reference for the SolidWorks **2022** COM API
(SP5.0, 30.5.0.0049). Every claim in `docs/` was validated on a real 2022 install —
parameter counts, which channel can actually touch a `ModelDoc2`, the 100+ pitfalls
that make a script return "success" while doing nothing, and section-view / line-art
export recipes. Ships machine-readable indexes: 2,164 command ids, 12,127 method pages,
889 `swconst` enums (5,142 values) and a 19-feature parameter table.
Only API metadata is published — no CAD models, drawings, customer data or machine
fingerprints. SolidWorks is a trademark of Dassault Systèmes SolidWorks Corporation;
this project is not affiliated with or endorsed by them.*
