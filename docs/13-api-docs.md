# 参数语义速查（来自 sldworksapi.chm 原文）

这份表是 **SolidWorks 官方英文文档的原话**，不是推测。生成方式见 `scripts/chm_index.py`：
把 `<SW_INSTALL>\api\sldworksapi.chm` 反编译成 17170 个 HTML，
抽出参数名/类型/说明，存成 `docs-index.json`（12,127 个方法，5,477 个有参数）。

查任意方法：`python scripts/chm_index.py` 后按 `接口.方法` 取键；插件里用 `sw_api_doc` 工具。

> 英文说明保留原文，避免翻译失真；单位一律 SI（米、弧度）。


## ISldWorks.NewDocument

```vb
Function NewDocument(  ByVal TemplateName As System.String,  ByVal PaperSize As System.Integer,  ByVal Width As System.Double,  ByVal Height As System.Double ) As System.Object
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `TemplateName` | String | Fully qualified path and name of the template to use for creating the new document |
| `PaperSize` | Integer | Size of paper as defined in swDwgPaperSizes_e |
| `Width` | Double | Width of paper; used only when PaperSize is swDwgPapersUserDefined |
| `Height` | Double | Height of paper; used only when PaperSize is swDwgPapersUserDefined |

## ISldWorks.NewPart

```vb
Function NewPart() As System.Object
```

_无参数（或文档未列参数表）。_

## ISldWorks.OpenDoc6

```vb
Function OpenDoc6(  ByVal FileName As System.String,  ByVal Type As System.Integer,  ByVal Options As System.Integer,  ByVal Configuration As System.String,  ByRef Errors As System.Integer,  ByRef Warnings As System.Integer ) As ModelDoc2
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `FileName` | String | Document name or full path if not in current directory, including extension |
| `Type` | Integer | Document type as defined in swDocumentTypes_e |
| `Options` | Integer | Mode in which to open the document as defined in swOpenDocOptions_e |
| `Configuration` | String | Model configuration in which to open this document       Applies to parts and assemblies, not drawings     If… |
| `Errors` | Integer | Load errors as defined in swFileLoadError_e ( See Remarks ) |
| `Warnings` | Integer | Warnings or extra information generated during the open operation as defined in swFileLoadWarning_e |

## ISldWorks.ActivateDoc2

```vb
Function ActivateDoc2(  ByVal Name As System.String,  ByVal Silent As System.Boolean,  ByRef Errors As System.Integer ) As System.Object
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `Name` | String | Name of document to activate |
| `Silent` | Boolean | True if dialogs and warning messages should be avoided, false if dialogs and warning messages should be displ… |
| `Errors` | Integer | Status of the document activate operation as defined in swActivateDocError_e ; if no errors or warnings are e… |

## ISldWorks.CloseDoc

```vb
Sub CloseDoc(  ByVal Name As System.String )
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `Name` | String | Name of document (see Remarks ) |

## IModelDoc2.SaveAs

```vb
Function SaveAs(  ByVal NewName As System.String ) As System.Boolean
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `NewName` | String | （文档缺） |

## IModelDoc2.Save3

```vb
Function Save3(  ByVal Options As System.Integer,  ByRef Errors As System.Integer,  ByRef Warnings As System.Integer ) As System.Boolean
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `Options` | Integer | Mode in which to save the document as defined in swSaveAsOptions_e |
| `Errors` | Integer | Errors that caused the save operation to fail as defined in swFileSaveError_e |
| `Warnings` | Integer | Warnings or extra information generated during the save operation as defined in swFileSaveWarning_e |

## IModelDoc2.EditRebuild3

```vb
Function EditRebuild3() As System.Boolean
```

_无参数（或文档未列参数表）。_

## IModelDoc2.ShowNamedView2

```vb
Sub ShowNamedView2(  ByVal VName As System.String,  ByVal ViewId As System.Integer )
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `VName` | String | Name of the view to display or an empty string to use ViewId instead |
| `ViewId` | Integer | ID of the view to display as defined by swStandardViews_e or -1 to use the VName argument instead; if you spe… |

## IModelDoc2.AddDimension2

```vb
Function AddDimension2(  ByVal X As System.Double,  ByVal Y As System.Double,  ByVal Z As System.Double ) As System.Object
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `X` | Double | Dimension text location in meters |
| `Y` | Double | Dimension text location in meters |
| `Z` | Double | Dimension text location in meters |

## IModelDocExtension.SelectByID2

```vb
Function SelectByID2(  ByVal Name As System.String,  ByVal Type As System.String,  ByVal X As System.Double,  ByVal Y As System.Double,  ByVal Z As System.Double,  ByVal Append As System.Boolean,  ByVal Mark As System.Integer,  ByVal Callout As Callout,  ByVal SelectOption As System.Integer ) As System.Boolean
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `Name` | String | Name of object to select or an empty string |
| `Type` | String | Type of object (uppercase) as defined in swSelectType_e or an empty string |
| `X` | Double | X selection location or 0 |
| `Y` | Double | Y selection location or 0 |
| `Z` | Double | Z selection location or 0 |
| `Append` | Boolean | If...   An, if entity is...   Then...       True   Not already selected   Entity is appended to the current s… |
| `Mark` | Integer | Value that you want to use as a mark; this value is used by other functions that require ordered selection (s… |
| `Callout` | Callout | Pointer to the associated callout |
| `SelectOption` | Integer | Selection option as defined in swSelectOption_e (see Remarks ) |

## IModelDocExtension.SelectByRay

```vb
Function SelectByRay(  ByVal WorldX As System.Double,  ByVal WorldY As System.Double,  ByVal WorldZ As System.Double,  ByVal RayVecX As System.Double,  ByVal RayVecY As System.Double,  ByVal RayVecZ As System.Double,  ByVal RayRadius As System.Double,  ByVal TypeWanted As System.Integer,  ByVal Append As System.Boolean,  ByVal Mark As System.Integer,  ByVal Option As System.…
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `WorldX` | Double | x coordinate of ray start point |
| `WorldY` | Double | y coordinate of ray start point |
| `WorldZ` | Double | z coordinate of ray start point |
| `RayVecX` | Double | x coordinate of ray direction vector |
| `RayVecY` | Double | y coordinate of ray direction vector |
| `RayVecZ` | Double | z coordinate of ray direction vector |
| `RayRadius` | Double | Radius |
| `TypeWanted` | Integer | Type of entities to select as defined in swSelectType_e |
| `Append` | Boolean | If...   And if entity is...   Then...       True   Not already selected   Entity is appended to the current s… |
| `Mark` | Integer | Value to use as a mark; this value is used by other functions that require ordered selection |
| `Option` | Integer | Selection option as defined in swSelectOption_e (see Remarks ) |

## IModelDocExtension.GetMassProperties2

```vb
Function GetMassProperties2(  ByVal Accuracy As System.Integer,  ByRef Status As System.Integer,  ByVal UseSelected As System.Boolean ) As System.Object
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `Accuracy` | Integer | 0 = as is     1 = default     2 = maximum |
| `Status` | Integer | Error code as defined in swMassPropertiesStatus_e |
| `UseSelected` | Boolean | True to return the mass properties of the selected components only, false to return the mass properties of th… |

## IModelDocExtension.SetUserPreferenceToggle

```vb
Function SetUserPreferenceToggle(  ByVal UserPref As System.Integer,  ByVal UserPrefOption As System.Integer,  ByVal Value As System.Boolean ) As System.Boolean
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `UserPref` | Integer | User preference as defined in swUserPreferenceToggle_e |
| `UserPrefOption` | Integer | User-preference option for customizing annotation and dimension drafting standards and as defined in swUserPr… |
| `Value` | Boolean | True to toggle UserPref on, false to toggle UserPref off |

## ISketchManager.InsertSketch

```vb
Sub InsertSketch(  ByVal UpdateEditRebuild As System.Boolean )
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `UpdateEditRebuild` | Boolean | True to rebuild the part with any changes made to the sketch and exit sketch mode, false to not |

## ISketchManager.CreateCornerRectangle

```vb
Function CreateCornerRectangle(  ByVal X1 As System.Double,  ByVal Y1 As System.Double,  ByVal Z1 As System.Double,  ByVal X2 As System.Double,  ByVal Y2 As System.Double,  ByVal Z2 As System.Double ) As System.Object
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `X1` | Double | Upper-left X coordinate for point 1 |
| `Y1` | Double | Upper-left Y coordinate for point 1 |
| `Z1` | Double | Upper-left Z coordinate for point 1 |
| `X2` | Double | Lower-right X coordinate for point 2 |
| `Y2` | Double | Lower-right Y coordinate for point 2 |
| `Z2` | Double | Lower-right Z coordinate for point 2 |

## ISketchManager.CreateCircleByRadius

```vb
Function CreateCircleByRadius(  ByVal XC As System.Double,  ByVal YC As System.Double,  ByVal Zc As System.Double,  ByVal Radius As System.Double ) As SketchSegment
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `XC` | Double | X coordinate of the circle center point in meters |
| `YC` | Double | Y coordinate of the circle center point in meters |
| `Zc` | Double | Z coordinate of the circle center point in meters |
| `Radius` | Double | Radius of the circle in meters |

## ISketchManager.CreateCircle

```vb
Function CreateCircle(  ByVal XC As System.Double,  ByVal YC As System.Double,  ByVal Zc As System.Double,  ByVal Xp As System.Double,  ByVal Yp As System.Double,  ByVal Zp As System.Double ) As SketchSegment
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `XC` | Double | X coordinate of the circle center point, in meters |
| `YC` | Double | Y coordinate of the circle center point, in meters |
| `Zc` | Double | Z coordinate of the circle center point, in meters |
| `Xp` | Double | X coordinate of the point on the circle, in meters |
| `Yp` | Double | Y coordinate of the point on the circle, in meters |
| `Zp` | Double | Z coordinate of the point on the circle, in meters |

## ISketchManager.CreateLine

```vb
Function CreateLine(  ByVal X1 As System.Double,  ByVal Y1 As System.Double,  ByVal Z1 As System.Double,  ByVal X2 As System.Double,  ByVal Y2 As System.Double,  ByVal Z2 As System.Double ) As SketchSegment
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `X1` | Double | X coordinate of the line start point |
| `Y1` | Double | Y coordinate of the line start point |
| `Z1` | Double | Z coordinate of the line start point |
| `X2` | Double | X coordinate of the line end point |
| `Y2` | Double | Y coordinate of the line end point |
| `Z2` | Double | Z coordinate of the line end point |

## ISketchManager.CreateArc

```vb
Function CreateArc(  ByVal XC As System.Double,  ByVal YC As System.Double,  ByVal Zc As System.Double,  ByVal X1 As System.Double,  ByVal Y1 As System.Double,  ByVal Z1 As System.Double,  ByVal X2 As System.Double,  ByVal Y2 As System.Double,  ByVal Z2 As System.Double,  ByVal Direction As System.Short ) As SketchSegment
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `XC` | Double | X coordinate of the circle center point in meters |
| `YC` | Double | coordinate of the circle center point in meters |
| `Zc` | Double | Z coordinate of the circle center point in meters |
| `X1` | Double | X coordinate of the start point of the arc in meters |
| `Y1` | Double | coordinate of the start point of the arc in meters |
| `Z1` | Double | Z coordinate of the start point of the arc in meters |
| `X2` | Double | X coordinate of the end point of the arc in meters |
| `Y2` | Double | Y coordinate of the end point of the arc in meters |
| `Z2` | Double | coordinate of the end point of the arc in meters |
| `Direction` | Short | +1 : Go from the start point to the end point in a counter-clockwise direction     -1 : Go from the start poi… |

## IFeatureManager.FeatureExtrusion2

```vb
Function FeatureExtrusion2(  ByVal Sd As System.Boolean,  ByVal Flip As System.Boolean,  ByVal Dir As System.Boolean,  ByVal T1 As System.Integer,  ByVal T2 As System.Integer,  ByVal D1 As System.Double,  ByVal D2 As System.Double,  ByVal Dchk1 As System.Boolean,  ByVal Dchk2 As System.Boolean,  ByVal Ddir1 As System.Boolean,  ByVal Ddir2 As System.Boolean,  ByVal Dang1 As…
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `Sd` | Boolean | True for single ended, false for double ended |
| `Flip` | Boolean | True to flip side to cut |
| `Dir` | Boolean | True to flip the direction to extrude |
| `T1` | Integer | Termination type for first end as defined in swEndConditions_e |
| `T2` | Integer | Termination type for second end as defined in swEndConditions_e |
| `D1` | Double | Depth of extrusion for first end in meters |
| `D2` | Double | Depth of extrusion for second end in meters |
| `Dchk1` | Boolean | True allows draft angle in first direction, false does not allow drafting |
| `Dchk2` | Boolean | True allows draft angle in second direction, false does not allow drafting |
| `Ddir1` | Boolean | True for first draft angle to be inward, false to be outward |
| `Ddir2` | Boolean | True for second draft angle to be inward, false to be outward |
| `Dang1` | Double | Draft angle for first end |
| `Dang2` | Double | Draft angle for second end |
| `OffsetReverse1` | Boolean | If you chose to offset the first end condition from another face or plane, then True specifies offset in dire… |
| `OffsetReverse2` | Boolean | If you chose to offset the second end condition from another face or plane, then True specifies offset in dir… |
| `TranslateSurface1` | Boolean | When you choose swEndcondOffsetFromSurface as the termination type for the first end, then True specifies tha… |
| `TranslateSurface2` | Boolean | When you choose swEndcondOffsetFromSurface as the termination type for the second end, then True specifies th… |
| `Merge` | Boolean | True to merge the results in a multibody part, false to not |
| `UseFeatScope` | Boolean | True if the feature only affects selected bodies, false if the feature affects all bodies |
| `UseAutoSelect` | Boolean | True to automatically select all bodies and have the feature affect those bodies, false to select the bodies … |
| `T0` | Integer | Start condition as defined in swStartConditions_e |
| `StartOffset` | Double | If t0 set to swStartOffset, then specify offset value |
| `FlipStartOffset` | Boolean | If t0 set to swStartOffset, then True to flip the direction or false to not |

## IFeatureManager.FeatureCut4

```vb
Function FeatureCut4(  ByVal Sd As System.Boolean,  ByVal Flip As System.Boolean,  ByVal Dir As System.Boolean,  ByVal T1 As System.Integer,  ByVal T2 As System.Integer,  ByVal D1 As System.Double,  ByVal D2 As System.Double,  ByVal Dchk1 As System.Boolean,  ByVal Dchk2 As System.Boolean,  ByVal Ddir1 As System.Boolean,  ByVal Ddir2 As System.Boolean,  ByVal Dang1 As Syste…
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `Sd` | Boolean | True for a single-ended cut, false for a doubled-ended cut |
| `Flip` | Boolean | True to remove material outside of the profile of the flip side to cut, false to not |
| `Dir` | Boolean | True for Direction 1 to be opposite of the default direction (see Remarks ) |
| `T1` | Integer | Termination type for the first end as defined in swEndConditions_e |
| `T2` | Integer | Termination type for the second end as defined in swEndConditions_e |
| `D1` | Double | Depth of extrusion for the first end in meters |
| `D2` | Double | Depth of extrusion for the second end in meters |
| `Dchk1` | Boolean | True allows a draft angle in the first direction, false does not allow drafting in the first direction |
| `Dchk2` | Boolean | True allows a draft angle in the second direction, false does not allow drafting in the second direction |
| `Ddir1` | Boolean | True for the first draft angle to be inward, false to be outward; only valid when Dchk1 is true |
| `Ddir2` | Boolean | True for the second draft angle to be inward, false to be outward; only valid when Dchk2 is true |
| `Dang1` | Double | Draft angle for the first end; only valid when Dchk1 is true |
| `Dang2` | Double | Draft angle for the second end; only valid when Dchk2 is true |
| `OffsetReverse1` | Boolean | If you chose to offset the first end condition from another face or plane, then true specifies offset in dire… |
| `OffsetReverse2` | Boolean | If you chose to offset the second end condition from another face or plane, then true specifies offset in dir… |
| `TranslateSurface1` | Boolean | When you choose swEndConditions_e.swEndCondOffsetFromSurface as the termination type for the first end, then … |
| `TranslateSurface2` | Boolean | When you choose swEndConditions_e.swEndCondOffsetFromSurface as the termination type for the second end, then… |
| `NormalCut` | Boolean | True to create the cut normal to the sheet metal thickness, false to not (only valid for sheet metal parts; u… |
| `UseFeatScope` | Boolean | True if the feature only affects selected bodies or components, false if the feature affects all bodies or co… |
| `UseAutoSelect` | Boolean | True to automatically select all bodies or components and have the feature affect those bodies or components,… |
| `AssemblyFeatureScope` | Boolean | True if the assembly feature only affects selected components in the assembly, false if the assembly feature … |
| `AutoSelectComponents` | Boolean | True to automatically select all affected components, false to use only the selected components |
| `PropagateFeatureToParts` | Boolean | True to propagate the assembly feature to the components in the model that it affects, false to not |
| `T0` | Integer | Start conditions as defined in swStartConditions_e |
| `StartOffset` | Double | If T0 is swStartConditions_e.swStartOffset, then specify an offset value |
| `FlipStartOffset` | Boolean | If T0 is swStartConditions_e.swStartOffset, then true to flip the direction of cut, false to not |
| `OptimizeGeometry` | Boolean | True to optimize the normal cut in a sheet metal part, false to not; only valid for sheet metal parts and whe… |

## IFeatureManager.FeatureRevolve2

```vb
Function FeatureRevolve2(  ByVal SingleDir As System.Boolean,  ByVal IsSolid As System.Boolean,  ByVal IsThin As System.Boolean,  ByVal IsCut As System.Boolean,  ByVal ReverseDir As System.Boolean,  ByVal BothDirectionUpToSameEntity As System.Boolean,  ByVal Dir1Type As System.Integer,  ByVal Dir2Type As System.Integer,  ByVal Dir1Angle As System.Double,  ByVal Dir2Angle As Sy…
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `SingleDir` | Boolean | True if the revolve is in one direction, false if in two directions (see Remarks ) |
| `IsSolid` | Boolean | True if this is a solid revolve feature, false if not |
| `IsThin` | Boolean | True if this is a thin revolve feature, false if not |
| `IsCut` | Boolean | True if this is a cut revolve feature, false if not |
| `ReverseDir` | Boolean | True reverses the angle of the revolution, false does not; only applies if Dir1Type is not swEndConditions_e.… |
| `BothDirectionUpToSameEntity` | Boolean | True if the revolve is up to the same entity in both directions, false if not; only applies if SingleDir is f… |
| `Dir1Type` | Integer | Revolve end condition as defined in swEndConditions_e |
| `Dir2Type` | Integer | Revolve end condition in direction 2; as defined in swEndConditions_e and only applies if Dir1Type is not swE… |
| `Dir1Angle` | Double | Angle in radians of revolution in direction 1; only applies if Dir1Type is swEndConditions_e.swEndCondBlind |
| `Dir2Angle` | Double | Angle in radians of revolution in direction 2; only applies if Dir2Type is swEndConditions_e.swEndCondBlind |
| `OffsetReverse1` | Boolean | True to reverse the offset direction in direction 1, false to not; only applies if Dir1Type is swEndCondition… |
| `OffsetReverse2` | Boolean | True to reverse the offset direction in direction 2, false to not; only applies if Dir2Type is swEndCondition… |
| `OffsetDistance1` | Double | Offset distance in direction 1; only applies if Dir1Type is swEndConditions_e.swEndCondOffsetFromSurface |
| `OffsetDistance2` | Double | Offset distance in direction 2; only applies if Dir2Type is swEndConditions_e.swEndCondOffsetFromSurface |
| `ThinType` | Integer | Type and direction as defined in swThinWallType_e |
| `ThinThickness1` | Double | Wall thickness in direction 1 (if ThinType is swThinWallType_e.swThinWallMidPlane, (ThinThickness1)/2 is used… |
| `ThinThickness2` | Double | Wall thickness in direction 2 (only applies if ThinType is swThinWallType_e.swThinWallTwoDirection) |
| `Merge` | Boolean | True to merge the results into a multi-body part, false to not |
| `UseFeatScope` | Boolean | True if the feature only affects selected bodies, false if the feature affects all bodies (see Remarks ) |
| `UseAutoSelect` | Boolean | True to automatically select all bodies and have the feature affect those bodies, false to select the bodies … |

## IFeatureManager.FeatureLinearPattern5

```vb
Function FeatureLinearPattern5(  ByVal Num1 As System.Integer,  ByVal Spacing1 As System.Double,  ByVal Num2 As System.Integer,  ByVal Spacing2 As System.Double,  ByVal FlipDir1 As System.Boolean,  ByVal FlipDir2 As System.Boolean,  ByVal DName1 As System.String,  ByVal DName2 As System.String,  ByVal GeometryPattern As System.Boolean,  ByVal VaryInstance As System.Boolean, …
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `Num1` | Integer | Number of instances of the linear pattern in Direction 1, including the original |
| `Spacing1` | Double | Spacing in meters between each instance of the linear pattern in Direction 1 |
| `Num2` | Integer | Number of instances of the linear pattern in Direction 2, including the original |
| `Spacing2` | Double | Spacing in meters between each instance of the linear pattern in Direction 2 |
| `FlipDir1` | Boolean | True to reverse the direction of the linear pattern in Direction 1, false to not |
| `FlipDir2` | Boolean | True to reverse the direction of the linear pattern in Direction 2, false to not |
| `DName1` | String | Name of the dimension defining Direction 1 |
| `DName2` | String | Name of the dimension defining Direction 2 |
| `GeometryPattern` | Boolean | True to use geometry pattern, false to not |
| `VaryInstance` | Boolean | True to vary the dimensions and spacing of individual pattern instances, false to not; valid only if Geometry… |
| `HasOffset1` | Boolean | True if using Offset1 to specify an offset of the pattern seed from a selected reference in Direction 1, fals… |
| `HasOffset2` | Boolean | True if using Offset2 to specify an offset of the pattern seed from a selected reference in Direction 2, fals… |
| `CtrlByNum1` | Boolean | True to control pattern spacing using Num1, false to control it using Spacing1; valid only if HasOffset1 is t… |
| `CtrlByNum2` | Boolean | True to control pattern spacing using Num2, false to control it using Spacing2; valid only if HasOffset2 is t… |
| `FromCentroid1` | Boolean | True if Offset1 is measured from the centroid of the seed instance, false if it is measured from a selected r… |
| `FromCentroid2` | Boolean | True if Offset2 is measured from the centroid of the seed instance, false if it is measured from a selected r… |
| `RevOffset1` | Boolean | True to reverse the direction of Offset1, false to not; valid only if HasOffset1 is true |
| `RevOffset2` | Boolean | True to reverse the direction of Offset2, false to not; valid only if HasOffset2 is true |
| `Offset1` | Double | Offset in meters from a selected reference in Direction 1; valid only if HasOffset1 is true (see Remarks ) |
| `Offset2` | Double | Offset in meters from a selected reference in Direction 2; valid only if HasOffset2 is true (see Remarks ) |
| `D2PatternSeedOnly` | Boolean | True to create a linear pattern in Direction 2 using the seed features only, without replicating the pattern … |
| `SyncSubAssemblies` | Boolean | True to move components in the patterned instances when components are moved in the seed flexible subassembly… |

## IFeatureManager.FeatureCircularPattern4

```vb
Function FeatureCircularPattern4(  ByVal Number As System.Integer,  ByVal Spacing As System.Double,  ByVal FlipDirection As System.Boolean,  ByVal DName As System.String,  ByVal GeometryPattern As System.Boolean,  ByVal EqualSpacing As System.Boolean,  ByVal VaryInstance As System.Boolean ) As Feature
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `Number` | Integer | Number of instances of the circular pattern to insert, including the original instance |
| `Spacing` | Double | Spacing between each instance of the circular pattern; total angle in radians if EqualSpacing is true |
| `FlipDirection` | Boolean | True to flip the direction of the circular pattern, false to not |
| `DName` | String | Name of the angular dimension defining the direction of the pattern |
| `GeometryPattern` | Boolean | True to use geometry pattern, false to not |
| `EqualSpacing` | Boolean | True to use equal spacing, false to not |
| `VaryInstance` | Boolean | True to vary the dimensions or spacing of individual pattern instances, false to not; valid only if GeometryP… |

## IFeatureManager.CreateDefinition

```vb
Function CreateDefinition(  ByVal Type As System.Integer ) As System.Object
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `Type` | Integer | Feature name ID as defined in swFeatureNameID_e :     swFMBaseFlange (sheet metal base flange)   swFMBeltAndC… |

## IFeatureManager.CreateFeature

```vb
Function CreateFeature(  ByVal FeatureData As System.Object ) As Feature
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `FeatureData` | Object | thread , sweep , library , tab/slot , bounding box , ground plane , mirror components , projection curve , sh… |

## IAssemblyDoc.AddComponent5

```vb
Function AddComponent5(  ByVal CompName As System.String,  ByVal ConfigOption As System.Integer,  ByVal NewConfigName As System.String,  ByVal UseConfigForPartReferences As System.Boolean,  ByVal ExistingConfigName As System.String,  ByVal X As System.Double,  ByVal Y As System.Double,  ByVal Z As System.Double ) As Component2
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `CompName` | String | Path name of a pre-loaded part or assembly to add as a component (see Remarks ) |
| `ConfigOption` | Integer | Mode in which to open the document as specified in swAddComponentConfigOptions_e |
| `NewConfigName` | String | Name for the new assembly configuration;   valid only if ConfigOption =     swAddComponentConfigOptions_e.swA… |
| `UseConfigForPartReferences` | Boolean | If true, the configuration specified in ExistingConfigName is used |
| `ExistingConfigName` | String | Name of the configuration of the loaded component ; valid only if UseConfigForPartReferences = true |
| `X` | Double | X coordinate of the component center |
| `Y` | Double | Y coordinate of the component center |
| `Z` | Double | Z coordinate of the component center |

## IAssemblyDoc.AddMate5

```vb
Function AddMate5(  ByVal MateTypeFromEnum As System.Integer,  ByVal AlignFromEnum As System.Integer,  ByVal Flip As System.Boolean,  ByVal Distance As System.Double,  ByVal DistanceAbsUpperLimit As System.Double,  ByVal DistanceAbsLowerLimit As System.Double,  ByVal GearRatioNumerator As System.Double,  ByVal GearRatioDenominator As System.Double,  ByVal Angle As System.Double,…
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `MateTypeFromEnum` | Integer | Type of mate as defined in swMateType_e (see Remarks ) |
| `AlignFromEnum` | Integer | Type of alignment as defined in swMateAlign_e |
| `Flip` | Boolean | True to flip the mate entities, false to not; valid only if MateTypeFromEnum is swMatetype_e.swMateDISTANCE |
| `Distance` | Double | Distance value; valid only if MateTypeFromEnum is swMateType_e.swMateDISTANCE |
| `DistanceAbsUpperLimit` | Double | Absolute maximum distance value; valid only if MateTypeFromEnum is swMateType_e.swMateDISTANCE (see Remarks ) |
| `DistanceAbsLowerLimit` | Double | Absolute minimum distance value; valid only if MateTypeFromEnum is swMateType_e.swMateDISTANCE (see Remarks ) |
| `GearRatioNumerator` | Double | Gear ratio numerator value; valid only if MateTypeFromEnum is swMateType_e.swMateGEAR |
| `GearRatioDenominator` | Double | Gear ratio denominator value; valid only if MateTypeFromEnum is swMateType_e.swMateGEAR |
| `Angle` | Double | Angle value; valid only if MateTypeFromEnum is swMateType_e.swMateANGLE |
| `AngleAbsUpperLimit` | Double | Absolute maximum angle value; valid only if MateTypeFromEnum is swMateType_e.swMateANGLE |
| `AngleAbsLowerLimit` | Double | Absolute minimum angle value; valid only if MateTypeFromEnum is swMateType_e.swMateANGLE |
| `ForPositioningOnly` | Boolean | True to only position the components according to the mating relationship and not return a mate, false to ret… |
| `LockRotation` | Boolean | True to lock component rotation, false to not |
| `WidthMateOption` | Integer | Width mate options as defined in swMateWidthOptions_e ; valid only if MateTypeFromEnum is swMateType_e.swMate… |
| `ErrorStatus` | Integer | Success or error as defined by swAddMateError_e |

## IDrawingDoc.CreateDrawViewFromModelView3

```vb
Function CreateDrawViewFromModelView3(  ByVal ModelName As System.String,  ByVal ViewName As System.String,  ByVal LocX As System.Double,  ByVal LocY As System.Double,  ByVal LocZ As System.Double ) As View
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `ModelName` | String | Full pathname of the model document for which to create the drawing view (see Remarks ) |
| `ViewName` | String | Name of the model view from which to create the drawing view (see Remarks ) |
| `LocX` | Double | x location of drawing view center in meters |
| `LocY` | Double | y location of drawing view center in meters |
| `LocZ` | Double | z location of drawing view center in meters |

## IDrawingDoc.Create3rdAngleViews2

```vb
Function Create3rdAngleViews2(  ByVal ModelName As System.String ) As System.Boolean
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `ModelName` | String | Name of the document from which to create views |

## IPartDoc.GetBodies2

```vb
Function GetBodies2(  ByVal BodyType As System.Integer,  ByVal BVisibleOnly As System.Boolean ) As System.Object
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `BodyType` | Integer | Type of body as defined in swBodyType_e |
| `BVisibleOnly` | Boolean | True gets only the visible bodies, false gets all of the bodies in the part |

## IPartDoc.GetPartBox

```vb
Function GetPartBox(  ByVal NoConversion As System.Boolean ) As System.Object
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `NoConversion` | Boolean | Convert to user units or not; true retains system units, false changes to user units |

## IBody2.GetMassProperties

```vb
Function GetMassProperties(  ByVal Density As System.Double ) As System.Object
```

| 参数 | 类型 | 官方说明 |
| --- | --- | --- |
| `Density` | Double | Density to use for the mass property calculations on this body |
---

## 同名重载：`SelectByRay` 有两个版本（实测踩过）

| 接口 | 实参 | 形态 |
|---|---|---|
| `IModelDoc2.SelectByRay` | **2** | `(Object DoubleInfoIn, Integer TypeWanted)` —— 7 个 double 打成一个 SAFEARRAY 传 |
| `IModelDocExtension.SelectByRay` | **11** | `(WorldX,Y,Z, RayVecX,Y,Z, RayRadius, TypeWanted, Append, Mark, Option)` |

本技能与 `swe.select_face()` 用的是 **11 参的 IModelDocExtension 版**。查文档时必须写限定名，
只写 `SelectByRay` 会命中另一个版本（参数表完全不同）。同类情况还有 `SelectByID2`
（`IModelDoc2` 与 `IModelDocExtension` 各一份，只有 Extension 版能用）。