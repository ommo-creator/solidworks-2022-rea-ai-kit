#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""02 · 显示模式：用 RunCommand 切，并验证"写 DisplayMode 是无效的"

这个脚本现场证明两件事：

1. ``IModelView.DisplayMode = 2`` **不生效**（回读不变）——这是本版本的真实行为，
   网上大量示例教你这么写，在本版本上只会静默失败。
2. ``ISldWorks.RunCommand(命令号, "")`` **立即生效且可回读**。

全程只改视图状态，不保存文档、不改任何系统选项。

用法:
    python examples/02_display_modes.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

import swe  # noqa: E402

# data/enums.json -> swViewDisplayMode_e（与实测回读值一致）
MODES = [
    (334, "wireframe",        1),
    (335, "hidden-lines-removed (HLR)", 2),
    (336, "hidden-lines-visible (HLV)", 3),
    (337, "shaded",           4),
    (506, "shaded-with-edges", 5),
]


def active_md(sw):
    """拿到当前活动文档的 IModelDoc2（无文档则报错）。"""
    md = sw.ActiveDoc
    if md is None:
        raise SystemExit("没有打开的文档：先打开一个零件或装配体")
    return md


def main():
    sw = swe.connect(visible=True)
    md = active_md(sw)
    mv = md.ActiveView

    print("=== 实验 A：直接写 DisplayMode（预期失败）")
    before = mv.DisplayMode
    try:
        mv.DisplayMode = 2            # 想切 HLR
    except Exception as exc:
        print("  赋值抛错:", type(exc).__name__, exc)
    after = mv.DisplayMode
    print(f"  写入前={before}  写入后={after}  ->",
          "生效" if after == 2 else "**未生效**（本版本已知行为）")

    print("\n=== 实验 B：RunCommand（预期成功）")
    for cmd, label, expect in MODES:
        ok = sw.RunCommand(cmd, "")
        got = mv.DisplayMode
        flag = "OK " if got == expect else "!! "
        print(f"  {flag}RunCommand({cmd:>3}) {label:<28} 回读={got}  期望={expect}  ok={ok}")

    # 收尾：回到带边线上色并报告（不写盘，不改设置）
    sw.RunCommand(506, "")
    print(f"\n已复位为带边线上色，当前 DisplayMode={mv.DisplayMode}")
    print("提示：本脚本没有保存任何文档。")


if __name__ == "__main__":
    main()
