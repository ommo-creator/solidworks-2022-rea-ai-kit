---
name: solidworks-automation-engineering
description: "要一套工程化的 SolidWorks 自动化骨架（单例复用会话、能力分级 capabilities.yaml、W-A-R 闭环断言、结果自审查、MCP 工具化、子技能路由）时调用。上游以 SolidWorks 2026 为验收目标，本仓库只在 2022 上验证过参数与坑，两套结论不要混用。"
metadata:
  category: engineering-cad
  version: 5.4.0
  upstream_target: "SolidWorks 2026"
  packaged_in: solidworks-2022-rea-ai-kit
---

# SolidWorks 自动化工程骨架

这个技能是**第三种东西**，别和另外两个搞混：

| 技能 | 给什么 | 版本 |
|---|---|---|
| [`../solidworks-2022-automation/`](../solidworks-2022-automation/SKILL.md) | 2022 上**实测过**的签名、坑、配方、判据 | 2022 SP5.0 |
| [`../solidworks-design/`](../solidworks-design/SKILL.md) | **怎么设计**：策略、参数化、可制造性 | 与版本无关 |
| **本技能** | **怎么组织一个自动化工程**：会话、能力分级、断言、审查、工具化 | 上游 2026 |

三者能串起来用，但**事实优先级**是：2022 实测 > 本技能手册 > 上游文档。

随附手册与 2022 实测有 **3 处正面冲突**（连接语义、`FeatureCut4` 可用性、`AddMate5` 实参个数），
逐条裁定见 [`../README.md`](../README.md) 的「已知冲突与裁定」。照手册抄之前先看那张表。

---

## 三条铁律（整套骨架就是为了兜这三条）

### 铁律 1 · 复用已有实例，但**别用错语义**

每次无脑 `Dispatch` 都可能在背后起一个新实例，脚本越跑越慢、窗口越开越多，
最后 COM 自己断开。

两条栈的规矩**不一样**，照抄会踩坑：

```python
# 栈 A：comtypes（本仓库 2022 实测路线）—— 用 CreateObject 语义
import comtypes.client
sw = comtypes.client.CreateObject("SldWorks.Application")   # ✅ SolidWorks 会复用已运行实例
# ❌ comtypes 的 GetActiveObject 在 SolidWorks 上常报 0x800401E3「操作不可用」（docs/01）

# 栈 B：pywin32（上游手册的路线）—— 先取已有，失败再新建
import win32com.client as w
try:
    sw = w.GetActiveObject("SldWorks.Application")
except Exception:
    sw = w.Dispatch("SldWorks.Application")
```

**以 [`../../docs/01-channel-and-rules.md`](../../docs/01-channel-and-rules.md) 为准**：
2022 实测走的是栈 A，`CreateObject` 语义本身就会复用运行中的实例，
不需要、也不该在 comtypes 里调 `GetActiveObject`。

### 铁律 2 · W-A-R 闭环：Write → Assert → Read

任何一次修改，都要走完三步：**写进去 → 强制重建 → 读回来比对**。
只做第一步的脚本，在 SolidWorks 上有很高概率"看起来成功"。

```python
before = read_signature(model)          # 修改前指纹
apply_change(model)                     # 执行修改
model.ForceRebuild3(False)              # 强制重建（pywin32 下可能是方法也可能是属性）
after = read_signature(model)           # 读回
assert after != before, "改了但没生效"   # 硬断言，不要用 print 提醒自己
```

### 铁律 3 · 反幻觉：不查证就不写调用

长参数 COM 方法（14、20、23、27 个实参那种）**凭记忆猜必错**，而且错了不报错。

```python
# ❌ 靠记忆
fm.FeatureExtrusion2(*args)            # 参数个数差一个就 TypeError，顺序错就建出别的东西

# ✅ 先探测可用成员与签名，再写
[name for name in dir(fm) if "Extrusion" in name]
# -> ['FeatureExtrusion2', 'FeatureExtrusion3', ...]  确认后再用
```

2022 上的精确参数个数直接查 [`../../docs/02-signatures.md`](../../docs/02-signatures.md)，
换版本就查 `data/docs-index.json`。

---

## 能力分级：`capabilities.yaml` 是唯一真源

上游用一张能力表管理"哪些能无人值守，哪些必须人看"，四级：

| 等级 | 含义 | 能不能无人值守交付 |
|---|---|---|
| `verified` | 真跑过、有判据 | 可以 |
| `pilot` | 跑通过，边界不明 | **不可以**，必须人工复核 |
| `reference_only` | 只有方法，没验证 | **不可以** |
| `not_implemented` | 明确没做 | 不是"暂不支持"，是"别试" |

本项目把同样的口径用在 [`../README.md`](../README.md) 的缺口清单里——那份表里的
`not_implemented`（钣金、焊件、Routing、FEA、2023+ 版本差异）**不是待办，是边界**。

---

## 标准的执行顺序

```text
1. 自检        python scripts/sw_preflight.py        # 依赖 / COM 注册 / 模板
2. 能力探测    python scripts/sw_capability_probe.py # 本版本到底有什么
3. 后端路由    python scripts/backend_router.py --list
4. 干活        SolidWorksSession() → 建模/装配/出图
5. 自查        ForceRebuild3 → ViewZoomtofit2 → run_review() → 读 *_review_report.json
6. 交付        文件字节数 + 重开读回 + SHA-256（跨机时）
```

第 5 步的判据是**报告内容**，不是"脚本没抛异常"：

```python
from sw_review import run_review
model.ForceRebuild3(False)
model.ViewZoomtofit2()
report, path = run_review(model, out_dir, basename="part",
                          expected_outputs=[part_path, step_path])
print(report["evaluation"]["status"], report["evaluation"]["issues"])
```

`run_review()` 会导出 isometric / front / top / right 四个视图 + `*_review_report.json`。
**"保存成功"不算完成**，这是本仓库和上游唯一完全一致的一条。

---

## 版本闸门（最容易出事的地方）

| 项目 | 本仓库（2022 实测） | 上游（2026 验收） |
|---|---|---|
| `FeatureExtrusion2` | **23 个实参** | 可能不同 |
| `FeatureCut4` | **27 个实参**，`T1=1` 才是完全贯穿 | 同族但需复核 |
| `AddMate5` | **14 参**，末位 `ErrorStatus` 是 [out] 被摘 | 同族 |
| 工程图 GD&T 落图 | 未验证 | 有工具链，`pilot` |
| Pack and Go | 未验证 | SW2026 SP01.1 三次通过（`pilot`） |

端着 2026 的脚本往 2022 上跑，**第一件会炸的事就是参数个数**。
反之亦然。跨版本时先跑 `examples/` 里的最小脚本，确认参数个数对得上，再搬业务逻辑。

---

## 随附手册

[`references/automation-manual.md`](references/automation-manual.md) 是一份自包含的实操手册
（Delancy 版，v5.4.0）：单例管理、W-A-R 断言、反幻觉熔断、草图与特征逐条写法、
装配与工程图、常见报错表。它的现场结论多在 SW 2024 附近采集，
**与本仓库 `docs/`（2022）冲突时以 `docs/` 为准**。

读法同设计手册：`rg` 定位章节，不要整本导入。

---

## 与上游代码的关系

上游 `solidworks-automation` 是独立项目（600+ 文件、12 MB 代码、自带 `LICENSE` / `pyproject.toml` /
`uv.lock` / `mcp-server/` / `subskills/`），验收目标是 **SolidWorks 2026**。

**它没有随本仓库分发**，理由见 [`../README.md`](../README.md) 的缺口清单：
整包塞进一个"2022 实测"仓库，会制造两套互相矛盾的事实来源，而且上游本来就有自己的发布渠道。

需要用时按上游自己的方式安装到 `~/.agents/skills/solidworks-automation/` 或
`~/.openclaw/skills/solidworks-automation/`，然后：

- 先 `python <SKILL_DIR>/scripts/sw_preflight.py`；
- 读 `capabilities.yaml` 确认你要做的那条路是不是 `verified`；
- 2022 上的具体签名/坑/判据，仍然回本仓库 `docs/` 查。

## 边界

- 不含任何模型、图纸、客户数据、机器路径。
- 不暴露"任意 Python/VBA 执行"这种能力；工具化只暴露已封装的原子操作。
- `pilot` / `reference_only` / `not_implemented` 一律不得宣称完成。
