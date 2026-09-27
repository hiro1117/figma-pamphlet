#!/usr/bin/env python3
"""レイアウトマスク(幾何図形のみ)と系統色チップを生成する。

- 出典: docs/prep/physical-size.md(表紙面 99×210mm、k=5.69)、Figma #config(2057:2) presets.K2B_panel.by_family(B.1 v2、2026-09-28)
- テンプレや完成見本のスクショは一切使わない(白/灰の矩形だけ)。文字は描かない(生成 AI の参照に渡すため)

出力: docs/library/masks/
  K2B-mask-face-<family>.png  表紙面 99×210mm 全体(塗り足し込み 102×213mm)。白パネル・ヒーロー枠・地域モチーフ帯・人物/車両の想定位置・文字ゾーン
  K2B-mask-hero-<family>.png  ヒーロー枠だけ(裁ち落としなし、系統ごとに 488×329〜500px = 85.8×57.8〜87.9mm)。背景生成の参照
  chips-<family>.png          系統の色チップ
  _old_K2-*.png / _old_K1-*.png  旧 K2(上ビジュアル 102×125mm)用。B.1 v2 で不採用
"""
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[2] / "docs/library/masks"
S = 10          # マスクの px/mm(Figma の k とは無関係)
K = 5.69        # Figma px/mm
FACE_W, FACE_H = 99.0, 210.0
BLEED = 3.0
FOLD_MARGIN = 8.0
COVER_X = 1127.3  # 表紙面のフレーム内 x(#config.cover_face)

# Figma #config presets.K2B_panel.by_family(表紙面ローカル px は frame 座標 − 1127.3)
K2B = {
    "aitoma":        dict(hero=(1169, 172, 488, 398), motif=(1169, 310, 488, 143), vehicle=(1353, 397, 300, 173), person=(1183, 249, 113, 317)),
    "nachikatsuura": dict(hero=(1169, 241, 488, 329), motif=(1169, 380, 488, 143), vehicle=(1353, 397, 300, 173), person=(1183, 283, 92, 283)),
    "noboribetsu":   dict(hero=(1165, 217, 488, 354), motif=(1169, 380, 488, 143), vehicle=(1353, 397, 300, 173), person=(1183, 249, 126, 317)),
    "mitt":          dict(hero=(1169, 200, 488, 500), motif=(1169, 420, 488, 143), vehicle=(1353, 527, 300, 173), person=(1183, 379, 151, 317)),
}
# 白パネル(ヒーローの外側に 8px 程度の白地。実測ではなく描画用の目安)
PANEL_PAD = 8

C_IMAGE = (255, 255, 255)
C_BLEED = (200, 200, 200)
C_INFO = (160, 160, 160)
C_ZONE = (110, 110, 110)
C_BAND = (235, 235, 235)
C_FG = (215, 215, 215)
C_LINE = (60, 60, 60)


def mm(v):
    return int(round(v * S))


def px2mm(v):
    return v / K


def draw_face(fam):
    """表紙面全体(塗り足し込み)。原点 = 塗り足し込みの左上。"""
    c = K2B[fam]
    W, H = mm(FACE_W + BLEED), mm(FACE_H + BLEED)
    im = Image.new("RGB", (W, H), C_INFO)
    d = ImageDraw.Draw(im)
    top = mm(BLEED)
    # 塗り足し域(上・右)
    d.rectangle([0, 0, W, top], fill=C_BLEED)
    d.rectangle([W - mm(BLEED), 0, W, H], fill=C_BLEED)

    def box(px, pad=0):
        x, y, w, h = px
        x0 = mm(px2mm(x - COVER_X - pad)); y0 = top + mm(px2mm(y - pad))
        return [x0, y0, x0 + mm(px2mm(w + 2 * pad)), y0 + mm(px2mm(h + 2 * pad))]

    d.rectangle(box(c["hero"], PANEL_PAD), fill=C_IMAGE)        # 白パネル
    d.rectangle(box(c["hero"]), fill=C_IMAGE, outline=C_LINE, width=2)  # ヒーロー枠
    d.rectangle(box(c["motif"]), fill=C_BAND)                    # 地域モチーフ帯
    d.rectangle(box(c["vehicle"]), fill=C_FG, outline=C_LINE, width=1)
    d.rectangle(box(c["person"]), fill=C_FG, outline=C_LINE, width=1)
    # 文字ゾーン: ヒーロー上(タイトル)とヒーロー下(CTA)
    hx0, hy0, hx1, hy1 = box(c["hero"])
    d.rectangle([mm(FOLD_MARGIN), top + mm(10), hx1, hy0 - mm(6)], fill=C_ZONE)
    d.rectangle([mm(FOLD_MARGIN), hy1 + mm(8), W - mm(BLEED + 3), H - mm(FOLD_MARGIN + 30)], fill=C_ZONE)
    d.rectangle([0, top, W - mm(BLEED), H], outline=C_LINE, width=2)  # 仕上がり・折り線
    return im


def draw_hero(fam):
    """ヒーロー枠だけ(裁ち落としなし)。地域モチーフ帯と人物・車両の想定位置を薄く示す。"""
    x, y, w, h = K2B[fam]["hero"]
    W, H = mm(px2mm(w)), mm(px2mm(h))
    im = Image.new("RGB", (W, H), C_IMAGE)
    d = ImageDraw.Draw(im)

    def rel(px):
        px_, py_, pw, ph = px
        x0 = mm(px2mm(px_ - x)); y0 = mm(px2mm(py_ - y))
        return [x0, y0, x0 + mm(px2mm(pw)), y0 + mm(px2mm(ph))]

    d.rectangle(rel(K2B[fam]["motif"]), fill=C_BAND)
    d.rectangle(rel(K2B[fam]["vehicle"]), fill=C_FG)
    d.rectangle(rel(K2B[fam]["person"]), fill=C_FG)
    d.rectangle([0, 0, W - 1, H - 1], outline=C_LINE, width=2)
    return im


# docs/prep/colors.md の実測値
FAMILIES = {
    "aitoma": ["#EB6EA5", "#F6BED1", "#FFD8E3", "#FFFFFF", "#000000"],
    "nachikatsuura": ["#1B98D0", "#76C1E3", "#E3F7FF", "#FFFFFF", "#000000"],
    "noboribetsu": ["#D7835F", "#F9F2DC", "#FFF9B3", "#FFFFFF", "#513A1E"],
    "mitt": ["#254F99", "#258FC2", "#143747", "#FAEF50", "#FFFFFF", "#231815"],
}

# Gemini 3 Pro Image の対応比率(横長のみ)
GEMINI_RATIOS = {"1:1": 1.0, "5:4": 1.25, "4:3": 4 / 3, "3:2": 1.5, "16:9": 16 / 9, "21:9": 21 / 9}


def ratio_table():
    rows = []
    for fam, c in K2B.items():
        w, h = c["hero"][2], c["hero"][3]; fr = w / h
        name, r = min(GEMINI_RATIOS.items(), key=lambda kv: abs(kv[1] - fr))
        # CROP(枠を満たす): 画像が枠より横長なら左右が切れる、縦長なら上下が切れる
        if r > fr:
            cut = (1 - fr / r) * 100; where = "左右"
        else:
            cut = (1 - r / fr) * 100; where = "上下"
        rows.append((fam, w, h, round(fr, 3), name, round(r, 3), where, round(cut, 1)))
    return rows


def draw_chips(colors):
    n = len(colors)
    im = Image.new("RGB", (n * 200, 200), (255, 255, 255))
    d = ImageDraw.Draw(im)
    for i, c in enumerate(colors):
        d.rectangle([i * 200, 0, (i + 1) * 200, 200], fill=c, outline=(128, 128, 128), width=2)
    return im


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for fam in K2B:
        draw_face(fam).save(OUT / f"K2B-mask-face-{fam}.png")
        draw_hero(fam).save(OUT / f"K2B-mask-hero-{fam}.png")
    for name, cols in FAMILIES.items():
        draw_chips(cols).save(OUT / f"chips-{name}.png")
    for p in sorted(OUT.glob("K2B-*.png")):
        w, h = Image.open(p).size
        print(f"{p.name}: {w}x{h}px = {w/S:.1f}x{h/S:.1f}mm ratio {w/h:.3f}")
    print("\n| 系統 | 枠 px | 枠比率 | Gemini 比率 | CROP で切れる側 | 切れる量 |")
    print("|---|---|---|---|---|---|")
    for fam, w, h, fr, name, r, where, cut in ratio_table():
        print(f"| {fam} | {w}×{h} | {fr} | {name} ({r}) | {where} | {cut}% |")
