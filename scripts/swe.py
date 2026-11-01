# -*- coding: utf-8 -*-
"""SolidWorks comtypes 逆向 harness（v2，RE 阶段全部实测函数）。

沿用早期实测记录的四个坑：
 1. comtypes 类型库模块名是 SldWorks（不是 SolidWorks）
 2. GetActiveObject 不可用（0x800401E3），必须 CreateObject
 3. _vartype_to_ctype 缺 VT_DISPATCH(9) 映射，读 SAFEARRAY 会 KeyError: 9
 4. AddComponent* 要求零件已作为文档加载

v2 增补（都在本机跑通过）：
  quiet / new_assembly / new_drawing / sketch_on_plane / select_face
  feature_profile / real_features / bodies / bodies_count / bbox / mass2
  segments / save / export_step
"""
import ctypes

import comtypes.automation as ca
import comtypes.client as cc

# 坑 3
if ca.VT_DISPATCH not in ca._vartype_to_ctype:
    ca._vartype_to_ctype[ca.VT_DISPATCH] = ctypes.POINTER(ca.IDispatch)

from comtypes.gen import SldWorks  # noqa: E402

SW = SldWorks  # 便捷别名：SW.IDimension / SW.ISketchSegment / SW.IDocumentSpecification ...

ISldWorks = SldWorks.ISldWorks
IModelDoc2 = SldWorks.IModelDoc2
IPartDoc = SldWorks.IPartDoc
IAssemblyDoc = SldWorks.IAssemblyDoc
IDrawingDoc = SldWorks.IDrawingDoc
IFeatureManager = SldWorks.IFeatureManager
ISketchSegment = SldWorks.ISketchSegment

DOC_PART, DOC_ASSEMBLY, DOC_DRAWING = 1, 2, 3
PAPER_A4 = 6                 # swDwgPaperSizes_e.swDwgPaperA4size
LU = 0.0174532925199433      # 1 度，弧度

# swEndConditions_e 实测值（8 空缺，不是连续编号）
BLIND, THROUGH_ALL, THROUGH_NEXT = 0, 1, 2
THROUGH_ALL_BOTH, MID_PLANE = 9, 6

# 特征树里的固定文件夹 / 真实几何特征
SKIP_TYPES = {
    "Favorites", "History", "Selection Sets", "SensorFolder", "DocsFolder",
    "DetailCabinet", "InkMarkupFolder", "EnvFolder", "SolidBodyFolder",
    "SurfaceBodyFolder", "CommentsFolder", "EqnFolder", "MaterialFolder",
    "RefPlane", "OriginProfileFeature", "ConfigTableFolder",
}
FEATURE_TYPES = {
    "ProfileFeature", "Extrusion", "ICE", "Cut", "CutExtrusion",
    "CirPattern", "LPattern", "MirrorPattern", "Fillet", "Chamfer",
    "Revolve", "RevolveCut", "Reference", "MateGroup",
}


# ---------------------------------------------------------------- 连接 / 文档
def connect(visible=True):
    """附加到运行中的 SolidWorks（坑 2：只能 CreateObject）。"""
    sw = cc.CreateObject("SldWorks.Application")
    try:
        sw.Visible = visible
    except Exception:
        pass
    return sw


def quiet(sw):
    """关掉会卡死脚本的模态对话框。

    10  = swInputDimValOnCreate（建尺寸时弹"修改"框）
    100 = swSketchOverdefiningDimsPromptToSetState
    """
    for pref in (10, 100):
        try:
            sw.SetUserPreferenceToggle(pref, False)
        except Exception:
            pass


def new_part(sw):
    doc = None
    try:
        doc = sw.INewPart()
    except Exception as e:
        print("  INewPart 失败:", e)
    if doc is None:
        doc = sw.NewPart()
    return md2(doc)


def new_assembly(sw):
    doc = None
    try:
        doc = sw.INewAssembly()
    except Exception as e:
        print("  INewAssembly 失败:", e)
    if doc is None:
        doc = sw.NewAssembly()
    return md2(doc)


def new_drawing(sw, paper=PAPER_A4):
    doc = None
    try:
        doc = sw.INewDrawing(paper)
    except Exception as e:
        print("  INewDrawing 失败:", e)
    if doc is None:
        doc = sw.NewDrawing(paper)
    return md2(doc)


def md2(doc):
    return doc.QueryInterface(IModelDoc2)


def part(md):
    return md.QueryInterface(IPartDoc)


def asm(md):
    return md.QueryInterface(IAssemblyDoc)


def drw(md):
    return md.QueryInterface(IDrawingDoc)


def P(obj, name, *args):
    """统一取属性/方法：comtypes 有时把无参方法当属性返回（坑 5）。"""
    v = getattr(obj, name)
    if callable(v):
        return v(*args)
    return v


# ---------------------------------------------------------------- 特征树
def features(md):
    out = []
    f = P(md, "FirstFeature")
    guard = 0
    while f is not None and guard < 500:
        out.append(f)
        f = P(f, "GetNextFeature")
        guard += 1
    return out


def feature_names(md):
    return [(P(f, "Name"), P(f, "GetTypeName2")) for f in features(md)]


def real_features(md):
    """只留几何特征名（跳过历史/注解/实体等文件夹）。"""
    return [P(f, "Name") for f in features(md) if P(f, "GetTypeName2") in FEATURE_TYPES]


def feature_profile(md, mark=0, last=True):
    """选中草图（中文版叫"草图N"，不能硬编码 Sketch1）。

    last=True 取**最后一张**草图——第一个 ProfileFeature 永远是最早那张，
    切孔/二次特征时选它会得到 None（坑 70）。
    """
    hits = []
    for f in features(md):
        if P(f, "GetTypeName2") == "ProfileFeature":
            hits.append(f)
    if not hits:
        return False
    targets = [hits[-1]] if last else hits
    ok = False
    for f in targets:
        try:
            ok = f.Select2(False, mark) or ok
        except Exception:
            continue
    return ok


# ---------------------------------------------------------------- 草图 / 选面
def sketch_on_plane(md, plane="前视基准面"):
    return md.Extension.SelectByID2(plane, "PLANE", 0, 0, 0, False, 0, None, 0)


def select_face(md, x, y, z, dx, dy, dz, mark=0, append=False):
    """射线选面：11 参，RayRadius=0.001、TypeWanted=2(面)。自动化会话里 SelectByID2("","FACE") 会失败。"""
    return md.Extension.SelectByRay(x, y, z, dx, dy, dz, 0.001, 2, append, mark, 0)


def segments(sk):
    """草图线段：元素是 POINTER(IDispatch)，必须 QueryInterface 才有 Select2。"""
    raw = None
    try:
        raw = sk.GetSketchSegments
        raw = raw() if callable(raw) else raw
    except Exception:
        raw = None
    if raw is None:
        raw = P(sk, "GetSketchSegments2")
    out = []
    for s in (raw or []):
        try:
            out.append(s.QueryInterface(ISketchSegment))
        except Exception:
            out.append(s)
    return out


# ---------------------------------------------------------------- 质量 / 几何
def mass(md):
    """CreateMassProperty：Volume 可信；未指定材质时 Mass=Volume、Density=1。"""
    mp = md.Extension.CreateMassProperty()
    return {"volume": P(mp, "Volume"), "mass": P(mp, "Mass"), "density": P(mp, "Density")}


def mass2(md):
    """GetMassProperties2(1, False) → (status, 13 项数组)。

    数组顺序：[Xcm, Ycm, Zcm, Volume, Area, Mass, Ixx, Iyy, Izz, Ixy, Iyz, Ixz, 密度]
    """
    r = md.Extension.GetMassProperties2(1, False)
    if isinstance(r, tuple):
        status = r[0]
        arr = next((x for x in r[1:] if not isinstance(x, (int, float))), r[1:])
    else:
        status, arr = 0, r
    return status, list(arr)


def bodies(md):
    out = []
    try:
        got = part(md).EnumBodies3(0, True)
        out = [] if got is None else list(got)
    except Exception:
        out = []
    return out


def bodies_count(md):
    return len(bodies(md))


def body_mass(md, index=0):
    """IBody2.GetMassProperties：索引 3 是体积（索引 1 不是）。"""
    bl = bodies(md)
    if not bl:
        return None
    return list(bl[index].GetMassProperties(0.0))


def bbox(md):
    """GetPartBox(False)：本机实测返回**毫米**（0.1m 的件给 100）。"""
    return list(part(md).GetPartBox(False))


# ---------------------------------------------------------------- 落盘
def save(md, path):
    """IModelDoc2.SaveAs：.SLDPRT / .SLDASM / .SLDDRW / .STEP 都用它。

    目标已存在时返回 False，但文件仍会写入 —— 不能当失败判据。
    """
    ok = md.SaveAs(path)
    return {"ok": ok, "exists": __import__("os").path.exists(path),
            "size": __import__("os").path.getsize(path) if __import__("os").path.exists(path) else 0}


def export_step(md, path):
    return save(md, path)


def clear(md):
    md.ClearSelection2(True)


def step(n, label, fn):
    try:
        r = fn()
        print("[%s] OK   %-42s -> %r" % (n, label, r))
        return r
    except Exception as e:
        print("[%s] FAIL %-42s -> %s: %s" % (n, label, type(e).__name__, e))
        return None


# ---------------------------------------------------------------- 圆角 / 倒角 / 抽壳 / 剖视
def select_edge(md, x, y, z, dx, dy, dz, radius=0.0004):
    """射线选棱边（TypeWanted=1）。返回选中数。

    坑 25：不要用 GetSelectedObjectType3 判类型（恒返回 0），只认选中数。
    """
    md.ClearSelection2(True)
    md.Extension.SelectByRay(x, y, z, dx, dy, dz, radius, 1, False, 0, 0)
    return md.SelectionManager.GetSelectedObjectCount2(-1)


def fillet(md, r=0.005, options=2):
    """FeatureFillet3：options=2(swFeatureFilletUniformRadius) 必须带上，否则 R1 不生效。"""
    fm = P(md, "FeatureManager")
    return fm.FeatureFillet3(options, r, 0.0, 0.0, 0, 0, 0,
                             None, None, None, None, None, None, None)


def chamfer(md, w=0.003, angle=0.7853981633974483, chamfer_type=1, options=0):
    """InsertFeatureChamfer：chamfer_type 1=AngleDistance 2=DistanceDistance 3=Vertex 16=EqualDistance。"""
    fm = P(md, "FeatureManager")
    return fm.InsertFeatureChamfer(options, chamfer_type, w, angle, w, 0.0, 0.0, 0.0)


def shell(md, thickness=0.002, outward=False):
    """InsertFeatureShell(Thickness, Outward)：返回 Void。先选中面 = 开口壳；不选 = 闭合壳。"""
    md.InsertFeatureShell(thickness, outward)
    return True


def section_view(d, part_path, view_name="*前视", view_at=(0.10, 0.15),
                 line=None, label="A", section_at=(0.10, 0.19), options=0,
                 make_view=True, scale=2.0, pad=0.0035):
    """工程图剖视图（R3）。

    比例是硬条件：CreateSectionViewAt5 的成功率取决于「视图比例 × 剖切线长」的组合，
    自动比例在多数零件上静默返回 None（1:1 连测 0/5、2:1 连测 5/5）；见坑 74。
    line 不给时按视图实际轮廓 GetOutline() 上下各外扩 pad 自动生成。
    失败会退回自动比例再试一次；仍失败返回 None（此时请换 GUI 手画）。
    """
    dm = md2(d)
    if make_view:
        d.CreateDrawViewFromModelView3(part_path, view_name, view_at[0], view_at[1], 0.0)
    sheet = P(d, "GetFirstView")
    v = P(sheet, "GetNextView")
    tries = [scale, None] if scale else [None]
    for sc in tries:
        try:
            if sc:
                v.ScaleDecimal = float(sc)
                dm.EditRebuild3()
        except Exception:
            pass
        ln = line
        if ln is None:
            try:
                x0, y0, x1, y1 = P(v, "GetOutline")
                ln = (((x0 + x1) / 2.0, y0 - pad), ((x0 + x1) / 2.0, y1 + pad))
            except Exception:
                ln = ((view_at[0], view_at[1] - 0.025), (view_at[0], view_at[1] + 0.030))
        dm.ClearSelection2(True)
        sk = P(dm, "SketchManager")
        sk.InsertSketch(True)
        (ax, ay), (bx, by) = ln
        seg = sk.CreateLine(ax, ay, 0, bx, by, 0)
        if seg is None:
            sk.InsertSketch(True)
            continue
        seg.Select2(False, 0)
        d.MakeSectionLine()
        sec = d.CreateSectionViewAt5(section_at[0], section_at[1], 0.0, label, options, None, 0)
        sk.InsertSketch(True)
        if sec is not None:
            return sec
    return None


def view_count(d):
    dd = d
    try:
        dd = d.QueryInterface(SW.IDrawingDoc)
    except Exception:
        pass
    return P(dd, "GetViewCount")


def read_section(view):
    """读剖视图：GetSection 返回无类型 _Dispatch，晚绑定即可。"""
    sec = P(view, "GetSection")
    if sec is None:
        return None
    out = {}
    for f in ("GetLabel", "GetName", "GetArrowInfo", "GetLineInfo", "GetAutoHatch"):
        try:
            out[f.replace("Get", "").lower()] = P(sec, f)
        except Exception:
            pass
    return out


# ---------------------------------------------------------------- 工程图注记
def open_part(sw, path, doc_type=DOC_PART):
    """把零件预先装入会话：工程图注记的前置条件（坑 26）。已打开则直接返回。"""
    try:
        r = sw.OpenDoc6(path, doc_type, 1, "", 0, 0)
        return r[-1] if isinstance(r, (list, tuple)) else r
    except Exception:
        return None


def annotations(d, types=8, all_views=False, dup_dims=False):
    """工程图注记（R13）。两个必要条件缺一不可（坑 26）：

    1) 用 4 参旧版 InsertModelAnnotations —— …2/…3 在本机静默不做事；
    2) 视图引用的模型必须已在本会话打开（先调用 open_part）。

    调用前还要选中视图：
        dm.Extension.SelectByID2(name, "DRAWINGVIEW", 0, 0, 0, False, 0, None, 0)
    types: swInsertAnnotation_e.Dimensions = 8；孔向导位 65536 | 131072。
    """
    return d.InsertModelAnnotations(0, types, all_views, dup_dims)


def display_dims(view):
    """读视图里已导入的显示尺寸 -> [(FullName, 米), ...]。

    注意 IDimension.Value 是毫米、SystemValue 是米（坑 27），这里统一返回米。
    """
    out = []
    raw = P(view, "GetDisplayDimensions")
    if raw is None:
        return out
    for dd in raw:
        try:
            d2 = dd.QueryInterface(SW.IDisplayDimension)
            dim = P(d2, "GetDimension")
            out.append((P(dim, "FullName"), P(dim, "SystemValue")))
        except Exception:
            continue
    return out


# ==================================================== 一键建模函数（R27，均已实测）
# 设计原则：每个函数内部完成「选对象 → 建草图/特征 → EditRebuild3」，
# 失败的判定统一用体积对账，不拿 comtypes 返回值当结论（坑 1/17/31/68）。

CUT27 = (True, False, False, 1, 0, 0.0, 0.0,
         False, False, False, False, 0.0, 0.0,
         False, False, False, False, False, True, True,
         False, False, False, 0, 0.0, False, False)


def _sketch(md, plane="前视基准面", kind="rect", w=0.10, h=0.06, r=0.05,
            cx=0.0, cy=0.0):
    """在 plane 上开草图并画一个矩形/圆，退出草图，返回是否选中到轮廓。"""
    md.ClearSelection2(True)
    if plane:
        md.Extension.SelectByID2(plane, "PLANE", 0, 0, 0, False, 0, None, 0)
    sk = md.SketchManager
    sk.InsertSketch(True)
    if kind == "rect":
        sk.CreateCornerRectangle(cx - w / 2.0, cy - h / 2.0, 0.0,
                                cx + w / 2.0, cy + h / 2.0, 0.0)
    else:
        sk.CreateCircleByRadius(cx, cy, 0.0, r)
    sk.InsertSketch(True)
    md.ClearSelection2(True)
    return feature_profile(md)          # 默认 last=True（坑 70）


def _sketch_on_face(md, x, y, z, dx, dy, dz, kind="circle", w=0.02, h=0.02,
                    r=0.005, cx=0.0, cy=0.0):
    """射线打面 → 在命中面上开草图（切除必须建在被切面上，坑 5）。"""
    md.ClearSelection2(True)
    if not select_face(md, x, y, z, dx, dy, dz):
        return False
    sk = md.SketchManager
    sk.InsertSketch(True)
    if kind == "rect":
        sk.CreateCornerRectangle(cx - w / 2.0, cy - h / 2.0, 0.0,
                                cx + w / 2.0, cy + h / 2.0, 0.0)
    else:
        sk.CreateCircleByRadius(cx, cy, 0.0, r)
    sk.InsertSketch(True)
    md.ClearSelection2(True)
    return feature_profile(md)


def solid_rect(md, w=0.10, h=0.06, depth=0.02, plane="前视基准面", cx=0.0, cy=0.0):
    """矩形拉伸。返回 IFeature 或 False。"""
    if not _sketch(md, plane, "rect", w, h, 0, cx, cy):
        return False
    fm = md.FeatureManager
    f = fm.FeatureExtrusion2(True, False, False, 0, 0, depth, 0.0,
                             False, False, False, False, 0.0, 0.0,
                             False, False, False, False, True, True, True, 0, 0.0, False)
    md.EditRebuild3()
    return f


def solid_circle(md, r=0.05, depth=0.02, plane="前视基准面", cx=0.0, cy=0.0):
    """圆拉伸（圆柱/圆盘）。"""
    if not _sketch(md, plane, "circle", 0, 0, r, cx, cy):
        return False
    fm = md.FeatureManager
    f = fm.FeatureExtrusion2(True, False, False, 0, 0, depth, 0.0,
                             False, False, False, False, 0.0, 0.0,
                             False, False, False, False, True, True, True, 0, 0.0, False)
    md.EditRebuild3()
    return f


def cut_circle(md, x, y, z, dx, dy, dz, r=0.005, cx=0.0, cy=0.0, through=True):
    """在命中的面上画圆并切除（默认完全贯穿）。"""
    if not _sketch_on_face(md, x, y, z, dx, dy, dz, "circle", r=r, cx=cx, cy=cy):
        return False
    fm = md.FeatureManager
    f = fm.FeatureCut4(*CUT27) if through else None
    md.EditRebuild3()
    return f


def cut_rect(md, x, y, z, dx, dy, dz, w=0.02, h=0.02, cx=0.0, cy=0.0, through=True):
    """在命中的面上画矩形并切除（默认完全贯穿）。"""
    if not _sketch_on_face(md, x, y, z, dx, dy, dz, "rect", w=w, h=h, cx=cx, cy=cy):
        return False
    fm = md.FeatureManager
    f = fm.FeatureCut4(*CUT27) if through else None
    md.EditRebuild3()
    return f


def _last_feature_name(md, type_name=None):
    hits = [n for n, ty in feature_names(md) if (type_name is None or ty == type_name)]
    return hits[-1] if hits else None


def pattern_circular(md, count=4, axis=(0.10, 0.0, 0.01, -1.0, 0.0, 0.0),
                     feature_name=None, radius=None):
    """圆周阵列：轴用外圆柱面上的射线选面（mark=1），特征按名字选（mark=4，坑 72）。

    axis = (x, y, z, dx, dy, dz)：射线从外部指向轴线，命中外圆柱面当旋转轴。
    """
    md.ClearSelection2(True)
    if not select_face(md, axis[0], axis[1], axis[2], axis[3], axis[4], axis[5], mark=1):
        return False
    name = feature_name or _last_feature_name(md, "ICE")
    if not name:
        return False
    if not md.Extension.SelectByID2(name, "BODYFEATURE", 0, 0, 0, True, 4, None, 0):
        return False
    if P(md.SelectionManager, "GetSelectedObjectCount2", -1) < 2:
        return False
    f = md.FeatureManager.FeatureCircularPattern4(count, 6.283185307179586,
                                                  False, "", False, True, False)
    md.EditRebuild3()
    return f


def pattern_linear(md, count=3, spacing=0.025, plane="右视基准面",
                   feature_name=None, flip=False):
    """线性阵列：方向用基准面（mark=1），特征按名字选（mark=4）。"""
    md.ClearSelection2(True)
    name = feature_name or _last_feature_name(md, "ICE")
    if not name:
        return False
    if not md.Extension.SelectByID2(name, "BODYFEATURE", 0, 0, 0, False, 4, None, 0):
        return False
    if not md.Extension.SelectByID2(plane, "PLANE", 0, 0, 0, True, 1, None, 0):
        return False
    # 22 参（R1 已验证顺序，勿删减，否则报 required argument 'SyncSubAssemblies' missing）
    f = md.FeatureManager.FeatureLinearPattern5(count, spacing, 1, 0.0,
                                                flip, False, "", "",
                                                False, False, False, False,
                                                True, False, False, False,
                                                False, False, 0.0, 0.0,
                                                False, False)
    md.EditRebuild3()
    return f


def apply_material(md, name="普通碳钢", database="solidworks materials.sldmat",
                   config="默认"):
    """写材质（入口在 IPartDoc，不是 IModelDocExtension，坑 60 前身）。"""
    pd = part(md)
    rc = pd.SetMaterialPropertyName2(config, database, name)
    md.EditRebuild3()
    return rc


def measure(md):
    """一次拿齐：体积/面积/质量/包围盒(mm)/实体数/特征名。"""
    st, arr = mass2(md)
    out = {"ok": arr is not None, "volume": None, "area": None, "mass": None,
           "bbox_mm": None, "bodies": None, "features": feature_names(md)}
    if arr:
        out.update(volume=arr[3], area=arr[4], mass=arr[5])
    try:
        out["bbox_mm"] = bbox(md)
    except Exception:
        pass
    try:
        out["bodies"] = bodies_count(md)
    except Exception:
        pass
    return out


def flange(sw, r_out=0.06, h=0.06, r_bore=0.03, r_hole=0.0055, pcd=0.045,
           n_hole=4, fillet_r=0.003, chamfer_w=0.002,
           material="普通碳钢", save_path=None):
    """法兰盘端到端：圆柱 → 中心孔 → 一个螺栓孔 → 圆周阵列 → 圆角 → 倒角 → 材质。

    返回 (md, 测量字典)。全部数值与解析式对得上（见 R26/R27 的回归表）。
    """
    md = new_part(sw)
    res = {"steps": []}

    solid_circle(md, r_out, h)
    res["steps"].append(("圆柱", measure(md)["volume"]))

    cut_circle(md, 0.02, 0.0, h + 0.01, 0.0, 0.0, -1.0, r_bore)
    res["steps"].append(("中心孔", measure(md)["volume"]))

    cut_circle(md, pcd, 0.0, h + 0.01, 0.0, 0.0, -1.0, r_hole, cx=pcd)
    res["steps"].append(("单孔", measure(md)["volume"]))

    pattern_circular(md, n_hole, (r_out + 0.02, 0.0, h / 2.0, -1.0, 0.0, 0.0))
    res["steps"].append(("圆周阵列", measure(md)["volume"]))

    if fillet_r:
        clear(md)
        select_edge(md, r_out, 0.0, h, 1.0, 0.0, 1.0, radius=0.0006)
        fillet(md, fillet_r)
        res["steps"].append(("圆角", measure(md)["volume"]))

    if chamfer_w:
        clear(md)
        select_edge(md, r_bore, 0.0, h, 1.0, 0.0, 1.0, radius=0.0006)
        chamfer(md, chamfer_w)
        res["steps"].append(("倒角", measure(md)["volume"]))

    if material:
        apply_material(md, material)
        res["steps"].append(("材质", measure(md)["mass"]))

    res.update(measure(md))
    if save_path:
        res["saved"] = save(md, save_path)
    return md, res


def drawing_front_section(sw, part_path, out_path=None, view="*前视",
                          view_at=(0.10, 0.15), sec_at=(0.10, 0.19), paper=PAPER_A4):
    """新建 A4 工程图 → 插入一个标准视图 → 画剖切线出剖视图 → 存盘。

    返回 dict(view_count, section_label, path)。必须先 open_part 过模型（坑 26 的另一面）。
    """
    d = drw(new_drawing(sw, paper))
    n0 = view_count(d)
    d.CreateDrawViewFromModelView3(part_path, view, view_at[0], view_at[1], 0.0)
    n1 = view_count(d)
    section_view(d, part_path, view, view_at, make_view=False, section_at=sec_at)
    n2 = view_count(d)
    label = None
    v = P(d, "GetFirstView")
    while v is not None:
        # 剖视图不一定是 Type==2，直接问它有剖面对象没有（本机实测更可靠）
        info = read_section(v)
        if info and info.get("label"):
            label = info["label"]
            break
        v = P(v, "GetNextView")
    out = {"view_count": (n0, n1, n2), "section_label": label}
    if out_path:
        out["saved"] = save(md2(d), out_path)
    return out

def table_rows(table, strip_tags=True):
    """把 ITableAnnotation（写在图上或视图上的表）读成二维字符串列表。"""
    import re as _re
    q = table.QueryInterface(SW.ITableAnnotation) if hasattr(table, "QueryInterface") else table
    rows = int(P(q, "RowCount")); cols = int(P(q, "ColumnCount"))
    out = []
    for r in range(rows):
        line = []
        for c in range(cols):
            txt = str(P(q, "DisplayedText", r, c))
            if strip_tags:
                txt = _re.sub(r"<[^>]+>", "", txt)
            line.append(txt)
        out.append(line)
    return out


def bom_table(drawing):
    """返回图纸上第一张表的二维内容 + 列标题；没有表就返回 (None, None)。

    坑 77：InsertBomTable2 返回的是 ITableAnnotation（不是 IBomTableAnnotation），
    行/列/文字都在 ITableAnnotation 上；IView.GetBomTable 是只写属性，
    用图纸的 GetTableAnnotations() 取最稳。
    """
    sheet = P(drawing, "GetFirstView")
    if int(P(sheet, "GetTableAnnotationCount")) < 1:
        return None, None
    arr = P(sheet, "GetTableAnnotations")
    table = arr[0] if hasattr(arr, "__getitem__") else arr
    rows = table_rows(table)
    q = table.QueryInterface(SW.ITableAnnotation)
    titles = [str(P(q, "GetColumnTitle", c)) for c in range(int(P(q, "ColumnCount")))]
    import re as _re
    return rows, [_re.sub(r"<[^>]+>", "", x) for x in titles]


def bom_components(table, row):
    """BOM 第 row 行（0-based）对应的组件列表（QI 成 IComponent2）。"""
    qb = table.QueryInterface(SW.IBomTableAnnotation)
    out = []
    for c in (P(qb, "GetComponents", row) or []):
        out.append(c.QueryInterface(SW.IComponent2))
    return out


def comp_path(comp):
    """组件对应的零件文件全路径；GetModelPathNames 常返回空，用组件自身最稳。"""
    for getter in ("GetPathName", "GetPathName2"):
        try:
            v = P(comp, getter)
            if v:
                return v
        except Exception:
            continue
    return None

def view_components(view):
    """剖视图/投影图上可见零件的 (名称, IComponent2) 列表。"""
    out = []
    try:
        arr = P(view, "GetVisibleComponents")
    except Exception:
        return out
    for c in (arr or []):
        try:
            cc = c.QueryInterface(SW.IComponent2)
        except Exception:
            cc = c
        try:
            nm = P(cc, "Name2")
        except Exception:
            nm = "?"
        out.append((nm, cc))
    return out


def view_basis(view):
    """IView.ModelToViewTransform 的 (xAxis, yAxis, zAxis, trans, scale)。

    ArrayData 是 16 个 double：[xAxis 0-2][yAxis 3-5][zAxis 6-8][trans 9-11][scale 12]。
    """
    a = [float(x) for x in list(P(P(view, "ModelToViewTransform"), "ArrayData"))]
    return a[0:3], a[3:6], a[6:9], a[9:12], a[12]


def model_to_view(view, p_model, c_model):
    """模型点 → 图纸坐标（米）。c_model 是视图在模型空间的中心（零件/装配包围盒中心）。"""
    ax, ay, az, t, sc = view_basis(view)
    d = [p_model[i] - c_model[i] for i in range(3)]
    v = [ax[i] * d[0] + ay[i] * d[1] + az[i] * d[2] for i in range(3)]
    return [t[i] + sc * v[i] for i in range(3)]


def auto_balloon(drawing, layout=1, ignore_multiple=False):
    """给当前选中的工程图视图自动加 BOM 气球，返回球标列表（可能为 None）。

    坑 79：AutoBalloon5(IAutoBalloonOptions) 在本机返回 None；AutoBalloon2(layout, ignoreMultiple) 可用。
    """
    got = P(drawing, "AutoBalloon2", layout, ignore_multiple)
    if not got:
        return None
    return list(got)
