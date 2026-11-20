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
