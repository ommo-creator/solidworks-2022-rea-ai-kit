#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""01 · 连接与体检（只读，不改任何设置）

跑通这个脚本，说明你的通道是对的：能连上、能读到 Application 级信息、
能枚举已打开的文档。如果这里就报 0x8002000B DISP_E_BADINDEX，说明你在用
PowerShell + Interop RCW —— 换 Python + comtypes。

用法:
    python examples/01_connect.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

import swe  # noqa: E402


def main():
    sw = swe.connect(visible=True)

    print("revision      :", sw.RevisionNumber)        # 2022 SP5.0 -> 30.5.0
    print("executable    :", sw.GetExecutablePath())
    print("visible       :", sw.Visible)

    # 模板目录：NewPart 要用到，路径随安装变化，别硬编码
    try:
        print("part template :", sw.GetUserPreferenceStringValue(196))   # swFileLocationsPartTemplates
    except Exception as exc:                                            # pragma: no cover
        print("part template : <unavailable>", type(exc).__name__)

    docs = sw.GetDocuments()
    n = 0 if docs is None else len(docs)
    print("open documents:", n)

    for d in (docs or []):
        md = d if hasattr(d, "GetPathName") else None
        try:
            title = swe.P(d, "GetTitle")
            path = swe.P(d, "GetPathName")
            ro = swe.P(d, "IsOpenedReadOnly")
        except Exception:
            title, path, ro = "<n/a>", "<n/a>", "<n/a>"
        print(f"  - {title!r}")
        print(f"      path      : {path}")
        print(f"      read-only : {ro}")

    print("\nOK：通道可用。下一步跑 examples/02_display_modes.py")


if __name__ == "__main__":
    main()
