#!/usr/bin/env python3
"""自作のスタイル見本(幾何図形だけの人物図)を描く。生成 AI に「頭身・点目・ミトン手・単色ベタ・均一線」の作りを示すための参照画像。
参照ページやフリー素材は一切使わない(PIL の円・矩形・線だけ)。

  .venv/bin/python scripts/library/make_style_tile.py  → docs/library/masks/style-tile-person.png
"""
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[2] / "docs/library/masks/style-tile-person.png"
INK = (35, 24, 21)
SKIN = (251, 224, 200)
LW = 6  # 均一な線幅


def figure(d, cx, top, hair, top_col, bottom_col, shoe, arm_up=False):
    """4.5 頭身の立ち姿。頭=円、胴=角丸矩形、手足=太線+ミトン。"""
    H = 120  # 頭の直径
    # 頭
    d.ellipse([cx - H / 2, top, cx + H / 2, top + H], fill=SKIN, outline=INK, width=LW)
    # 髪(1 色の塊: 上半分の弧)
    d.chord([cx - H / 2, top, cx + H / 2, top + H], 190, 350, fill=hair, outline=INK, width=LW)
    d.rectangle([cx - H / 2 + LW, top + H * 0.28, cx - H / 2 + 26, top + H * 0.62], fill=hair)  # もみあげ
    d.rectangle([cx + H / 2 - 26, top + H * 0.28, cx + H / 2 - LW, top + H * 0.62], fill=hair)
    # 目=点、口=線 1 本、鼻なし
    for ex in (cx - 22, cx + 22):
        d.ellipse([ex - 5, top + 62, ex + 5, top + 72], fill=INK)
    d.arc([cx - 16, top + 70, cx + 16, top + 96], 20, 160, fill=INK, width=LW - 1)
    # 胴(角丸矩形)
    ty = top + H + 6
    d.rounded_rectangle([cx - 52, ty, cx + 52, ty + 150], radius=24, fill=top_col, outline=INK, width=LW)
    # 脚
    d.rounded_rectangle([cx - 46, ty + 140, cx + 46, ty + 270], radius=18, fill=bottom_col, outline=INK, width=LW)
    d.line([cx, ty + 190, cx, ty + 268], fill=INK, width=LW)
    # 靴
    for sx in (cx - 44, cx + 6):
        d.rounded_rectangle([sx, ty + 262, sx + 40, ty + 284], radius=10, fill=shoe, outline=INK, width=LW)
    # 腕(太線)+ミトンの手
    if arm_up:
        d.line([cx + 48, ty + 30, cx + 82, ty - 10], fill=INK, width=LW + 14)
        d.line([cx + 48, ty + 30, cx + 82, ty - 10], fill=top_col, width=LW + 2)
        d.ellipse([cx + 66, ty - 30, cx + 100, ty + 4], fill=SKIN, outline=INK, width=LW)
        # 受話器(単純な棒)
        d.rounded_rectangle([cx + 70, ty - 70, cx + 96, ty + 0], radius=12, fill=(255, 255, 255), outline=INK, width=LW)
    else:
        d.line([cx + 48, ty + 30, cx + 74, ty + 120], fill=INK, width=LW + 14)
        d.line([cx + 48, ty + 30, cx + 74, ty + 120], fill=top_col, width=LW + 2)
        d.ellipse([cx + 58, ty + 108, cx + 92, ty + 142], fill=SKIN, outline=INK, width=LW)
    d.line([cx - 48, ty + 30, cx - 74, ty + 120], fill=INK, width=LW + 14)
    d.line([cx - 48, ty + 30, cx - 74, ty + 120], fill=top_col, width=LW + 2)
    d.ellipse([cx - 92, ty + 108, cx - 58, ty + 142], fill=SKIN, outline=INK, width=LW)


if __name__ == "__main__":
    im = Image.new("RGB", (900, 700), (255, 255, 255))
    d = ImageDraw.Draw(im)
    figure(d, 230, 60, hair=(150, 120, 100), top_col=(246, 190, 209), bottom_col=(120, 110, 100), shoe=(200, 200, 200), arm_up=True)
    figure(d, 520, 60, hair=(80, 80, 90), top_col=(230, 220, 200), bottom_col=(60, 70, 90), shoe=(80, 60, 50))
    figure(d, 760, 90, hair=(235, 110, 165), top_col=(255, 255, 255), bottom_col=(235, 110, 165), shoe=(200, 200, 200))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    im.save(OUT)
    print(OUT, im.size)
