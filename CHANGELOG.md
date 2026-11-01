# Changelog

版本号规则：`<验证的 SW 主版本>.<内容修订>`。`2022.x` 表示全部结论在 SolidWorks 2022 上实测。

## [2022.1.0] — 2026-11-01

首个公开版本。

### 新增 · 方法库

- `SKILL.md` —— AI 入口：通道矩阵、六条铁律、签名速查、坑清单压缩版、配方表
- `docs/01-channel-and-rules.md` —— 五条通道的实测结论（Python+comtypes 全通；
  PowerShell + Interop RCW 一律 `0x8002000B DISP_E_BADINDEX`）
- `docs/02-signatures.md` —— 精确签名：实参个数、`[out]` 位置、枚举值
- `docs/03-pitfalls.md` —— 完整坑清单（近 100 条），每条含现象 / 机制 / 判据
- `docs/04-recipes.md` —— 配方 R1–R36（建模 / 装配 / 工程图 / 剖视 / 导出）
- `docs/05-sections.md` —— 剖切：3D 剖切与 2D 工程图剖视两条路线
- `docs/06-line-art-figures.md` —— 纯线稿附图：A4 无图框、单图单页、编号引线、图序
- `docs/07-silence.md` —— 静默打开：25 个对话框抑制开关
- `docs/08-hole-wizard.md` / `docs/09-toolbox.md` —— 异型孔向导与 Toolbox 表库
- `docs/10-data-model.md` / `docs/11-feature-matrix.md` —— 对象模型与特征参数对照
- `docs/12-commands.md` —— `swCommands_e` 驱动 UI 级操作
- `docs/13-api-docs.md` / `docs/14-chm-decompile.md` / `docs/15-gui-map.md` ——
  官方文档检索、CHM 反编译、会话日志读法
- `docs/16-kernel.md` / `docs/17-motion.md` / `docs/18-ui-strings.md` ——
  内核容差、运动算例、中英文界面字符串

### 新增 · 机器可读索引（`data/`）

- `commands.json` —— **2,164 个** `swCommands_e` 命令号 → 菜单路径
- `docs-index.json` —— **12,127 个**官方方法页索引
- `examples-index.json` —— 官方示例索引（C#/VB/C++ 正文片段）
- `features.json` —— 19 行特征参数表
- `enums.json` —— **889 个 `swconst` 枚举 / 5,142 个数值**，另有 113 个枚举的
  2,599 个成员名（用于补齐"comtypes 里没有任何 `sw*` 常量"这个缺口）

### 新增 · 脚本（`scripts/`）

- `swe.py` —— 连接、选择、特征、剖视、导出、体积对账的一站式助手
- `extract_enums.py` —— 从反编译 CHM 重建 `data/enums.json`
- `preflight.py` —— 环境自检
- `gb9124_2019.py` —— GB/T 9124.1-2019 板式平焊法兰尺寸表（示例数据）

### 新增 · 可运行示例（`examples/`）

五个脚本，每个都带"怎么算成功"的判据：

1. `01_connect.py` —— 通道是否可用
2. `02_display_modes.py` —— **现场证明**写 `IModelView.DisplayMode` 无效、`RunCommand` 有效
3. `03_display_mode_bands.py` —— 五种模式 × 亮度分带统计（定位显示异常的主武器）
4. `04_section_and_export.py` —— 建剖切 + 导出 + **空帧校验**
5. `05_readonly_audit.py` —— 只读体检：加载 / 轻化 / 压缩 / 重建 / 图像品质

### 新增 · 故障诊断（`troubleshooting/`）

- `display-artifacts.md` —— 剖切/线稿显示异常的完整诊断记录：
  「断线 / 白块 / 多重轮廓」的根因是**用着色模式看剖切** +
  **文档图像品质 61** + **`SaveBMP` 读前缓冲**，与显卡、驱动、分辨率、模型几何无关。
  附五模式亮度分带判据表、排除清单（9 项）、最小修复步骤、可复用诊断顺序。

### 已验证的关键结论（首次发布即收录）

- `IModelView.DisplayMode` **写入无效**，显示模式必须走 `ISldWorks.RunCommand`（命令号见 `data/commands.json`）
- `SaveBMP` **读当前视口前缓冲**，窗口最小化时导出空白帧**且返回 `True`**
- `SelectionManager.GetSelectedObjectType3` 恒返回 `0`，不能用于判类型
- 装配对象必须**分层 QI**（`IAssemblyDoc` / `IModelDoc2` / `IFeature`）
- `CreateDefinition` / `GetOpenDocSpec` 返回无类型 `_Dispatch`，**必须先 QI**
- `ISectionViewData` 的属性必须用 setter 包装逐项写，直接赋值 → `0x80020006`

### 已知未验证（欢迎 PR）

- 「增强图形性能」/「使用软件 OpenGL」两条渲染路径的对照测试（需关文档 + 重启）
- SolidWorks 2023–2026 上的签名与枚举差异
- Windows 11 上的行为
