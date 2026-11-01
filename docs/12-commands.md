# swCommands_e 命令面（SolidWorks 2022 SP5 / v30.5.0）

从 `swcommands.chm` 反编译页抽出 **2164** 条命令，其中 **2154** 条带数值 ID。
命令 ID 可直接喂给 `ISldWorks.RunCommand(Int32 CommandID, Int32 NewTitle)`，这也是 `swcommands.chm` 之外唯一能批量驱动 UI 动作的入口（自动化里比点菜单可靠）。

## 分类统计

| 分类 | 条数 |
| --- | --- |
| 其他 | 1775 |
| Insert | 88 |
| View | 78 |
| Edit | 71 |
| Tools | 31 |
| Sketch | 21 |
| Component | 14 |
| Feature | 10 |
| Dimension | 10 |
| File | 6 |
| Annotation | 6 |
| Mate | 5 |
| Ref | 5 |
| Design | 4 |
| Drawing | 4 |
| Note | 3 |
| Display | 3 |
| Surface | 3 |
| Table | 3 |
| Help | 3 |
| Weldment | 3 |
| Custom | 3 |
| Simulation | 3 |
| Assembly | 2 |
| Model | 2 |
| Mold | 2 |
| Window | 2 |
| Equation | 1 |
| Selection | 1 |
| SheetMetal | 1 |
| Configuration | 1 |

> 全量表见 `data/commands.json`；每类此处只列前 60 条，按命令 ID 升序。

## 其他（1775 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 0 | `swCommands_Open` | Standard toolbar > Open |
| 1 | `swCommands_New` | Standard toolbar > New |
| 2 | `swCommands_Save` | Older version file |
| 3 | `swCommands_RebuildAndSaveConfigActive` | RMB menu > Rebuild/Save Mark > Add Mark for This Configuration |
| 4 | `swCommands_ShowCurvatureCombs` | Spline Tools toolbar > Show Curvature Combs |
| 5 | `swCommands_ClickHereToSeeThePreview` | View menu > Toolbars > Quick Snaps |
| 6 | `swCommands_EnterTheOffsetOfTheSupportArea` | View menu > Toolbars > Table |
| 7 | `swCommands_SmartFasteners` | Assembly toolbar > Smart Fasteners |
| 8 | `swCommands_ExtrudedBossBase` | Features toolbar > Extruded Boss/Base |
| 9 | `swCommands_Fillet` | Features toolbar > Fillet |
| 10 | `swCommands_ExtrudedCut` | Features toolbar > Extruded Cut |
| 11 | `swCommands_Chamfer` | Features toolbar > Chamfer |
| 12 | `swCommands_SimpleHole` | Sheet Metal toolbar > Simple Hole |
| 14 | `swCommands_Suppress` | Edit menu > Suppress > This Configuration |
| 15 | `swCommands_Unsuppress` | Edit menu > Unsuppress > This Configuration |
| 16 | `swCommands_Delete` | Standard toolbar > Delete |
| 17 | `swCommands_Rebuild` | Standard toolbar > Rebuild |
| 18 | `swCommands_LinearPattern` | Features toolbar > Linear Pattern |
| 19 | `swCommands_SaveAll` | Standard toolbar > Save |
| 20 | `swCommands_MoveComponent` | RMB menu > Move Component |
| 21 | `swCommands_RotateComponent` | Assembly toolbar > Rotate Component |
| 22 | `swCommands_Axis` | Features toolbar > Reference Geometry > Axis |
| 24 | `swCommands_RevolvedBossBase` | Features toolbar > Revolved Boss/Base |
| 25 | `swCommands_LoftedBossBase` | Features toolbar > Lofted Boss/Base |
| 27 | `swCommands_RelativeView` | Drawing toolbar > Relative View |
| 28 | `swCommands_ProjectedView` | Drawing toolbar > Projected View |
| 29 | `swCommands_RecordPauseMacro` | Macro toolbar > Record\Pause Macro |
| 30 | `swCommands_RunMacro` | Macro toolbar > Run Macro |
| 31 | `swCommands_StopMacro` | Macro toolbar > Stop Macro |
| 32 | `swCommands_Shell` | Features toolbar > Shell |
| 33 | `swCommands_AuxiliaryView` | Drawing toolbar > Auxiliary View |
| 35 | `swCommands_DetailView` | Drawing toolbar > Detail View |
| 37 | `swCommands_Balloon` | Annotations toolbar > Balloon |
| 38 | `swCommands_SmartDimension` | Dimensions/Relations toolbar > Smart Dimension |
| 39 | `swCommands_HoleWizard` | Insert menu > Assembly Feature > Hole > Wizard |
| 41 | `swCommands_GridSnap` | Quick Snaps toolbar > Grid Snap |
| 42 | `swCommands_Standard3View` | Drawing toolbar > Standard 3 View |
| 43 | `swCommands_Line` | Sketch toolbar > Line |
| 44 | `swCommands_CenterpointArc` | Sketch toolbar > Arcs > Centerpoint Arc |
| 46 | `swCommands_Circle` | Sketch toolbar > Circle |
| 47 | `swCommands_Spline` | Sketch toolbar > Spline |
| 48 | `swCommands_RevolvedCut` | Features toolbar > Revolved Cut |
| 49 | `swCommands_Centerline` | Sketch toolbar > Centerline |
| 50 | `swCommands_UnsuppressWithDependents` | Edit menu > Unsuppress with Dependents > This Configuration |
| 52 | `swCommands_AutomaticRelations` | Dimensions/Relations toolbar > Automatic Relations |
| 57 | `swCommands_ConvertEntities` | Sketch toolbar > Convert Entities |
| 58 | `swCommands_GeometricTolerance` | Annotation toolbar > Geometric Tolerance |
| 59 | `swCommands_TrimEntities` | Layout Tools toolbar > Trim Entities |
| 61 | `swCommands_MirrorEntities` | Layout Tools toolbar > Mirror Entities |
| 63 | `swCommands_ExtendEntities` | Sketch toolbar > Extend Entities |
| 64 | `swCommands_SweptBossBase` | Features toolbar > Swept Boss/Base |
| 65 | `swCommands_SweptCut` | Features toolbar > Swept Cut |
| 66 | `swCommands_HorizontalDimension` | Dimensions/Relations toolbar > Horizontal Dimension |
| 67 | `swCommands_HideShowAnnotations` | Annotation toolbar > Hide/Show Annotations |
| 68 | `swCommands_VerticalDimension` | Dimensions/Relations toolbar > Vertical Dimension |
| 69 | `swCommands_TangentArc` | Sketch toolbar > Tangent Arc |
| 71 | `swCommands_AddRelation` | Dimensions/Relations toolbar > Add Relation |
| 72 | `swCommands_Point` | Sketch toolbar > Point |
| 73 | `swCommands_CircularPattern` | Features toolbar > Circular Pattern |
| 74 | `swCommands_ProjectCurve` | Features toolbar > Curves > Project Curve |
| … | 另有 1715 条 | 见 `data/commands.json` |

## Insert（88 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 13 | `swCommands_InsertComponents` | Assembly toolbar > Insert Component |
| 23 | `swCommands_InsertPlane` | Features toolbar > Reference Geometry > Plane |
| 26 | `swCommands_InsertPart` | Features toolbar > Insert Part |
| 34 | `swCommands_InsertDrawingviewSection` | Drawing toolbar > SectionView |
| 40 | `swCommands_InsertFaceDraft` | Features toolbar > Draft |
| 105 | `swCommands_InsertOffsetRefSurface` | Mold Tools toolbar > Offset Surface |
| 111 | `swCommands_InsertPartingLine` | Feature toolbar > Curves > Split Line |
| 118 | `swCommands_InsertBends` | Sheet Metal toolbar > Insert Bends |
| 134 | `swCommands_InsertHyperlink` | Web toolbar > Insert Hyperlink |
| 140 | `swCommands_InsertSplinePoint` | Spline Tools toolbar > Insert Spline Point |
| 155 | `swCommands_InsertRefsurfaceRadiate` | Mold Tools toolbar > Radiate Surface |
| 156 | `swCommands_InsertRefsurfaceSew` | Mold Tools toolbar > Knit Surface |
| 168 | `swCommands_InsertPlanarSurface` | Mold Tools toolbar > Planar Surface |
| 322 | `swCommands_InsertFeatureBlend` | Mold Tools toolbar > Filled Surface |
| 350 | `swCommands_InsertScale` | Mold Tools toolbar > Scale |
| 397 | `swCommands_InsertSplitFeat` | Features toolbar > Split |
| 410 | `swCommands_InsertFamilyTable` | Tables toolbar > Design Table |
| 425 | `swCommands_InsertDetailCenterLine` | Annotation toolbar > Centerline |
| 448 | `swCommands_InsertRuledSurfaceFromEdge` | Mold Tools toolbar > Ruled Surface |
| 449 | `swCommands_InsertPartingPlane` | Mold Tools toolbar > Parting Surfaces |
| 455 | `swCommands_InsertRefpoint` | Reference Geometry toolbar > Point |
| 470 | `swCommands_InsertBlock` | Blocks toolbar > Insert Block |
| 538 | `swCommands_InsertFeatureMoveFace` | Features toolbar > Move Face |
| 546 | `swCommands_InsertMoldFolders` | Mold Tools toolbar > Insert Mold Folders |
| 611 | `swCommands_InsertSketchBelt` | Blocks toolbar > Belt/Chain |
| 616 | `swCommands_InsertBelt` | Blocks toolbar > Belt/Chain |
| 618 | `swCommands_InsertBoundarySurface` | Insert menu > Surface > Boundary Surface |
| 818 | `swCommands_Insert_Object` | Insert menu > Object |
| 845 | `swCommands_Insert_Cthread_Callout` | RMB menu > Insert Callout |
| 857 | `swCommands_Insert_Sheet` | Insert menu > Sheet |
| 909 | `swCommands_Insert_Refdim` | valid for drawings, activates the dimensioning cursor; after calling this command, select one or two edges/v… |
| 924 | `swCommands_Insert_Sectionline` | Insert menu > Make Section Line |
| 988 | `swCommands_Insert_Mirrored_Part` | Insert menu > Mirror Part |
| 1024 | `swCommands_Insert_Weld` | valid for assemblies, opens the Weld Bead Type dialog |
| 1044 | `swCommands_Insert_Target_Point` | valid for a selected drawing view, activates the point cursor; after calling this command, select the locati… |
| 1131 | `swCommands_Insert_Picture` | Insert > Picture |
| 1139 | `swCommands_Insert_Zone` | valid for assemblies, opens an Open dialog with which to select the component to insert as an envelope feature |
| 1208 | `swCommands_Insert_Custom_Symbol_Save` | RMB menu > Save to File |
| 1212 | `swCommands_Insert_Ref_Line` | opens a Reference Line dialog |
| 1222 | `swCommands_Insert_Route_Point` | Routing Tools toolbar > Route Point |
| 1223 | `swCommands_Insert_Connection_Point` | Routing toolbar > Connection Point |
| 1244 | `swCommands_Insert_Ff_View_3rd` | RMB menu > Insert From File |
| 1293 | `swCommands_Insert_Light_Pointlight` | Scene, Lights, and Cameras > SOLIDWORKS Lights RMB menu > Add Point Light |
| 1294 | `swCommands_Insert_Light_Spotlight` | Scene, Lights, and Cameras > SOLIDWORKS Lights RMB menu > Add Spot Light |
| 1295 | `swCommands_Insert_Light_Distantlight` | Scene, Lights, and Cameras > SOLIDWORKS Lights RMB menu > Add Directional Light |
| 1325 | `swCommands_Insert_Form_Assembly` | Insert menu > Component > Assembly from [Selected] Components |
| 1408 | `swCommands_Insert_Sketch_Import` | Insert menu > Sketch from Drawing |
| 1442 | `swCommands_Insert_Bendtable_Open` | Insert menu > Bend Table > From File |
| 1443 | `swCommands_Insert_Bendtable_New` | Insert menu > Bend Table > New |
| 1632 | `swCommands_Insert_Schematic` | Insert menu > Schematic |
| 1638 | `swCommands_Insert_Mirror_Subassembly` | Assembly toolbar > Mirror Components |
| 1829 | `swCommands_Insert_Folder` | RMB menu > Add to New Folder |
| 1833 | `swCommands_Insert_Sketch_Dxfdwg` | Insert menu > DXF/DWG |
| 1849 | `swCommands_Insert_Drw_Dxfdwg` | Insert menu > DXF/DWG |
| 1878 | `swCommands_Insert_Geometry_Import` | Features toolbar > Imported Geometry |
| 1974 | `swCommands_Insert_Create_Assy_Feat` | Cut list or Solid bodies folder RMB menu > Save Bodies; |
| 2175 | `swCommands_Insert_Cut_Net` | Features toolbar > Boundary Cut |
| 2176 | `swCommands_Insert_Stock_Net` | Features toolbar > Boundary Boss/Base |
| 2191 | `swCommands_Insert_Camera` | Scene, Lights, and Cameras > Camera RMB menu > Add Camera |
| 2220 | `swCommands_Insert_Smart_Features` | RMB menu > Insert Smart Feature |
| … | 另有 28 条 | 见 `data/commands.json` |

## View（78 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 99 | `swCommands_ViewTemporaryAxes` | View toolbar > View Temporary Axes |
| 126 | `swCommands_ViewOrigins` | View toolbar > View Origins |
| 153 | `swCommands_ViewCoordinateSystems` | View toolbar > View Coordinate Systems |
| 338 | `swCommands_ViewPlanes` | View toolbar > View Planes |
| 339 | `swCommands_ViewAxes` | View toolbar > View Axes |
| 341 | `swCommands_ViewOrientation` | Press SPACEBAR |
| 402 | `swCommands_ViewCurves` | View toolbar > View Curves |
| 403 | `swCommands_ViewSketches` | View toolbar > View Sketches |
| 404 | `swCommands_ViewAllAnnotations` | View toolbar > View All Annotations |
| 440 | `swCommands_ViewSketchRelations` | View toolbar > View Sketch Relations |
| 498 | `swCommands_View` | View menu > Toolbars > View |
| 510 | `swCommands_ViewRoutingPoints` | View toolbar > View Routing Points |
| 511 | `swCommands_ViewPoints` | View toolbar > View Points |
| 547 | `swCommands_ViewPartingLines` | View toolbar > View Parting Lines |
| 561 | `swCommands_View3DSketchPlane` | View toolbar > View 3D Sketch Plane |
| 562 | `swCommands_View3DSketchDimensions` | View toolbar > View Sketch Dimensions |
| 607 | `swCommands_ViewLights` | View toolbar > View Lights |
| 608 | `swCommands_ViewCameras` | View toolbar > View Cameras |
| 747 | `swCommands_View_Assy_Opaque` | RMB menu > Assembly Transparency > Opaque |
| 748 | `swCommands_View_Assy_Full` | RMB menu > Assembly Transparency > Force Transparency |
| 749 | `swCommands_View_Assy_Maintain` | RMB menu > Assembly Transparency > Maintain Transparency |
| 875 | `swCommands_View_Hide_Behind_Plane` | RMB menu > Hide Behind Plane |
| 891 | `swCommands_View_Query_Select` | RMB menu > Select Other |
| 897 | `swCommands_View_Sheet_Previous` | View menu > Previous Sheet |
| 898 | `swCommands_View_Sheet_Next` | View menu > Next Sheet |
| 916 | `swCommands_View_Orientation_Rmb` | RMB menu > View Orientation |
| 993 | `swCommands_View_Explode_Assembly` | RMB menu > Explode |
| 995 | `swCommands_View_Collapse_Assembly` | RMB menu > Collapse |
| 1030 | `swCommands_View_Fm_By_Feat` | View menu > User Interface > FeatureManager Tree > By Features |
| 1031 | `swCommands_View_Fm_By_Dep` | View menu > User Interface > FeatureManager Tree > By Dependencies |
| 1043 | `swCommands_View_Edit_Perspective` | View menu > Modify > Perspective |
| 1060 | `swCommands_View_This_Camera` | RMB menu > Camera View |
| 1061 | `swCommands_View_Lock_Camera` | > RMB menu > Lock Camera |
| 1303 | `swCommands_View_Ruler` | View menu > User Interface > Rulers |
| 1390 | `swCommands_View_Hideshow` | View menu > Hide / Show > Bodies |
| 1468 | `swCommands_View_Rotateplusy` | Press RIGHT ARROW |
| 1469 | `swCommands_View_Rotateminusy` | Press LEFT ARROW |
| 1470 | `swCommands_View_Rotateplusz` | Press Alt-RIGHT ARROW |
| 1471 | `swCommands_View_Rotateminusz` | Press Alt-LEFT ARROW |
| 1472 | `swCommands_View_Rotateminusx` | Press DOWN ARROW |
| 1473 | `swCommands_View_Rotateplusx` | Press UP ARROW |
| 1474 | `swCommands_View_Rotx_Minusninety` | Press Shift-DOWN ARROW |
| 1475 | `swCommands_View_Rotx_Plusninety` | Press Shift-UP ARROW |
| 1476 | `swCommands_View_Roty_Minusninety` | Press Shift-LEFT ARROW |
| 1477 | `swCommands_View_Roty_Plusninety` | Press Shift-RIGHT ARROW |
| 1478 | `swCommands_View_Transplusx` | Press Ctrl-RIGHT ARROW |
| 1479 | `swCommands_View_Transminusx` | Press Ctrl-LEFT ARROW |
| 1480 | `swCommands_View_Transplusy` | Press Ctrl-DOWN ARROW |
| 1481 | `swCommands_View_Transminusy` | Press Ctrl-UP ARROW |
| 1482 | `swCommands_View_Zoomin` | Press Shift-Z |
| 1483 | `swCommands_View_Zoomout` | Press Z |
| 1541 | `swCommands_View_Clear_Select` | valid in many contexts; pop-up menu item "Clear Selections" |
| 1584 | `swCommands_View_Undo_Last` | View menu > Modify > Previous View |
| 1640 | `swCommands_View_Normal_To` | RMB menu > Normal To |
| 1803 | `swCommands_View_Zoom_About_Center` | View menu > Modify > Zoom About Screen Center |
| 1810 | `swCommands_View_Disp_Hideall` | View menu > Hide / Show > Hide All Types |
| 1895 | `swCommands_View_Showantn_Linkerrors` | View menu > Hide / Show > Annotation Link Errors |
| 1982 | `swCommands_View_Animate_Explode_Assembly` | RMB menu > Animate explode |
| 1983 | `swCommands_View_Animate_Collapse_Assembly` | RMB menu > Animate collapse |
| 1993 | `swCommands_View_Move_Manipulator` | RMB menu > Move with Triad |
| … | 另有 18 条 | 见 `data/commands.json` |

## Edit（71 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 84 | `swCommands_EditMacro` | Macro toolbar > Edit Macro |
| 119 | `swCommands_EditComponent` | Assembly toolbar > Edit Component |
| 170 | `swCommands_EditColor` | View toolbar > Edit Sketch or Curve Color |
| 471 | `swCommands_EditBlock` | Blocks toolbar > Edit Block |
| 501 | `swCommands_EditMaterial` | Standard toolbar > Edit Material |
| 623 | `swCommands_EditFeature` | Tables folder > Design Table RMB menu > Edit Feature |
| 655 | `swCommands_Edit_Def_Assy` | Smart Feature folder > RMB menu > Edit in Defining Assembly |
| 813 | `swCommands_Edit_Undolist` | Standard toolbar > Undo |
| 815 | `swCommands_Edit_Rollback` | Edit menu > Rollback |
| 831 | `swCommands_Edit_Dragitem` | RMB menu > Edit Definition |
| 859 | `swCommands_Edit_Sketch` | RMB context toolbar > Edit Sketch |
| 863 | `swCommands_Edit_Sketchplane` | RMB context toolbar > Edit Sketch Plane |
| 866 | `swCommands_Edit_Familytable` | Tables folder > Design Table RMB menu > Edit Table |
| 867 | `swCommands_Edit_Familytable_Open` | Tables folder > Design Table RMB menu > Edit Table in New Window |
| 868 | `swCommands_Edit_Incontext` | RMB menu > Edit in Context |
| 965 | `swCommands_Edit_Part` | Assembly toolbar > Edit Component |
| 967 | `swCommands_Edit_Assembly` | Assembly toolbar > Edit Component |
| 1129 | `swCommands_Edit_Vsection` | View menu > Modify > Section View |
| 1242 | `swCommands_Edit_Seed_Feature` | RMB menu > Edit Seed Feature |
| 1324 | `swCommands_Edit_Dissolve_Assembly` | Edit menu > Dissolve Assembly |
| 1391 | `swCommands_Edit_Lsk_Pattern` | RMB menu > Edit Linear Pattern |
| 1392 | `swCommands_Edit_Csk_Pattern` | RMB menu > Edit Circular Pattern |
| 1398 | `swCommands_Edit_Polygon` | RMB menu > Edit polygon |
| 1417 | `swCommands_Edit_Suppress_All_Configs` | Edit menu > Suppress > All Configurations |
| 1419 | `swCommands_Edit_Suppress_Select_Configs` | Edit menu > Suppress > Specified Configurations |
| 1421 | `swCommands_Edit_Unsuppress_All_Configs` | Edit menu > Unsuppress > All Configurations |
| 1422 | `swCommands_Edit_Unsuppress_Select_Configs` | Edit menu > Unsuppress > Specified Configurations |
| 1424 | `swCommands_Edit_Unsuppress_Dependent_All_Configs` | Edit menu > Unsuppress with Dependents > All Configurations |
| 1425 | `swCommands_Edit_Unsuppress_Dependent_Select_Configs` | Edit menu > Unsuppress with Dependents > Specified Configurations |
| 1456 | `swCommands_Edit_Redolist` | Standard toolbar > Redo |
| 1501 | `swCommands_Edit_Template` | Sheet Format toolbar > Edit Sheet Format |
| 1502 | `swCommands_Edit_Sheet` | RMB menu > Edit Sheet |
| 1507 | `swCommands_Edit_Ordinate` | RMB Menu > Add to Ordinate |
| 1530 | `swCommands_Edit_Drawview_Sketch` | RMB menu > Edit Sketch |
| 1578 | `swCommands_Edit_Equation` | RMB menu > Edit Equation |
| 1583 | `swCommands_Edit_Importfolder` | RMB menu > Edit import folder |
| 1588 | `swCommands_Edit_Findinfm` | RMB menu > Go To |
| 1678 | `swCommands_Edit_Broken_Out_Section` | RMB menu > Edit Definition |
| 1741 | `swCommands_Edit_Cavity_Part` | RMB menu > Edit Cavity Part |
| 1787 | `swCommands_Edit_Exit_No_Save` | Edit menu > Exit Sketch without Saving Changes |
| 1811 | `swCommands_Edit_Text` | RMB menu > Edit Text |
| 1816 | `swCommands_Edit_Sk_Pattern` | RMB menu > Edit Pattern |
| 1856 | `swCommands_Edit_Smart_Insert` | RMB menu > Edit Smart Insert |
| 1907 | `swCommands_Edit_Delete_Replay` | RMB menu > Delete Replay |
| 2018 | `swCommands_Edit_Swift_Schema` | RMB menu > Properties |
| 2068 | `swCommands_Edit_Paragraph` | Formatting toolbar > Paragraph Properties |
| 2071 | `swCommands_Edit_Comment` | RMB menu > Edit Comment |
| 2166 | `swCommands_Edit_Rtl_Mode` | Text editor popup menu > Right to left reading order |
| 2207 | `swCommands_Edit_Decal` | Render Tools toolbar > Edit Decal |
| 2221 | `swCommands_Edit_Smart_Comp_Inst` | RMB menu > Edit Feature |
| 2234 | `swCommands_Edit_Annotation_View` | RMB menu > Edit Annotation View |
| 2256 | `swCommands_Edit_Pipe_Rt` | Piping toolbar > Edit Route |
| 2260 | `swCommands_Edit_Flex_Tube_Rt` | Flexible Tubing toolbar > Edit Route |
| 2360 | `swCommands_Edit_Weldment_Props` | Weldment RMB menu > Properties |
| 2390 | `swCommands_Edit_Folder_Feat` | Mates folder RMB menu > Edit Features |
| 2463 | `swCommands_Edit_Smart_Fastener` | RMB menu > Edit Smart Fastener |
| 2498 | `swCommands_Edit_Suppress_Feature` | RMB menu > Suppress |
| 2499 | `swCommands_Edit_Unsuppress_Feature` | RMB menu > Unsuppress |
| 2502 | `swCommands_Edit_Rolltoprevious` | Edit menu > Roll to Previous |
| 2503 | `swCommands_Edit_Rolltoend` | Edit menu > Roll to End |
| … | 另有 11 条 | 见 `data/commands.json` |

## Tools（31 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 636 | `swCommands_Tools_Drw_Dimtext_Link` | RMB menu > Link external dim text |
| 889 | `swCommands_Tools_Align_Horz` | Tools > Align Drawing View > Horizontal Edge |
| 890 | `swCommands_Tools_Align_Vert` | Tools > Align Drawing View > Vertical Edge |
| 945 | `swCommands_Tools_Dim_Pref` | RMB menu > Document Properties |
| 973 | `swCommands_Tools_Configuration` | valid for parts and assemblies, opens the SOLIDWORKS ConfigurationManager dialog |
| 979 | `swCommands_Tools_Hide_Dv` | View menu > Hide / Show > Hidden Views |
| 1073 | `swCommands_Tools_Addins` | Tools menu > Add-Ins |
| 1077 | `swCommands_Tools_Show_Tan` | View menu > Display > Tangent Edges Visible |
| 1078 | `swCommands_Tools_Font_Tan` | View menu > Display > Tangent Edges as Phantom |
| 1079 | `swCommands_Tools_Remove_Tan` | View menu > Display > Tangent Edges Removed |
| 1137 | `swCommands_Tools_Customize` | Tools menu > Customize |
| 1245 | `swCommands_Tools_Addview_Ff` | RMB menu > Insert From File |
| 1254 | `swCommands_Tools_Arrange_Components` | Tools menu > Reorganize Components |
| 1388 | `swCommands_Tools_Crop_Edit` | RMB menu > Crop View > Edit Crop |
| 1389 | `swCommands_Tools_Crop_Delete` | RMB menu > Crop View > Remove Crop |
| 1515 | `swCommands_Tools_Remove_Tangent_Edges` | View menu > Display > Tangent Edges Removed |
| 1545 | `swCommands_Tools_Show_Tangent_Edges` | View menu > Display > Tangent Edges Visible |
| 1546 | `swCommands_Tools_Font_Tangent_Edges` | View menu > Display > Tangent Edges With Font |
| 1573 | `swCommands_Tools_Drw_Autoregen` | RMB menu > Automatic view update |
| 2376 | `swCommands_Tools_Macro_Mru_1` | Tools menu > Macro > |
| 2377 | `swCommands_Tools_Macro_Mru_2` | Tools menu > Macro > |
| 2378 | `swCommands_Tools_Macro_Mru_3` | Tools menu > Macro > |
| 2379 | `swCommands_Tools_Macro_Mru_4` | Tools menu > Macro > |
| 2380 | `swCommands_Tools_Macro_Mru_5` | Tools menu > Macro > |
| 2381 | `swCommands_Tools_Macro_Mru_6` | Tools menu > Macro > |
| 2382 | `swCommands_Tools_Macro_Mru_7` | Tools menu > Macro > |
| 2383 | `swCommands_Tools_Macro_Mru_8` | Tools menu > Macro > |
| 2384 | `swCommands_Tools_Macro_Mru_9` | Tools menu > Macro > |
| 2791 | `swCommands_ToolsGrid` | Sketch toolbar > Grid/Snap |
| 2892 | `swCommands_ToolsSensor` | Tools toolbar > Sensor |
| — | `swCommands_Tools` | View menu > Toolbars > Tools |

## Sketch（21 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 45 | `swCommands_Sketch` | Sketch toolbar > Sketch |
| 62 | `swCommands_SketchFillet` | Sketch toolbar > Sketch Fillet |
| 304 | `swCommands_SketchDrivenPattern` | Features toolbar > Sketch Driven Pattern |
| 323 | `swCommands_SketchedBend` | Sheet Metal toolbar > Sketched Bend |
| 358 | `swCommands_SketchChamfer` | Sketch toolbar > Sketch Chamfer |
| 368 | `swCommands_SketchPicture` | Sketch toolbar > Sketch Picture |
| 489 | `swCommands_SketchToolbar` | View menu > Toolbars > Sketch |
| 555 | `swCommands_SketchGroupRebuild` | Blocks toolbar > Rebuild |
| 617 | `swCommands_SketchCreateChain` | RMB menu > Make Path |
| 1547 | `swCommands_Sketch_Detach` | Sketch toolbar > Detach Segment On Drag |
| 1817 | `swCommands_Sketch_Jog_Flip` | RMB menu > Flip Direction |
| 1936 | `swCommands_Sketch_Suppress_Constraints` | RMB menu > Toggle Suppression |
| 2681 | `swCommands_Sketchplane_Delete` | RMB menu > Delete |
| 2682 | `swCommands_Sketchplane_Deleteall` | RMB menu > Delete all |
| 2683 | `swCommands_Sketchplane_Rename` | RMB menu > Rename |
| 2727 | `swCommands_Sketch_Align_Grid_Origin` | Tools > Sketch Tools > Align > Align Grid/Origin |
| 2864 | `swCommands_SketchSlot_Line` | Sketch toolbar > Straight Slot |
| 2865 | `swCommands_SketchSlot_Line_Center` | Sketch toolbar > Centerpoint Straight Slot |
| 2866 | `swCommands_SketchSlot_Arc3P` | Sketch toolbar > 3 Point Arc Slot |
| 2867 | `swCommands_SketchSlot_Arc_Center` | Sketch toolbar > Centerpoint Arc Slot |
| 3399 | `swCommands_SketchSlicing` | Sketch toolbar > Slicing |

## Component（14 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 653 | `swCommands_Component_Color` | Edit menu > Appearance > Sketch/Curve Color |
| 654 | `swCommands_Component_Texture` | valid for a selected component in an assembly, opens the Texture PropertyManager page |
| 864 | `swCommands_Component_Properties` | RMB menu > Component Line Font |
| 1016 | `swCommands_Component_Pattern` | Insert menu > Component Pattern submenu |
| 1527 | `swCommands_Component_Reload` | RMB menu > Reload |
| 1941 | `swCommands_Component_Pattern_Linear` | Assembly toolbar > Linear Component Pattern |
| 1942 | `swCommands_Component_Pattern_Circular` | Assembly toolbar > Circular Component Pattern |
| 1943 | `swCommands_Component_Pattern_Feature` | Assembly toolbar > Pattern Driven Component Pattern |
| 2561 | `swCommands_Component_Display` | RMB menu > Component Display submenu |
| 2898 | `swCommands_Component_RV_Appearance` | RMB context toolbar > Appearances > |
| 3108 | `swCommands_Component_Pattern_Sketch` | Assembly toolbar > Sketch Driven Component Pattern |
| 3109 | `swCommands_Component_Pattern_Curve` | Assembly toolbar > Curve Driven Component Pattern |
| 3126 | `swCommands_Component_Pattern_Chain` | Assembly toolbar > Chain Component Pattern |
| 3171 | `swCommand_Component_Preview_Window` | Assembly toolbar > Component Preview Window |

## Feature（10 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 70 | `swCommands_FeatureImportDiagnosis` | Tools toolbar > Import Diagnostics |
| 438 | `swCommands_Featureworks` | SOLIDWORKS Add-ins toolbar > FeatureWorks |
| 479 | `swCommands_Features` | View menu > Toolbars > Features |
| 651 | `swCommands_Feature_Color` | RMB menu > Sketch Color |
| 652 | `swCommands_Feature_Texture` | valid for a selected feature, opens the Texture PropertyManager page |
| 2391 | `swCommands_Feature_Pop_Make_Weld_Bead` | RMB menu > Make Weld Bead |
| 2392 | `swCommands_Feature_Pop_Suppress_Weld_Beads` | Weldment RMB menu > Suppress Weld Beads |
| 2393 | `swCommands_Feature_Pop_Remove_Weld_Bead` | RMB menu > Make Non Weld Bead |
| 2394 | `swCommands_Feature_Pop_Unsuppress_Weld_Beads` | Weldment RMB menu > Unsuppress Weld Beads |
| 2897 | `swCommands_Feature_RV_Appearance` | RMB context toolbar > Appearances |

## Dimension（10 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 490 | `swCommands_DimensionRelations` | View menu > Toolbars > Dimensions/Relations |
| 2973 | `swCommands_DimensionSpaceEvenly` | Align toolbar > Dimension Space Evenly/Radial |
| 2974 | `swCommands_DimensionAlignCollinear` | Align toolbar > Align Collinear |
| 2975 | `swCommands_DimensionStagger` | Align toolbar > Align Stagger |
| 2977 | `swCommands_DimensionTextAlignTop` | Align toolbar > Top Justify Dimension Text |
| 2978 | `swCommands_DimensionTextAlignBottom` | Align toolbar > Bottom Justify Dimension Text |
| 2979 | `swCommands_DimensionTextAlignLeft` | Align toolbar > Left Justify Dimension Text |
| 2980 | `swCommands_DimensionTextAlignRight` | Align toolbar > Right Justify Dimension Text |
| 3025 | `swCommands_Dimension_Driven_Toggle` | Sketch toolbar > Sketch Dimension Driven |
| 3101 | `swCommands_DimensionPattern` | Features toolbar > Dimension Pattern |

## File（6 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 113 | `swCommands_FileReload` | Standard toolbar > Reload |
| 963 | `swCommands_File_Summaryinfo` | Standard toolbar > File Properties |
| 977 | `swCommands_File_Find` | File menu > Find References |
| 992 | `swCommands_File_Derive_Comp` | File menu > Derive Component Part |
| 2295 | `swCommands_File_Copy_Design` | File menu > Pack and Go |
| 2789 | `swCommands_FileClose` | Standard toolbar > Close |

## Annotation（6 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 307 | `swCommands_AnnotationAlignLeft` | Align toolbar > Align Left |
| 308 | `swCommands_AnnotationAlignRight` | Align toolbar > Align Right |
| 475 | `swCommands_Annotations` | View menu > Toolbars > Annotation |
| 2210 | `swCommands_Annotation_View_Create` | Annotations folder RMB menu > Insert Annotation View |
| 2232 | `swCommands_Annotation_View_Show` | RMB menu > Show |
| 2233 | `swCommands_Annotation_View_Hide` | RMB menu > Hide |

## Mate（5 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 90 | `swCommands_Mate` | Assembly toolbar > Mate |
| 160 | `swCommands_MateReference` | Reference Geometry toolbar > Mate Reference |
| 698 | `swCommands_Mate_Cancel` | Undo |
| 702 | `swCommands_Mate_Preview` | Preview |
| 2517 | `swCommands_Mate_Delete` | RMB menu > Delete |

## Ref（5 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 484 | `swCommands_ReferenceGeometry` | View menu > Toolbars > Reference Geometry |
| 771 | `swCommands_Ref_Help` | Edit Referenced File Locations dialog > Help |
| 3113 | `swCommands_RefPlane_Flip_Normal` | RMB context toolbar > Flip Normal |
| 3138 | `swCommands_Reference_arrow` | RMB menu context toolbar > Dynamic Reference Visualization (Parent) |
| 3151 | `swCommand_ReferenceArrow_PopUp` | Assembly toolbar > Dynamic Reference Visualization (Parent) |

## Design（4 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 413 | `swCommands_DesignTable` | Tools toolbar > Design Table |
| 460 | `swCommands_DesignChecker` | SOLIDWORKS Add-ins toolbar > Design Checker |
| 2953 | `swCommands_Design_Study` | Tools toolbar > Design Study |
| 2955 | `swCommands_DesignStudy_Add_Parameters` | Insert menu > Design Study > Parameters |

## Drawing（4 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 478 | `swCommands_Drawings` | View menu > Toolbars > Drawing |
| 2172 | `swCommands_Drawing_Stats` | Tools menu > Evaluate > Performance Evaluation |
| 2497 | `swCommands_Drawing_Feat_Edit_Def` | RMB menu > Edit Definition |
| 2693 | `swCommands_Drawing_Feat_Edit` | RMB menu > Edit Feature |

## Note（3 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 36 | `swCommands_Note` | Annotation toolbar > Note |
| 2993 | `swCommands_NoteLPat` | Annotation toolbar > Linear Note Pattern |
| 2994 | `swCommands_NoteCPat` | Annotation toolbar > Circular Note Pattern |

## Display（3 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 60 | `swCommands_DisplayDeleteRelations` | Layout toolbar > Display/Delete Relations |
| 572 | `swCommands_DisplayControlPolygon` | Spline Tools toolbar > Display Control Polygon |
| 3195 | `swCommands_Display_States_Target` | Render Tools toolbar > Display States Target |

## Surface（3 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 112 | `swCommands_SurfaceFinish` | Annotation toolbar > Surface Finish |
| 495 | `swCommands_Surfaces` | View menu > Toolbars > Surfaces |
| 3139 | `swCommands_Surface_Flatten` | Surfaces toolbar > Surface Flatten |

## Table（3 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 300 | `swCommands_TableDrivenPattern` | Features toolbar > Table Driven Pattern |
| 1975 | `swCommands_Table_Cell_Sub_Total` | inserts "Sub-total" into a selected table cell |
| 1976 | `swCommands_Table_Cell_Total` | inserts "Total" into a selected table cell |

## Help（3 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 340 | `swCommands_Help` | Standard toolbar > Help |
| 1423 | `swCommands_Help_Onlinetutorial` | Help menu > SOLIDWORKS Tutorials |
| 1882 | `swCommands_Help_Autocad_Users` | Help menu > Moving from 2D to 3D |

## Weldment（3 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 450 | `swCommands_Weldment` | Weldments toolbar > Weldment |
| 463 | `swCommands_WeldmentCutList` | Table toolbar > Weldment Cut List |
| 508 | `swCommands_Weldments` | View menu > Toolbars > Weldments |

## Custom（3 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 1938 | `swCommands_Customization_And_More` | RMB menu > Customize menu |
| 2238 | `swCommands_Custom_Msg_Display_Vw_By_Name` | menu item valid only in context of view orientations |
| 2239 | `swCommands_Custom_Msg_Display_Camera_By_Name` | RMB menu > View Orientation > |

## Simulation（3 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 3433 | `swCommands_SimulationStd` | SOLIDWORKS Add-ins toolbar > SOLIDWORKS Simulation Standard |
| 3434 | `swCommands_SimulationPro` | SOLIDWORKS Add-ins toolbar > SOLIDWORKS Simulation Professional |
| 3435 | `swCommands_SimulationPremium` | SOLIDWORKS Add-ins toolbar > SOLIDWORKS Simulation Premium |

## Assembly（2 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 3 | `swCommands_AssemblyTransparency` | RMB menu > Assembly Transparency |
| 1215 | `swCommands_Assembly_Stats` | Assembly toolbar > Performance Evaluation |

## Model（2 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 77 | `swCommands_ModelView` | Drawing toolbar > Model View |
| 513 | `swCommands_ModelItems` | Annotation toolbar > Model Items |

## Mold（2 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 414 | `swCommands_MoldflowxpressAnalysisWizard` | runs the MoldflowXpress Analysis Wizard, if the product is available |
| 483 | `swCommands_Molds` | View menu > Toolbars > Mold Tools |

## Window（2 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 1033 | `swCommands_Window_Closeall` | Window menu > Close All |
| 1494 | `swCommands_Window_Redraw` | View menu > Redraw |

## Equation（1 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 51 | `swCommands_Equations` | Tools toolbar > Equations |

## Selection（1 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 486 | `swCommands_SelectionFilters` | View menu > Toolbars > Selection Filter |

## SheetMetal（1 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 487 | `swCommands_SheetMetal` | View menu > Toolbars > Sheet Metal |

## Configuration（1 条）

| ID | 命令 | 菜单路径 / 说明 |
| --- | --- | --- |
| 3117 | `swCommands_ConfigurationsToolbar` | View menu > Toolbars > Configurations |
