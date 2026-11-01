# -*- coding: utf-8 -*-
"""GB/T 9124.1-2019 板式平焊钢制管法兰（PLF）尺寸表（单位：毫米）。

数据来源：河北广浩管件有限公司公开的 PN10 / PN16 版式平焊法兰尺寸表
  https://www.ghfitting.com/news/chinese-flange/132.html   （PN10）
  https://www.ghfitting.com/news/chinese-flange/133.html   （PN16）
并抽样与第三方 CAD 库对照（DN100 PN16：D=220、C=22、密封面 d=158）。

字段：
  A1/A2  钢管外径 系列I / 系列II
  D      法兰外径
  K      螺栓孔中心圆直径
  L      螺栓孔直径
  n      螺栓孔数量
  thd    螺栓螺纹规格
  C      法兰厚度
  d      密封面外径（凸面 d4）
  f      密封面高度（凸面 f）
  B1/B2  法兰内径 系列I / 系列II

注意：DN10~DN40 按标准注释放宽到 PN40 尺寸；PN10 与 PN16 两页在 DN50~DN150 上给出相同数值，
若用于承压计算请以纸质标准复核。本表只用于建模尺寸驱动。
"""

# DN: (A1, A2, D, K, L, n, thd, C, d, f, B1, B2)
_ROWS = {
    50:  (60.3, 57, 165, 125, 18, 4, "M16", 20, 102, 3, 61.5, 59),
    65:  (73.0, 76, 185, 145, 18, 8, "M16", 20, 122, 3, 77.5, 78),
    80:  (88.9, 89, 200, 160, 18, 8, "M16", 20, 138, 3, 90.5, 91),
    100: (114.3, 108, 220, 180, 18, 8, "M16", 22, 158, 3, 116.0, 110),
    125: (139.7, 133, 250, 210, 18, 8, "M16", 22, 188, 3, 141.5, 135),
    150: (168.3, 159, 285, 240, 22, 8, "M20", 24, 212, 3, 170.5, 161),
    200: (219.1, 219, 340, 295, 22, 8, "M20", 24, 268, 3, 221.5, 222),
}

PN_SUPPORTED = ("PN10", "PN16")


def get(dn, pn="PN16", series=1):
    """取一条法兰尺寸，长度单位换算成米，方便直接喂给 swe.flange()。

    返回 dict：
      dn, pn, series, D, K, L, n, C, d_face, f_face, bore, a_od, thd
    以及可直接使用的几何参数：r_out / h / r_bore / r_hole / pcd
    """
    if dn not in _ROWS:
        raise KeyError("DN%d 不在本表（可用 %s）" % (dn, sorted(_ROWS)))
    if pn not in PN_SUPPORTED:
        raise KeyError("PN %s 不在本表（可用 %s）" % (pn, PN_SUPPORTED))
    if series not in (1, 2):
        raise KeyError("series 只能是 1 或 2")
    a1, a2, D, K, L, n, thd, C, d, f, b1, b2 = _ROWS[dn]
    bore = b1 if series == 1 else b2
    mm = 0.001
    return {
        "dn": dn, "pn": pn, "series": series,
        "A_od": (a1 if series == 1 else a2), "D": D, "K": K, "L": L, "n": n,
        "C": C, "d_face": d, "f_face": f, "bore": bore, "thd": thd,
        "r_out": D * mm / 2.0, "h": C * mm, "r_bore": bore * mm / 2.0,
        "r_hole": L * mm / 2.0, "pcd": K * mm / 2.0,
    }


def table(pn="PN16", series=1):
    return [get(dn, pn, series) for dn in sorted(_ROWS)]
