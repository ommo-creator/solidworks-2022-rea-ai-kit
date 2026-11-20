# Changelog

版本号规则：`<验证的 SW 主版本>.<内容修订>`。`2022.x` 表示全部结论在 SolidWorks 2022 上实测。

## [2022.2.0] — 2026-11-20

第二个版本：把一轮 **403 组件整机批量改型**（径向卡匣 A13 → A14 改型）中暴露的问题固化。
素材来自 11/7–11/12 的改模记录与模型审查（让位槽四次失败、72 实例位姿重写、配合求解把件甩飞、
保存"返回 True 但盘上不变"、干涉汇总句漏过真实互穿）。

### 新增 · 文档

- `docs/19-assembly-scale.md` —— **大装配批量改型**：`IMathTransform` 16 元素布局与读回复核、
  `AddComponent5` 三前提、`AddMate5` 只在活动文档生效与距离限位事故、批量删件通道对比、
  保存的证据链（字节数 + 重开 + 体积）、进程消失的三类 HRESULT 与 `swxJRNL.swj` 栈、
  全装配干涉读数、装配级半剖、复测纪律五条、症状速查表
- `docs/03-pitfalls.md` —— 追加 **坑 99–119**（共 21 条）：`SetAddToDB` 自动推断吸走孔位、
  `GetFaces`/`GetBodies2` 返回裸 `POINTER(IDispatch)`、`ISurface.IsPlane` 是属性、
  `CloseDoc` 少括号致文件被锁、`FeatureCut4` 的 `T1/T2=1` 是完全贯穿、偏移面 u/v 基向量、
  环带切除要画同轴两圆、`FeatureRevolve2` 的两类静默 `None`、单位四联表、
  残留草图导致服务器异常、长循环进程消失、`Select4` 不可靠、`Save()` 模态阻塞、
  `Transform2` 布局写错不报错
- `docs/04-recipes.md` —— 追加 **配方 R38–R44**：组件位姿、批量插入、批量删件、
  保存并校验、全装配干涉、装配级半剖、盲切让位槽

### 关键新增结论

- `IMathTransform` / `CreateTransform` 的 16 个 double：`[0..8]` 旋转、`[9..11]` 平移（**米**）、
  `[12]=1`、`[13..15]=0`；**必须传 `array('d', …)`**，`CreateTransform` 返回的 `_Dispatch` 要 QI。
  "行主序 / 列式"两种说法实为**读向**之争——写入后一律读回比对，位姿正确性再靠 `GetBox` 几何复核
- 变换矩阵**第一列不能反推方位**：同文件两个件读出 `112°+45k` / `114°+45k`，几何真值都是 `113°+45k`
- 旋转符号会反：对件加 `+2°` 实测变成 `−2°`，改 `−4°` 才到位 → 每类装配变换都要有一次符号标定
- 装配绕 Y 转 θ 后，件在世界的方位 = 件自身方位 `− θ`；72 个实例按目标方位重写 `Transform2` 后
  才是 72 个唯一位置、相邻 `gap = 5.00°`
- `AddMate5` 只在目标装配**是活动文档**时真正建配合（否则返回指针但 `ErrorStatus≠0`）；
  `0~4 mm` 的短行程加"距离限位"会让求解器把零件甩到 2.1~2.2 m 外，且**删配合不恢复原位置**
  → 短行程由几何（导向副 + 挡圈 + 装配高）保证，不用自动限位
- `IComponent2.Select4` 删件实测 `0/472`；`SelectByID2(名称,"COMPONENT",…)` + `EditDelete`
  才有效，第 8 参 `Callout` 必须 `None`，每批 25 件
- `Save()` 会弹「另存为」模态框永久阻塞 COM；`SaveAs` 在文件被占用时**返回 `True` 而盘上不变**
  → 保存判据必须是「字节数 + 重开 + 体积回读」
- 全装配干涉 403 组件 `2.7 s`；"主要干涉已清零"这类汇总句会漏掉真实互穿
  （实测漏过 `2.82e6 mm³ × 8 对`）→ 要按体积排序逐对看，并回答"重叠落在哪个面上"
- 细薄环形切除（0.11 mm 整周窄槽）用 `FeatureRevolve2` 恒返 `None`（同尺寸槽在简单件上可切）
  → 改成独立零件（节流套），不要硬凑
- 开审查前必须**冻结写入**：审查中途文件被改写（`03:58:47`），已测数据整批作废

### 修订

- `README.md` —— 仓库内容表补 `docs/19`；坑清单 119 条 / 配方 R1–R44 / 正文 19 篇
- `docs/03-pitfalls.md` —— 由 98 条扩到 119 条
- `docs/04-recipes.md` —— 由 R1–R36 扩到 R1–R44

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
