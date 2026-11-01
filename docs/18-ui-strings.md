# 中文界面词汇（实测，非扫描）

> 说明：直接扫 `slduiu.dll`（45,195,928 字节）的明文 UTF-16LE **不可行** —— 命中 40 万条但几乎全是噪声，
> 按「文件/编辑/视图/插入/工具」关键词过滤后只剩 15 条，该 DLL 的界面文本不以连续明文存放（压缩或资源化）。
> 下表全部来自**运行时实测**（建出来的文档里真实出现的名字），可直接用于 GUI 动作映射与断言。

## 文档与视图

| 场景 | 实测中文 |
| --- | --- |
| `INewPart` 新零件默认名 | `零件1`、`零件2`… |
| `INewAssembly` 新装配默认名 | `装配体4` |
| `INewDrawing(5/6)` 新图纸 | `工程图4 - 图纸1` |
| 图纸对象 | `图纸1`（`GetFirstView()` 返回的就是它，不是视图） |
| 自动生成的标准视图 | `工程图视图1`…`工程图视图4` |
| 中文视图名（可直接传 `CreateDrawViewFromModelView3`） | `*前视`、`*上视`、`*右视`、`*等轴测` |
| 三个基准面 | `前视基准面`、`上视基准面`、`右视基准面` |
| 原点 | `原点` |

## 特征默认名（`GetTypeName2()` 的英文类型在括号里）

| 特征 | 走 API 建出来后显示的名字 |
| --- | --- |
| 草图 | `草图1`…（类型 `ProfileFeature`） |
| 拉伸 | `凸台-拉伸1`（类型 `Extrusion`） |
| 切除 | `切除-拉伸1`（类型 `ICE`） |
| 旋转 | `旋转1`（类型名**未实测**） |
| 线性阵列 | `阵列(线性)1`（类型名**未实测**） |
| 圆周阵列 | `阵列(圆周)1`（类型 `CirPattern`，实测） |
| 装配组件 | `文件名-1`（类型 `Reference`） |
| 配合文件夹 | `配合`（类型 `MateGroup`） |

## 特征树里必须跳过的固定文件夹（中文名 → 英文类型）

`传感器`(SensorFolder)、`设计活页夹`(DocsFolder)、`注解`(DetailCabinet)、`Markups`(InkMarkupFolder)、
`光源、相机与布景`(EnvFolder)、`实体`(SolidBodyFolder)、`曲面实体`(SurfaceBodyFolder)、`备注`(CommentsFolder)、
`方程式`(EqnFolder)、`材质`(MaterialFolder)、`历史记录`、`收藏`、`选择集`（这三项中文名未逐一核实）、
`Tables`(ConfigTableFolder)、`原点`(OriginProfileFeature)、`RefPlane`×3。

## 教训

别写 `SelectByID2("Sketch1", ...)` —— 中文版里草图叫 `草图1`。可靠做法是遍历
`FirstFeature/GetNextFeature` 取 `GetTypeName2() == "ProfileFeature"` 再 `Select2(False, 0)`。