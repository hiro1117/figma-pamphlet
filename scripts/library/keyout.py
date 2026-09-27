#!/usr/bin/env python3
"""単色背景(緑 #00FF00 系 / 白)で生成した前景 PNG/JPEG をキー抜きして実 alpha の PNG にする。

  .venv/bin/python scripts/library/keyout.py in.png out.png [--key auto|00FF00|FFFFFF] [--erode 1] [--feather 1] [--trim]
                                             [--crop L,T,R,B] [--clear-above Y]

方式(有彩色キー = 緑など):
  1. 「キー色が支配的な画素」(dom = G - max(R,B) など)を背景候補にする。明るさの違う緑(2 段の帯・島)もまとめて拾える
  2. 背景候補のうち外周から連結した領域 + 連結していない島(内部の穴・帯)を透明にする
  3. 境界画素の alpha は支配度から連続的に決め、despill(前景色の復元)で緑のにじみを取る
方式(無彩色キー = 白):
  外周から連結した「白に近い画素」だけを透明にする(内部の白いシャツは残す)
その後 erode(収縮)→ feather(ぼかし)→ trim。
Gemini 系は真の alpha を出さないため、この後処理が必須(計画書 5.1)。
"""
import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def border_color(im):
    a = np.asarray(im.convert("RGB"))
    edge = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    return "".join(f"{int(v):02X}" for v in np.median(edge, axis=0))


def hex2arr(h):
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


def flood_from_border(mask):
    """bool マスクのうち外周から連結した領域を True で返す(PIL floodfill を 2 値画像に適用)。"""
    h, w = mask.shape
    img = Image.fromarray((mask * 255).astype(np.uint8), "L")
    marker = 128
    step = max(8, min(w, h) // 64)
    seeds = [(x, 0) for x in range(0, w, step)] + [(x, h - 1) for x in range(0, w, step)] + \
            [(0, y) for y in range(0, h, step)] + [(w - 1, y) for y in range(0, h, step)]
    for sx, sy in seeds:
        if img.getpixel((sx, sy)) == 255:
            ImageDraw.floodfill(img, (sx, sy), marker, thresh=0)
    return np.asarray(img) == marker


def keyout(im, key_hex, erode, feather):
    rgb = np.asarray(im.convert("RGB")).astype(np.float32)
    key = hex2arr(key_hex)
    chromatic = (key.max() - key.min()) > 60
    if chromatic:
        dom = int(np.argmax(key)); others = [c for c in range(3) if c != dom]
        dominance = rgb[..., dom] - np.maximum(rgb[..., others[0]], rgb[..., others[1]])  # 背景 ≈ 150〜255、前景 ≈ ≤30
        g_lo, g_hi = 40.0, 140.0
        alpha = np.clip((g_hi - dominance) / (g_hi - g_lo), 0.0, 1.0)
        keylike = dominance > g_lo
        outside = flood_from_border(keylike)
        island = keylike & ~outside          # 外周に連結していない緑(帯・穴)も透明
        transparent = outside | island
        alpha = np.where(transparent, 0.0, alpha)
        # 境界帯: 透明領域の近傍 7px は連続 alpha、それ以外の前景は不透明
        near = np.asarray(Image.fromarray((transparent * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(15))) > 0
        alpha = np.where(near, alpha, 1.0)
        # despill: 半透明画素は 前景色×α + キー色×(1-α) とみなし前景色を復元
        band = near & (alpha > 0.02) & (alpha < 0.98)
        a3 = alpha[..., None]
        restored = (rgb - (1.0 - a3) * key) / np.maximum(a3, 0.05)
        rgb = np.where(band[..., None], np.clip(restored, 0, 255), rgb)
        # 不透明側に残る緑かぶり(支配度 > 0 の画素)は支配チャンネルを抑える
        spill = near & (alpha >= 0.98) & (dominance > 0)
        lim = np.maximum(rgb[..., others[0]], rgb[..., others[1]])
        rgb[..., dom] = np.where(spill, lim, rgb[..., dom])
    else:
        dist = np.sqrt(((rgb - key) ** 2).sum(axis=2))
        near_t, far_t = 40.0, 110.0
        alpha = np.clip((dist - near_t) / (far_t - near_t), 0.0, 1.0)
        outside = flood_from_border(dist < near_t)
        nearm = np.asarray(Image.fromarray((outside * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(7))) > 0
        alpha = np.where(nearm, alpha, 1.0)
        alpha = np.where(outside, 0.0, alpha)
    a = Image.fromarray((alpha * 255).astype(np.uint8), "L")
    if erode > 0:
        a = a.filter(ImageFilter.MinFilter(2 * erode + 1))
    if feather > 0:
        a = a.filter(ImageFilter.GaussianBlur(feather))
    out = Image.fromarray(rgb.astype(np.uint8), "RGB").convert("RGBA")
    out.putalpha(a)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--key", default="auto", help="キー色 hex または auto(外周の中央値)")
    ap.add_argument("--erode", type=int, default=1)
    ap.add_argument("--feather", type=float, default=0.8)
    ap.add_argument("--trim", action="store_true")
    ap.add_argument("--crop", help="L,T,R,B px を先に切り落とす(外周の線などを除く)")
    ap.add_argument("--clear-above", type=int, help="この y(px、crop 後)より上の alpha を 0 にする")
    ns = ap.parse_args()
    im = Image.open(ns.src)
    if ns.crop:
        L, T, R, B = (int(v) for v in ns.crop.split(","))
        im = im.crop((L, T, im.width - R, im.height - B))
    key = border_color(im) if ns.key == "auto" else ns.key.lstrip("#").upper()
    out = keyout(im, key, ns.erode, ns.feather)
    if ns.clear_above is not None:
        a = np.asarray(out.getchannel("A")).copy(); a[:ns.clear_above, :] = 0
        out.putalpha(Image.fromarray(a, "L"))
    if ns.trim:
        bbox = out.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
        if bbox:
            out = out.crop(bbox)
    out.save(ns.dst)
    a = np.asarray(out.getchannel("A"))
    print(f"{ns.dst}: key={key} {out.size[0]}x{out.size[1]} opaque={100*(a>250).mean():.1f}% semi={100*((a>4)&(a<=250)).mean():.1f}%")
