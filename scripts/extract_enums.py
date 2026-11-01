#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract every `swconst` enumeration (name -> {member: value}) from the
decompiled SolidWorks API CHM and write ``data/enums.json``.

Why this exists
---------------
SolidWorks 2022 does **not** expose its enum values to Python through
``comtypes``: the generated ``comtypes.gen.SldWorks`` module contains methods
but zero ``sw*`` constants (``hasattr(SldWorks, "swDocPART")`` is ``False``),
and the CHM's method index has no enumeration pages either.  The values live
in the separate ``swconst`` namespace of ``sldworksapi.chm``.

So the recovery route is: decompile the CHM once, then parse the
``SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.<Enum>_e.html`` pages.

Decompile step (run once, needs the CHM installed by SolidWorks):

    hh.exe -decompile <out_dir> "<SW_INSTALL>\\api\\sldworksapi.chm"

Then:

    python scripts/extract_enums.py <out_dir> -o data/enums.json

Only the *name → value* pairs are published here.  No page prose, no help
URLs, nothing machine- or customer-specific.
"""
from __future__ import annotations

import argparse
import glob
import html
import json
import os
import re
import sys

# <TR><TD CLASS=MemberNameCell><strong>swFoo</strong></TD><TD CLASS="DescriptionCell">7</TD></TR>
ROW = re.compile(
    r"MemberNameCell>\s*<strong>\s*([A-Za-z_][A-Za-z0-9_]*)\s*</strong>\s*"
    r"</TD>\s*<TD[^>]*>\s*([^<]*?)\s*</TD>",
    re.I | re.S,
)
TITLE = re.compile(r"<title>\s*([A-Za-z_][A-Za-z0-9_]*)\s+Enumeration\s*</title>", re.I)
NAME_FROM_FILE = re.compile(
    r"swconst~(?:SolidWorks\.Interop\.swconst\.)?([A-Za-z_][A-Za-z0-9_]*?)_e\.html?$", re.I
)
# member name regardless of what the description cell holds (links, prose, numbers)
ALLNAMES = re.compile(
    r"MemberNameCell>\s*<strong>\s*([A-Za-z_][A-Za-z0-9_]*)\s*</strong>", re.I
)
INT = re.compile(r"^-?\d+$")


def parse_int(text: str):
    """Return the enum's numeric value, or None when the cell is prose."""
    t = html.unescape(text).strip().rstrip(".,;")
    if INT.match(t):
        return int(t)
    # some cells read like "0x0004" or "4 = swFooBar"
    if re.match(r"^0x[0-9A-Fa-f]+$", t):
        return int(t, 16)
    m = re.match(r"^(-?\d+)\b", t)
    if m:
        return int(m.group(1))
    return None


def parse_page(path: str):
    try:
        raw = open(path, "r", encoding="utf-8", errors="replace").read()
    except OSError:
        return None, None, None

    name = None
    m = TITLE.search(raw)
    if m:
        name = m.group(1)
    if not name:
        m = NAME_FROM_FILE.search(os.path.basename(path).replace("\\", "/"))
        if m:
            name = m.group(1).replace("\\", "")
    if not name:
        return None, None, None

    # only the Members block matters; stop before "See Also"
    start = raw.find("enummembersSection")
    body = raw[start:] if start >= 0 else raw
    cut = body.find("seealsoSection")
    if cut > 0:
        body = body[:cut]

    members, names_only = {}, []
    for mm in ROW.finditer(body):
        member, cell = mm.group(1), mm.group(2)
        val = parse_int(cell)
        if val is not None:
            members[member] = val
    # every member that did not yield a number (prose/link cells) is kept by name
    all_names = []
    for mm in ALLNAMES.finditer(body):
        n = mm.group(1)
        if n not in all_names:
            all_names.append(n)
    names_only = sorted(n for n in all_names if n not in members)
    return name, members, names_only


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("chm_dir", help="directory produced by `hh.exe -decompile`")
    ap.add_argument("-o", "--out", default="data/enums.json")
    ap.add_argument("--indent", type=int, default=1)
    args = ap.parse_args(argv)

    pattern = os.path.join(args.chm_dir, "**", "*swconst*_e.html*")
    files = sorted(glob.glob(pattern, recursive=True))
    if not files:
        print(f"ERROR: no enum pages under {args.chm_dir!r} "
              f"(looked for {pattern})", file=sys.stderr)
        return 2

    enums, names_only, skipped = {}, {}, 0
    for path in files:
        name, members, bare = parse_page(path)
        if not name:
            skipped += 1
            continue
        if members:
            enums[name] = members
        if bare:
            names_only[name] = bare
        if not members and not bare:
            skipped += 1

    payload = {
        "_meta": {
            "source": "sldworksapi.chm / SolidWorks.Interop.swconst (SolidWorks 2022)",
            "note": "enums = name -> value; namesOnly = members whose value is not "
                    "documented numerically in the CHM (classic swUserPreference* / "
                    "swAppearance* tables). Pages scanned: %d." % len(files),
            "enumsWithValues": len(enums),
            "enumsNamesOnly": len(names_only),
            "membersWithValues": sum(len(v) for v in enums.values()),
            "memberNamesOnly": sum(len(v) for v in names_only.values()),
        },
        "enums": enums,
        "namesOnly": names_only,
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=args.indent,
                  sort_keys=True)
        fh.write("\n")

    print(f"pages scanned : {len(files)}")
    print(f"enums w/values: {len(enums)}  ({payload['_meta']['membersWithValues']} members)")
    print(f"enums names   : {len(names_only)}  ({payload['_meta']['memberNamesOnly']} members)")
    print(f"skipped       : {skipped}")
    print(f"output        : {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
