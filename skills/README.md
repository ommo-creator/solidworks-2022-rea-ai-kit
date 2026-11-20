# skills/ — 可被 AI 直接加载的技能包

`docs/` 是**事实库**（2022 上逐条实测出来的签名、坑、配方）；`skills/` 是**入口**：
每个子目录是一份可被 agent 加载的 `SKILL.md`，告诉它在什么情况下按什么顺序做事、做到什么
算完成、什么时候必须停下来问人。

两者分离是刻意的：事实会长（119 条坑、44 条配方还在加），入口要短（每次对话都会被读进上下文）。

---

## 技能清单

| 技能 | 什么时候加载 | 验证等级 | 来源 |
|---|---|---|---|
| [`solidworks-2022-automation/`](solidworks-2022-automation/SKILL.md) | 要在 **SolidWorks 2022** 上写/跑 COM 脚本、改模、装配、出图、导出 | `verified` — 全部结论在本仓库 `docs/` 有实测出处 | 本仓库原创 |
| [`solidworks-design/`](solidworks-design/SKILL.md) | 还没写代码，先定建模策略、参数化结构、设计审查、可制造性检查 | `reference` — 方法论，不带版本结论 | 作者 Delancy（v2.7.0），随附 `references/design-manual.md` 全文 |
| [`solidworks-automation/`](solidworks-automation/SKILL.md) | 要一套工程化的 SW 自动化工程骨架（会话管理、能力分级、MCP、子技能、审查） | `pilot` — 上游以 **2026** 为验收目标，2022 上未逐项复跑 | 上游 wzyn 版 + Delancy 版（v5.4.0）手册，见该目录 `references/` |
| [`patent-agent-cn/`](patent-agent-cn/SKILL.md) | 要写专利申请文件、做代理师视角盲审、答复审查意见 | `pilot` — 提示词骨架经过实际盲审使用，但结论必须由执业代理师复核 | 本仓库原创 |

### 验证等级怎么读

沿用上游 `capabilities.yaml` 的口径，四级：

- **`verified`** — 在本仓库指名的版本上真跑过，有体积/像素/文件字节级判据。
- **`pilot`** — 跑通过一次或几次，但没系统复跑，边界条件不明 → 必须人工复核才能交付。
- **`reference`** — 只有方法论，不带"在本版本上成立"的承诺。
- **`not_implemented`** — 明确没做，别当成能做的。

**`pilot` 和 `reference` 不得作为无人值守交付**——这是上游和本仓库共同的口径，
因为"脚本跑完没报错"在 SolidWorks 上是出了名的不等于"事做了"。

---

## 缺口清单（看看什么没有）

这是"把现有技能全打包进来"时顺手盘出来的账。右边两列是真话，不是待办清单美化版：

| 能力 | 状态 | 说明 |
|---|---|---|
| 零件建模 / 草图 / 拉伸切除 / 阵列 | `verified` | `docs/04-recipes.md` R1–R44 |
| 大装配批量改型（位姿/配合/删件/保存/干涉） | `verified` | [`docs/19-assembly-scale.md`](../docs/19-assembly-scale.md) |
| 剖视图（3D 剖切 + 装配级半剖） | `verified` | [`docs/05-sections.md`](../docs/05-sections.md)，坑见 R37 |
| 纯线稿附图导出 | `verified` | [`docs/06-line-art-figures.md`](../docs/06-line-art-figures.md) |
| 静默批处理（25 个对话框开关） | `verified` | [`docs/07-silence.md`](../docs/07-silence.md) |
| 异型孔向导 / Toolbox 表库 | `pilot` | [`docs/08-hole-wizard.md`](../docs/08-hole-wizard.md)、[`docs/09-toolbox.md`](../docs/09-toolbox.md)，非默认规格未逐条验 |
| 运动算例（`IMotionStudy*`） | `pilot` | [`docs/17-motion.md`](../docs/17-motion.md)，只摸清 COM 面，未做结果审计 |
| **钣金 / 焊件** | `not_implemented` | 仓库里一个字都没有。要做就得从 `swconst` 与 CHM 重新实测 |
| **Routing（管路布线）** | `not_implemented` | 上游有 `routing_review.py`，但那是中性复核，不是原生写入 |
| **Simulation / FEA** | `not_implemented` | 上游走 CalculiX 外部求解器（`pilot`），与本仓库 2022 台账无关 |
| **GD&T、尺寸公差落图** | `not_implemented` | 上游有 `sw_gdt_copy.py` / `sw_tolerance_extract.py`（2026 版），本仓库未复跑 |
| **2023 / 2024 / 2025 / 2026 版本差异** | `not_implemented` | 参数个数会变，`FeatureExtrusion2` 在 2022 是 23 个实参，别的版本请用 `data/docs-index.json` 重新核对 |
| 专利撰写 / 盲审 / 答复 OA 的方法与提示词 | `pilot` | 本仓库新增，见 [`patent-agent-cn/`](patent-agent-cn/SKILL.md) |
| 专利检索、查新、FTO 分析 | `not_implemented` | 只有"审自己写的稿"，没有"查别人写的稿"；检索需要数据库访问，故意不打包 |

**上游 `solidworks-automation` 的 12 MB 代码没有随仓库分发。** 它是独立项目（自带
`LICENSE` / `pyproject.toml` / `uv.lock`），验收目标是 2026，把它整包塞进一个"2022 实测"
仓库会制造两种互相矛盾的事实来源。这里的做法是：只留入口与差异说明
（[`solidworks-automation/SKILL.md`](solidworks-automation/SKILL.md)），代码按需从上游安装。

---

## 已知冲突与裁定（**以 2022 实测为准**）

把外部手册一起打包，就必然带进它们的口径。逐条对过一遍之后，有 5 处和本仓库的 2022 实测
**正面冲突**。裁定只有一条原则：**`docs/` 是唯一事实源**；手册与上游的说法一律降级为"方法论参考"，
冲突时以 `docs/` 为准，并且下面写清为什么。

| # | 冲突点 | 外部手册 / 上游的说法 | 本仓库 2022 实测 | 裁定 |
|---|---|---|---|---|
| 1 | 怎么连上 SolidWorks | `GetActiveObject` **优先**，失败再 `Dispatch`（automation-manual Sec 20/25/39） | comtypes 栈用 **`CreateObject` 语义**；`GetActiveObject` 常报 `0x800401E3 操作不可用`（[`docs/01`](../docs/01-channel-and-rules.md)） | **分栈**：comtypes → `CreateObject`；pywin32 → `GetActiveObject` 失败再 `Dispatch`。两个栈的行为不能互推 |
| 2 | `FeatureCut4` 能不能在 Python 里用 | **不能**："参数 >12 的 IDispatch 调用全部返回 `None`，必须转 VBA 宏"，于是走"加法建模策略"（automation-manual M6 / Sec 36） | **能用**：27 实参在 Python + comtypes 下正常，孔、让位槽、装配级半剖全是 Python 跑的（[`docs/04`](../docs/04-recipes.md) R38–R44、[`docs/19`](../docs/19-assembly-scale.md) §19.8） | **以实测为准**。`FeatureCut4` 返回 `None` 的真因通常是：草图没画在**被切的那个面**上（铁律 4），或 `T1/T2` 误用 `1`（完全贯穿，坑 103）。"长参数必失败"是把调用错误归因给了 IDispatch |
| 3 | `AddMate5` 几个实参 | **15 个**（automation-manual Sec 2161） | **14 个**：末位 `ErrorStatus` 是 `[out]`，被 comtypes 摘掉（[`docs/02`](../docs/02-signatures.md)） | 不是版本差异，是**栈差异**：pywin32 保留 `byref` 出参 → 15；comtypes 摘掉 → 14。2022 实测用 14 |
| 4 | 基准面怎么选 | `SelectByID2("Front Plane", "PLANE", …)`、`"Top Plane"`（design-manual L115、L286） | **中文名不可硬编码**：`草图1` ≠ `Sketch1`，基准面名随语言包变（铁律 5、[`docs/18`](../docs/18-ui-strings.md)） | 英文名只对英文版成立。稳的写法是遍历特征树按 `GetTypeName2()` 找，或按双语兜底 |
| 5 | 版本基线 | 手册现场结论多在 **SW2024 / 2026**（`FeatureExtrusion2` 标题写 `(SW2024)`） | 全部 = **2022 SP5.0 (30.5.0.0049)** | 参数个数**跨版本会变**。搬之前用 `data/docs-index.json` 重新核对，并先跑 `examples/` 的最小脚本 |

### 两处"同名/同源"要留意

- 本仓库的 `skills/solidworks-design/` 与磁盘上已有的 `sw-designer` 技能**同源**
  （同一份 17 章手册）。**二选一安装**，否则两份会各自漂移，agent 不知道该信哪份。
- 仓库根 [`SKILL.md`](../SKILL.md) 的 frontmatter `name` 是 `sw-com-reversed`，
  与 `dsh-sw-reversed` 插件里那份快照**同名**。同装会撞名——插件那份是旧版
  （98 条坑 / R1–R36），**以仓库为准**。

---

## 安装 / 使用

两个位置 agent 都能加载，选一个：

```text
<AGENTS_SKILLS_DIR>/            # 例如 ~/.agents/skills/ 或 ~/.openclaw/skills/
├── solidworks-2022-automation/
├── solidworks-design/
├── solidworks-automation/
└── patent-agent-cn/
```

直接复制整个子目录即可，路径里没有写死任何绝对路径；技能内部对 `docs/`、`data/` 的引用
都是相对仓库根的，所以**也可以不安装**，让 agent 直接读仓库里的这两个文件：

```text
skills/<name>/SKILL.md     # 什么时候做什么
docs/                      # 做的时候查什么
```

---

## 数据边界（硬约束）

这几个技能**只包含方法**，不含任何一次真实工作的原始数据。具体到三类：

- **SolidWorks 侧**：没有 `.SLDPRT/.SLDASM/.SLDDRW`、没有体积台账、没有件号命名规则、
  没有客户图纸。`docs/` 里的数字是演示几何的解析值（`100×60×20` 板 = `1.2e-4 m³`）。
- **专利侧**：没有说明书正文、没有权利要求原文、没有审查意见通知书、没有案号、
  没有申请号、没有附图。提示词里一律用 `<CASE_DIR>`、`<DRAFT_PDF>`、`<FIGURE_LIST>`
  这样的占位符，用之前必须替换成你自己文件的位置。
- **机器侧**：没有用户名、绝对路径、机器名、IP。CI 会扫，见
  [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) 的泄漏检查一步。

技能里的提示词模板同理：它们是**怎么问**，不是**答案**。

---

## 遗留：插件里的文档快照已过期（决定：**暂不同步**）

`dsh-sw-reversed` 插件 `lib/data/` 里冻结的是本仓库的旧快照（`pitfalls.md` 84 KB = 98 条版、
`recipes.md` = R1–R36 版、`SKILL.md` 22 KB）。仓库现在已经是 119 条 / R1–R44 + `docs/19` + `skills/`。

**不把新内容回灌进插件**，理由三条：

1. 插件是**独立发布产物**，它的文档副本随插件打包，改了 `lib/data/` 不重打包也不会热更新，
   下一次装插件又被覆盖 —— 同步一次等于制造第三份会漂移的副本。
2. 插件内置的是 `swe.py` 的裁剪版（26 KB vs 仓库 26 KB 结构不同），文档与代码是配套的；
   只换文档会造出"文档说的 `swe.py` 里有、插件里没有"的错配。
3. 冲突已经用**名分**解决了：插件那份 frontmatter `name` 与仓库根 `SKILL.md` 同名
   （都是 `sw-com-reversed`），本文件上一节已写明"以仓库为准"。再复制一遍只是让两份更像，
   不会让任何一份更对。

要真同步，正确做法是**改插件的发布流程**（构建时从仓库拷 `docs/` + `SKILL.md` 并打版本号），
而不是手工覆盖 `lib/data/`。这件事记在这里，作为插件的待办，不是本仓库的待办。
