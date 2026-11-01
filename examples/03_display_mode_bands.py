#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""03 · 把"显示很难看"变成可测的数字：五种模式 × 亮度分带

这是定位显示异常的主武器。它做三件事：

1. 把窗口恢复并前置（``SaveBMP`` 读的是**当前视口前缓冲**，最小化时导出的是陈旧帧）；
2. 逐一切换五种显示模式，各导出一张同尺寸图；
3. 按亮度分带统计像素，输出一张可比较的表。

判读方法（实测基准，见 troubleshooting/display-artifacts.md）：

* ``<128``   = 真正的黑线
* ``128-190``= 灰线 / 隐藏线
* ``190-235``= 背景渐变或着色面（纯白背景下应为 0）
* 五种模式的 ``<128`` 都接近 0  -> 导出链路坏了（前缓冲没重绘），不是模型问题

依赖: comtypes（COM 侧）、Pillow + numpy（图像侧）::

    pip install pillow numpy

用法:
    python examples/03_display_mode_bands.py --out ./shots
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

import swe  # noqa: E402

MODES = [
    (334, "M1_wireframe"),
    (335, "M2_hlr"),
    (336, "M3_hlv"),
    (337, "M4_shaded"),
    (506, "M5_shaded_edges"),
]

W, H = 2560, 1440


def ensure_visible():
    """把 SolidWorks 主窗口恢复、最大化并前置。

    ``SaveBMP`` 不是离屏渲染器：窗口最小化时它会把上一帧甚至空白帧存下来，
    而且照样返回 True。所以导出前必须先保证窗口可见。
    """
    try:
        import win32con
        import win32gui
    except ImportError:
        print("  ! 没装 pywin32，无法自动恢复窗口：请手动把 SolidWorks 窗口放到前台")
        return False

    found = []

    def cb(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if "SOLIDWORKS" in title.upper():
            found.append((hwnd, title))

    win32gui.EnumWindows(cb, None)
    if not found:
        print("  ! 找不到 SolidWorks 主窗口（可能已最小化到托盘）")
        return False

    hwnd, title = found[0]
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass
    print(f"  窗口: {title!r} -> 已恢复/最大化")
    return True


def bands(path):
    """按亮度分带统计，返回 dict。"""
    import numpy as np
    from PIL import Image

    a = np.asarray(Image.open(path).convert("L"), dtype=np.int16)
    return {
        "lt128": int((a < 128).sum()),
        "mid": int(((a >= 128) & (a < 190)).sum()),
        "bg": int(((a >= 190) & (a < 235)).sum()),
        "white": int((a >= 235).sum()),
        "min": int(a.min()),
        "mean": round(float(a.mean()), 1),
    }


def export_bmp(md, path):
    """SaveBMP 并确认文件真的写出来了。"""
    ok = swe.P(md, "SaveBMP", path, W, H)
    if not ok or not os.path.exists(path) or os.path.getsize(path) < 1024:
        raise RuntimeError(f"SaveBMP 失败: {path}")
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="shots", help="导出目录")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    sw = swe.connect(visible=True)
    md = sw.ActiveDoc
    if md is None:
        raise SystemExit("没有打开的文档")

    print("=== 第 0 步：保证窗口可见")
    ensure_visible()

    print("\n=== 第 1 步：五种模式各导一张")
    rows = []
    for cmd, label in MODES:
        sw.RunCommand(cmd, "")
        path = os.path.join(args.out, label + ".bmp")
        export_bmp(md, path)
        b = bands(path)
        rows.append((label, b))
        print(f"  {label:<18} dark<128={b['lt128']:>7}  mid={b['mid']:>6}  "
              f"bg={b['bg']:>7}  min={b['min']:>3}")

    print("\n=== 第 2 步：判读")
    dark = {label: b["lt128"] for label, b in rows}
    if max(dark.values()) < 200:
        print("  !! 所有模式都没有黑线 -> 导出链路有问题（前缓冲未重绘 / 窗口不可见）")
        print("     先把窗口放到前台重跑，不要怀疑模型或显卡。")
    else:
        best = max(dark, key=dark.get)
        print(f"  线像素最多的模式: {best}")
        print("  注意：线最多 != 最好看。着色模式的线会互相叠加（多重轮廓），")
        print("        线稿用途应该选 M2_hlr（隐藏线消除）。")

    sw.RunCommand(506, "")
    print(f"\n已复位为带边线上色。图片在 {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
