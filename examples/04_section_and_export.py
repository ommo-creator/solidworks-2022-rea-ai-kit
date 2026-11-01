#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""04 · 剖切 + 导出，并验证导出的不是空图

覆盖三件在别处很少写清楚的事：

1. ``ISectionViewData`` 的属性**必须用 setter 包装逐项写**，直接赋值会得到
   ``COMError: (-2147352570, '未知名称。')``；``FirstPlane`` 要先选中基准面再取回 Dispatch。
2. ``SaveBMP`` 读的是**当前视口前缓冲**，窗口不可见 / 未重绘时导出空白帧且返回 True。
3. 所以导出必须**自带像素校验**，否则你会拿着空图去标注。

全程只改视图状态；**不保存文档**，结束时移除剖面视图。

用法:
    python examples/04_section_and_export.py --out ./shots
    python examples/04_section_and_export.py --plane 上视基准面 --cap off --hlr
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

import swe  # noqa: E402

W, H = 2560, 1440
MIN_DARK = 200          # 经验阈值：正常线稿远高于此；0 说明是空帧


def find_plane(md, keyword):
    """按名字关键字找基准面特征。不硬编码中文字符串更稳：先按名称匹配，匹配不到就取序号。

    RefPlane 序号：1 = 前视, 2 = 上视, 3 = 右视（见 docs/18-ui-strings.md）。
    """
    planes = []
    for f in swe.features(md):
        try:
            if f.GetTypeName2() == "RefPlane":
                planes.append(f)
        except Exception:
            continue
    for f in planes:
        try:
            if keyword and keyword in f.Name:
                return f
        except Exception:
            continue
    order = {"前视": 0, "上视": 1, "右视": 2,
             "Front": 0, "Top": 1, "Right": 2}
    for k, idx in order.items():
        if k in (keyword or "") and len(planes) > idx:
            return planes[idx]
    return planes[0] if planes else None


def plane_dispatch(md, plane_feat):
    """选中基准面，再从 SelectionManager 取回 Dispatch。

    直接拿 IFeature 指针赋给 ``FirstPlane`` 在本版本上不稳定；"选中再取回"才是稳的路径。
    （注意：``md.SelectByID2`` 在部分安装上抛 COMError，所以这里用特征对象自己的 Select2。）
    """
    md.ClearSelection2(True)
    plane_feat.Select2(False, 0)
    sel = swe.P(md, "SelectionManager")
    disp = swe.P(sel, "GetSelectedObject6", 1, -1)
    md.ClearSelection2(True)
    if disp is None:
        raise RuntimeError("没能取回基准面的 Dispatch")
    return disp


def create_section(md, plane_feat, cap=False, graphics_only=True, transparent=False):
    mvm = swe.P(md, "ModelViewManager")
    svd = swe.P(mvm, "CreateSectionViewData")
    if svd is None:
        raise RuntimeError("CreateSectionViewData 返回 None")

    # 全部走 setter 包装：直接赋值 -> 0x80020006 DISP_E_UNKNOWNNAME
    swe.P(svd, "FirstPlane", plane_dispatch(md, plane_feat))
    swe.P(svd, "FirstOffset", 0.0)
    swe.P(svd, "FirstReverseDirection", False)
    swe.P(svd, "ShowSectionCap", cap)
    swe.P(svd, "GraphicsOnlySection", graphics_only)
    swe.P(svd, "TransparentSection", transparent)
    swe.P(svd, "Redraw")

    ok = swe.P(mvm, "CreateSectionView", svd)
    if not ok:
        raise RuntimeError("CreateSectionView 返回 False")
    return ok


def remove_section(md):
    try:
        return swe.P(swe.P(md, "ModelViewManager"), "RemoveSectionView")
    except Exception:
        return False


def export_checked(md, path):
    """SaveBMP + 像素校验。返回暗像素数。"""
    import numpy as np
    from PIL import Image

    ok = swe.P(md, "SaveBMP", path, W, H)
    if not ok:
        raise RuntimeError(f"SaveBMP 返回 False: {path}")
    a = np.asarray(Image.open(path).convert("L"), dtype=np.int16)
    dark = int((a < 128).sum())
    if dark < MIN_DARK:
        raise RuntimeError(
            f"导出疑似空/陈旧帧（dark={dark}, min={int(a.min())}）: {path}\n"
            "  原因几乎总是窗口不可见或未重绘。把 SolidWorks 窗口放到前台、"
            "先做一次改变模型状态的操作（切显示模式/重建），再导出。"
        )
    return dark, int(a.min())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="shots")
    ap.add_argument("--plane", default="前视基准面")
    ap.add_argument("--cap", choices=["on", "off"], default="off")
    ap.add_argument("--hlr", action="store_true", help="先切到隐藏线消除再导出（推荐）")
    ap.add_argument("--graphics-only", action="store_true", default=True)
    ap.add_argument("--real-section", dest="graphics_only", action="store_false",
                    help="用真剖切而不是图形剖切")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    sw = swe.connect(visible=True)
    md = sw.ActiveDoc
    if md is None:
        raise SystemExit("没有打开的文档")

    plane = find_plane(md, args.plane)
    if plane is None:
        raise SystemExit("找不到任何基准面")
    print(f"基准面: {plane.Name}")

    if args.hlr:
        sw.RunCommand(335, "")          # 隐藏线消除
        print("显示模式: 隐藏线消除 (335)")

    created = False
    try:
        create_section(md, plane, cap=(args.cap == "on"),
                       graphics_only=args.graphics_only, transparent=False)
        created = True
        print(f"剖面已建立: cap={args.cap} graphics_only={args.graphics_only}")

        path = os.path.join(args.out, "section_export.bmp")
        dark, mn = export_checked(md, path)
        print(f"导出: {path}")
        print(f"校验: dark<128 = {dark}   min = {mn}   -> 非空图 OK")
    finally:
        if created:
            print("移除剖面:", "ok" if remove_section(md) else "失败（请手动清除）")
        print("本脚本没有保存任何文档。")


if __name__ == "__main__":
    main()
