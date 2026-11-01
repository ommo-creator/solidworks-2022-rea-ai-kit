# Motion Study（运动算例）实测 —— 独立 interop 程序集，与 sldworks 主库分开

> 实测环境：SolidWorks 2022 SP5 / 30.5.0，Windows，comtypes 1.4.17 + 类型库 `SldWorks`。
> 状态标记：✅ 已实测出数；📄 官方元数据已核；⚠️ 推断。

## 0 一句话结论

运动算例**不在** `SolidWorks.Interop.sldworks.dll` 里，而在**另一个** interop 程序集 `SolidWorks.Interop.swmotionstudy.dll`；
入口是 `IModelDocExtension.GetMotionStudyManager()`，返回的是**无类型 `_Dispatch`**（`dir()` 只有 `QueryInterface`），
但按名字动态派发**完全可用**（`swe.P` 就是干这个的）。

## 1 程序集与对象（📄 反射所得）

| 文件 | 大小 | 关键类型 |
|---|---|---|
| `<SW_INSTALL>\SolidWorks.Interop.swmotionstudy.dll` | 42,648 B | `IMotionStudyManager`(8 方法) / `IMotionStudy`(35 方法 + 5 属性) / `IMotionStudyResults`(9 方法) / `IMotionStudyProperties` / 事件 `DMotionStudyEvents` |
| `cmotionswapi.dll` | 3,811,840 B | Motion 的实现侧（COM 服务） |
| `cmotionsw.dll` / `cmotionsw_wrapper.dll` | 395,776 / 14,150,552 B | 内核 / 包装层 |

`IMotionStudyManager` 全部成员：`CreateMotionStudy()`、`DeleteMotionStudy(name)`、`GetMotionStudy(name)`、
`ActivateMotionStudy(name)`、`GetMotionStudyCount()`、`GetMotionStudyNames()`、`IGetMotionStudyNames(count)`、`CreateAVIParameter()`。

`IMotionStudy` 关键成员：`Name`/`StudyType`/`IsActive`/`PlayMode`/`IsPlaying`（属性）、
`Calculate()`、`Play()`/`PlayFromStart()`/`Stop()`、`SetDuration(s)`/`GetDuration()`、`GetResults(type)`、`GetProperties(type)`、
`GetMotionFeaturesCount()`/`GetMotionFeatures()`、`CreateDefinition(swFmAEM*)` + `CreateFeature(obj)`、
`CreateByRotateModel(...)`/`CreateByExplode(...)`/`CreateByCollapse(...)`（动画类）、`SaveToAVI(path, aviParam)`。

`IMotionStudyResults`：`GetLinearVelocity(t, obj)`、`GetAngularVelocity`、`GetLinearAcceleration`、`GetAngularAcceleration`、
`GetCMPosition`、`GetEulerAngles`、`GetForceFromMate`、`GetTorqueFromMate`、`IsOutOfDate`。

## 2 实测步骤（✅，装配体）

```python
# 装配体里放两个零件（零件必须先 OpenDoc6 预加载，见坑 21）
mgr = swe.P(md.Extension, 'GetMotionStudyManager')
print(swe.P(mgr, 'GetMotionStudyNames'))     # ('运动算例 1',)  —— 新建装配体自带 1 个
stu = swe.P(mgr, 'CreateMotionStudy')        # -> 运动算例 2
print(stu.Name, stu.StudyType)               # 运动算例 2 / 1
print(swe.P(stu, 'SetDuration', 2.0))        # True
print(swe.P(stu, 'GetDuration'))             # 2.0
print(swe.P(stu, 'Calculate'))               # True
print(type(swe.P(stu, 'GetResults', 1)))     # _Dispatch（结果对象，可按时间取速度/加速度）
```

实测数字：新建装配体 `GetMotionStudyCount()` = **1**、名字 `('运动算例 1',)`；
`CreateMotionStudy()` 后 = **2**、`('运动算例 1', '运动算例 2')`；`StudyType` = 1；`SetDuration(2.0)` → `True`，`GetDuration()` = **2.0**；
`GetMotionFeaturesCount()` = **0**；`Calculate()` → **True**。

## 3 驱动特征（马达/力/重力）需要先选对象

`swFeatureNameID_e`（121 项）里的运动专用 ID：
`swFmAEMGravity=74`、`swFmAEMLinearForce=75`、`swFmAEMLinearMotor=77`、`swFmAEMRotationalMotor=78`、
`swFmAEMLinearSpring=79`、`swFmAEMTorsionalSpring=80`、`swFmAEMLinearMotionSpring=81`、`swFmAEMTorsionalMotionSpring=82`。

实测：在**没有预选任何对象**时 `stu.CreateDefinition(77/78/74)` **全部返回 None**（不是报错，是静默 None）。
→ 正确顺序应为：先 `SelectByRay/SelectByID2` 选中要驱动的零件面或棱边 → `CreateDefinition(77)` → QI
`ISimulationMotorFeatureData`（属性 `MotorType`/`MotionType`/`Speed`/`Location`/`DirectionReference` 等 14 项）→ `stu.CreateFeature(q)`。
该步尚未跑通，记 ⚠️。

## 4 Simulation（FEA）在本机不可用

- `IAssemblyDoc.GetSimulation()` → **None**；`sw.GetAddInObject('SldMotion.SldMotionAddin')`、
  `('CosmosWorks.CosmosWorks')`、`('SldWorks.Simulation')` 全部 **None**。
- 注册表 `HKLM\SOFTWARE\SolidWorks\Addins` 只有 3 项：SOLIDWORKS Composer、XML Paper Specification Driver、Presentation Manager for MBD
  —— **Motion / Simulation 都没有注册为加载项**（安装时未勾选或未授权）。
- 但 `SolidWorks.Interop.swmotionstudy.dll` 与 `cmotionswapi.dll` 文件是**在的** → Motion 走 `GetMotionStudyManager()` 仍能用（属于主程序内置的算例管理，
  只有物理求解才依赖 Motion 加载项）；Simulation(FEA) 则整体不可用。

## 5 坑

1. `GetMotionStudyManager()` 返回的对象**没有接口**（`dir()` 只有 `QueryInterface`），必须按名字动态调用；
   零参方法在 comtypes 下会退化成属性（`mgr.GetMotionStudyCount` 返回 int，加 `()` 报 `'int' object is not callable`）→ 一律走 `swe.P(mgr, '名字', ...)`。
2. 类型库里 `motion/study/simulation` 相关符号只有 20 个，且**全是 feature-data**（马达/力/弹簧/阻尼/重力/绘图），没有 study manager —— 别在 `comtypes.gen.SldWorks` 里找管理器，它在 `swmotionstudy` 程序集。
3. `CreateDefinition` 在算例上**静默返回 None**（缺预选），与 `IFeatureManager.CreateDefinition` 的失败表现一致，注意区分"不支持"和"缺选择"。
