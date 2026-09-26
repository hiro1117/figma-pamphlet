"""B.1 設計: 表紙スクショに K2 ヒーロー枠・折り線・安全域・新規プレースホルダを重ねる。
座標はすべてフレームローカル(px)。18:2 はキャンバス上で 180° 回転しているので先に正立化する。
"""
from PIL import Image, ImageDraw, ImageFont
import os

ROOT = '/Users/hirokihashimoto/dev/work/cicac/figma-pamphlet/docs/reports/B1-shots'
PAD = 60  # 塗り足し(17px)を描くためのキャンバス余白
K = 5.69
B = 17    # 3mm
T = 46    # 8mm
FX1, FX2, FY = 563.7, 1127.3, 1196.0
FACE = (1127.3, 0, 1691, 1196)          # 表紙面
HERO_VIS = (1127.3, 0, 1691, 694)      # 見える部分(58.0%)
HERO = (1127.3, -17, 1708, 694)        # 塗り足し込み 580.7×711
MOTIF = (1127.3, 260, 1708, 480)
PERSON = (1462, 330, 1674, 640)
VEHICLE = (1145, 440, 1445, 640)
BAND = (1144.3, 640, 1708, 694)
BG = (1127.3, -17, 1708, 1196)

SERIES = {
    '18-2': {'title': '18:2 あいとま', 'rot': True,
             'ai': (1176, 1126, 1662, 1148),
             'legacy': [((1229, 141, 1603, 465), '#サービスロゴ置き場 残す'), ((1249, 378, 1583, 690), '#地区名ロゴ置き場 残す')],
             'moved': []},
    '20-2': {'title': '20:2 那智勝浦', 'rot': False,
             'ai': (1176, 1120, 1662, 1142),
             'legacy': [((1370, 564.8, 1457, 645.9), '固定ロゴ(表紙中央) 残す/要判断'), ((1202, 168, 1625, 505), 'ブロック:タイトル 残す')],
             'moved': [((1173, 661, 1661.9, 1117.9), (1173, 691, 1661.9, 1147.9), 'ブロック:ご登録・ご予約 +30px')]},
    '21-2': {'title': '21:2 登別', 'rot': False,
             'ai': (1176, 1097, 1662, 1119),
             'legacy': [((1272, 595, 1456, 701), 'イラスト:車 隠す'), ((1421, 516, 1587, 734), '#マスコット置き場 隠す(要判断)'), ((1204, 247, 1615, 490), '#サービスロゴ置き場 → タイトルへ移動(層)')],
             'moved': []},
    '24-2': {'title': '24:2 MITT', 'rot': False,
             'ai': (301, 1126, 916, 1148),
             'legacy': [((1127, 607, 1627.2, 1216), 'イラスト:表紙(人物群) 隠す'), ((1127, 944, 1535, 1216), '#車両写真置き場 隠す+縮小')],
             'moved': [((1155, 377, 1664.4, 555.7), (1155, 777, 1664.4, 955.7), 'Group 283(QR/まずは登録) +400px')]},
}

def font(sz):
    for p in ['/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc', '/System/Library/Fonts/Hiragino Sans GB.ttc',
              '/Library/Fonts/Arial Unicode.ttf', '/System/Library/Fonts/Supplemental/Arial Unicode.ttf']:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()

def P(x, y):
    return (x + PAD, y + PAD)

def rect(d, box, color, width=3, dash=None):
    x0, y0, x1, y1 = box
    if dash is None:
        d.rectangle([P(x0, y0), P(x1, y1)], outline=color, width=width)
    else:
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            dline(d, (ax, ay), (bx, by), color, width, dash)

def dline(d, a, b, color, width, dash):
    ax, ay = a; bx, by = b
    L = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
    n = int(L // (dash * 2)) + 1
    for i in range(n):
        t0 = min(1, (i * 2 * dash) / L); t1 = min(1, (i * 2 * dash + dash) / L)
        d.line([P(ax + (bx - ax) * t0, ay + (by - ay) * t0), P(ax + (bx - ax) * t1, ay + (by - ay) * t1)], fill=color, width=width)

def band(ov, box, rgba):
    x0, y0, x1, y1 = box
    ImageDraw.Draw(ov).rectangle([P(x0, y0), P(x1, y1)], fill=rgba)

def label(d, xy, text, color, sz=22, bg=(255, 255, 255, 220)):
    f = font(sz)
    x, y = P(*xy)
    w = d.textlength(text, font=f)
    d.rectangle([x - 4, y - 2, x + w + 4, y + sz + 6], fill=bg)
    d.text((x, y), text, fill=color, font=f)

def build(fr, cfg):
    im = Image.open(f'{ROOT}/orig_{fr}.png').convert('RGB')
    if cfg['rot']:
        im = im.rotate(180)
    W, H = im.size
    canvas = Image.new('RGBA', (W + 2 * PAD, H + 2 * PAD), (245, 245, 245, 255))
    canvas.paste(im, (PAD, PAD))
    ov = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    # 安全域: 折り線±46(文字) と ±17(装飾)
    for x in (FX1, FX2):
        band(ov, (x - T, 0, x + T, H), (255, 0, 0, 28))
        band(ov, (x - B, 0, x + B, H), (255, 0, 0, 45))
    band(ov, (0, FY - T, W, FY + T), (255, 0, 0, 28))
    band(ov, (0, FY - B, W, FY + B), (255, 0, 0, 45))
    # 仕上がり端の外側 17px(塗り足し域)
    band(ov, (-B, -B, W + B, 0), (0, 120, 255, 40)); band(ov, (W, -B, W + B, H + B), (0, 120, 255, 40))
    band(ov, (-B, H, W + B, H + B), (0, 120, 255, 40)); band(ov, (-B, -B, 0, H + B), (0, 120, 255, 40))
    # ヒーロー枠の面(半透明)
    band(ov, HERO, (0, 170, 0, 40))
    canvas = Image.alpha_composite(canvas, ov)
    d = ImageDraw.Draw(canvas)
    # 折り線
    for x in (FX1, FX2):
        dline(d, (x, -B), (x, H + B), (220, 0, 0), 3, 18)
    dline(d, (-B, FY), (W + B, FY), (220, 0, 0), 3, 18)
    # 仕上がり枠
    rect(d, (0, 0, W, H), (0, 90, 200), 3)
    # 表紙面
    rect(d, FACE, (255, 140, 0), 4)
    # ヒーロー枠(見える部分=実線、塗り足し込み=破線)
    rect(d, HERO_VIS, (0, 150, 0), 6)
    rect(d, HERO, (0, 150, 0), 4, dash=14)
    # 新規プレースホルダ
    rect(d, MOTIF, (150, 0, 200), 4, dash=10)
    rect(d, PERSON, (0, 0, 220), 4, dash=10)
    rect(d, VEHICLE, (0, 0, 220), 4, dash=10)
    rect(d, BAND, (200, 120, 0), 4, dash=8)
    rect(d, cfg['ai'], (0, 0, 0), 3, dash=6)
    for box, name in cfg['legacy']:
        rect(d, box, (255, 0, 120), 4, dash=6)
        label(d, (box[0] + 6, box[1] + 6), name, (200, 0, 90), 20)
    for src, dst, name in cfg['moved']:
        rect(d, src, (120, 120, 120), 3, dash=6)
        rect(d, dst, (0, 160, 160), 4, dash=6)
        label(d, (dst[0] + 6, dst[3] - 30), name, (0, 120, 120), 20)
    # ラベル
    label(d, (1135, -52), '#キービジュアル K2 (1127.3,-17) 580.7×711 / 見える部分 563.7×694 = 58.0%', (0, 110, 0), 20)
    label(d, (1135, 265), '#地域モチーフ y260-480', (120, 0, 160), 20)
    label(d, (1466, 334), '#人物', (0, 0, 180), 20)
    label(d, (1150, 444), '#車両', (0, 0, 180), 20)
    label(d, (1150, 644), '#帯(非表示)', (160, 90, 0), 20)
    label(d, (cfg['ai'][0] + 4, cfg['ai'][1] - 26), '#AI表記(非表示)', (0, 0, 0), 18)
    label(d, (1133, 1150), '折り線 y=1196 / 文字±46 装飾±17', (200, 0, 0), 20)
    label(d, (430, 1212), '折り線 x=563.7', (200, 0, 0), 20)
    label(d, (900, 1212), '折り線 x=1127.3', (200, 0, 0), 20)
    label(d, (20, 20), f"{cfg['title']}  (フレームローカル座標、18:2 は正立化済み)", (0, 0, 0), 28)
    # 全体(50%)と表紙面 1:1
    full = canvas.convert('RGB')
    full.resize((full.width // 2, full.height // 2), Image.LANCZOS).save(f'{ROOT}/overlay_{fr}_full.png')
    x0, y0 = int(FACE[0]) - 60 + PAD, -60 + PAD
    x1, y1 = int(FACE[2]) + 60 + PAD, int(FACE[3]) + 60 + PAD
    crop = full.crop((x0, max(0, y0), min(full.width, x1), min(full.height, y1)))
    crop.save(f'{ROOT}/overlay_{fr}_cover.png')
    return full.size, crop.size

if __name__ == '__main__':
    for fr, cfg in SERIES.items():
        print(fr, build(fr, cfg))
