---
name: solidworks-2022-kit
description: "在 SolidWorks 2022（SP5.0 / 30.5.0.0049）上用 Python + comtypes 写或调试 COM 脚本时调用：通道选型、精确参数个数、119 条坑、44 条带判据的配方、剖视与线稿导出、大装配批量改型。它不教建模设计思路（那是 solidworks-design），也不含任何模型或图纸数据。"
metadata:
  category: engineering-cad
  version: 3.0.0
  verified_on: "SolidWorks Premium 2022 SP5.0 (30.5.0.0049), Windows x64; Python 3.13 + comtypes 1.4.17"
  evidence: "REA 逆向 Interop 元数据 + 官方 CHM 反编译 + swxJRNL 会话日志 + 端到端实跑"
---

# SolidWorks 2022 实测自动化

**这个技能只负责"让代码真的动起来"**：哪条通道能碰文档对象、每个特征方法到底几个实参、
哪些"返回成功"其实什么都没做。建模策略与设计审查走 [`../solidworks-design/`](../solidworks-design/SKILL.md)。

仓库根目录的 [`SKILL.md`](../../SKILL.md) 是本技能的完整版（同一份事实，压成 226 行）；
本文件是"怎么用"，不是"事实本体"。

---

## 0. 开工前三十秒

```bat
python scripts\preflight.py
```

问三个问题，任何一个答不上来就先解决它，不要开始写建模代码：

1. `RevisionNumber` 是不是 `30.5.0`？不是就**停下**——本仓库全部结论只对 2022 成立。
2. `comtypes.gen.SldWorks` 生成没有？没生成时枚举常量一律 `hasattr == False`。
3. 目标文件在哪、是零件还是装配、要不要出图？—— 判据取决于交付物。

---

## 1. 六条铁律（违反任何一条，后面全白做）

| # | 铁律 | 违反后的症状 |
|---|---|---|
| 1 | 单位**米 / 弧度**（唯一例外 `IPartDoc.GetPartBox()` 返回毫米） | 建出 1/1000 或 1000 倍的东西，判据还是"通过" |
| 2 | 文档对象方法**必须晚绑定**（Python comtypes / VBA / cscript） | PowerShell 一律 `0x8002000B DISP_E_BADINDEX`，且**注册 tlb 也修不好** |
| 3 | 新建零件用 `NewPart()`，**不要** `NewDocument(模板, ...)` | 模板路径差一点就建出"僵尸零件1"再报错 |
| 4 | 切除草图**画在被切的那个面上**（`SelectByRay` 先选面） | `FeatureCut4` 返回 `None`、不去料、特征数 +1 |
| 5 | 中文名**不可硬编码**（`草图1` ≠ `Sketch1`） | 换台机器或换语言包就崩 |
| 6 | **别信"没报错"**：每次建模后读体积/质量对账 | 空草图、空导出、空阵列，全都返回 `True` |

铁律 6 是本仓库存在的理由。**判据表**在 [`README.md`](../../README.md#已验证的关键数字用来判断到底建成了没有)：
`100×60×20` 板 = `1.2e-4 m³`，同板 + 1×D12 通孔 = `1.17738e-4 m³`，`D160×80` 圆柱 = `1.6084954e-3 m³`。

---

## 2. 查，不要猜

写任何一次性脚本之前，先花 30 秒查表，比试错快一个数量级：

| 要查什么 | 查哪里 |
|---|---|
| 这个特征方法几个实参、第几个是角度 | [`docs/02-signatures.md`](../../docs/02-signatures.md)；机读版 `data/features.json` |
| 枚举值（`swDocPART`、`swViewDisplayMode_*`） | `data/enums.json`（889 枚举 / 5,142 值） |
| 菜单命令号（`RunCommand`） | `data/commands.json`（2,164 条 → 菜单路径） |
| 官方参数语义 | `data/docs-index.json`（12,127 个方法页） |
| 这个坑踩过没有 | [`docs/03-pitfalls.md`](../../docs/03-pitfalls.md)（119 条），先搜症状关键字 |
| 有没有现成配方 | [`docs/04-recipes.md`](../../docs/04-recipes.md)（R1–R44，每条带判据） |

`SelectByRay` 11 参、`FeatureExtrusion2` 23 参、`FeatureCut4` 27 参、
`FeatureRevolve2` 20 参——**参数个数是硬约束**，少一个就是 `TypeError`，
多一个就是静默走偏。

---

## 3. 按任务找入口

| 你要做的事 | 先读 | 再读 |
|---|---|---|
| 基础零件、草图、拉伸切除、阵列 | [`docs/04-recipes.md`](../../docs/04-recipes.md) R1–R20 | `examples/` 里对应脚本 |
| 大装配批量插件 / 改位姿 / 删件 / 保存 | [`docs/19-assembly-scale.md`](../../docs/19-assembly-scale.md) | R38–R44 |
| 干涉检查 | [`docs/19-assembly-scale.md`](../../docs/19-assembly-scale.md) §19.7 | R42 |
| 剖视图（3D 剖切 / 工程图剖视 / 装配半剖） | [`docs/05-sections.md`](../../docs/05-sections.md) | R37、R43 |
| 纯线稿附图（单图单页、引线、图序） | [`docs/06-line-art-figures.md`](../../docs/06-line-art-figures.md) | R36 |
| 静默批处理（别弹对话框卡住脚本） | [`docs/07-silence.md`](../../docs/07-silence.md) | R30 附近配方 |
| 异型孔 / Toolbox 标准件 | [`docs/08-hole-wizard.md`](../../docs/08-hole-wizard.md)、[`docs/09-toolbox.md`](../../docs/09-toolbox.md) | —— |
| 导出图是空图 / 显示不对 | [`troubleshooting/display-artifacts.md`](../../troubleshooting/display-artifacts.md) | `docs/07` |
| 脚本在长循环里进程消失 | [`docs/19-assembly-scale.md`](../../docs/19-assembly-scale.md) §19.6 | 坑 111 |

---

## 4. 交付前的自检（缺一条就别报"完成"）

1. **数值判据**：体积/质量对理论解析值，偏差符号与量级都要能解释。
2. **文件判据**：导出文件字节数 > 0 且 > 阈值；重开一次读回体积，别只信 `SaveAs` 的返回值。
3. **像素判据**：`SaveBMP` 存的是当前视口前缓冲，最小化时会把空白帧存下来**并返回 `True`**
   → 统计 `min(luma) < 128` 的像素数，为 0 就是空图。
4. **两头查**：`zmin` 和 `zmax` 都要验，只查一头会漏掉"半件"。
5. **留痕**：把判据写进脚本输出（不是写进记忆），下一次复跑才能对比。

---

## 5. 版本闸门

- 只在 **2022 SP5.0 (30.5.0.0049)** 上验证过。
- **2023 / 2024 / 2025 / 2026 参数个数与枚举值都可能变**，不要直接搬。
  换版本时用 `data/docs-index.json` 重新核对签名，再复跑 `examples/`。
- 上游那套以 **2026** 为验收目标的工程化技能（会话管理、能力分级、MCP、子技能）
  见 [`../solidworks-automation/SKILL.md`](../solidworks-automation/SKILL.md)；
  两套的结论**不要混用**，冲突时以本技能（2022 实测）为准。

---

## 6. 边界

- **不含**任何模型、图纸、客户数据、件号规则、机器路径。`docs/` 里的数字都是演示几何的解析值。
- **不提供**绕过许可、破解或逆向二进制的方法；"逆向"指的是对公开 API 元数据
  （type library、随软件发布的帮助文件、软件自己的日志）做结构化整理。
- **不做**设计决策：该不该这样建模、公差怎么给、能不能加工，走
  [`../solidworks-design/`](../solidworks-design/SKILL.md)。
