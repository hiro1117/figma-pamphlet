#!/usr/bin/env python3
"""レイアウトマスク(幾何図形のみ)と系統色チップを生成する。

- 出典: docs/prep/physical-size.md(表紙面 99×210mm、塗り足し 上/右 3mm、K2 ヒーロー = 表紙面の上 55〜60%)
- テンプレや完成見本のスクショは一切使わない(白/灰の矩形だけ)
- 文字は描かない(生成 AI の参照に渡すため)

出力: docs/library/masks/
  K2-mask-face.png  表紙面+塗り足し(102×213mm)全体。ヒーロー枠・塗り足し・下情報域・タイトル/CTA ゾーン
  K2-mask-hero.png  ヒーロー枠+塗り足しだけ(102×125mm)。生成画像と同じ範囲
  K1-mask-face.png  (任意)全面ビジュアル K1 用。タイトル帯・CTA ゾーンを無地で示す
  chips-<系統>.png  系統の色チップ(濃/淡/紙白/文字色)
"""
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[2] / "docs/library/masks"
S = 10  # px per mm(マスクの解像度。Figma の k=5.69 とは無関係)

# 物理寸法(mm)
FACE_W, FACE_H = 99.0, 210.0
BLEED = 3.0
HERO_RATIO = 0.581   # 122mm / 210mm → ヒーロー+塗り足し = 102×125mm(≈102:125)
HERO_H = round(FACE_H * HERO_RATIO)  # 122
FOLD_MARGIN = 8.0    # 折り線側(左・下)の余白
TRIM_MARGIN = 3.0    # 仕上がり端側の内側余白(塗り足しとは別)
HORIZON = 0.60       # 地平線帯の位置(ヒーロー上端から)

# 色(白/灰のみ)
C_IMAGE = (255, 255, 255)   # 絵が入る領域
C_BLEED = (200, 200, 200)   # 塗り足し域(断裁で消える)
C_INFO = (160, 160, 160)    # 下情報域(文字ゾーン、絵を入れない)
C_ZONE = (110, 110, 110)    # タイトル/CTA ゾーン
C_BAND = (235, 235, 235)    # 地平線帯(地域モチーフで覆う余地)
C_LINE = (60, 60, 60)


def mm(v):
    return int(round(v * S))


def draw_face(k1=False):
    # キャンバス = 表紙面 + 上/右塗り足し。原点 = 塗り足し込みの左上
    W, H = mm(FACE_W + BLEED), mm(FACE_H + BLEED)
    im = Image.new("RGB", (W, H), C_INFO)
    d = ImageDraw.Draw(im)
    top = mm(BLEED)  # 仕上がり上端の y
    hero_bottom = H if k1 else top + mm(HERO_H)
    # ヒーロー(塗り足し込み)
    d.rectangle([0, 0, W, hero_bottom], fill=C_IMAGE)
    # 地平線帯
    hero_h_mm = (FACE_H if k1 else HERO_H) + BLEED
    by = int(hero_h_mm * HORIZON * S)
    d.rectangle([0, by - mm(6), W, by + mm(6)], fill=C_BAND)
    # 塗り足し域(上・右)
    d.rectangle([0, 0, W, top], fill=C_BLEED)
    d.rectangle([W - mm(BLEED), 0, W, hero_bottom], fill=C_BLEED)
    # 仕上がり線・折り線(細線)
    d.rectangle([0, top, W - mm(BLEED), H], outline=C_LINE, width=2)
    if not k1:
        d.line([0, hero_bottom, W, hero_bottom], fill=C_LINE, width=2)
    # 文字ゾーン
    if k1:
        # K1: タイトル帯は上部、CTA は下部(いずれも絵の上に無地パネルで載る)
        d.rectangle([mm(FOLD_MARGIN), top + mm(14), mm(FOLD_MARGIN + 0.7 * FACE_W), top + mm(56)], fill=C_ZONE)
        d.rectangle([mm(40), H - mm(FOLD_MARGIN + 34), W - mm(BLEED + TRIM_MARGIN), H - mm(FOLD_MARGIN)], fill=C_ZONE)
    else:
        # K2: 下情報域(hero_bottom〜下端)にタイトル(左)と CTA(右下)
        d.rectangle([mm(FOLD_MARGIN), hero_bottom + mm(8), mm(FOLD_MARGIN + 0.7 * FACE_W), hero_bottom + mm(46)], fill=C_ZONE)
        d.rectangle([mm(40), H - mm(FOLD_MARGIN + 30), W - mm(BLEED + TRIM_MARGIN), H - mm(FOLD_MARGIN)], fill=C_ZONE)
    return im


def draw_hero():
    W, H = mm(FACE_W + BLEED), mm(HERO_H + BLEED)
    im = Image.new("RGB", (W, H), C_IMAGE)
    d = ImageDraw.Draw(im)
    by = int((HERO_H + BLEED) * HORIZON * S)
    d.rectangle([0, by - mm(6), W, by + mm(6)], fill=C_BAND)
    d.rectangle([0, 0, W, mm(BLEED)], fill=C_BLEED)
    d.rectangle([W - mm(BLEED), 0, W, H], fill=C_BLEED)
    d.rectangle([0, mm(BLEED), W - mm(BLEED), H], outline=C_LINE, width=2)
    return im


# docs/prep/colors.md の実測値
FAMILIES = {
    "aitoma": ["#EB6EA5", "#F6BED1", "#FFD8E3", "#FFFFFF", "#000000"],
    "nachikatsuura": ["#1B98D0", "#76C1E3", "#E3F7FF", "#FFFFFF", "#000000"],
    "noboribetsu": ["#D7835F", "#F9F2DC", "#FFF9B3", "#FFFFFF", "#513A1E"],
    "mitt": ["#254F99", "#258FC2", "#143747", "#FAEF50", "#FFFFFF", "#231815"],
}


def draw_chips(colors):
    n = len(colors)
    im = Image.new("RGB", (n * 200, 200), (255, 255, 255))
    d = ImageDraw.Draw(im)
    for i, c in enumerate(colors):
        d.rectangle([i * 200, 0, (i + 1) * 200, 200], fill=c, outline=(128, 128, 128), width=2)
    return im


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    draw_face().save(OUT / "K2-mask-face.png")
    draw_hero().save(OUT / "K2-mask-hero.png")
    draw_face(k1=True).save(OUT / "K1-mask-face.png")
    for name, cols in FAMILIES.items():
        draw_chips(cols).save(OUT / f"chips-{name}.png")
    for p in sorted(OUT.glob("*.png")):
        w, h = Image.open(p).size
        print(f"{p.name}: {w}x{h}px = {w/S:.0f}x{h/S:.0f}mm ratio {w/h:.3f}")
