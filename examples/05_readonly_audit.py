#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""05 · 只读体检：完整加载 / 轻化 / 压缩 / 重建 / 图像品质

诊断"显示异常是不是模型或加载的问题"时，先把这些事实读出来，
再决定要不要继续怀疑模型。

要点：

* 打开用 ``IDocumentSpecification``，**必须先 QI**，否则 ``OpenDoc7`` 报
  ``0x80020006 DISP_E_UNKNOWNNAME``（与 ``CreateDefinition`` 同源）。
* ``LightWeight=False`` + ``UseLightWeightDefault=False`` 强制全量加载，
  否则大装配会以轻化打开，边线/遮挡表现和全量加载不同。
* ``ReadOnly=True`` 打开，全程**不保存**。注意：建立/移除剖面视图会在内存里
  把文档标脏（标题出现 ``*``），所以结束时要**明确不保存**地关闭。

用法:
    python examples/05_readonly_audit.py --file "D:\\path\\to\\model.SLDASM"
    python examples/05_readonly_audit.py --file model.SLDASM --close   # 结束后不保存关闭
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

import swe  # noqa: E402


def open_readonly(sw, path):
    """只读 + 全量加载打开文档。"""
    spec = swe.P(sw, "GetOpenDocSpec", path)
    # 关键：无类型 _Dispatch 必须 QI 到 IDocumentSpecification 才能设属性
    spec = spec.QueryInterface(swe.SW.IDocumentSpecification)
    spec.Silent = True
    spec.ReadOnly = True
    spec.LightWeight = False
    spec.UseLightWeightDefault = False
    spec.InteractiveAdvancedOpen = False
    spec.AddToRecentDocumentList = False

    doc = swe.P(sw, "OpenDoc7", spec)
    if doc is None:
        raise RuntimeError(f"OpenDoc7 失败 (Error={getattr(spec, 'Error', '?')}, "
                           f"Warning={getattr(spec, 'Warning', '?')})")
    return doc.QueryInterface(swe.SW.IModelDoc2), spec


def audit(md):
    facts = {}
    facts["title"] = swe.P(md, "GetTitle")
    facts["path"] = swe.P(md, "GetPathName")
    facts["read_only"] = bool(swe.P(md, "IsOpenedReadOnly"))
    facts["display_mode"] = md.ActiveView.DisplayMode
    facts["tess_quality"] = swe.P(md, "GetTessellationQuality")
    facts["feature_count"] = swe.P(md, "GetFeatureCount")
    facts["save_flag"] = swe.P(md, "GetSaveFlag")

    try:
        asm = md.QueryInterface(swe.SW.IAssemblyDoc)
        comps = asm.GetComponents(False) or []
        facts["components"] = len(comps)
        facts["suppressed"] = sum(1 for c in comps if c.IsSuppressed())
        facts["hidden"] = sum(1 for c in comps if c.IsHidden())
        facts["lightweight"] = swe.P(asm, "GetLightWeightComponentCount")
    except Exception:
        facts["components"] = None      # 不是装配体

    facts["rebuild_ok"] = bool(swe.P(md, "EditRebuild3"))
    return facts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="零件或装配体路径")
    ap.add_argument("--close", action="store_true", help="结束后不保存关闭（仅自己打开的文档）")
    args = ap.parse_args()

    path = os.path.abspath(args.file)
    if not os.path.exists(path):
        raise SystemExit(f"文件不存在: {path}")

    sw = swe.connect(visible=True)

    already = swe.P(sw, "GetOpenDocumentByName", path)
    opened_here = False
    if already is not None:
        md = already.QueryInterface(swe.SW.IModelDoc2)
        print("文档已在会话中打开，直接复用")
    else:
        md, _spec = open_readonly(sw, path)
        opened_here = True
        print("已只读打开")

    facts = audit(md)
    for k, v in facts.items():
        print(f"  {k:<14}: {v}")

    print("\n判读")
    if facts.get("components") is not None:
        if facts["suppressed"] or facts["hidden"]:
            print(f"  !! 有压缩/隐藏组件（suppressed={facts['suppressed']}, "
                  f"hidden={facts['hidden']}）——先解决这个再看显示问题")
        else:
            print(f"  OK 组件全部参与，无压缩/隐藏（{facts['components']} 个）")
    if facts["rebuild_ok"]:
        print("  OK 重建无错误")
    else:
        print("  !! 重建报错——先查特征/配合，再谈显示")
    if facts["tess_quality"] and facts["tess_quality"] < 80:
        print(f"  !! 文档图像品质只有 {facts['tess_quality']}：圆/球会被折线化，"
              + f"这是「碎线」的独立贡献项（见 troubleshooting/display-artifacts.md）")

    if opened_here and args.close:
        if facts.get("save_flag"):
            print("\n注意：文档在内存中已标脏（'*'）。按你的要求**不保存**。")
        sw.CloseDoc(facts["title"])
        print("已不保存关闭")
    else:
        print("\n文档保持打开。若标题出现 '*'，关闭时请选「不保存」。")


if __name__ == "__main__":
    main()
