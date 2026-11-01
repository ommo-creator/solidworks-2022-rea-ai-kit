#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sw-com-reversed 环境自检。

用法：
    python preflight.py            # 只查环境，不连 SolidWorks
    python preflight.py --connect  # 额外建一个可见实例并读版本号

退出码：0 = 全部关键项通过；1 = 有 FAIL。
"""
import importlib
import json
import os
import subprocess
import sys

# Windows 下子进程 stdout 默认走本地代码页（GBK），调用方按 UTF-8 解码会乱码。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

OK = "[ OK ]"
NO = "[FAIL]"
WARN = "[WARN]"

failures = []
result = {}


def check(label, fn):
    try:
        detail = fn()
        print(f"{OK} {label}: {detail}")
        result[label] = {"ok": True, "detail": str(detail)}
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"{NO} {label}: {exc}")
        result[label] = {"ok": False, "detail": str(exc)}
        failures.append(label)
        return False


def py_version():
    return sys.version.split()[0] + f" ({sys.executable})"


def comtypes_info():
    ct = importlib.import_module("comtypes")
    return getattr(ct, "__version__", "unknown")


def gen_module():
    try:
        importlib.import_module("comtypes.gen.SldWorks")
        return "comtypes.gen.SldWorks 已生成"
    except Exception:  # noqa: BLE001
        return "未生成（首次 CreateObject 后会自动生成，或需 GetModule）"


def sw_process():
    out = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq SLDWORKS.exe", "/NH"],
        capture_output=True, text=True, timeout=30,
    ).stdout
    n = out.lower().count("sldworks.exe")
    return f"{n} 个 SLDWORKS.exe 在运行" + ("" if n else "（不影响，CreateObject 会自己拉起）")


def templates():
    roots = [
        r"C:\ProgramData\SolidWorks\SOLIDWORKS 2022\templates",
        r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2022\templates",
    ]
    hits = [d for d in roots if os.path.isdir(d)]
    if not hits:
        raise FileNotFoundError("找不到模板目录，检查安装版本")
    root = hits[0]
    parts = [f for f in os.listdir(root) if f.endswith((".prtdot", ".asmdot", ".drwdot"))]
    return f"{root}（{len(parts)} 个模板）"


def connect_and_version():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import swe  # noqa: PLC0415

    sw = swe.connect(visible=True)
    try:
        rev = swe.P(sw, "RevisionNumber")
    except Exception:  # noqa: BLE001
        rev = "?"
    return f"已连上，RevisionNumber={rev}"


def main():
    print("=" * 60)
    print("sw-com-reversed preflight")
    print("=" * 60)
    check("python", py_version)
    check("comtypes", comtypes_info)
    check("comtypes.gen.SldWorks", gen_module)
    check("SolidWorks 进程", sw_process)
    check("模板目录", templates)
    if "--connect" in sys.argv:
        check("COM 连接", connect_and_version)
    print("-" * 60)
    print(json.dumps({"failures": failures}, ensure_ascii=False))
    if failures:
        print(f"{len(failures)} 项失败：{', '.join(failures)}")
        return 1
    print("全部关键项通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
