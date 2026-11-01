# GUI 槽位对照：2,164 个 swCommands_e vs API 成员（严格版）

> `commands.json`（2,164 条，来自 swcommands.chm）+ `sw-api-index.json`（8,659 个去重成员名）。
> 打分：把命令名按驼峰切词，看**同一个** API 成员名里能容纳命令的几个词，得分 = 覆盖词数 / 命令词数。
> 得分低 ≠ 一定没有 API，只表示"名字上对不上"，需要人工确认。

## 覆盖度分布

| 得分 | 命令数 |
|---|---|
| 0.00 | 32 |
| 0.17 | 1 |
| 0.20 | 10 |
| 0.25 | 79 |
| 0.33 | 325 |
| 0.40 | 38 |
| 0.43 | 1 |
| 0.50 | 743 |
| 0.56 | 1 |
| 0.60 | 9 |
| 0.62 | 1 |
| 0.67 | 396 |
| 0.75 | 31 |
| 0.80 | 2 |
| 1.00 | 492 |

## 弱映射命令（得分 ≤ 0.34，共 447 条）

| 类别 | 数量 |
|---|---|
| 其他 | 408 |
| View | 10 |
| Edit | 8 |
| Tools | 5 |
| Insert | 4 |
| Annotation | 2 |
| Dimension | 2 |
| Mold | 1 |
| Feature | 1 |
| Weldment | 1 |
| Sketch | 1 |
| Help | 1 |

### 示例（每类最多 4 条）

**Annotation**
- `swCommands_AnnotationAlignLeft`（id=307）→ 词: annotation, align, left
- `swCommands_AnnotationAlignRight`（id=308）→ 词: annotation, align, right

**Custom**
- `swCommands_Customization_And_More`（id=1938）→ 词: customization, and, more

**Dimension**
- `swCommands_DimensionSpaceEvenly`（id=2973）→ 词: dimension, space, evenly
- `swCommands_Dimension_Driven_Toggle`（id=3025）→ 词: dimension, driven, toggle

**Edit**
- `swCommands_Edit_Csk_Pattern`（id=1392）→ 词: edit, csk, pattern
- `swCommands_Edit_Exit_No_Save`（id=1787）→ 词: edit, exit, save
- `swCommands_Edit_Swift_Schema`（id=2018）→ 词: edit, swift, schema
- `swCommands_Edit_Rtl_Mode`（id=2166）→ 词: edit, rtl, mode

**Feature**
- `swCommands_Featureworks`（id=438）→ 词: featureworks

**File**
- `swCommands_File_Copy_Design`（id=2295）→ 词: file, copy, design

**Help**
- `swCommands_Help_Autocad_Users`（id=1882）→ 词: help, autocad, users

**Insert**
- `swCommands_Insert_Light_Distantlight`（id=1295）→ 词: insert, light, distantlight
- `swCommands_Insert_Drw_Dxfdwg`（id=1849）→ 词: insert, drw, dxfdwg
- `swCommands_InsertSubdExtrude`（id=3328）→ 词: insert, subd, extrude
- `swCommands_InsertStudWiz`（id=3489）→ 词: insert, stud, wiz

**Mold**
- `swCommands_MoldflowxpressAnalysisWizard`（id=414）→ 词: moldflowxpress, analysis, wizard

**Ref**
- `swCommand_ReferenceArrow_PopUp`（id=3151）→ 词: command, reference, arrow, pop

**Sketch**
- `swCommands_SketchGroupRebuild`（id=555）→ 词: sketch, group, rebuild

**Tools**
- `swCommands_Tools_Drw_Dimtext_Link`（id=636）→ 词: tools, drw, dimtext, link
- `swCommands_Tools_Arrange_Components`（id=1254）→ 词: tools, arrange, components
- `swCommands_Tools_Crop_Edit`（id=1388）→ 词: tools, crop, edit
- `swCommands_Tools_Crop_Delete`（id=1389）→ 词: tools, crop, delete

**View**
- `swCommands_ViewAllAnnotations`（id=404）→ 词: view, all, annotations
- `swCommands_View3DSketchDimensions`（id=562）→ 词: view3, sketch, dimensions
- `swCommands_View_Assy_Opaque`（id=747）→ 词: view, assy, opaque
- `swCommands_View_Assy_Maintain`（id=749）→ 词: view, assy, maintain

**Weldment**
- `swCommands_Weldments`（id=508）→ 词: weldments

**其他**
- `swCommands_ClickHereToSeeThePreview`（id=5）→ 词: click, here, see, the, preview
- `swCommands_EnterTheOffsetOfTheSupportArea`（id=6）→ 词: enter, the, offset, the, support, area
- `swCommands_ExtrudedBossBase`（id=8）→ 词: extruded, boss, base
- `swCommands_RevolvedBossBase`（id=24）→ 词: revolved, boss, base
